import logging

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Formatter:
    
    def __init__(self):
        pass
        
    @staticmethod
    def remove_unnamed_cols(df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove columns from the dataframe that contain the word 'Unnamed' in their names.

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe from which to remove columns.

        Returns
        -------
        pd.DataFrame
            The dataframe with 'Unnamed' columns removed.
        """
        # Filter columns that do not contain 'Unnamed'
        columns_to_keep = [col for col in df.columns if 'Unnamed' not in col]
        # Return the dataframe with only the selected columns
        return df[columns_to_keep]
    
    @staticmethod
    def lower_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert all column names in the dataframe to lowercase.

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe with columns to convert.

        Returns
        -------
        pd.DataFrame
            The dataframe with column names converted to lowercase.
        """
        df.columns = [col.lower() for col in df.columns]
        return df
    
    @staticmethod
    def spaces_to_underscores(df: pd.DataFrame) -> pd.DataFrame:
        """
        Replace spaces in column names with underscores.

        Parameters
        ----------
        df: pd.DataFrame:
            The dataframe with columns to modify.

        Returns
        -------
        pd.DataFrame
            The dataframe with column names modified.
        """
        df.columns = [col.replace(' ', '_') for col in df.columns]
        return df
    
    @staticmethod
    def df_index_to_dt(data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates the index of a DataFrame and converts it to a DatetimeIndex if it is not.
        
        Parameters
        ----------
        data_df: pd.DataFrame
            The DataFrame to be validated.
        
        Returns
        -------
        pd.DataFrame
            The DataFrame with a validated index.
        """
        if not isinstance(data_df.index, pd.DatetimeIndex):
            logging.info(
                "Converting index of loaded DataFrame to 'datetime' ..."
            )
            if isinstance(data_df.index, pd.PeriodIndex):
                formated_index = data_df.index.to_timestamp()
            elif isinstance(data_df.index, pd.Index):
                formated_index = pd.to_datetime(data_df.index)
            else:
                raise ValueError(
                    "Unable to identify the type of index in the DataFrame"
                )
            data_df.index = formated_index

        return data_df