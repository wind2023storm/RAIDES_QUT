import numpy as np
from scipy.stats import mode
from sklearn.base import BaseEstimator
from sklearn.base import TransformerMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.utils.validation import check_array
from sklearn.utils.validation import check_is_fitted


class MissForest(BaseEstimator, TransformerMixin):
    """
    Contains methods for calculating and transforming data with MissForest.
    """

    def __init__(self, max_iterations: int=10, missing_values=np.nan):
        """Initialises variables to prepare for imputation.
        
        Args:
            max_iterations: The maximum number of iterations that MissForest
              should run for. If the stopping criterion is met first, that
              will halt the method first.
            missing_values: Values that are considered missing. This should be
              a list if there is more than one value to consider.

        """
        self.max_iterations = max_iterations
        self.missing_values = missing_values

    def calculate_gamma(self, data_new, data_old):
        """Calculates the stopping criterion for MissForest."""

        gamma_new = np.sum(
            (data_new[:, self.num_vars_] - data_old[:, self.num_vars_]) ** 2 \
                    / np.sum((data_new[:, self.num_vars_]) ** 2)
        )

        return gamma_new

    def missforest(self, data, mask):
        """Calculates the MissForest algorithm.
        
        Args:
            data: The pd.DataFrame to impute.
            mask: This is calculated by get_mask equation, """
        
        # Get the number of missing values per column
        col_missing_count = mask.sum(axis=0)

        # Get the row and col indexes for each missing value
        missing_row_indexes, missing_col_indexes = np.where(mask)

        # Initialise Models
        if self.num_vars_ is not None:

            # Get only indexes for numerical data
            keep_index_num = np.in1d(missing_col_indexes, self.num_vars_)
            missing_row_indexes_num = missing_row_indexes[keep_index_num]
            missing_col_indexes_num = missing_col_indexes[keep_index_num]

            # Make initial guess of imputed values with the mean

            # First fill with nan if it is still not explicitly nan.
            means = np.full(data.shape[1], fill_value=np.nan)

            # Get means and then replace with the mean
            means[self.num_vars_] = self.statistics_.get('col_means')
            data[missing_row_indexes_num, missing_col_indexes_num] = np.take(
                    means, missing_col_indexes) # Replace this better?

            # Initialise the regression model
            rf_regressor = RandomForestRegressor()

        if self.cat_vars_ is not None:
            pass # TODO

        # Get sorted indexes of columns by missing count
        miss_count_indexes = np.argsort(col_missing_count)

        # Initialise stopping criterion
        self.iter_count = 0
        gamma_new = 0
        gamma_old = np.inf
        gamma_new_cat = 0
        gamma_old_cat = np.inf
        col_index = np.arange(data.shape[1])
        
        # Keep computing iterations until stopping criterion is met. Do not
        # compute more iterations than self.max_iterations.
        while (gamma_new < gamma_old or gamma_new_cat < gamma_old_cat) and \
                self.iter_count < self.max_iterations:
            
            # Get current imputed data
            data_old = np.copy(data)

            # Update stopping criterion if not first iteration
            if self.iter_count != 0:
                gamma_old = gamma_new
                gamma_old_cat = gamma_new_cat

            # Using notation in pseudo_code, s is features that contain
            # missing values.
            for s in miss_count_indexes:
                # The other column indexes
                s_prime = np.delete(col_index, s)

                # Get the row indexes for the missing and non-missing
                filled_rows = np.where(~mask[:, s])[0]
                missing_rows = np.where(mask[:, s])[0]

                # Skip if no missing values
                if len(missing_rows) == 0:
                    continue

                # Get the filled values of s
                s_filled = data[filled_rows, s]

                # Get the filled and missing data under different vars
                data_filled = data[np.ix_(filled_rows, s_prime)]
                data_missing = data[np.ix_(missing_rows, s_prime)]

                # Fit the random forest
                if self.cat_vars_ is not None and s in self.cat_vars_:
                    pass # TODO

                else:
                    # Fit the predictor
                    rf_regressor.fit(X=data_filled, y=s_filled)

                    # Predict the missing values
                    s_missing = rf_regressor.predict(data_missing)

                    # Update the imputed data
                    data[missing_rows, s] = s_missing

            # Update stopping criterion
            if self.cat_vars_ is not None:
                pass # TODO

            if self.num_vars_ is not None:
                gamma_new = self.calculate_gamma(data, data_old)

            self.iter_count += 1

        return data_old

    @staticmethod
    def get_mask(X, value_to_mask):
        """Compute the boolean mask X == missing_values.
        
        This is from the missingpy package.
        """
        if value_to_mask == "NaN" or np.isnan(value_to_mask):
            return np.isnan(X)
        else:
            return X == value_to_mask

    def fit(self, data, cat_vars=None):
        """Fits an imputer to the data."""
        # Validate the data
        data = check_array(data, accept_sparse=False, dtype=np.float64,
                force_all_finite='allow-nan')

        # Raise ValueError if there are any infinite values
        if np.any(np.isinf(data)):
            raise ValueError('Infinite values are not supported.')

        # Check if any columns are completely empty
        print("missing",self.missing_values)
        mask = MissForest.get_mask(data, self.missing_values)
        if np.any(mask.sum(axis=0) >= (data.shape[0])):
            raise ValueError('One or more columns have missing values.')

        if cat_vars is not None:
            pass # TODO

        # Identify numerical variables
        num_vars = np.setdiff1d(np.arange(data.shape[1]), cat_vars)
        num_vars = num_vars if len(num_vars) > 0 else None
        
        # Get mean of numerical cols, mode of categorical cols
        if num_vars is not None:
            col_means = np.nanmean(data[:, num_vars], axis=0)
        else:
            col_means = None

        if cat_vars is not None:
            col_modes = mode(data[:, cat_vars], axis=0, nan_policy='omit')[0] 
        else:
            col_modes = None

        self.cat_vars_ = cat_vars
        self.num_vars_ = num_vars
        self.statistics_ = {"col_means": col_means, "col_modes": col_modes}

        return self

    def transform(self, data):
        """Transforms the data using MissForest."""
        check_is_fitted(self, ["cat_vars_", "num_vars_", "statistics_"])

        # Validate the data
        val_data = check_array(data, accept_sparse=False, dtype=np.float64,
                force_all_finite='allow-nan')

        # Raise ValueError if there are any infinite values
        if np.any(np.isinf(val_data)):
            raise ValueError('Infinite values are not supported.')

        # Check if any columns are completely empty
        mask = MissForest.get_mask(val_data, self.missing_values)
        if np.any(mask.sum(axis=0) >= (val_data.shape[0])):
            raise ValueError('One or more columns have missing values.')

        imp_data_array = self.missforest(val_data, mask)

        # Now need to put it back into the pandas dataframe
        data.loc[:, :] = imp_data_array

        return data

    def fit_transform(self, data, y=None, **fit_params):
        """As in sklearn, calls fit and then transform."""
        return self.fit(data, **fit_params).transform(data)
