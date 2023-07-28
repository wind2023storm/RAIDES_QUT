from django.contrib.auth import get_user_model

import pandas as pd
import numpy as np
import regex as re
from ..utils import data_utils
from ..utils import missforest
import miceforest as mf
import math
from django.http import HttpResponse, JsonResponse


UserModel = get_user_model()


"""Example Options:

options = {
    'defineUnits': {
        'mode': 'default', 
        'unit': 'ppb'
    }, 
    'imputeEmpty': {
        'mode': 'zero'
    },
    'removeNonNumeric': {
        'columns': ['Class', 'Country', 'Deposit Name']
    },
    'removeComma': {
        'columns': ['Class', 'Country', 'Deposit Name']
    },
    'handleInequalities': {
        'setInequalityTolerance': '', 
        'columns': ['Class', 'Country', 'Deposit Name']
    },
    'convertUnits': {
        'unit': 'ppb', 
        'updateColumnSuffix': '', 
        'columns': ['Class', 'Country', 'Deposit Name']
    },
    'removeColumns': {
        'columns': ['Class', 'Country', 'Deposit Name']
    }, 
    'removeDuplicates': {}
}
"""


class DataCleaner:

    def __init__(self, df: pd.DataFrame, options: dict, save_on_completion=False):
        self.df = df
        self.options = options
        self.save_on_completion = save_on_completion
        self.units = None
        self.datacleaning_result = []
        self.columns = [] 
        self.unit_mode = "default"
        #Preprocessing of data
        self.df = data_utils.dataclean_preprocessing(self.df)
        # Initialize the units used for the file
     
    @property
    def numerical_columns(self):
        return self.df.select_dtypes(include=np.number).columns.tolist()

    def to_csv(self):
        return self.df.to_csv()

    def check_column_numeric(self,column):
        if(~(column.isna().any())):
            print("enter")
            is_numeric = pd.to_numeric(column, errors='coerce').notnull().all()
        else:
            is_numeric = False
        if is_numeric:
            return True
        else:
            return False
    def check_all_columns_numeric(self):
        for column in self.df.columns:
                is_numeric = self.check_column_numeric(self.df[column])
                if(is_numeric):
                    self.df[column] = pd.to_numeric(self.df[column], errors='coerce', downcast="float")    
    def column_intersect(self, columns):
        """Gets the intersection between the columns supplied and the current columnns in the dataframe
        When removing columns, this is going to be needed"""
        return list(set(self.df.columns) & set(columns))
    def check_unit(self,unit):
            all_units = ['ppb','ppm','pc']
            # If unit has a different value
            if not unit in all_units:
                raise Exception("Define Unit : Units available are ppb, ppm, pc")

    def run(self):
        # This dict below is just an easy way to call a function for every option in the supplied dict
        # the order of the keys determines the other in which the methods are activated (IMPORTANT!)
        clean_methods = {
            'removeColumns': self.remove_columns,
            'removeDuplicates': self.remove_duplicates,
            'handleInequalities': self.handle_inequalities,
            'removeComma': self.remove_comma,
            'removeNonNumeric': self.remove_non_numeric,
            # Any numerical applications need to be done after all string components are gone, otherwise
            # we're going to have a bad time
            'imputeEmpty': self.impute_empty,
            'convertUnits': self.convert_units,
        }
        
        self.df = data_utils.dataclean_preprocessing(self.df)

        result = ''
        #compare_result = {}
        # Run the methods in order of method keys
        self.columns = self.df.columns
        if "removeColumns" not in self.options:
            self.define_units(**self.options.pop('defineUnits') if 'defineUnits' in self.options else {})

        for method in clean_methods.keys():
            if method in self.options:
                result=""
                kwargs = self.options.get(method)
                df_copy = self.df.copy(deep=True)
                result = clean_methods[method](**kwargs)
                if(method != "removeColumns"):
                    result += "detail:" + str(self.percentage_data_changed(df_copy,self.df,method))
                else:
                    self.define_units(**self.options.pop('defineUnits') if 'defineUnits' in self.options else {})
                    result += "detail:" + str(kwargs)
           
                self.datacleaning_result.append(result) 
               #self.compare_result[method] = df_copy.compare(self.df).to_string() 
                
            # mode in  self.options:      
    
        return self.df

    def define_units(self, **options):
        """Defines the measured units for the dataset, certain calculations rely on this

        Parameters
        ----------
        options : dict
            'mode': str | 'default', 'row', 'suffix'
            'unit': str | 'ppm', 'ppb', 'pct'
        """
        try:
            mode = options.get('mode')
            self.unit_mode = mode
            if mode == 'default':
                self.units = pd.Series([options.get('unit')] * len(self.df.columns), index=self.df.columns)
            elif mode == 'row':
                row = int(options.get('row')) - 1

                self.units = self.df.iloc[row, :].apply(lambda x: str(x).lower())
                if self.units is None:
                    raise Exception("Define Unit: Units cannot be none")
                else:
                    for column,unit in self.units.items():
                        self.check_unit(unit)
                self.df.drop(self.df.iloc[row].name, inplace=True)  # Drop the unit row
                self.check_all_columns_numeric()
            elif mode == 'suffix':
                self.units = pd.Series(self.df.columns, index=self.df.columns).apply(lambda x: x.split('_')[-1].lower())
                if self.units is None:
                    raise Exception("Define Unit : Units cannot be none")
                else:
                    for column,unit in self.units.items():
                        self.check_unit(unit)
        except Exception as e:
            error_message = str(e)
            raise Exception(error_message)
    
    def remove_columns(self, **options):
        """Removes supplied columns from DF"""
        print("before remove columns",self.df)    
     
        try:
            columns = self.column_intersect(options.get('columns'))
        except Exception as e:
           raise Exception("Remove Columns : No columns Selected for this cleaning method")
        try: 
            self.df.drop(columns, axis=1, inplace=True)
            string = 'REMOVE_COLUMNS:'
            first_loop = True
            for column in columns:
                if column not in self.df.columns:
                    if first_loop:
                        string += str(column)
                        first_loop = False
                    else:
                        string += ',' + str(column)
            self.check_all_columns_numeric()            
            return string
        except Exception as e:
            error_message = str(e)
            raise Exception("Remove Columns :  "+error_message)

    def remove_duplicates(self, **options):
        """Removes duplicate indices, need the **_ argument just so the main caller doesnt break"""
        try:
            columns = self.column_intersect(options.get('columns'))
        except Exception as e:
             raise Exception("Remove Duplicates : No columns Selected for this cleaning method")
        try:
            if len(columns) == 0:
                self.df = self.df
            else:
                self.df.drop_duplicates(subset=columns, keep='first', 
                    inplace=True)
                self.df = self.df[~self.df.index.duplicated(keep='first')]
            self.check_all_columns_numeric()
            return "Completed Remove duplicates"
        except Exception as e:
            error_message = str(e)
            raise Exception("Remove Duplicate : "+error_message)

    def handle_inequalities(self, **options):
        """Replaces the cells that involve inequalities rather than specific
        measurements.

        Parameters
        ----------
        options : dict
            'columns': []
            'setInequalityTolerance': {}
        """
        try:
            columns = self.column_intersect(options.get('columns'))
        except Exception as e:
             raise Exception("Remove Inequalities : No columns Selected for this cleaning method")
        try:
            set_inequality_tolerance = True if options.get('setInequalityTolerance') == ""  else False
            non_decimal = re.compile(r'[^\d.]+')  # checks for non-digit or a single '.' characters

            def _replace_tolerance(x):
                result = x
                try:
                    tolerance = x[0]

                    if tolerance == '<':
                        result = x[1:] if set_inequality_tolerance else 0
                    elif tolerance == ">":
                        # This seems silly to me
                        result = x[1:]
                    # Remove any non-numerical values from the string and convert to float
                    #if(math.isnan(result)):
                    #result = float(non_decimal.sub('', result))
                except:
                    # Just ignore any errors since we're returning the original value either way
                    pass
                return result

          #  for column in columns:
                #self.df[column] = pd.to_numeric(self.df[column], errors='ignore', downcast="float")
               # self.df[column].replace( np.nan,"", inplace=True)

            self.df[columns] = self.df[columns].applymap(_replace_tolerance)
            string = 'HANDLE_INEQUALITIES:'
            first_loop = True
            for index, column in enumerate(self.df.columns):

                # Skip if not in used columns
                if column not in columns:
                    continue
                
                if first_loop:
                    string += str(column)
                    first_loop = False
                else:
                    string += ',' + str(column)       
            self.check_all_columns_numeric()             
            return string
        except Exception as e:
            error_message = str(e)
            raise Exception("Remove Inequalities : " +error_message)    

    def remove_comma(self, **options):
        """Removes commas from the selected rows

        Parameters
        ----------
        options : dict
            'columns': []
        """
     
        try:
            columns = self.column_intersect(options.get('columns'))
        except Exception as e:
             raise Exception("Comma Separation : No columns Selected for this cleaning method")
        try:
            self.df[columns] = self.df[columns].applymap(lambda x: re.sub(',', '', x) if isinstance(x, str) else x)
            string = 'REMOVED_COMMA_SEP:'
            first_loop = True
            for column in columns:
                    if first_loop:
                        string += str(column)
                        first_loop = False
                    else:
                        string += ',' + str(column)
            self.check_all_columns_numeric()            
            return string
        except Exception as e:
            error_message = str(e)
            raise Exception("Remove Comma : "+error_message)
        
    def remove_non_numeric(self, **options):
        """Remove non-numeric rows

        Parameters
        ----------
        options : dict
            'columns': []
        """
        try:
                columns = self.column_intersect(options.get('columns'))
        except Exception as e:
                 raise Exception("Remove Non-Numeric : No columns Selected for this cleaning method")
        try:
            use_columns = []
            for column in columns:
                # Only apply to non-numerical columns
                if not isinstance(self.df[column], (int, float)):
                    self.df[column] = pd.to_numeric(self.df[column], errors='coerce', downcast="float")
                    #self.df[column].fillna('', inplace=True)
                    #self.df[column].astype(float)
                    use_columns.append(column)
            string = 'REMOVE_NON_NUMERIC:'
            first_loop = True
            for column in use_columns:
                    if first_loop:
                        string += str(column)
                        first_loop = False
                    else:
                        string += ',' + str(column)   
            self.check_all_columns_numeric() 
            print("after non numeric", self.df)                
            return string    
        except Exception as e:
            error_message = str(e)
            raise Exception("Remove Non-Numeric : " +error_message)
            
    def remove_entries(self, **options):
        """Supposed to remove indices, though kinda hard to implement a GUI for it for datasets with thousands
        of entries. Maybe need to re-think this operation"""
        # TODO: Figure out what to do with this
        pass

    def impute_empty(self, values: dict=None,
            subset_X: list=None, inplace: bool=True, 
            aca_source: str='CRC', mice_save_filepath: str=None, **options):
        """Fills in numerical data that is missing using a variety of methods

        Parameters
        ----------
        options : dict
            mode: str
                'zero': Column values to zero
                'median': Median of column
                'mean': Mean of column
                'mode': Mode of column
                'mice': Multiple Imputation by chained equations
                'missforest': MissForest algorithm
                'aca': Average Crustal Abundance
        """
        columns = self.df.columns 
        #self.df  = self.df.replace(r'^\s*$', np.nan, regex=True)
        def _mice(x,mice_save_filepath_local,mice_save_filepath ):
            datasets = 5
            kernel = mf.ImputationKernel(data=x, datasets=datasets, save_all_iterations=False, random_state=10)
            if(mice_save_filepath == None):
                mice_save_filepath = mice_save_filepath_local
            if mice_save_filepath is not None:
                try:
                    datasets = 5
                    kernel = mf.ImputationKernel(
                        data=x,
                        datasets=datasets,
                        save_all_iterations=False,
                        random_state=10
                    )

                    iterations = 5
                    kernel.mice(iterations, verbose=False)

                    for i in range(datasets):   
                        kernel.complete_data(i).to_csv(mice_save_filepath + 
                                                       str(i) + '.csv')
            
                except ValueError as e:
                   
                    error_message = str(e)
                    raise Exception(error_message)

            else:
                raise Exception('Please provide mice save path')
            return kernel.complete_data(4)

        def _aca(x):
             # Load in ACA data, indexed by element symbol
            try: 
                aca = pd.read_csv('geochem/resources/aca.csv', index_col=3)
                # Remove unit appended at end
                # for column in columns:
                    # Assumes in the form '{symbol}_{unit}'
                element = x.name.split('_')[0].capitalize()
            # Skip weight column
                if element == 'Wt':
                    return x 
                    
                if x.name[-2:] == 'pc':
                    # Convert the aca to pc to make consistent with column
                    value = aca[aca_source][element] / 10000
                else:
                    value = aca[aca_source][element]
                return x.fillna(value)
            except Exception as e:
                error_message = str(e)
                raise Exception(error_message)
                
        mode = options.get('mode')
        impute_methods = {
            'zero': lambda x: x.fillna(0),
            'median': lambda x: x.fillna(x.median()),
            'mean': lambda x: x.fillna(x.mean()),
            'mode': lambda x: x.fillna(x.mode()),
            'mice': _mice,
            'aca': _aca,
            None: lambda x: x
        }
        # Apply the correct mode function to the numerical columns within the dataset
        try:
            if(mode == "missforest"):
                    # Initialise, fit and transform imputer to self.data
                mf_imputer = missforest.MissForest()
                # A copy is required as directly using the data might give
                # undesired results
                self.df[self.numerical_columns] = mf_imputer.fit_transform(self.df[self.numerical_columns].copy())
                # return self.df[columns]
            elif(mode == "mice"):
                self.df[self.numerical_columns] = _mice(self.df[self.numerical_columns],'geochem/resources/mice_outputs/',mice_save_filepath)
            else:
                self.df[self.numerical_columns] = self.df[self.numerical_columns].apply(impute_methods[mode])
            # Beginning of string
            string = 'IMPUTE_VALUES:MODE{}:'.format(mode)
            
            # Columns that are attempted to impute
            first_loop = True
            for column in columns:
                if first_loop:
                    string += str(column)
                    first_loop = False
                else:
                    string += ',' + str(column)
            self.check_all_columns_numeric()     
            return string
        except Exception as e:
            error_message = str(e)
            raise Exception("Impute Empty : " +error_message)

    def convert_units(self, unit: str='ppm',**options):
            try:
                columns = self.column_intersect(options.get('columns'))
            except Exception as e:
                raise Exception("Convert Uniform Units : No columns Selected for this cleaning method")
                
            """Converts the unit types of selected columns

        This converts all ppm/ppb/pc values to one of these.
        
        Assumes that all values are either ppm, ppb or something that does 
        not need to be converted because it is already uniform.

        Args:
            unit: The unit to convert to. Must be one of {ppm, ppb, pc}.
            subset_X: List of columns to use, if None, use all columns.
            update_col_suffix: True will update the column header at the end
              to represent the unit that column is now in.
            append_suffix: If True, adds the unit to the end of the column,
              False will replace the last split (_ as a delimiter).
        """
        
            if options.get('updateColumnSuffix') =="":
              update_col_suffix = True
            else :
              update_col_suffix = False  
            # If the dataset has no units
            if self.units is None:
                raise Exception("Convert Units : Need to define units for the dataset")
            
            all_units = ['ppb','ppm','pc']
            # If unit has a different value
            if not unit in all_units:
                raise Exception("Convert Units : Units available are ppb, ppm, pc")
            
            new_units = {}
            def func_update_suffix(column):
                    if update_col_suffix:
                        # Get updated string
                    
                            # Get first parts of the string
                            result = ''
                            split = column.split('_')
                            # Add new unit to string, and update column name
                        
                            if(self.unit_mode  == "suffix"):
                                if len(split) == 1:
                                    result += split[0] + '_'
                                else:
                                    for string in split[:-1]:
                                        result += string + '_'
                            else:
                                result = column + "_"+ unit
                       
                            self.df.rename(columns={column: result},
                                    inplace=True)
                            new_units[result] = unit
                    
                    else:
                        new_units[column] = unit
            for column in self.units.keys():
                
                # Ignore columns that are not in columns
                if columns is not None:
                    if not column in columns:
                        new_units[column] = self.units[column]
                        func_update_suffix(column)
                        continue

                # Already in the correct unit
                if self.units[column] == unit:
                    new_units[column] = self.units[column]
                    func_update_suffix(column)
                    continue

                # Ignore columns with unwanted units
                if not self.units[column] in all_units:
                    new_units[column] = self.units[column]
                    func_update_suffix(column)
                    continue
                # Ignore columns with unwanted values
                if not np.issubdtype(self.df[column].dtype, np.number):
                    new_units[column] = self.units[column]
                    func_update_suffix(column)
                    continue
                if unit == 'ppb':
                    if self.units[column] == 'ppm':
                        # Convert from ppm to ppb
                        self.df[column] = self.df[column] * 1000
                    elif self.units[column] == 'pc':
                        # Convert from pc to ppb
                        self.df[column] = self.df[column] * 10000000 
                    func_update_suffix(column)
                elif unit == 'ppm':
                    if self.units[column] == 'ppb':
                        # Convert from ppb to ppm
                        self.df[column] = self.df[column] / 1000
                    elif self.units[column] == 'pc':
                        # Convert from pc to ppm 
                        self.df[column] = self.df[column] * 10000
                    func_update_suffix(column)
                elif unit == 'pc':
                    if self.units[column] == 'ppm':
                        # Convert from ppm to pc
                        self.df[column] = self.df[column] / 10000
                    elif self.units[column] == 'ppb':
                        self.df[column] = self.df[column] / 10000000
                    func_update_suffix(column)   
                
            self.units = new_units
            string = 'UNITS: {}'.format(unit)
            for column in columns:
                string += ',' + str(column)
            self.check_all_columns_numeric()    
            return string
    def percentage_data_changed(self,df1,df2,method):
        """
        Returns a dictionary where the keys are the names of columns that differ
        in their values between the two DataFrames, and the values are tuples
        of the index of the row where these columns differ and the total number
        of values changed in that column.
        """
        #make column names same
        df2 = df2.rename(columns=dict(zip(df2.columns, df1.columns)))
        if(method != "imputeEmpty") :
            df1 = df1.fillna(0)
            df2 = df2.fillna(0)
        
        # Find the differences between the two DataFrames
        diff_df = df1 != df2
        
        # Create an empty dictionary to store the results
        diff_dict = {}
        
        # Loop over each column in the DataFrame
        for column in diff_df:
            # Find the rows where the values in this column differ
            diff_rows = diff_df[column].index[diff_df[column]].tolist()
            
            # If there are any differences, add them to the dictionary
            if len(diff_rows) > 0:
                # Store the row indices and number of values changed as a tuple
                num_changed = diff_df[column].sum()
                percentage_changed = round(((num_changed / len(df1[column])) * 100),2)
                diff_dict[column] = (diff_rows, num_changed, percentage_changed)
        
        # Return the dictionary of differences
        return diff_dict
    
   
