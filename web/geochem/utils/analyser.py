"""Holds a class for analysing data."""

import logging
import os
from sys import getsizeof
import time
from typing import Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from scipy.cluster.hierarchy import linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import FactorAnalysis
from sklearn.decomposition import PCA
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras import layers
import xgboost as xgb

from . import exceptions
from . import data_utils

class Analyser:
    """Holds methods for analysing data from a datacleaner.
    
    Attributes:
        datacleaner: A DataCleaner that holds the data to perform analysis on.
        logger: The logger from datacleaner to log events.
        kmeans: An instance of sklearn.cluster.KMeans.
        rf: An instance of sklearn.ensemble.RandomForestRegressor.
        pca: An instance of sklearn.decomposition.PCA.
        fa: An instance of sklearn.decomposition.FactorAnalysis.
        hca: Holds the return of linkage from scipy HCA.
        stats: Holds preliminary stats of the data.
    """

    # Initialise these variables now
    kmeans = None
    rf = None
    pca = None
    fa = None
    hca = None
    stats = None
    summaries = None
    correlations = None
    adaboost = None
    xgboost = None
    nn = None
    model_filename = None
    history_filename = None

    def __init__(self, dataframe, project, options: dict):
        """Create an Analyser.

        Parameters
        ----------
            dataframe : Dataframe
                Dataset to be analysed 
            project: Project
                Project in which analysis will be performed
            options: dict
                Analysis options selected by user
        """
        self.dataframe = dataframe
        self.options = options
        self.project = project

        # Get the logger as a member of this class to make logging calls
        # less complicated

        # Make TensorFlow log to file
        if not os.path.isdir("logs/"):
            os.mkdir("logs/")
        handler = logging.FileHandler(
                f'logs/{datetime.now().strftime("%d-%m-%Y_%H_%M_%S")}_tf.log')
        tf.get_logger().addHandler(handler)

    def run(self):
        # This dict below is just an easy way to call a function for every option in the supplied dict
        # the order of the keys determines the other in which the methods are activated (IMPORTANT!)
        analysis_methods = {
            'pca': self.pca_handler,
            'correlationCoefficients': self.correlation_coefficients,
            'simpleDatasetStats': self.get_dataset_stats,
            'summariseFloatColumn': self.get_summaries,
            'KMeans': self.k_means_handler,
            'randomForest': self.random_forest_handler,
            'neuralNetwork': self.nn_regression_handler,
            'hierarchicalClustering': self.hierarchical_clustering,
            'functionalAnalysis': self.factor_analysis,
            'adaBoost': self.ada_boost_handler,
            'xgBoost': self.xg_boost_handler
        }
        print("methods selected by user", self.options)
        if not self.options:
            raise Exception("Data Analysis Option is needed")
        # Run the methods in order of method keys
        try:
            for method in analysis_methods.keys():

                if method in self.options:
                    kwargs = self.options.get(method)
                    analysis_methods[method](**kwargs)
        except Exception as e:
            raise Exception(e, method)
    def get_dataset_stats(self) -> float:
        """Gets overall stats of data.

        Dictionary is saved as the following set of (key, value) pairs:
            num_features: The number of columns in the dataset.
            num_entries: The number of rows, not including header.
            num_empty: The number of empty data entries.
            empty_cells_per_row: A dictionary of rows: num_empty pairs where
              the value is specifically the number of empty rows in that row.
            empty_cells_per_column: Same as above but column wise.
            data_size: The return of getsizeof(data).

        Returns:
            Time taken to complete this method.
        """
        # Get the start time
        try:
            start_time = time.time()

            stats = {}

            # Store number of columns and rows in the data
            stats['num_features'] = self.dataframe.shape[1]
            stats['num_entries'] = self.dataframe.shape[0]

            # Count empty cells 
            empty_coords = np.where(pd.isnull(self.dataframe))
            stats['num_empty'] = len(empty_coords[0])

            # Initialise all rows to 0
            rows = {}
            for row in range(self.dataframe.shape[0]):
                rows[row] = 0

            # Now count the number of empty cells per row
            for row in empty_coords[0]:
                rows[row] += 1

            stats['empty_cells_per_row'] = rows

            # Now do the same for columns
            columns = {}
            for column in range(self.dataframe.shape[1]):
                columns[column] = 0

            for column in empty_coords[1]:
                columns[column] += 1

            stats['empty_cells_per_column'] = columns

            # Size of data
            stats['data_size'] = getsizeof(self.dataframe)

            # Log success

            self.stats = stats
            return time.time() - start_time
        except Exception as e:
            error_message = str(e)
            raise Exception("Simple Dataset Stats :"+error_message)

    def get_summaries(self):
        """
        Gets the descriptions of each column in a {column: summary} dict.
        """
        try:
            result = {}
            for column in self.dataframe.columns:
                result[column] = self.dataframe[column].describe()
            self.summaries = result
            return result
        except Exception as e:
            error_message = str(e)
            raise Exception("Summarize Columns : "+error_message)

    def k_means_handler(self, **options):
        """

        Parameters
        ----------
        options : dict
            'randomState': []
            'maxIter': int
            'data': dataframe
            'updateModel': bool
            'train': bool
            'KValue': int
        """
        if 'train' in options:
            randomState = int(options.get('randomState'))
            maxIter = int(options.get('maxIter'))
            KValue = int(options.get('KValue'))
            self.k_means(KValue, random_state=randomState, max_iter=maxIter)
        else:
            update_model = options.get('updateModel')
            self.predict_from_kmeans(self.dataframe, update_model=update_model)

    def k_means(self, k: int, random_state: int=10,
            max_iter: int=300) -> float:
        """Computes the k means algorithm on the data.

        Parameters
        ----------
            k: int
                The number of clusters to assign the data to.
            random_state: int
                Assign an int to ensure reproducible results.
            max_iter: int
                The maximum number of iterations to run when fitting.
        Returns
        -------
            Time taken to compute the algorithm
        """

        # Get start time
        start_time = time.time()

        # Log initial call to begin k means
        
        # Filtering data
        subset_X = data_utils.check_list_datatype(
            data_set=self.dataframe, 
            given_list=self.dataframe.columns,
            data_type=np.float32)

        # Perform k means, save results and k
        self.kmeans = KMeans(n_clusters=int(k), random_state=random_state,
                max_iter=max_iter).fit(self.dataframe[subset_X])
        
        self.k = k
        
        # Log success

        return time.time() - start_time

    def get_kmeans_summary_string(self) -> str:
        """Returns a string summary of a k means analysis."""

        # Check that there is kmeans to represent
        if self.kmeans is None:
            raise Exception("K means has not been trained yet.")

        return str(self.kmeans)

    def predict_from_kmeans(self, data: pd.DataFrame, 
            update_model: bool=True) -> Tuple[list, float]:
        """Predicts cluster classification with an already trained model.

        Parameters
        ----------
            data: Dataframe
                Dataframe of entries to predict clusters for.
            update_model: bool
                If True, changes the model saved to account for 
                this new data too.
        Returns
        -------
            A tuple, with first element being the cluster index for each entry 
            of the input data and the time taken for the function to compute. 
            Second element is time taken.
        """

        # Get start time
        start_time = time.time()

        # Log beginning of prediction

        # Check that there is kmeans to plot on
        if self.kmeans is None:
            raise Exception("K means has not been trained yet")

        # Filtering data
        subset_X = data_utils.check_list_datatype(
            data_set=data, 
            given_list=data.columns,
            data_type=np.float32)
        
        if update_model:
            classifications = self.kmeans.fit_predict(data[subset_X].values)
        else:
            classifications = self.kmeans.predict(data[subset_X].values)

        # Log success

        return (classifications, time.time() - start_time)

    def random_forest_handler(self, **options):
        """

        Parameters
        ----------
        options : dict
            'targetColumn': str
            'subsetX': []
            'data_split': float
            'data': dataframe
            'train': bool
        """
        if 'train' in options:
            target = options.get('target')
            subsetX = options.get('columns')
            dataSplit = float(options.get('dataSplit'))
            self.random_forest(target_column=target, subset_X=subsetX, data_split=dataSplit)
        else:
            self.predict_random_forest(self.dataframe)        
        
    def random_forest(self, target_column: str, subset_X: list=None,
            data_split: float=0.2, random_state: int=10,
            n_estimators: int=100, max_features='auto', 
            criterion='squared_error', max_depth=None, bootstrap=True,
            min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, 
            max_samples=None, ccp_alpha=0.0, min_impurity_decrease=0.0,
            min_weight_fraction_leaf=0.0, oob_score=False) -> float:
        """ Performs a random forest regression.

        For information on the hyperparameters used, they directly interface
        with sklearn's attributes.

        Parameters
        ----------
            target_column: str
                The header for the column to target.
            subset_X: list
                A list of column headers to use only, instead of all of
                the data. None will use all of the data.
            data_split: float
                The proportion of the data to use in the testing set.
            random_state: int
                Set to an int for reproducible results.

        Returns
        -------
            The predictions made on the testing set after training.
            The actual values of the testing set.
            Time taken to complete.
        """
        # Get start time
        start_time = time.time()
        
        # Log beginning of rf analysis

        # Checking target column and column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                            data_set=self.dataframe,
                                            target_column=target_column)

        data = data_utils.remove_nan_rows(self.dataframe)
        
        # Get the target column and data without the target column
        y = data[target_column].values

        self.rf_subset_X = subset_X

        # Save this for the importance plotter
        self.rf_target_column = target_column

        X = data[subset_X].values
        self.rf_num_predictors = len(subset_X)
        
        if not 0 < data_split < 1:
            raise exceptions.DataSplitOutOfBoundsError(data_split) 

        train_X, test_X, train_y, test_y = train_test_split(X, y, 
                test_size=data_split, random_state=random_state)
        # Create and fit the random forest
        self.rf = RandomForestRegressor(
                random_state=random_state,
                n_estimators=n_estimators,
                max_features=max_features,
                criterion=criterion,
                max_depth=max_depth,
                bootstrap=bootstrap,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_leaf_nodes=max_leaf_nodes,
                max_samples=max_samples,
                ccp_alpha=ccp_alpha,
                min_impurity_decrease=min_impurity_decrease,
                min_weight_fraction_leaf=min_weight_fraction_leaf,
                oob_score=oob_score)

        self.rf.fit(train_X, train_y)

        test_predictions = self.rf.predict(test_X)
        
        # Save these as class attribute for later visualisations
        self.rf_test_predictions = test_predictions
        self.rf_test_y = test_y

        # Log success

        return test_predictions, test_y, time.time() - start_time

    def predict_random_forest(self, 
            data: pd.DataFrame) -> Tuple[list, float]:
        """Makes a prediction off of data with a pretrained random forest.

        Parameters
        ----------
            data: Dataframe
                A dataframe of entries to predict.

        Returns
        -------
            A 2-tuple of predictions, time taken.
        """
        # Get start time
        start_time = time.time()

        # Log start

        # Check that there is an rf to predict on
        if self.rf is None:
            raise Exception("Random forest has not been trained yet.")
        


        # Filtering data
        subset_X = data_utils.check_list_datatype(
            data_set=data, 
            given_list=data.columns,
            data_type=np.float32)

        data = data_utils.remove_nan_rows(data)

        # Log success

        return (self.rf.predict(data[subset_X].values), time.time() - start_time)

    def nn_regression_handler(self, **options):
        """
        Parameters
        ----------
        options : dict
            'subset_X': []
            'target_column': int
            'data_split': dataframe
            'filename': bool
            'epochs': bool
            'ranom_state': int
            'data':
            'train':
        """
        if 'train' in options:
            target = options.get('target')
            subsetX = options.get('columns')
            randomState = int(options.get('randomState'))
            epochs = int(options.get('epochs'))
            dataSplit = float(options.get('dataSplit'))

            self.dense_nn_regression(target_column=target, subset_X=subsetX, data_split=dataSplit,
                epochs=epochs, random_state=randomState)
        else:
            target = options.get('target')
            self.predict_from_nn(self.dataframe, target_column=target, model_path=None)    

    def dense_nn_regression(self, target_column: str, subset_X: list=None,
            data_split: float=0.8, filename: str=None, hist_filename: str=None,
            epochs: int=5, random_state: int=10, verbosity: int=2) -> (float):
        """Uses a simple dense neural network to perform a regression.

        Parameters
        ----------
            subset_X: list
                The columns to use in the model. If None the model will
                use all column in the data.
            target_column: str
                The label of the column to predict.
            data_split: float
                The proportion of data that should be used for the
                training and testing sets. The training testing split will be
                one quarter of this value.
            filename: str
                None doesn't save model.
            epochs: int
                The number of epochs to train with.
            random_state: int
                Set to int for reproducible data splits.
            verbosity: int
                Set verbosity for tf.keras.Model.fit

        Returns
        -------
            Time taken to complete this method.
        """
        # Log start

        # Get start time
        start_time = time.time()
        # Checking target column and column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                            data_set=self.dataframe,
                                            target_column=target_column)
        
        # add the target column if not present in the subset
        if target_column not in subset_X:
            subset_X += [target_column]

        data = self.dataframe[subset_X]

        if not 0 < data_split < 1:
            raise exceptions.DataSplitOutOfBoundsError(data_split)

        # Split data into training and testing sets
        train_data, test_data = train_test_split(data, train_size=data_split,
                random_state=random_state)

        # Split the target out of each set
        train_X = train_data.copy()
        test_X = test_data.copy()
        train_y = train_X.pop(target_column)
        test_y = test_X.pop(target_column)

        # Create a normalisation layer to normalise the data first
        normaliser = tf.keras.layers.experimental.preprocessing.Normalization()
        normaliser.adapt(np.array(train_X))

        # Define the model
        model = tf.keras.Sequential([
            normaliser,
            layers.Dense(64, activation='relu'),
            layers.Dense(128, activation='relu'),
            layers.Dense(1)
        ])

        # Compile the model with standard inputs
        model.compile(loss='mean_absolute_error', 
                optimizer=tf.keras.optimizers.Adam())

        # Train the model
        history = model.fit(train_X, train_y, validation_split=0.25, 
                epochs=epochs, verbose=verbosity)

        self.dense_nn = history.history

        # Log success
        
        if filename is not None:
            model.save(filename)
            self.model_filename = filename

        if hist_filename is not None:
            self.save_history_nn(hist_filename)
            self.history_filename = hist_filename

        # Save these as class attribute for later visualisations
        self.nn_test_predictions = model.predict(test_X)
        self.nn_test_y = test_y

        self.nn_params = {
            'n_layers': 3,
            'n_filters': (64,128,1),
            'activation': 'relu',
            'loss': 'mae',
            'epochs': epochs,
            'random_state': random_state
        }

        self.nn = model
        
        return time.time() - start_time

    def save_history_nn(self, filename: str) -> None:
        """Saves the history variable to a file (named filename)."""
 
        hist_df = pd.DataFrame(self.dense_nn)
        with open(filename, mode='w') as f:
            hist_df.to_csv(f)

    def predict_from_nn(self, data: pd.DataFrame, target_column: str,
            model_path: str) -> Tuple[list, list]:
        """Makes predictions from a neural network.
        
        Parameters
        ----------
            data: DataFrame
                dataset on which predictions will be made
            target_column: str
            model_path: str

        Returns
        -------
            predictions: 
            loss: List[int] or int
                Measure of inaccuracy of model predictions
        """

        if target_column not in self.dataframe.columns:
            raise Exception("Target column is not a column header.")
        elif self.dataframe[target_column].dtypes == 'object':
            raise TypeError("Please choose column with numerical data")

        if model_path == None and self.nn == None:
            raise Exception("Neural network has not been trained")
        elif self.nn != None:
            model = self.nn
        else:
            model = tf.keras.models.load_model(model_path)

        subset_X = data_utils.check_list_datatype(
            data_set=data, 
            given_list=data.columns,
            data_type=np.float32)
        
        X = data[subset_X].copy()
        y = X.pop(target_column)

        loss = model.evaluate(X, y)
        predictions = model.predict(X)
        return predictions, loss

    def pca_handler(self, **options):
        """
        Parameters
        ----------
        options : dict
            'subset_X': []
            'target_column': int
            'data_split': dataframe
            'filename': bool
            'epochs': bool
            'ranom_state': int
            'data':
            'train':
        """
        target = options.get('target')
        subsetX = options.get('columns')
        normalise = True if options.get('normalise') else False
        self.pca_sk(subset_X=subsetX, normalise_data=normalise, target_column=target)

    def pca_sk(self, subset_X: list=None, 
            normalise_data: bool=True, n_components: int=None,
            target_column: str=None, save_transform_name: str=None,
            svd_solver: str='auto', tol: float=0.0, iterated_power: str='auto',
            whiten: bool=False, random_state: int=10) -> float:
        """Create and fit a dataset to a PCA.

        For information on the hyperparameters used, they directly interface
        with sklearn's attributes.

        Parameters
        ----------
            subset_X: list
                A list of column headers to use in model. None will use
                all columns in the dataframe.
            normalise_data: bool
                Whether or not to normalise the data first.
            n_components: int
                As in sickit, (0, 1) will give a proportion of
                variance explained, < n (n features) will give that number of
                principal components.
            target_column: str
                If None, PCA will be done on every column. If
                a column is specified, then that column will not be included
                in the PCA. Note if subset_X is specified, this arg will not be
                used, and the PCA will be performed on subset_X.
            save_transform_name: str
                If the transformed data is to be saved, this
                arg specifies the filename.

        Returns
        -------
            Time taken to complete this method.
        """

        # Get start time
        start_time = time.time()

        # Log start
        
        # Drop the target column if necessary
        if subset_X is None:
            # Check data to remove categorical and target columns
            subset_X = data_utils.check_analyser(given_list=subset_X,
                                        data_set=self.dataframe,
                                        target_column=target_column)
        else:
            # Check to remove categorical columns
            subset_X = data_utils.check_analyser(given_list=subset_X,
                                        data_set=self.dataframe)
            
        data = self.dataframe[subset_X]
        
        # Simplified the code
        # Creates a copy with a scaled version
        if normalise_data:
            scaled = pd.DataFrame(MinMaxScaler().fit_transform(data))
        else:
            scaled = data

        self.pca = PCA(
                    n_components=n_components,
                    svd_solver=svd_solver,
                    tol=tol,
                    iterated_power=iterated_power,
                    whiten=whiten,
                    random_state=random_state)
        
        self.pca.fit(pd.DataFrame(scaled))

        # Log success

        # Save transformed data if necessary
        if save_transform_name is not None:
            transformed_data = self.pca.transform(data)
            transformed_data.to_csv(save_transform_name)

        return (time.time() - start_time)

    def factor_analysis(self, **options) -> pd.DataFrame:
        """Performs a factor analysis on the data.

        Parameters
        ----------
        options : dict
            'normalise_data': bool
            'random_state': int

        Returns
        -------
            The dataframe transformed into the latent space.    
        """
        # Log start

        random_state = int(options.get('randomState'))
        normalise_data = True if options.get('normalise') else False


        # Filtering data
        subset_X = data_utils.check_list_datatype(
            data_set=self.dataframe, 
            given_list=self.dataframe.columns,
            data_type=np.float32)
        
        if normalise_data:
            scaled = MinMaxScaler().fit_transform(
                self.dataframe[subset_X])
        else:
            scaled = self.dataframe[subset_X]
            
        self.fa = FactorAnalysis(random_state=random_state)

        new_data = self.fa.fit_transform(scaled)

        return new_data

    def hierarchical_clustering(self, **options) -> float:
        """Performs a hierarchical clustering on the data.

        Parameters
        ----------
            options : dict
                'transpose': bool
                'normalise': int
                'subset_X': list
                    Specifies the columns to use in the algorithm. None will
                    use all columns in the dataframe.

        Returns
        -------
            Time taken to complete method.
        """
        subset_X = options.get('columns')
        method = 'ward'
        metric = 'euclidean'

        # Get start time
        start_time = time.time()

        # Log start

        # Checking column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                        data_set=self.dataframe)
        
        data = data_utils.remove_nan_rows(self.dataframe[subset_X])

        # Normalise if necessary
        if options.get('normalise'):
            data = MinMaxScaler().fit_transform(data)
        
        # Transpose if necessary
        if options.get('transpose'):
            self.hca_subset_X = subset_X
            data = data.T
        else:
            self.hca_subset_X = self.dataframe.index
        self.hca = linkage(data, method=method, metric=metric)
        # Save hyperparams
        self.hca_hyperparams = {'method': method, 'metric': metric}

        # Log success

        return time.time() - start_time

    def correlation_coefficients(self, **options) -> float:
        """Calculates various correlation coefficients for the data.

        Parameters
        ----------
            options : dict
                'subset_X': list 
                    Specifies the columns to use in the algorithm. None will
                    use all columns in the dataframe.

        Returns
        -------
            Time taken to complete method.
        """

        subset_X = options.get('columns')

        # Get start time
        start_time = time.time()

        # Log start
        
         # Checking column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                        data_set=self.dataframe)
        
        data = self.dataframe[subset_X]
        self.cc_subset_X = subset_X
        
        pearson = data.corr(method='pearson')
        kendall = data.corr(method="kendall")
        spearman = data.corr(method="spearman")

        self.correlations = {
            'pearson': pearson,
            'kendall': kendall,
            'spearman': spearman
        }

        # Log success
        
        return time.time() - start_time

    def ada_boost_handler(self, **options):
        target = options.get('target')
        subsetX = options.get('columns')
        randomState = int(options.get('randomState'))

        self.ada_boost(target_column=target, subset_X=subsetX, random_state=randomState)

    def ada_boost(self, target_column: str, subset_X: list=None,
            random_state: int=10, data_split: float=0.8, 
            base_estimator=None, n_estimators=50, learning_rate=1.0,
            loss='linear') -> float:
        """Creates and fits an AdaBoost regressor.

        Parameters
        ----------
            target_column: str
                The name of the column to target.
            subset_X: list
                A list of columns to use as predictors. None will use
                the entire dataset with the target column dropped.
            random_state: int
                Set the random state in sklearn.
            data_split: float
                Split between testing and training dataset

        Returns
        -------
            Predictions made on the testing set.
            The actual values of the testing set.
            Time taken to complete function.
        """

        # Start time
        start_time = time.time()
        
        # Checking target column and column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                            data_set=self.dataframe,
                                            target_column=target_column)

        self.adaboost = AdaBoostRegressor(
                base_estimator=base_estimator,
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                loss=loss,
                random_state=random_state)

        data = data_utils.remove_nan_rows(self.dataframe)

        # Get the target column and data without the target column
        y = data[target_column]

        self.adaboost_subset_X = subset_X

        # Save this for the importance plotter
        self.ada_target_column = target_column

        X = data[subset_X]
        self.adaboost_num_predictors = len(subset_X)
        
        if not 0 < data_split < 1:
            raise exceptions.DataSplitOutOfBoundsError(data_split) 

        train_X, test_X, train_y, test_y = train_test_split(X, y, 
                train_size=data_split, random_state=random_state)


        # Fit the training data        
        self.adaboost.fit(X=train_X, y=train_y)

        test_predictions = self.adaboost.predict(test_X)

        # Save these as class attribute for later visualisations
        self.ada_test_predictions = test_predictions
        self.ada_test_y = test_y

        # Log success

        return test_predictions, test_y, time.time() - start_time

    def xg_boost_handler(self, **options):
        target = options.get('target')
        subsetX = options.get('columns')
        randomState = int(options.get('randomState'))

        self.xg_boost(target_column=target, subset_X=subsetX, random_state=randomState)

    def xg_boost(self, target_column: str, subset_X: list=None,
            random_state: int=10, data_split: float=0.8,
            objective='reg:squarederror', learning_rate=0.3, gamma=0,
            base_score=0.5, booster='gbtree', tree_method='auto',
            n_estimators=100, colsample_bytree=1, colsample_bylevel=1,
            colsample_bynode=1, importance_type='gain', 
            monotone_constraints='()', interaction_constraints='',
            max_delta_step=0, max_depth=6, min_child_weight=1):
        """Trains and tests an XG Boost decision tree on the data.

        Parameters
        ----------
            target_column: str
                The name of the column to target.
            subset_X: list
                A list of columns to use as predictors. None will use
                the entire dataset with the target column dropped.
            random_state: int
                Set the random state in sklearn.

        Returns
        -------
            Predictions made on the testing set.
            The actual values of the testing set.
            Time taken to complete function.
        """

        start_time = time.time()

        # Checking target column and column names in subset_X
        subset_X = data_utils.check_analyser(given_list=subset_X,
                                            data_set=self.dataframe,
                                            target_column=target_column)
        
        self.xgboost = xgb.XGBRegressor(
                objective=objective,
                learning_rate=learning_rate,
                gamma=gamma,
                base_score=base_score,
                booster=booster,
                tree_method=tree_method,
                n_estimators=n_estimators,
                random_state=random_state,
                colsample_bytree=colsample_bytree,
                colsample_bylevel=colsample_bylevel,
                colsample_bynode=colsample_bynode,
                importance_type=importance_type,
                interaction_constraints=interaction_constraints,
                monotone_constraints=monotone_constraints,
                max_delta_step=max_delta_step,
                max_depth=max_depth,
                min_child_weight=min_child_weight)

        # Get the target column and data without the target column
        y = self.dataframe[target_column]

        self.xgboost_subset_X = subset_X

        # Save this for the importance plotter
        self.xgboost_target_column = target_column

        # Get Data
        X = self.dataframe[subset_X]
        self.xgboost_num_predictors = len(subset_X)
        
        if not 0 < data_split < 1:
            raise exceptions.DataSplitOutOfBoundsError(data_split) 

        train_X, test_X, train_y, test_y = train_test_split(X, y, 
                train_size=data_split, random_state=random_state)

        # Fit the training data        
        self.xgboost.fit(X=train_X, y=train_y)

        test_predictions = self.xgboost.predict(test_X)

        # Save these as class attribute for later visualisations
        self.xgboost_test_predictions = test_predictions
        self.xgboost_test_y = test_y

        # Log success

        return test_predictions, test_y, time.time() - start_time
