import logging

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Validator:
    
    def __init__(self):
        pass
    
    @staticmethod
    def validate_columns(
        df: pd.DataFrame, 
        required_cols: list
    ) -> tuple:
        """
        Check if the dataframe contains all the required columns and return the extra and missing columns.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to validate.
        required_cols : list
            The list of required columns.

        Returns
        -------
        tuple
            A tuple containing the extra columns and missing columns.
        """
        input_cols = set(df.columns)
        required_cols = set(required_cols)
        if not input_cols == required_cols:
            extra_cols = list(input_cols - required_cols)
            missing_cols = list(required_cols - input_cols)
            return extra_cols, missing_cols
        return [], []
    
    @staticmethod
    def validate_strategies(
        df: pd.DataFrame, 
        required_strats: list,
        strategy_col: str = "strategy", 
    ) -> tuple:
        """
        Check if the dataframe contains all the required strategy labels in the specific column.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to validate.
        required_strats : list
            The list of required strategy labels.
        strategy_col : str, optional
            The name of the column containing the strategy labels. Default is "strategy".

        Returns
        -------
        tuple
            A tuple containing the missing strategy labels and extra strategy labels.
        """
        input_strats = set(df[strategy_col].unique())
        required_strats = set(required_strats)
        if not input_strats == required_strats:
            extra_strats = list(input_strats - required_strats)
            missing_strats = list(required_strats - input_strats)
            return extra_strats, missing_strats
        else:
            return [], []
    
    @staticmethod
    def validate_date_prices(
        prices_df: pd.DataFrame, 
        date: str, 
    ) -> tuple:
        """
        Check for null and zeroo prices in a DataFrame and return the the corresponding tickers.

        Parameters
        ----------
        prices_df : pd.DataFrame
            The DataFrame containing prices.
        date : str
            The date for which prices are checked.

        Returns
        -------
        tuple
            A tuple containing two lists: null_prices and zero_prices.
            null_prices : list
                A list of tickers with missing prices.
            zero_prices : list
                A list of tickers with prices equal to 0.0.
        """
        prices_date = prices_df.loc[date]
        if prices_date.isna().any() or (prices_date == 0).any():
            null_prices = list(prices_date[prices_date.isna()].index)
            zero_prices = list(prices_date[prices_date == 0].index)
            return null_prices, zero_prices
        else:
            return [], []
    
    @staticmethod
    def validate_interval_dates(
        data_df: pd.DataFrame, 
        init_date: str, 
        end_date: str
    ) -> pd.DataFrame:
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
    def validate_tickers(prices_df: pd.DataFrame, req_tickers: list) -> pd.DataFrame:
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
        existing_tickers = set(prices_df.columns.get_level_values(1).unique())
        req_tickers = set(req_tickers)
        if not req_tickers == existing_tickers:
            extra_tickers = list(existing_tickers - req_tickers)
            missing_tickers = list(req_tickers - existing_tickers)
            return extra_tickers, missing_tickers
        return [], []