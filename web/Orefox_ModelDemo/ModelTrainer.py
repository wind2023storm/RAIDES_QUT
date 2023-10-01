#####  Import Libraries  ####
import os
#Disable Tensorflow warnings
#Comment to enable
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

import random
import numpy
import numpy.matlib
import scipy
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras import backend as K

from sklearn import decomposition
from sklearn import discriminant_analysis
from sklearn import datasets
from sklearn.manifold import TSNE
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.ensemble import RandomForestClassifier

import glob
import imageio.v2 as iio

#####  Functions  #####
#This function loads all images from a given directory and returns an numpy array of the images
def loadImagesFromDirectory(filepath):
    #Open an array
    images = []
    
    #Cycle through filepath and append all images to images array
    for image_path in glob.glob(filepath):
        image = iio.imread(image_path)
        images.append(image)
    
    images = numpy.array(images).astype(numpy.float32)[:, :, :, :3] / 255
    #images = images.astype(numpy.float32)
    #images = images / 255
    #return numpy array of images
    return images

#Takes an array of images and an int for the number of copies and an augmentation layer
#Returns ground truth and augmented images
def augmentImages(imagesToAugment, numberOfAugmentedCopies, augmentationLayer):
    uniqueImages = imagesToAugment.shape[0]
    augmentedImages = []
    gnd = []
    for gnd_truth in range(uniqueImages):
        for sample_index in range(numberOfAugmentedCopies):
            #Add new ground truth to gnd
            gnd.append(gnd_truth)
            #Add augmented image to augmented_positive_samples
            augmented_image = augmentationLayer(tf.expand_dims(imagesToAugment[gnd_truth, :, :, :], 0), True)
            augmentedImages.append(augmented_image[0])
            
    return augmentedImages, gnd

##################################################

#####Helper Functions#####
#generates siamese pairs for training
def GetSiameseData(imgs, labels, batch_size):

    image_a = numpy.zeros((batch_size, numpy.shape(imgs)[1], numpy.shape(imgs)[2], numpy.shape(imgs)[3]));
    image_b = numpy.zeros((batch_size, numpy.shape(imgs)[1], numpy.shape(imgs)[2], numpy.shape(imgs)[3]));
    label = numpy.zeros(batch_size);
    
    for i in range(batch_size):
        
        if (i % 2 == 0):
            idx1 = random.randint(0, len(imgs) - 1)
            idx2 = random.randint(0, len(imgs) - 1)
            l = 1
            while (labels[idx1] != labels[idx2]):
                idx2 = random.randint(0, len(imgs) - 1)            
                
        else:
            idx1 = random.randint(0, len(imgs) - 1)
            idx2 = random.randint(0, len(imgs) - 1)
            l = 0
            while (labels[idx1] == labels[idx2]):
                idx2 = random.randint(0, len(imgs) - 1)

        image_a[i, :, :, :] = imgs[idx1,:,:,:]
        image_b[i, :, :, :] = imgs[idx2,:,:,:]
        label[i] = l

    return [image_a, image_b], label

#Generator object for using the above function
def PairGenerator(imgs, labels, batch_size):
    while True:
        [image_a, image_b], label = GetSiameseData(imgs, labels, batch_size)
        yield [image_a, image_b], label
        
#Used to create a convolutional block in VGG style
def conv_block(inputs, filters, spatial_dropout = 0.0, max_pool = True):
    
    x = layers.Conv2D(filters=filters, kernel_size=(3,3), padding='same', activation='relu')(inputs)
    x = layers.Conv2D(filters=filters, kernel_size=(3,3), padding='same', activation=None)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    if (spatial_dropout > 0.0):
        x = layers.SpatialDropout2D(spatial_dropout)(x)
    if (max_pool == True):
        x = layers.MaxPool2D(pool_size=(2, 2))(x)
    
    return x

#Used to create a fully connected block in VGG stle
def fc_block(inputs, size, dropout):
    x = layers.Dense(size, activation=None)(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    if (dropout > 0.0):
        x = layers.Dropout(dropout)(x)
    
    return x

#Creates a VGGnet model using conv_block and fc_block
def vgg_net(inputs, filters, fc, spatial_dropout = 0.0, dropout = 0.0):
    
    x = inputs
    for idx,i in enumerate(filters):
        x = conv_block(x, i, spatial_dropout, not (idx==len(filters) - 1))
    
    x = layers.Flatten()(x)
    
    for i in fc:
        x = fc_block(x, i, dropout)
        
    return x

#Calculates euclidian distance between points
def euclidean_distance(vects):
    x, y = vects
    x = K.l2_normalize(x, axis=1)
    y = K.l2_normalize(y, axis=1)
    sum_square = K.sum(K.square(x - y), axis=1, keepdims=True)
    return K.sqrt(K.maximum(sum_square, K.epsilon()))

def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)

