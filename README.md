# Steps to follow:

1. Clone the repository

```
git clone https://github.com/acil-bwh/DeepPneumonia.git
```
2. Instal requirements.txt
```
cd DeepPneumonia
pip install -r requirements.txt
```
3. Download datasets and models from (...). 

4. Save all datasets in the ./data repository folder and all the models in the ./model repository folder

5. Execute apply_model giving your images folder as an argument. This will save a dataframe with all images names and its predictions in ./your_images_folder_path/pneumonia_classification_model_results.csv
```
python apply_model.py -p ./your_images_folder_path
```
6. Execute any of the other execute_* to test the repository
```
python execute_hyperpar_tuning.py
python execute_training.py
python execute_validation.py
python execute_external_validation.py
python execute_explainability.py
```
Definitive models are saved  as **./models/pneumonia_classification_mask_model.h5** and **./models/pneumonia_classification_model.h5**. All scripts that require a model are prepared to be applied using **./models/pneumonia_classification_model.h5**, but this can be changed using arg *-m pneumonia_classification_mask_model*.

# DATA
## Principal dataset
### Original Datasets
Data was extracted from three different datasets: 

- NIH Chest X-ray: 112,120 images of 30,805 patients (https://arxiv.org/abs/1705.02315) 

- Chexpert: 224,316 images of 65,240 patients (https://arxiv.org/abs/1901.07031) 

- PadChest: 160,000 images of 67,000 patients (https://arxiv.org/abs/1901.07441) 

### Exclusion criteria 
From all these images some were excluded: 

- Those with two or more external devices (cables, leads, tubes, pacemakers...) over the lung field 

- Those with extreme angular rotations or positioning 

- Those with lack of pulmonary fields (image truncation) 

### Curation 
Five 5 trained readers reviewed the images diagnosed with pneumonia and classified them under 3 categories: exclusion, mild, and moderate-severe. A subset of normal labeled images from the three cohorts was reviewed for quality control and used 

The classification criteria were the following: 

- No Pneumonia: no opacities or reticular pattern in the lung parenchyma  

- Mild Disease: opacities or reticular pattern covering less than 25% (Grade 1-2) 

- Moderate-Severe Disease: opacities or reticular pattern covering more than 25% (Grade 3 – 5) 

Label consensus was reached by using the Dawid-Skene method19 
 
### Resulting dataset 
The resulting dataset (***./data/training_validation_dataset.h5***) had 59439 training images and 14859 validation images. This dataset was divided in X_train, y_train, X_val and y_val. The label proportion in the dataset was 47% of no pneumonia images, 35% of mild disease images and 17% of moderate-severe disease images.

For optimal results training dataset (X_train and y_train) was balanced removing some no pneumonia and mild disease images. The resulting *training dataset* had 32088 with 33% proportion of each class. *Validation dataset* (X_val and y_val) remained the same. 

In order to perform hyperparameter tuning a subset of images was generated selecting some index from X_train and y_train. This subset had 1000 images of each class for training and another 1000 images of each class for testing. So, there was an hyperparameter tuning training dataset of 3000 images and an hyperparameter tuning validation dataset of 3000 images.

For the dataset selection a pickle with each index has been saved in ***./index***.

- Hyperparameter tuninig training dataset: ***./index/ht_train_subset***
    
- Hyperparameter tuning validation dataset: ***./index/ht_val_subset***

- Training dataset: ***./index/train***

## External testing and validation dataset
A dataset with external images was also prepared to test how good were the models generalizing. The external dataset was made with the following datasets.  

- **Pediatric** (https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia): This dataset is divided into train and test folders. All images from train and test have been taken (5840). Pneumonia images are 4265, and they are divided in viral images (1493) and bacterial images (2772). There are 1341 no pneumonia images. Al pneumonia images were labeled the same in order to evaluate the model.  

- **COVID** (https://www.kaggle.com/datasets/prashant268/chest-xray-covid19-pneumonia): This dataset has 4575 images, divided in three folders: normal images (1525), COVID images (1525) and pneumonia images (1525). All images labeled as COVID were also labeled as pneumonia in order to evaluate the model, so we had 3050 pneumonia images vs 1525 no pneumonia images 

- **Mask COVID** (https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database ): This is a database with 21165 images with its masks. Images are divided in four folders: normal (10192), lung opacity (6012), COVID (3616) and viral pneumonia (1345). All non-normal images were labeled as pneumonia, so we had 10973 pneumonia images vs 10192 normal images.  

All images from these three datasets were joined, however, some images were duplicated. We deleted images that had the exact same name as other, also ImageHash package (https://kaggle.com/code/kretes/duplicate-and-similar-images) was used to find duplicated images with different name (hash size of 8). The resulting dataset had 26793 images, with 14908 pneumonia images and 11885 non-pneumonia images. There were 2752 images labelled as bacterial, 1615 images labelled as viral, 4390 images labelled as COVID and 6151 images labelled as lung opacity. 

This **external dataset** was split in two: 20% of the dataset was used as *external testing dataset* for testing how good was each model in generalizing its results (***./data/external_dataset/test***), and the remaining 80% was used as *external validation dataset* for real validation (***./data/external_dataset/val***).


# PREPROCESSING
***./image_functions/mask_funct.py*** -> ***./image_functions/prepare_img_fun.py*** -> ***./image_functions/data_generator.py***

All images were transformed using local contrast enhancement using adaptative histogram equalization, noise was removed after this using median filter and a global contrast stretching was perform using percentile adjustment (***./image_functions/prepare_image_fun.equalize()***). 

Since different approaches were used to achieve the best results, in some cases after initial preprocessing a mask was applied over the chest x-ray images, to segment the whole thorax using ***./models/thorax_segmentation_model.h5*** (***./image_functions/mask_funct.apply_mask()***).  

After applying or not this segmentation images were all transformed into (512, 512, 1) shape and they were normalized using z-score (***./prepare_img_fun.get_prepared_img()***). 


# MODEL DEVELOPMENT
To develop pneumonia diagnosis model three different pre-trained models were used as backbone, and their results were compared, to choose the best option: Xception, InceptionResNetV2 or EfficientNetB3. 

These models had an input shape with 3 channels, so an initial 2D convolution was added to transform (512,512,1) shape into (512,512,3). Last fully connected layer from the backbone was removed and after the last layer a global max pooling was added. Finally, four dense layers and two dropouts were added, in order to reach 3 outputs (***execute_training.create_model()***). 

For fine-tuning different approaches were tested (***execute_hyperpar_tuning.py***), it was tried to froze the whole backbone and then different proportions of it were unfrozen until the whole backbone was unfrozen. Results from different approaches were compared to reach the best result. 

## Hyperparameters
Some hyperparameters were static and we did not try any different approach with them. Batch size was always 8, mainly because of GPU memory capacity. Input shape of (512,512,1) was maintained. The train-validation proportion was always 0.8-0.2. Adam optimizer was always used, same as categorical cross entropy loss. 

On the other hand, these other parameters were tuned. As it has been said, different backbones were tried. Also, since backbones were pretrained, we tried to freeze different proportions of each, but all trainings started from pre-trained weights. Learning rate was also tuned, varying from 1e-5 to 1e-3. Finally, as it has been mentioned, some models were trained with masked thorax and others were trained with the whole chest x-ray image.


# EVALUATION TOOLS
***./evaluation_functions/evaluation.py***

***./evaluation_functions/external_evaluation.py***

***./evaluation_functions/metrics_and_plots.py***

***./evaluation_functions/prediction.py***

Apart from the automatic metrics from keras (training metrics and model.evaluate()), we developed our own metrcis. We used model.predict(), over our testing and validation data and compared ground truth with prediction results (***./evaluation_functions/prediction.py***). With these results we calculated precision, recall, accuracy, f1 score and AUC for each label, and also different posible thresholds (younden, maximum f1 score, maximum precision+recall, cut between precision and recall). Moreover we generate a AUC, precision-recall and f1 score plots for each label (***./evaluation_functions/metrics_and_plots.py***).

So we have: 
- **Training results**: results over the training dataset and the testing dataset (saved in: ***./results/train***)

- **Evaluate results**: results calculated using model.evaluate()

    - If they are applied over the testing dataset they will be saved in ***./results/testing/evaluation.csv***: these results will be the same as those reported in Trainig results (val_)

    - If they are applied over the validation dataset they will be saved in ***./results/validation/evaluation.csv***

- **Prediction results**: results calculated using model.predict()

    - If they are applied over the testing dataset they will be saved in ***./results/testing/evaluation.csv***: these results will be different from those reported in Training results, one metric for each label.
        
    - If they are applied over the validation dataset they will be saved in ***./results/validation/evaluation.csv***: one metric for each label


# TRAININGS
In each training, training data was split into train and test folders with a proportion of 0.8/0.2. For each training, best results in each metric (loss, BinaryAccuracy, Precision and AUC) are saved in ***./results/train/train_max.csv***, and all training data are saved in ***./results/train/each_model_train/model_name_data.csv***

## Hyperparameter tuning 
***./other_functions/hyperparameter_trainer.py*** -> ***execute_hyperpar_tuning.py***

For hyperparameter tuning mango tool was used (https://github.com/ARM-software/mango). The hyperparameter tuning train dataset was used for training and the hyperparameter tuning validation dataset was used for validation. All the above mentioned hyperparameters were tuned, and 139 different combinations were tried. Each combination of parameters was trained and tested 3 times. We use the mean f1 score of all labels over the validation dataset as each training outcome, and the mean between the three trainings, as combination outcome. 

Each predict results over the hyperparameter tuning validation dataset are saved in ***./results/hyperparameter_tuning/internal.csv***, also, the results extracted from mango are saved in ***./results/hyperparameter_tuning/results_internal.json***

In a second round we selected the hyperparameters that obtained the best results (Xception backbone, frozen proportion between 0.3 and 0.8, learning rate between 1e-5 and 5e-4 and both with mask and without) and we did another tuning with 30 combinations. In this new tuning we used as outcome metric pneumonia vs non-pneumonia AUC over the external testing dataset, in order to find the best parameters for generalization.

Each training results over the hyperparameter tuning validation dataset are saved in ***./results/hyperparameter_tuning/external.csv***, also, the results extracted from mango are saved in ***./results/hyperparameter_tuning/results_external.json***

- ***execute_hyperpar_tuning.py*** takes many arguments that can be checked in the code, but if it is executed as it is, it will execute a hyperparameter tuning using *hyperparameter tuning training dataset* (X_train and y_train using ht_train_subset index) and metrics will be calculated using internal validation (X_train and y_train using ht_val_subset index). 
```
python execute_hyperparameter_tuning.py
```
- If a external validation wants to be made it is just necesary to add -ev external, and the metrics will be calculated using *external testing dataset* (***./data/external_dataset/test***)
```
python execute_hyperparameter_tuning.py -ev external
```

## Definitive models 
***execute_training.py***

After selecting the best combinations of hyperparameters, definitive models were trained over the whole training dataset (***./index/train***). Seven trainings were made with each combination of parameters selected. They were tested over the test subset and the external test subset.

- ***execute_training.py*** takes many arguments that can be checked in the code (all hyperparameters can be changed: backbone, frozen proportion, batch, learning rate, mask...). If it is executed as it is, it will execute a training using *training dataset* (X_train and y_train using train index)


# VALIDATION
***execute_validation.py***

***execute_external_validation.py***

Validation was made over the validation dataset (X_val and y_val from ***./data/training_validation_dataset.h5***) and over the external validation dataset (***external_dataset/val***). AUC, f1 score, sensibility, specificity, precision, recall and accuracy were used as metrics. In the validation dataset, all labels discrimination capacity was tested, however in the external validation dataset, it is just posible to test the pneumonia discrimination capacity, that is why external validation has its own scripts (***./evaluation_functions/external_evaluation.py*** -> ***execute_external_validation.py***)

The folder where the external validation images are located requires a dataframe containing a column called **img_name** with all the names of the images and a column called **normal** that indicates whether the image is non-pathological (1) or presents pneumonia (0). When ***execute_external_validation.py*** is executed, prediction results are saved in ***./results/external_validation/model_results_model_name_val_results*** or ***./results/external_validation/model_results_model_name_test_results***, and the results comparation over different models are saved in ***.results/external_validation/results_comparation_test.csv*** and in ***./results/external_validation/results_comparation_val.csv*** depending on which of the test or train folders the validation has been applied. Also, if plots are calculated they will be saved in ***.results/external_validation/model_name***

- ***execute_validation.py*** takes many arguments that can be checked in the code, but if it is executed as it is, it will execute an internal validation over *validation dataset* (X_val and y_val) using **./models/pneumonia_classification_model.h5**. 
```
python execute_validation.py
```
- If the validation wants to be made with the masked model is just necesary to add *-m pneumonia_classification_mask_model*.
```
python execute_validation.py -m pneumonia_classification_mask_model
```

- ***execute_external_validation.py*** takes many arguments that can be checked in the code, but if it is executed as it is, it will execute an external validation over *external validation dataset* (***./data/external_dataset/val***) using **./models/pneumonia_classification_model.h5**. 
```
python execute_external_validation.py
```
- If the validation wants to be made with the masked model is just necesary to add *-m pneumonia_classification_mask_model*.
```
python execute_external_validation.py -m pneumonia_classification_mask_model
```
- It is possible to validate the model using ***./data/external_dataset/test***. It is also possible to add plots to the validation, that will be saved in ***./results/external_validation/model_name***
```
# apply using external test dataset
python execute_external_validation.py -vt test 
# generate plots and save them
python execute_external_validation.py -sp True 
```
- It is possible to validate the model using any other external dataset but it has to have the following extructure *./external_folder_dataframe/val/*. The *val* folder need to have all the images and a dataframe named data.csv with a column called *img_name* with all the names of the images and a column called *normal* that indicates whether the image is non-pathological (1) or presents pneumonia (0). Prediction values for each image will be saved in a dataframe in ***./results/external_dataset/model_results_model_name_val_results***
```
python execute_external_validation.py -p ./external_folder_dataframe
# the script is going to search for val folder inside the folder referenced
```

# EXPLAINABILITY
***./explainability/copy_old_model.py*** -> ***./explainability/grad_cam.py*** -> ***./explainabiligy/mask_quantification.py*** -> ***execute_explainability.py***

To explain the model, we used GradCAM. Since the last convolutional layer of the trained model was inside the backbone we need to recreate a new model with trained weights to extract the last convolutional layer out of the backbone (***./explainability/copy_old_model.py***). After recreating the model, GradCAM was applied and a heatmap was generated (***./explainability/grad_cam.py***) and with this we checked how much of the model attention was placed inside the thorax. To do this, the heatmap of an image was binarized, using a threshold of 0.1. Also, a thorax segmentation over the image was applied. The matching points between the binarized heatmap and the mask were the model attention points inside the thorax, and those points from the binarized heatmap not matching with the mask were attention points outside the thorax. We measured the model attention points outside the thorax related to the whole area outside the thorax (***./explainability/mask_quantification.extract_proportion()***).  

This method was applied over the 5359 images from the external test dataset (***./data/external_validation/test***) for the best models selected (with and without mask). With this method we tried to find out if those models trained without mask were paying attention to other auxiliary information from outside the thorax, like devices, x ray projection and other potential confusion factors. 

When ***execute_explainability.py*** is applied, all heatmaps are saved in ***./results/heatmaps/model_name/*** and proportions are saved in ***./results/heatmaps/model_name/proportions*** as a pickle.

- ***execute_explainability.py*** takes many arguments that can be checked in the code, but if it is executed as it is, it will generate a heatmap for each image in the *external test dataset* (***./data/external_dataset/test***) using **./models/pneumonia_classification_model.h5**. 
```
python execute_explainability.py
```
- If the validation wants to be made with the masked model is just necesary to add -m pneumonia_classification_mask_model.
```
python execute_explainability.py -m pneumonia_classification_mask_model
```
- It is possible to generate heatmaps and explainability using any image folder, just adding the arg -im ./path, and it is possible also to modify the binarization threshold
```
# using other folder with images
python execute_explainability.py -im path/with/images
# using the mask model and with other binarization threshold
python execute_explainability.py -m pneumonia_classification_mask_model -th 0.05
```