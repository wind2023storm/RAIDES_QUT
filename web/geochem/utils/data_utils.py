import pandas as pd

def training_error_string(error):
    if "not" in str(error) and "trained" in str(error):
        if '(' in str(error) or ')' in str(error):
            x = str(error).split("'")
            return x[1]
        else:
            return str(error)
    
    return None

def get_columns_selected(options):
    columns_selected = []

    for method, contents in options.items():
        if not options[method].get('columns'):
            continue
        for col in options[method].get('columns'):
            if col not in columns_selected:
                columns_selected.append(col)
    
    return columns_selected

def generate_error_string_ending(options, problem_columns):
    error_message_end = ""

    if options.get('KMeans'):
        error_message_end += ": KMeans function"

    for method, contents in options.items():
        if options[method].get('columns') and any(col in problem_columns for col in options[method]['columns']):
            error_message_end += ": " + method

    return error_message_end

def get_columns_containing_text(dataset):
    problem_columns = []

    for i, v in enumerate(dataset.columns):
        try:
            subset = dataset.iloc[0:len(dataset.index),[i]]
            _ = subset.astype("float")
            continue
        except:
            problem_columns.extend(subset.columns)

    return problem_columns

def selected_columns_with_empty_cells(df: pd.DataFrame):
    empty_cols = []
    for col in df.columns:
        if df[col].isnull().any():
            empty_cols.append(col)
    return empty_cols

def remove_nan_rows(data: pd.DataFrame):
    return data[(~data.isnull()).all(axis=1)]

def dataclean_preprocessing(data: pd.DataFrame):
    """Handles not-a-number values in dataframe
    
    Parameters
    ----------
        data: DataFrame
            dataframe to be cleaned
    """
    print("cleaning")
    data.dropna(axis=0, how='all', inplace=True)
    data.dropna(axis=1, how='all', inplace=True)
    data = data[~data.index.duplicated(keep='first')]
    print("dataa",data)
    return data

def check_list(given_list: list, existing_list: list,
                  equal: bool=True):
    """

    Parameters
    ----------
        given_list: list
            list to be checked
        existing_list: list
            list to check from
        equal: bool
            Whether to return the list of column or row names with correct
            or incorrect names. True returns correct and False returns 
            incorrect. Defaults to True.

    Returns
    -------
        List of column or row names depending upon the choice
    """
    correct_list = []
    incorrect_list = []
    # separate correct names from incorrect
    for element in given_list:
        if element in existing_list:
            correct_list.append(element)
        else:
            incorrect_list.append(element)
    # list of names returned
    if equal:
        return correct_list
    else:
        return incorrect_list

def check_list_datatype(data_set: pd.DataFrame, given_list: list, data_type: type,
                          equal: bool=True):
    """

    Parameters
    ----------
        data_set: DataFrame
            Dataset whose columns or rows need to be checked
        given_list: list
            List of column or row names to check
        data_type: type
            Data type a column or row should have
        equal: bool
            Whether to return the list of column or row names with correct
            or incorrect names. True returns correct and False returns 
            incorrect. Defaults to True.

    Returns
    -------
        List of column or row names depending upon the choice
    """
    correct_list = []
    incorrect_list = []
    # separates columns or rows with matching data type
    for element in given_list:
        if data_set[element].dtypes == data_type:
            correct_list.append(element)
        else:
            incorrect_list.append(element)
    # list of names returned
    if equal:
        return correct_list
    else:
        return incorrect_list
    
def check_analyser(given_list: list, data_set:pd.DataFrame,
                        target_column: str=None):
    """

    Parameters
    ----------
        target_column: str
            Column name to check
        given_list: list
            list to be checked
        data_set: DataFrame
            Dataset containing all the columns

    Returns
    -------
        List of column names that can be used
    """
    # check target_column name and data
    if target_column is not None:
        if target_column not in data_set.columns:
            raise Exception("Target column is not a column header.")
        elif data_set[target_column].dtypes == 'object':
            raise TypeError("Please choose column with numerical data")

    # check given list name and data
    if given_list is None:
        given_list = list(data_set.columns)
        # column removed in every analyser method
        if target_column is not None:
            given_list.remove(target_column)
    else:
        given_list = check_list(given_list, data_set.columns)
    
    # to remove categorical or string columns     
    given_list = check_list_datatype(data_set, given_list, 'object', False)
    
    # if no column name is left after checking
    if len(given_list) == 0:
        raise Exception("All column headers are incorrect.")

    return given_list
