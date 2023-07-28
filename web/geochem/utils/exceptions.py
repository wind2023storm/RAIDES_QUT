import textwrap

class ModelNotTrainedError(Exception):
    
    def __init__(self, model_name: str):
        """Exception thrown when a model is selected to make predictions before being trained
        
        Parameters
	    ----------
            model_name : str
                Name of model on which exception was thrown
        """

        self.message = f'Error. {model_name} has not been trained.'

        self.message += textwrap.dedent('''
                An attempt was made to access a model that has not been trained 
                yet. Please ensure that before generating results, plots or 
                reports, that the necessary models have been trained as 
                required.''')

        super().__init__(self.message)


class FeatureCountDifferenceError(ValueError):

    def __init__(self, trained_model_features, new_data):
        """Error thrown when a model is trained on a dataset with a different number of features to a dataset on which it is selected to make predictions
        
        Parameters
        ----------
            trained_model_features : Dataframe
                Features on which trained model has been trained
            new_data: Dataframe
                Features of new dataset on which predictions are attempting to be made
	    """

        self.message = 'Error. '

        # Number of feature in new data
        self.message += \
                f'Number of features in the new data is {new_data.shape[0]}. '

        # Number of features in trained model
        num_features = len(trained_model_features)
        self.message += \
                f'Number of features in trained model is {num_features}. '

        self.message += \
            textwrap.dedent('''
                Ensure that the features in the new data are the same as the
                trained model.''')

        super().__init__(self.message)

class DataSplitOutOfBoundsError(ValueError):
    
    def __init__(self, datasplit_value:float):
        """Error thrown when split between training and testing datasets is not reasonable
        
        Parameters
        ----------
            datasplit_value : float
                Proportion of training dataset compared to total data
        """

        self.message = 'Value entered can not be '

        if datasplit_value < 0:
            self.message += 'negative.'
        elif datasplit_value > 1:
            self.message += 'greater than 1.'
        elif datasplit_value == 0:
            self.message += '0.'
        elif datasplit_value == 1:
            self.message += '1.'
        
        self.message += \
            textwrap.dedent('''
                The value needs to be a decimal number between 0 and 1 
                to ensure the creation of training and testing data sets.
                ''')
        
        super().__init__(self.message)