#Calculates the contrastive loss
def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    square_pred = K.square(y_pred)
    margin_square = K.square(K.maximum(margin - y_pred, 0))
    return K.mean(y_true * square_pred + (1 - y_true) * margin_square)

#####End of helper functions#####

#####  Data Loading  ####
#Positives
#5km
positive_samples_5km = loadImagesFromDirectory('positive_samples/5km/*.png')

#10km
positive_samples_10km = loadImagesFromDirectory('positive_samples/10km/*.png')

#20km
positive_samples_20km = loadImagesFromDirectory('positive_samples/20km/*.png')

#concatinate samples
positiveSamples = numpy.concatenate((positive_samples_5km, positive_samples_10km, positive_samples_20km))


#Negatives
negative_samples = loadImagesFromDirectory('negative_samples/*.png')



#####  Augmentation  #####
#Create augmentation layer
data_augmentation = keras.Sequential([
    layers.RandomRotation(factor = 1, fill_mode = 'nearest'),
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomTranslation(height_factor = (-0.025, 0.025), width_factor = (-0.025, 0.025))
    ])

#Apply augmentation
augmented_positive_samples, gnd = augmentImages(positiveSamples, 20, data_augmentation)


#####  Prepare Data For Model  #####
gnd = numpy.array(gnd)
augmented_positive_samples = numpy.array(augmented_positive_samples)
print("Ground Truth Shape:")
print(gnd.shape)
print("Augmented Positive Samples Shape:")
print(augmented_positive_samples.shape)
print("Negative Samples Shape:")
print(negative_samples.shape)

#Split augmented data into training and testing sets
test_frames = numpy.array(()).astype('int')
for i in numpy.unique(gnd):    
    indexes = numpy.where(gnd == i)[0]
    count = len(indexes);
    f = numpy.random.randint(count, size=6)
    test_frames = numpy.append(test_frames, indexes[f])
    
train_gnd = gnd
train_fea = augmented_positive_samples
train_fea = numpy.delete(train_fea, test_frames, 0)
train_gnd = numpy.delete(train_gnd, test_frames, 0)
test_fea = augmented_positive_samples[test_frames, :]
test_gnd = gnd[test_frames]

#####  Prepare The Model  #####
#use DCNN to reduce number of dimentions to embedding size
embedding_size = 32
#Create dummy imput with dimentions matiching sample size
dummy_input = keras.Input((256, 256, 3))
#Create backbone DCNN
base_network = vgg_net(dummy_input, [4, 8, 16, 32, 64], [256], 0.2, 0)
#Create final dense layer of embedding size
embedding_layer = layers.Dense(embedding_size, activation = None)(base_network)

#Create model
base_network = keras.Model(dummy_input, embedding_layer, name = 'SiameseBranch')
#Print model summary for sanity
base_network.summary()


#Create DCNN encoding on the pair
input_a = keras.Input((256, 256, 3), name = 'InputA')
input_b = keras.Input((256, 256, 3), name = 'InputB')

embedding_a = base_network(input_a)
embedding_b = base_network(input_b)

#Calculate distance
distance = layers.Lambda(euclidean_distance, output_shape = eucl_dist_output_shape)([embedding_a, embedding_b])

#Feed distance into siamese network
siamese_network = keras.Model([input_a, input_b], distance)
keras.utils.plot_model(siamese_network, show_shapes = True)

#Summarise the siamese network
siamese_network.summary()

#Calculate distance
distance = layers.Lambda(euclidean_distance, output_shape = eucl_dist_output_shape)([embedding_a, embedding_b])

#Feed distance into siamese network
siamese_network = keras.Model([input_a, input_b], distance)
keras.utils.plot_model(siamese_network, show_shapes = True)

#Summarise the siamese network
siamese_network.summary()


#Setup checkpoints
checkpoint_filepath = 'training_1/checkPoint.ckpt'
model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath = checkpoint_filepath,
    save_weights_only=True,
    verbose=1)

siamese_network.compile(loss = contrastive_loss, optimizer = keras.optimizers.Adam())

batch_size = 128
training_gen = PairGenerator(train_fea, train_gnd, batch_size)

siamese_test_x, siamese_test_y = GetSiameseData(train_fea, train_gnd, 300)
siamese_network.fit(training_gen,
                    steps_per_epoch= 50,
                    epochs= 10,
                    validation_data= (siamese_test_x, siamese_test_y),
                    callbacks= model_checkpoint_callback)




