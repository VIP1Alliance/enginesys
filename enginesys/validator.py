import logging

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DataFormatter:
    
    def __init__(self, required_columns=None):
        """
        Initialize the DataFrameFormatter with optional required columns.

        Parameters:
        required_columns: list
            List of column names that are required. Default is None.
        """
        self.required_columns = required_columns if required_columns is not None else []
        
        
    def set_required_columns(self, columns: list):
        """
        Set the required columns for the dataframe.

        Parameters:
        columns: list
            List of column names that are required.
        """
        self.required_columns = columns
    
    
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
        
        
    def validate_required_columns(self, df: pd.DataFrame) -> tuple:
        """
        Check if the dataframe contains all the required columns.

        Parameters
        ----------
        df: pd.DataFrame
            The dataframe to validate.

        Returns
        -------
        bool
            True if all required columns are present, False otherwise.
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
    def validate_date_prices(prices_df: pd.DataFrame, date: str):
        if prices_df.index[-1] != pd.to_datetime(date):
            raise ValueError(
                f"No se encontraron precios de cierre para la fecha {date}"
            )
        missing_prices_tickers = []
        if (prices_df.loc[date].isna().any()) or (prices_df.loc[date].eq(0).any()):
            last_prices = prices_df.loc[date]
            null_price_tickers = list(last_prices[last_prices.isna()].index)
            zero_price_tickers = list(last_prices[last_prices == 0].index)
            missing_prices_tickers = null_price_tickers + zero_price_tickers
            
        return missing_prices_tickers
    
    @staticmethod
    def validate_dt_index(data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates the index of a DataFrame and converts it to a DatetimeIndex if necessary.
        
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
            logging.warning(
                "The index of the loaded DataFrame is not of type 'datetime'. Converting..."
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
    
    
    @staticmethod
    def validate_dates(data_df, init_date, end_date):
        """
        Validates the given date range against the minimum and maximum available dates in the data DataFrame.
        
        Parameters
        ----------
        data_df: pandas.DataFrame
            The DataFrame containing the data.
        init_date: str
            The start date to be validated.
        end_date: str
            The end date to be validated.
        
        Returns
        -------
        pandas.DataFrame
            The original data DataFrame.
        
        Warnings
        --------
        * If the requested start date is earlier than the minimum available date, a warning message is logged.
        * If the requested end date is later than the maximum available date, a warning message is logged.
        """
        if data_df.index.min() > pd.to_datetime(init_date):
            logging.warning(
                f"The requested start date ({init_date}) is earlier than the minimum available date ({data_df.index.min()})"
            )
        if data_df.index.max() < pd.to_datetime(end_date):
            logging.warning(
                f"The requested end date ({end_date}) is later than the maximum available date ({data_df.index.max()})"
            )
        return data_df
    
    @staticmethod
    def validate_tickers(prices_df: pd.DataFrame, tickers: list) -> pd.DataFrame:
        """
        Validates the tickers in the given DataFrame against a list of tickers.
        
        Parameters
        ----------
        data_df: pd.DataFrame
            The DataFrame containing the data.
        tickers: list
            The list of tickers to validate.
            
        Returns
        -------
        pd.DataFrame
            The original DataFrame with tickers validated.
        """
        prices_df.columns.names = ["type", "symbol"]
        existing_tickers = list(prices_df.columns.get_level_values("symbol").unique())
        missing_tickers = set(tickers) - set(existing_tickers)

        if len(missing_tickers) > 0:
            logging.warning(
                f"Some tickers were not found in the data source:\n"
                f"\tMissing tickers: {missing_tickers}"
            )

        return prices_df