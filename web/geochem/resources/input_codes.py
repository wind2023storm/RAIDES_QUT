
class Codes:

    # Codes for different stages of the workflow
    WORKFLOW_STAGE = {
        'load_data': 0,
        'clean_data': 1,
        'analyse_data': 2,
        'plot': 3,
        'report': 4,
        'osnaca_workflow': 5,
        'petrosea_load_data': 6,
        'petrosea_clean_data': 7,
        'petrosea_analyse_data': 8,
    }

    # Loading actions
    LOADER_ACTIONS = {
        'initialise': 0, # constructor
        'load_data': 1,
        'read_units': 2,
        'change_units': 3,
        'get_datacleaner': 4,
        'get_petroseacleaner': 5,
    }

    # Codes for different labs
    CLEANER_LAB = {
        'Generic': 0,
        'ALS': 1,
    }

    # Different units for cleaner load
    CLEANER_UNITS = {
        'ppb': 0,
        'ppm': 1,
        'pc': 2,
    }

    # Cleaning actions
    CLEANER_ACTIONS = {
        'handle_inequalities': 0,
        'convert_uniform_units': 1,
        'remove_columns': 2,
        'remove_duplicate_entries': 3,
        'remove_entries': 4,
        'remove_empty_entries': 5,
        'impute': 6,
        'merge': 7,
        'set_dtype': 8,
        'write_csv': 9,
    }

    # Imputing actions
    CLEANER_IMPUTING_ACTIONS = {
        'zero': 0,
        'aca': 1,
        'median': 2,
        'mean': 3,
        'mice': 4,
        'none': 5,
        'missforest': 6,
    }

    # Petrosea cleaning actions
    PETROSEA_CLEANER_ACTIONS = {
        'split_legacy_data': 0,
    }

    # OSNACA workflow actions
    OSNACA_WORKFLOW_ACTIONS = {
        'initialise': 0,
        'fill_insig_entries': 1,
        'combine_user_osnaca': 2,
    }

    # Analyser actions
    ANALYSER_ACTIONS = {
        'get_stats': 0,
        'summarise_float_column': 1,
        'kmeans': 2,
        'kmeans_string_summary': 3,
        'kmeans_predict': 4,
        'random_forest': 5,
        'predict_random_forest': 6,
        'neural_network': 7,
        'predict_neural_network': 8,
        'pca': 9,
        'hca': 10,
        'cc': 11,
    }

    # Petrosea analyser actions
    PETROSEA_ANALYSER_ACTIONS = {
        'add_col_element_grades': 0,
        'train_ore_classifier_rf': 1,
        'predict_ore_classifier_rf': 2,
    }

    # Plotter actions
    PLOTTER_ACTIONS = {
        'visualise_empty_cells': 0,
        'visualise_empty_cells_bar': 1,
        '2d_kmeans': 2,
        'rf_importances': 3,
        'pca_feature_bar': 4,
        'pca_cumsum': 5,
        'dendrogram': 6,
        'cc_heatmap': 7,
        'tf_losses': 8,
        'tf_predictions': 9,
        'tf_predictions_hist': 10,
    }

    # Report actions
    REPORT_ACTIONS = {
        'data_report': 0,
        'cleaning_report': 1,
        'analysis_report': 2,
        'osnaca_report': 3,
    }


    @staticmethod
    def get_reversed_dictionary(dictionary: dict) -> dict:
        """
        Takes a dictionary and returns the same dictionary, with keys as
        values and values as keys.

        Args:
            dictionary: The dictionary to be reversed.
        """
        return  {value: key for key, value in dictionary.items()}


    @staticmethod
    def get_cleaner_constructor_dictionary(input: dict) -> dict:
        """Translates user inputs to the inputs dataclean needs.
        
        This is more or less keeping the input dictionary the same, but with
        the integer codes translated to the args the Cleaner needs.
        
        Args:
            input: A dictionary of str: generic pairs specifying how to use
              the DataCleaner.
        
        Returns:
            A dictionary that can be passed into the DataCleaner constructor.
        """
        
        args = {
            'filename': input['filename'], 
            'lab': Codes.get_reversed_dictionary(
                    Codes.CLEANER_LAB)[input['lab']],
            'unit': Codes.get_reversed_dictionary(
                    Codes.CLEANER_UNITS)[input['unit']],
            'index_col': input['index_col'],
            'username': input['username'],
            'is_excel': input['is_excel'],
            'is_xls': input['is_xls'],
            'sheet_name': input['sheet_name']
        }

        return args
