import pandas as pd


class DataFrameFormatter:
    
    def __init__(self, required_columns=None):
        """
        Initialize the DataFrameFormatter with optional required columns.

        Parameters:
        required_columns (list): List of column names that are required. Default is None.
        """
        self.required_columns = required_columns if required_columns is not None else []
        
        
    def set_required_columns(self, columns: list):
        """
        Set the required columns for the dataframe.

        Parameters:
        columns (list): List of column names that are required.
        """
        self.required_columns = columns
    
    
    @staticmethod
    def remove_unnamed_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove columns from the dataframe that contain the word 'Unnamed' in their names.

        Parameters:
        df (pd.DataFrame): The dataframe from which to remove columns.

        Returns:
        pd.DataFrame: The dataframe with 'Unnamed' columns removed.
        """
        # Filter columns that do not contain 'Unnamed'
        columns_to_keep = [col for col in df.columns if 'Unnamed' not in col]
        # Return the dataframe with only the selected columns
        return df[columns_to_keep]
    
    
    @staticmethod
    def lower_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert all column names in the dataframe to lowercase.

        Parameters:
        df (pd.DataFrame): The dataframe with columns to convert.

        Returns:
        pd.DataFrame: The dataframe with column names converted to lowercase.
        """
        df.columns = [col.lower() for col in df.columns]
        return df
    
    
    @staticmethod
    def spaces_to_underscores(df: pd.DataFrame) -> pd.DataFrame:
        """
        Replace spaces in column names with underscores.

        Parameters:
        df (pd.DataFrame): The dataframe with columns to modify.

        Returns:
        pd.DataFrame: The dataframe with column names modified.
        """
        df.columns = [col.replace(' ', '_') for col in df.columns]
        return df
        
        
    def validate_required_columns(self, df: pd.DataFrame) -> tuple:
        """
        Check if the dataframe contains all the required columns.

        Parameters:
        df (pd.DataFrame): The dataframe to validate.

        Returns:
        bool: True if all required columns are present, False otherwise.
        """
        input_columns = set(df.columns)
        required_columns = set(self.required_columns)
        if not input_columns == self.required_columns:
            extra_columns = input_columns - required_columns
            missing_columns = required_columns - input_columns
        
        if not self.required_columns:
            raise ValueError("Required columns have not been set.")
        
        return extra_columns, missing_columns
    
    @staticmethod
    def replace_column_names(df: pd.DataFrame, column_dict: dict) -> pd.DataFrame:
        """
        Replace column names in the dataframe using a dictionary.

        Parameters:
        df (pd.DataFrame): The dataframe with columns to replace.
        column_dict (dict): A dictionary where the keys are the current column names and the values are the new column names.

        Returns:
        pd.DataFrame: The dataframe with replaced column names.
        """
        df.rename(columns=column_dict, inplace=True)
        return df