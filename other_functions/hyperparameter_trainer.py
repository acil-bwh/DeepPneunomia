import pickle
import h5py as f
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.applications import InceptionResNetV2
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.applications import Xception
from tensorflow.keras import layers
from tensorflow.keras import models
import other_functions.logs as logs



def crear_modelo(input_shape, backbone_name, frozen_backbone_prop, pix = 512):
    if backbone_name == 'IncResNet':
        backbone = InceptionResNetV2(weights="imagenet", include_top=False, input_shape=input_shape)
    elif backbone_name == 'EffNet3':
        backbone = EfficientNetB3(weights="imagenet", include_top=False, input_shape=input_shape)
    elif backbone_name == 'Xception':
        backbone = Xception(weights="imagenet", include_top=False, input_shape=input_shape)
    model = models.Sequential()
    model.add(layers.Conv2D(3,3,padding="same", input_shape=(pix,pix,1), activation='elu', name = 'conv_inicial'))
    model.add(backbone)
    model.add(layers.GlobalMaxPooling2D(name="general_max_pooling"))
    model.add(layers.Dropout(0.2, name="dropout_out_1"))
    model.add(layers.Dense(768, activation="elu"))
    model.add(layers.Dense(128, activation="elu"))
    model.add(layers.Dropout(0.2, name="dropout_out_2"))
    model.add(layers.Dense(32, activation="elu"))
    model.add(layers.Dense(3, activation="softmax", name="fc_out"))
    # Freeze proportion of backbone
    fine_tune_at = int(len(backbone.layers)*frozen_backbone_prop)
    backbone.trainable = True
    for layer in backbone.layers[:fine_tune_at]:
        layer.trainable = False
    return model


def generate_index(trainprop = 0.8):
    with open("./index/ht_train_subset", "rb") as fp:
        index = pickle.load(fp)
    np.random.shuffle(index)
    idtrain = index[:int(len(index)*trainprop)]
    idtest = index[int(len(index)*trainprop):]
    return idtrain, idtest


def add_to_csv(data, path):
    df = pd.read_csv(path)
    df.loc[len(df.index)] = data
    df.to_csv(path, index = False)


def train(backbone, frozen_prop, lr, mask, dataframe_path, evaluation_type, external_dataframe_path = ''):
    batch = 8
    epoch = 100
    pix = 512

    # DATAFRAME
    df = f.File(dataframe_path, "r")
    for key in df.keys():
        globals()[key] = df[key]

    # DATA GENERATORS
    idtrain, idtest = generate_index()

    from image_functions.data_generator import DataGenerator as gen
    traingen = gen(X_train, y_train, batch, pix, idtrain, mask)
    testgen = gen(X_train, y_train, batch, pix, idtest, mask)

    # MODEL
    input_shape = (pix,pix,3)
    model = crear_modelo(input_shape, backbone, frozen_prop)    

    # Compile
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate = lr), 
                    loss = 'categorical_crossentropy',
                    metrics = ['BinaryAccuracy', 'Precision', 'AUC'])

    # CALLBACK
    callb = [logs.early_stop(5)]

    # TRAIN
    history = model.fit(traingen, 
                        validation_data = testgen,
                        batch_size = batch,
                        callbacks = callb,
                        epochs = epoch,
                        shuffle = True)
    

    # MÉTRICS
    characteristics = [backbone, frozen_prop, batch, lr, mask, pix]

    if evaluation_type == 'internal':
        import evaluation_functions.prediction as pred
        import evaluation_functions.metrics_and_plots as met
    
        with open("./index/ht_val_subset", "rb") as fp:
                val_index = pickle.load(fp)

        # Ver resultados sobre el test
        y_pred = pred.prediction_tensor(model, X_train, val_index, mask)
        y_real = y_train[val_index]

        metricas, _ = met.metricas_dict(y_real, y_pred)
        add_to_csv(characteristics + list(metricas.values()), './results/hyperparameter_tuning/internal.csv')
        metricas['f1_score_mean']= (metricas['f1_score_0']+metricas['f1_score_1']+metricas['f1_score_2'])/3
        return metricas['f1_score_mean']

    if evaluation_type == 'external':
        import evaluation_functions.external_evaluation as ex_ev
        images_names, prediction = ex_ev.prediction_tensor(model, external_dataframe_path, mask = mask)
        df = ex_ev.results_dataframe(images_names, prediction)
        results = ex_ev.calculate_metrics(df, external_dataframe_path)
        add_to_csv(characteristics[:-1] + 
                    [max(history.history['val_auc'])] + 
                    list(results[0].values()), 
                    './results/hyperparameter_tuning/external.csv')
        return results[0]['auc_']


