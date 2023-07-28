import pandas as pd

class Preprocessor:
    
  def __init__(self):
    self.data = None
    self.units = {}
    self.df = None
    self.elements = {}
    self.df_unit = None

  def load_data(self,filename: str, header_row_index: int=0,
            index_col: int=None, usecols: list=None, skiprows: int=None,
            na_values: list=None, low_memory_load: bool=False, 
            engine: str=None, sheet_name: str=None, legacy_data: bool=False):
        """Loads data from a file into a pandas DataFrame.
        
        Args:
            filename: String of the path to the data to be loaded. Must
              include the file extension.
            header_row_index: The index of the row that contains the names of
              columns. Leave as None to use the first row.
            index_col: The index of the column that contains the row names.
              Leave as None to create another column of integers.
            usecols: The columns to use at load.
            skiprows: The number of rows to skip from the beginning.
            engine: Either 'c' or 'python'.
            sheet_name: For the case where reading an excel spreadsheet.
            legacy_data: True if this data is legacy data.
        """

        # Check file exists
        #if not os.path.isfile(filename):
        #    raise FileNotFoundError

        # Get file type by reading extension
        file_extension = filename.split('.')[-1]

        if file_extension.lower() == 'csv':
            self.data = pd.read_csv(filename, index_col=index_col,
                    header=header_row_index, low_memory=low_memory_load,
                    engine=engine, na_values=na_values, usecols=usecols,
                    skiprows=skiprows)

        elif file_extension.lower() == 'xlsx':
            file_data = pd.read_excel(filename, index_col=index_col,
                    header=header_row_index, sheet_name=sheet_name,
                    skiprows=skiprows)
            for key in file_data.keys():
              self.data = file_data[key]
              break

        elif file_extension.lower() == 'xls':
            self.data = pd.read_excel(filename, index_col=index_col,
                    sheet_name=sheet_name, header=header_row_index,
                    low_memory=low_memory_load)
        else:
            raise ValueError
  def get_elements_and_units(self):
    # Splits the column name into element and unit and save it as dictionary
    for col in self.data.columns:
      name = col.split('_')
      if len(name)>1:
        unit = str(name[-1]).lower()
        if unit in ['ppm','ppb','ppt']:
          self.units[col] = unit

  def convert_data_units(self, unit: str='ppb') -> None:
        """This converts all ppm/ppb/ppt values to one of these.
        This makes the values being displayed are based on the same unit.
        
        Args:
            unit: The unit to convert to. Must be one of {ppm, ppb, ppt}.
        """

        new_units = {}
        for column in self.units.keys():
            # Already in the correct unit
            if self.units[column] == unit:
                new_units[column] = unit
                continue

            if unit == 'ppb':
                if self.units[column] == 'ppm':
                    # Convert from ppm to ppb
                    self.data[column] = self.data[column] * 1000
                elif self.units[column] == 'ppt':
                    # Convert from ppt to ppb
                    self.data[column] = self.data[column] /1000

            elif unit == 'ppm':
                if self.units[column] == 'ppb':
                    # Convert from ppb to ppm
                    self.data[column] = self.data[column] / 1000
                elif self.units[column] == 'ppt':
                    # Convert from ppt to ppm 
                    self.data[column] = self.data[column] / 1000000

            elif unit == 'ppt':
                if self.units[column] == 'ppm':
                    # Convert from ppm to pc
                    self.data[column] = self.data[column] * 1000000
                elif self.units[column] == 'ppb':
                    self.data[column] = self.data[column] / 1000
            # Changing column name
            self.data.rename(columns={column: column.split('_')[0] + '_' + unit}, 
                            inplace=True)
            
            new_units[column.split('_')[0] + '_' + unit] = unit

        self.units = new_units

  def convert_units(self, unit: str='ppb') -> None:
            """This converts all ppm/ppb/ppt values to one of these.
            This makes the values being displayed are based on the same unit.
        
            Args:
              unit: The unit to convert to. Must be one of {ppm, ppb, ppt}.
            """
            if unit == 'ppb':
                if self.df_unit == 'ppm':
                    # Convert from ppm to ppb
                    self.df['Value'] = self.df['Value'] * 1000
                elif self.df_unit == 'ppt':
                    # Convert from ppt to ppb
                    self.df['Value'] = self.df['Value'] /1000

            elif unit == 'ppm':
                if self.df_unit == 'ppb':
                    # Convert from ppb to ppm
                    self.df['Value'] = self.df['Value'] / 1000
                elif self.df_unit == 'ppt':
                    # Convert from ppt to ppm 
                    self.df['Value'] = self.df['Value'] / 1000000

            elif unit == 'ppt':
                if self.df_unit == 'ppm':
                    # Convert from ppm to pc
                    self.df['Value'] = self.df['Value'] * 1000000
                elif self.df_unit == 'ppb':
                    self.df['Value'] = self.df['Value'] / 1000
            
            self.df_unit = unit

            for i in range(len(self.df['Elements'])):
              self.df['Elements'][i] = self.df['Elements'][i].split('_')[0] + '_' + unit

  def get_latitude_and_longitude(self):
    # get longitude column
    for col in self.data.columns:
      if self.data[col].dtype == float and col.lower().find('lat') == 0:
        if min(self.data[col]) >= -90 and max(self.data[col]) <= 90:
          latitude = self.data[col]
          break
    
    # get latitude column
    for col in self.data.columns:
      if self.data[col].dtype == float and col.lower().find('long') == 0:
        if min(self.data[col]) >= -180 and max(self.data[col]) <= 180:
          longitude = self.data[col]
          break

    return latitude, longitude


  def get_elements(self):
    elementKeys = list(self.units.keys())
    elements = {}
    for col in elementKeys:
      elements[col] = self.data[col].to_list()
    
    return elements

  def create_dataframe(self):
    # create dataframe
    self.df = pd.DataFrame()
    # get all the elements in the data
    elements = list(self.units.keys())
    # get latitude and longitude columns of the data
    latitude, longitude = self.get_latitude_and_longitude()
    # create element column, multipying each element with thenumber of locations
    self.df['Elements'] = elements * len(latitude)
    
    df_latitude = []
    df_longitude = []
    df_value = []

    # creating latitude, longitude and value columns
    for i in range(len(latitude)):
      # Creating the latitude for each element in the location
      df_latitude += [latitude[i]] * len(elements)
      # Creating the longitude for each element in the location
      df_longitude += [longitude[i]] * len(elements)
      # Adding values in a sequential manner to ensure correct values get associated
      for col in elements:
        df_value.append(self.data[col][i])

    self.df['Latitude'] = df_latitude
    self.df['Longitude'] = df_longitude
    self.df['Value'] = df_value

  def get_element_coordinate(self):
    # find rows belonging to an element
    elements = {}
    for i in range(len(self.df['Elements'])):
      try:
        elements[self.df['Elements'][i]].append(i)
      except:
        elements[self.df['Elements'][i]] = [i]
    
    for element in elements.keys():
      name = element.split('_')
      self.elements[name[0]] = elements[element]

  def element_filtering(self, element):
    # generates a dataframe for the specified element
    return self.df.loc[self.elements[element]]


  def save_file(self, filename):
    # to save the new data file
    if self.df is not None:
      self.df.to_csv(filename)
    else:
      raise Exception("Data needs to be preprocessed before storing")

  def preprocessing(self, filename,unit ='ppb'):
    # Preprocessing the entire data
    self.load_data(filename)
    self.df_unit = unit
    self.get_elements_and_units()
    self.convert_data_units(unit)
    self.create_dataframe()
    self.get_element_coordinate()
    return self.df, self.elements
