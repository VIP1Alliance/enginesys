import concurrent.futures
import logging
import os
import threading
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Configuración del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DataFetcher:
    thread_local = threading.local()
 
    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        self.api_key = api_key
        self.session = session or self._get_session()
        self._dfs: Dict[str, pd.DataFrame] = {}
        self._errors: Dict[str, str] = {}
        self._tickers_bad: Dict[str, Exception] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
 
    def _get_session(self) -> requests.Session:
        """Get or create a session specific to the thread with increased pool size."""
        if not hasattr(self.thread_local, "session"):
            session = requests.Session()
            adapter = HTTPAdapter(
                pool_connections=100,  # Adjust to desired number
                pool_maxsize=100  # Adjust pool size accordingly
            )
            session.mount('https://', adapter)
            session.mount('http://', adapter)
            self.thread_local.session = session
        return self.thread_local.session
 
    @retry(stop=stop_after_attempt(5),  # Intenta 5 veces
           wait=wait_exponential(multiplier=1, min=2, max=10),  # Backoff exponencial
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def download(self, ticker: str, start: str, end: str, period: str = 'd', _filter: Optional[str] = None, format_data: bool = True) -> pd.DataFrame:
        """Download data for a single ticker."""
        base_url = f'https://eodhd.com/api/eod/{ticker}'
        payload = {
            'api_token': self.api_key,
            'period': period,
            'from': start,
            'to': end,
            'fmt': 'json',
            'filter': _filter
        }
 
        try:
            self.logger.debug(f"Sending request to URL: {base_url}")
            response = self.session.get(base_url, params=payload)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            if response.status_code == 429:
                # time.sleep(int(response.headers["Retry-After"]))
                self.logger("--------> Retry-after: {response.headers['Retry-After']}")
 
            data = response.json()
            df = pd.DataFrame(data)
            self.logger.debug(f"Received data for ticker: {ticker}, rows: {len(df)}")
           
            if format_data:
                df = self._format_data(df)
                self.logger.debug(f"Formatted data for ticker: {ticker}")
 
            return df
        except requests.RequestException as req_err:
            self.logger.error(f"Request error for ticker {ticker}: {repr(req_err)}")
            raise
        except Exception as e:
            self._tickers_bad[ticker] = e
            self.logger.error(f"Unexpected error for ticker {ticker}: {repr(e)}")
            return self._empty_df()
 
    def _format_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the downloaded data."""
        df.set_index('date', inplace=True)
        return df
 
    def _empty_df(self) -> pd.DataFrame:
        """Return an empty DataFrame when data is not available."""
        empty = pd.DataFrame({
            'open': np.nan, 'high': np.nan, 'low': np.nan,
            'close': np.nan, 'volume': np.nan, 'adjust_close': np.nan
        })
        empty.index.name = 'Date'
        return empty
 
    @staticmethod
    def format_monthly_data(df: pd.DataFrame) -> pd.DataFrame:
        df.index = pd.to_datetime(df.index)
        df_resampled = df.resample('MS').first()
        return df_resampled
 
    def handle_data(self, ticker: str, start: str, end: str, period: str = 'd', _filter: Optional[str] = None) -> pd.DataFrame:
        """Handle data download and error management for a single ticker."""
        try:
            data = self.download(ticker, start, end, period=period, _filter=_filter)
            if period == 'm':
                data = self.format_monthly_data(data)
            self._dfs[ticker.upper()] = data
        except Exception as e:
            self._dfs[ticker.upper()] = self._empty_df()
            self._errors[ticker.upper()] = repr(e)
            self.logger.error(f"Error for ticker {ticker}: {repr(e)}")
 
        return self._dfs[ticker.upper()]
 
    def download_multi(self, tickers: List[str], start: str, end: str, period: str = 'd', _filter: Optional[str] = None, group_by: str = 'column') -> pd.DataFrame:
        """Download data for multiple tickers concurrently."""
        if isinstance(tickers, str):
            tickers = [tickers]
 
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
            executor.map(lambda ticker: self.handle_data(ticker, start, end, period, _filter), tickers)
 
        data = pd.concat(self._dfs.values(), axis=1, sort=True, keys=self._dfs.keys())
 
        if group_by == 'column':
            data.columns = data.columns.swaplevel(0, 1)
            data.sort_index(level=0, axis=1, inplace=True)
 
        return data