import calendar
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Tuple, Union

import pandas as pd
import yfinance as yf

import enginesys.eodhd.eodhd as eodhd


class APIConnector:

    def __init__(self, data_path):
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        os.makedirs(self.output_data_path, exist_ok=True)
    
    
    @staticmethod
    @lru_cache(maxsize=None)
    def _fetch_eodhd_prices(
        update_time: str, # This is used to cache the data
        tickers: Union[str, Tuple[str, ...]], 
        start: str, 
        end: str, 
        period: Optional[str] = "m",
        complete_month: Optional[bool] = False,
    ) -> pd.DataFrame:
        """
        Fetches EODHD prices from the API, update.
        
        Parameters
        ----------
        update_time :str
            The time to update the data. This is used to cache the data.
        tickers :Union[str, Tuple[str, ...]]
            The tickers to fetch prices for.
        start :str
            The start date.
        end :str
            The end date.
        period :Optional[str]
            The period. Defaults to "m".
        complete_month :Optional[bool]
            Whether to fetch complete month data. Defaults to False.
        
        Returns
        -------
            pd.DataFrame: The fetched data.
        
        Raises
        ------
            Exception: If there is an error downloading data from the EODHD API.
        """
        end_corrected = end
        if period == "m" and complete_month:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            last_day_month = calendar.monthrange(end_dt.year, end_dt.month)[1]
            end_corrected = end_dt.replace(day=last_day_month)
            end_corrected.strftime("%Y-%m-%d")

        logging.info("Requesting data from EODHD API...")
        try:
            data = eodhd.download_multi(
                tickers=tickers, start=start, end=end_corrected, period=period
            )
        except Exception as e:
            raise ValueError(f"Error downloading data from EODHD API: {e}")
            
        return data
    
    @classmethod
    def fetch_eodhd_prices(
        cls, 
        tickers: Union[str, List[str]], 
        start: str,
        end: str,
        period: Optional[str] = "m",
        complete_month: Optional[bool] = False,
        update_mins: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetches EODHD prices from the API.
        
        Parameters
        ----------
        tickers :Union[str, Tuple[str, ...]]
            The tickers to fetch prices for.
        start :str
            The start date.
        end :str
            The end date.
        period :Optional[str]
            The period. Defaults to "m".
        complete_month :Optional[bool]
            Whether to fetch complete month data. Defaults to False.
        update_mins :Optional[int]
            The frequency to update the data in minutes. Defaults to None.
        
        Returns
        -------
            pd.DataFrame: The fetched data.
        
        Raises
        ------
            Exception: If there is an error downloading data from the EODHD API.
        """
        # Get the current time and round it to the nearest update_mins to get new data every update_mins minutes
        if update_mins:
            update_time = (
                datetime.now()
                .replace(minute=(datetime.now().minute // update_mins) * update_mins, second=0, microsecond=0)
                .strftime("%Y-%m-%d %H:%M")
            )
        # Modify the update time variable to get new data every second
        else:
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not isinstance(tickers, list) and not isinstance(tickers, str):
            raise ValueError("Tickers must be a list of strings or a single string")
        tickers = tickers if isinstance(tickers, list) else [tickers]
        return cls._fetch_eodhd_prices(update_time, tuple(tickers), start, end, period, complete_month)
    
    @staticmethod
    @lru_cache(maxsize=None)
    def _fetch_yf_prices(
        update_time: str,
        tickers: Tuple[str, ...], 
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: Optional[str] = "1mo", 
    ) -> pd.DataFrame:
        """
        Fetches EODHD prices from the API.
        
        Parameters
        ----------
        update_time :str
            The time to update the data. This is used to cache the data.
        tickers :Union[str, Tuple[str, ...]]
            The tickers to fetch prices for.
        start :str
            The start date.
        end :str
            The end date.
        period :Optional[str]
            The period. Defaults to "m".
        
        Returns
        -------
            pd.DataFrame: The fetched data.
        
        Raises
        ------
            Exception: If there is an error downloading data from the EODHD API.
        """
        if len(tickers) == 0:
            logging.error("No tickers provided")
            return None
        
        # Dictionary with defined replacements, where each key ends with '$' to indicate the end of the string
        yahoo_ext = {
            "LSE": "L",      # London Stock Exchange
            "EPA": "PA",     # Euronext Paris
            "BIT": "MI",     # Borsa Italiana (Milan)
            "BME": "MC",     # Bolsa de Madrid
            "FRA": "F",      # Frankfurt Stock Exchange
            "AMS": "AS",     # Euronext Amsterdam
            "SWX": "SW",     # Swiss Exchange
            "VIE": "VI",     # Vienna Stock Exchange
            "STO": "ST",     # Nasdaq Stockholm
            "HEL": "HE",     # Nasdaq Helsinki
            "CPH": "CO",     # Nasdaq Copenhagen
            "OSL": "OL",     # Oslo Stock Exchange
            "XETRA": "DE",   # XETRA
        }
        inv_yahoo_ext = {yf_ext: std_ext for std_ext, yf_ext in yahoo_ext.items()}

        # Function to map ticker extensions thrruogh a dictionary
        def map_symbol_extension(symbol: str, extension_map: dict) -> str:
            for extension_in, extension_out in extension_map.items():
                reg_exp = rf"\.{re.escape(extension_in)}$"
                new_extension = f".{extension_out}"
                symbol = re.sub(reg_exp, new_extension, symbol)
            return symbol

        # Apply the replacements to the list of strings
        yf_tickers = [map_symbol_extension(ticker, yahoo_ext) for ticker in tickers]

        kwargs = {
            "tickers": yf_tickers,
            "prepost": False,
            "auto_adjust": False,
            "progress": False,
        }
        if period is not None:
            kwargs["period"] = period
        if start is not None:
            kwargs['start'] = start
        if end is not None:
            kwargs['end'] = end
        
        logging.info("Requesting data from Yahoo Finance API ...")
        try:
            yf_data = yf.download(**kwargs)
        except Exception as e:
            logging.error(f"Error downloading data from Yahoo Finance API: {e}")
            yf_data = None
        
        # If there is only one ticker and the columns are not a MultiIndex, create a MultiIndex
        if len(yf_tickers) == 1 and not isinstance(yf_data.columns, pd.MultiIndex):
            yf_data.columns = pd.MultiIndex.from_product([yf_data.columns, [yf_tickers[0]]], names=['Price', 'Ticker'])
        
        # Replace the ticker extensions to the standard ones
        multiindex_cols = yf_data.columns
        new_multiindex = [
            (price, map_symbol_extension(ticker, inv_yahoo_ext))
            for price, ticker in multiindex_cols
        ]
        yf_data.columns = pd.MultiIndex.from_tuples(new_multiindex)
        
        return yf_data
    
    @classmethod
    def fetch_yf_prices(
        cls, 
        tickers: Union[str, List[str]], 
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: Optional[str] = "1mo", 
        update_mins: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetches EODHD prices from the API.
        
        Parameters
        ----------
        tickers :Union[str, Tuple[str, ...]]
            The tickers to fetch prices for.
        start :str
            The start date.
        end :str
            The end date.
        period :Optional[str]
            The period. Defaults to "m" (monthly).
        update_mins :Optional[int]
            The frequency to update the data in minutes. Defaults to None.
        
        Returns
        -------
        pd.DataFrame
            The fetched data.
        
        Raises
        ------
        Exception: 
            If there is an error downloading data from the EODHD API.
        """
        # Get the current time and round it to the nearest update_mins to get new data every update_mins minutes
        if update_mins:
            update_time = (
                datetime.now()
                .replace(minute=(datetime.now().minute // update_mins) * update_mins, second=0, microsecond=0)
                .strftime("%Y-%m-%d %H:%M")
            )
        # Modify the update time variable to get new data every second
        else:
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        if not isinstance(tickers, list) and not isinstance(tickers, str):
            raise ValueError("Tickers must be a list of strings or a single string")
        tickers = tickers if isinstance(tickers, list) else [tickers]
        return cls._fetch_yf_prices(update_time, tuple(tickers), start, end, period)

    def download_eodhd_prices(
        self, 
        file_name, 
        tickers, 
        start, 
        end, 
        period="m", 
        format: str ="pickle"
    ):
        """
        Downloads data from EODHD API for the given tickers and saves it to a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to save the downloaded data.
        tickers: list
            A list of ticker symbols for the stocks to download data for.
        start: str
            The initial date for the data to download in the format 'YYYY-MM-DD'.
        end: str
            The end date for the data to download in the format 'YYYY-MM-DD'.
        period: str, optional
            The period for the data to download. Defaults to 'm'.
        format: str, optional
            The format to save the downloaded data. Defaults to 'pickle'.
        
        Raises
        ------
        Exception
            If there is an error downloading data from EODHD API.
        
        Returns
        -------
        None
        """
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        last_day_month = calendar.monthrange(end_dt.year, end_dt.month)[1]
        end_corrected = end_dt.replace(day=last_day_month)
        end_corrected.strftime("%Y-%m-%d")

        logging.info("Downloading data from EODHD ...")
        try:
            data = eodhd.download_multi(
                tickers=tickers, start=start, end=end_corrected, period=period
            )
        except Exception as e:
            logging.error(f"Error downloading data from EODHD API: {e}")

        file_path = os.path.join(self.input_data_path, file_name)
        if format == "pickle":
            data.to_pickle(file_path)
        elif format == "excel":
            data.to_excel(file_path)
        elif format == "csv":
            data.to_csv(file_path)
        else:
            logging.error(f"Unsupported format: '{format}'")
            
        logging.info(f"Data downloaded from EODHD API and saved to file '{file_name}'")
    
    def download_yf_prices(
        self, 
        file_name, 
        tickers, 
        start, 
        end, 
        period="1mo", 
        # interval="1mo", 
        format: str ="pickle"
    ):
        """
        Downloads data from Yahoo Finance API for the given tickers and saves it to a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to save the downloaded data.
        tickers: list
            A list of ticker symbols for the stocks to download data for.
        start: str
            The initial date for the data to download in the format 'YYYY-MM-DD'.
        end: str
            The end date for the data to download in the format 'YYYY-MM-DD'.
        period: str, optional
            The period for the data to download. Defaults to '1mo'.
        interval: str, optional
            The interval for the data to download. Defaults to '1mo'.
        format: str, optional
            The format to save the downloaded data. Defaults to 'pickle'.
        
        Raises
        ------
        Exception: 
            If there is an error downloading data from Yahoo Finance API.
        
        Returns
        -------
        None
        """
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not isinstance(tickers, list) and not isinstance(tickers, str):
            raise ValueError("Tickers must be a list of strings or a single string")
        
        tickers = tickers if isinstance(tickers, list) else [tickers]
        yf_data = self._fetch_yf_prices(update_time, tuple(tickers), start, end, period)
        
        file_path = os.path.join(self.input_data_path, file_name)
        if format == "pickle":
            yf_data.to_pickle(file_path)
        elif format == "excel":
            yf_data.to_excel(file_path)
        elif format == "csv":
            yf_data.to_csv(file_path)
        else:
            logging.error(f"Unsupported format: '{format}'")
            
        logging.info(f"Data downloaded from Yahoo Finance API and saved to file '{file_name}'")