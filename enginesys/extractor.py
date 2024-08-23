import calendar
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd
import yfinance as yf

import enginesys.eodhd.eodhd as eodhd


class DataExtractor:

    def __init__(self, data_path):
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        os.makedirs(self.output_data_path, exist_ok=True)
    
    
    @staticmethod
    @lru_cache(maxsize=None)
    def fetch_eodhd_prices(
        tickers: Union[str, Tuple[str, ...]], 
        start: str, 
        end: str, 
        period: str = "m",
        complete_month: bool = False,
        date: str = datetime.now().strftime("%Y-%m-%d %H:%M"),
    ) -> pd.DataFrame:
        end_corrected = end
        if period == "m" and complete_month:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            last_day_month = calendar.monthrange(end_dt.year, end_dt.month)[1]
            end_corrected = end_dt.replace(day=last_day_month)
            end_corrected.strftime("%Y-%m-%d")

        logging.info("Requesting data from EODHD ...")
        try:
            data = eodhd.download_multi(
                tickers=tickers, start=start, end=end_corrected, period=period
            )
        except Exception as e:
            logging.error(f"Error downloading data from EODHD API: {e}")
            
        return data
    
    
    @staticmethod
    @lru_cache(maxsize=None)
    def fetch_yf_prices(
        tickers: Union[str, Tuple[str, ...]], 
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "1mo", 
        interval: str = "1mo", 
        date: str = datetime.now().strftime("%Y-%m-%d %H:%M"),
    ) -> pd.DataFrame:
        
        if len(tickers ) == 0:
            logging.error("No tickers provided")
            return None
        
        # Dictionary with defined replacements, where each key ends with '$' to indicate the end of the string
        extensions_dict = {
            r"\.LSE$": ".L",      # London Stock Exchange
            r"\.EPA$": ".PA",     # Euronext Paris
            r"\.BIT$": ".MI",     # Borsa Italiana (Milan)
            r"\.BME$": ".MC",     # Bolsa de Madrid
            r"\.FRA$": ".F",      # Frankfurt Stock Exchange
            r"\.AMS$": ".AS",     # Euronext Amsterdam
            r"\.SWX$": ".SW",     # Swiss Exchange
            r"\.VIE$": ".VI",     # Vienna Stock Exchange
            r"\.STO$": ".ST",     # Nasdaq Stockholm
            r"\.HEL$": ".HE",     # Nasdaq Helsinki
            r"\.CPH$": ".CO",     # Nasdaq Copenhagen
            r"\.OSL$": ".OL",     # Oslo Stock Exchange
            r"\.XETRA$": ".DE",   # XETRA
        }

        # Function to apply replacements using the dictionary
        def get_yf_extensions(symbol, extensions_dict):
            for extension, yf_extension in extensions_dict.items():
                symbol = re.sub(extension, yf_extension, symbol)
            return symbol

        # Apply the replacements to the list of strings
        yf_tickers = [get_yf_extensions(ticker, extensions_dict) for ticker in tickers]

        kwargs = {
            "tickers": yf_tickers,
            "period": period,
            "interval": interval,
            "prepost": False,
            "auto_adjust": False,
        }
        if start is not None:
            kwargs['start'] = start
        if end is not None:
            kwargs['end'] = end
        
        logging.info("Downloading data from Yahoo Finance API ...")
        try:
            yf_data = yf.download(**kwargs)
        except Exception as e:
            logging.error(f"Error downloading data from Yahoo Finance API: {e}")
            yf_data = None
            
        return yf_data


    def download_eodhd_prices(self, file_name, tickers, start, end, period="m", format: str ="pickle"):
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
        force_download: bool, optional
            Whether to force download the data even if it was previously downloaded. Defaults to False.
        
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

    
    def download_yf_prices(self, file_name, tickers, start, end, period="1mo", interval="1mo", format: str ="pickle"):
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
        force_download: bool, optional
            Whether to force download the data even if it was previously downloaded. Defaults to False.
        
        Raises
        ------
        Exception: 
            If there is an error downloading data from Yahoo Finance API.
        
        Returns
        -------
        None
        """
        # Dictionary with defined replacements, where each key ends with '$' to indicate the end of the string
        extensions_dict = {
            r"\.LSE$": ".L",      # London Stock Exchange
            r"\.EPA$": ".PA",     # Euronext Paris
            r"\.BIT$": ".MI",     # Borsa Italiana (Milan)
            r"\.BME$": ".MC",     # Bolsa de Madrid
            r"\.FRA$": ".F",      # Frankfurt Stock Exchange
            r"\.AMS$": ".AS",     # Euronext Amsterdam
            r"\.SWX$": ".SW",     # Swiss Exchange
            r"\.VIE$": ".VI",     # Vienna Stock Exchange
            r"\.STO$": ".ST",     # Nasdaq Stockholm
            r"\.HEL$": ".HE",     # Nasdaq Helsinki
            r"\.CPH$": ".CO",     # Nasdaq Copenhagen
            r"\.OSL$": ".OL",     # Oslo Stock Exchange
            r"\.XETRA$": ".DE",   # XETRA
        }

        # Function to apply replacements using the dictionary
        def get_yf_extensions(symbol, extensions_dict):
            for extension, yf_extension in extensions_dict.items():
                symbol = re.sub(extension, yf_extension, symbol)
            return symbol

        # Apply the replacements to the list of strings
        yf_tickers = [get_yf_extensions(ticker, extensions_dict) for ticker in tickers]

        logging.info("Downloading data from Yahoo Finance API ...")
        try:
            yf_data = yf.download(
                yf_tickers,
                start=start,
                end=end,
                period=period,
                interval=interval,
                prepost=False,
                auto_adjust=False,
            )
        except Exception as e:
            logging.error(f"Error downloading data from Yahoo Finance API: {e}")
        
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