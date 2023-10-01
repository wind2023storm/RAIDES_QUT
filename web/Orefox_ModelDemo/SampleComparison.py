#####  Import Libraries  ####
import os
#Disable Tensorflow warnings
#Comment to enable
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

import random
import numpy
import numpy.matlib
from numpy.linalg import norm
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
from math import sqrt

import glob
import imageio.v2 as iio

#####  Function  #####
#This function loads all images from a given directory and returns an numpy array of the images
def loadImagesFromDirectory(filepath):
    #Open an array
    images = []
    
    #Cycle through filepath and append all images to images array
    for image_path in glob.glob(filepath):
        image = iio.imread(image_path)
        images.append(image)
    
    images = numpy.array(images).astype(numpy.float32)[:, :, :, :3] / 255
    # images_array = numpy.array(images).astype(numpy.float32)
    # print(images_array.shape)
    #images = images.astype(numpy.float32)
    #images = images / 255
    #return numpy array of images
    return images

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

def cosineSimilarity(embeddingX, embeddingY):
    sum = 0
    sumX = 0
    sumY = 0
    for x, y in zip(embeddingX, embeddingY):
        sumX += x * x
        sumY += y * y
        sum += x * y
        
    sim = sum/(((sumX))*(sqrt(sumY)))
    return sim

def cosineSimilarityNump(embeddingX, embeddingY):
    sim = numpy.dot(embeddingX, embeddingY)/(norm(embeddingX)*norm(embeddingY))
    return sim


def runModel():
    #####  Load Positive Samples  ####
    #5km
    positive_samples_5km = loadImagesFromDirectory('Orefox_ModelDemo/positive_samples/5km/*.png')

    #10km
    positive_samples_10km = loadImagesFromDirectory('Orefox_ModelDemo/positive_samples/10km/*.png')

    #20km
    positive_samples_20km = loadImagesFromDirectory('Orefox_ModelDemo/positive_samples/20km/*.png')

    #Load selected sample
    selected_sample = loadImagesFromDirectory('Orefox_ModelDemo/selected_sample/*.png')


    #####  Reload Model Architechure
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

    #Create DCNN encoding on the pair
    input_a = keras.Input((256, 256, 3), name = 'InputA')
    input_b = keras.Input((256, 256, 3), name = 'InputB')

    embedding_a = base_network(input_a)
    embedding_b = base_network(input_b)

    #Calculate distance
    distance = layers.Lambda(euclidean_distance, output_shape=eucl_dist_output_shape)([embedding_a, embedding_b])

    #Feed distance into siamese network
    siamese_network = keras.Model([input_a, input_b], distance)
    keras.utils.plot_model(siamese_network, show_shapes = True)


    #####  Load Pretrained Weights Into Model
    #Load the weights
    siamese_network.load_weights("Orefox_ModelDemo/training_1/checkPoint.ckpt")


    #####  Create Embeddings  #####
    demoSamples = numpy.append(selected_sample, positive_samples_10km, axis = 0)

    demoEmbeddings = base_network.predict(demoSamples, verbose = False)
    Demo1 = demoEmbeddings[0]
    #For demonstration purposes change this value
    #from 1 to 6, they corespond to the 10km positive samples
    #1 is identical to the sample loaded
    Demo2 = demoEmbeddings[1]

    #This is the final similarity
    return cosineSimilarityNump(Demo1, Demo2)

#
# def main():
#     similarityResult = runModel()
#     print(similarityResult)
#
# if __name__ == "__main__":
#     main()

























