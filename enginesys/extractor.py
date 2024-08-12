import calendar
import logging
import os
import re
from datetime import datetime

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
        
        self.last_eodhd_download = {
            "file_name": "",
            "tickers": [],
            "init_date": "",
            "end_date": "",
            "period": "",
            "date": "",
        }
        
        self.last_yahoo_download = {
            "file_name": "",
            "tickers": [],
            "init_date": "",
            "end_date": "",
            "period": "",
            "interval": "",
            "date": "",
        }

    def download_eodhd_data(self, file_name, tickers, init_date, end_date, period="m", format: str ="pickle", force_download=False):
        """
        Downloads data from EODHD API for the given tickers and saves it to a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to save the downloaded data.
        tickers: list
            A list of ticker symbols for the stocks to download data for.
        init_date: str
            The initial date for the data to download in the format 'YYYY-MM-DD'.
        end_date: str
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
        new_eodhd_download = {
            "file_name": file_name,
            "format": format,
            "tickers": tickers,
            "init_date": init_date,
            "end_date": end_date,
            "period": period,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        if new_eodhd_download != self.last_eodhd_download or force_download:
            print("Downloading new data from EODHD ...")
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
            last_day_month = calendar.monthrange(end_date_dt.year, end_date_dt.month)[1]
            end_date_corrected = end_date_dt.replace(day=last_day_month)
            end_date_corrected.strftime("%Y-%m-%d")

            try:
                data = eodhd.download_multi(
                    tickers=tickers, start=init_date, end=end_date_corrected, period=period
                )
            except Exception as e:
                print(f"Error downloading data from EODHD API: {e}")

            file_path = os.path.join(self.input_data_path, file_name)
            if format == "pickle":
                data.to_pickle(file_path)
            elif format == "excel":
                data.to_excel(file_path)
            elif format == "csv":
                data.to_csv(file_path)
            else:
                logging.error(f"Unsupported format: '{format}'")
                
            print(f"Data downloaded from EODHD API and saved to file '{file_name}'")
            self.last_eodhd_download = new_eodhd_download

        else:
            print("No new data downloaded from EODHD")
            
    
    def download_yahoo_data(self, file_name, tickers, init_date, end_date, period="1mo", interval="1mo", format: str ="pickle", force_download=False):
        """
        Downloads data from Yahoo Finance API for the given tickers and saves it to a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to save the downloaded data.
        tickers: list
            A list of ticker symbols for the stocks to download data for.
        init_date: str
            The initial date for the data to download in the format 'YYYY-MM-DD'.
        end_date: str
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
        new_yahoo_download = {
            "file_name": file_name,
            "tickers": tickers,
            "init_date": init_date,
            "end_date": end_date,
            "period": period,
            "interval": interval,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        if new_yahoo_download != self.last_yahoo_download or force_download:
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

            try:
                yf_data = yf.download(
                    yf_tickers,
                    start=init_date,
                    end=end_date,
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
        
        else:
            logging.info("No new data downloaded from Yahoo Finance")
            

    def read_data(self, file_name: str, format: str ="pickle") -> pd.DataFrame:
        """
        Reads data from a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to read.
        format: str, optional
            The format of the file. Defaults to "pickle".
        
        Returns
        -------
        pandas.DataFrame: 
            The loaded data.
        
        Raises:
        -------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the format is not supported.
        """
        file_path = os.path.join(self.input_data_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_name}' was not found in the path '{self.input_data_path}'")
        if format == "pickle":
            data = pd.read_pickle(file_path)
        elif format == "excel":
            data = pd.read_excel(file_path)
        elif format == "csv":
            data = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported format: '{format}'")

        logging.info(f"Data loaded from file '{file_name}'")

        return data

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

    def validate_tickers(data_df: pd.DataFrame, tickers: list):
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
        data_df.columns.names = ["type", "symbol"]
        existing_tickers = list(data_df.columns.get_level_values("symbol").unique())
        missing_tickers = set(tickers) - set(existing_tickers)

        if len(missing_tickers) > 0:
            logging.warning(
                f"Some tickers were not found in the data source:\n"
                f"\tMissing tickers: {missing_tickers}"
            )

        return data_df

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
