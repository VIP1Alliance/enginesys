#!/usr/bin/env python

import requests
import pandas as pd
import numpy as np
from datetime import date

# import os
import time
import concurrent.futures
import threading
from functools import partial
import logging

logger = logging.getLogger()

# config.py ===========================================================
api_key = '6336087689a527.43617063'

# shared.py ===========================================================
_DFS = {}
_ERRORS = {}
_TICKERS_BAD = {}


# utils.py ============================================================
def empty_df(index):
    if index is None:
        index = []
    empty = pd.DataFrame(index=index, data={
        'open': np.nan, 'high': np.nan, 'low': np.nan,
        'close': np.nan, 'volume': np.nan, 'adjust_close': np.nan
    })
    empty.index.name = 'Date'
    return empty


# Main functions
thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def download(ticker, start, end, period='d', filter_=None,
             format_data=True):
    """
    """
    # _BASE_URL_ = f'https://eodhd.com/api/eod/{ticker}'

    # payload = {'api_token': api_key,
    #            'period': period,
    #            'from': start,
    #            'to': end,
    #            'fmt': 'json',
    #            'filter': _filter}
    # try:
    #     session = get_session()
    #     r = session.get(_BASE_URL_, params=payload)
    #     data = r.json()
    #     df = pd.DataFrame(data)

    #     if format_data:
    #         df = formatData(df)

    #     # print(f"\nX-RateLimit-Limit: {r.headers['X-RateLimit-Limit']}")
    #     # print(f"X-RateLimit-Remaining: {r.headers['X-RateLimit-Remaining']}\n")
    #     return df

    # except Exception as e:
    #     _TICKERS_BAD[ticker] = e
    _BASE_URL = f'https://eodhd.com/api/eod/{ticker}'

    payload = {'api_token': api_key,
               'period': period,
               'from': start,
               'to': end,
               'fmt': 'json',
               'filter': filter_}
    try:
        session = get_session()
        response = session.get(_BASE_URL, params=payload)
        if response.status_code == 200:
            data = response.json()
            if format_data:
                df = formatData(pd.DataFrame(data))
                return df
            return pd.DataFrame(data)
        else:
            # Log error if API request fails
            logger.error(f"Failed to fetch data for ticker {ticker}. HTTP Status Code: {response.status_code}")
            return None
    except Exception as e:
        # Log error if any exception occurs
        logger.error(f"An error occurred while downloading data for ticker {ticker}: {e}")
        return None


def formatData(df):
    """
    """
    # set index

    df.set_index('date', inplace=True)

    # adjust prices

    return df


def format_monthly_data(df):
    """
    """
    df = (df.reset_index())
    df["date"] = pd.to_datetime(df["date"])
    df["test"] = df["date"].dt.to_period('M')
    df["date"] = df["test"]
    df.drop(["test"], axis=1, inplace=True)
    df = df.set_index("date")

    return df


def handle_data(ticker, start, end, period='d', filter_=None):
    data = None

    try:
        data = download(ticker, start, end, period=period, filter_=None)
        if period == 'm':
            data = format_monthly_data(data)
    except Exception as e:
        _DFS[ticker.upper()] = empty_df()
        _ERRORS[ticker.upper()] = repr(e)
    else:
        _DFS[ticker.upper()] = data
    return data


def download_multi(tickers, start, end, period='d', filter_=None,
                   group_by='column'):
    """
    Parameters
    ----------
    tickers: list or string
        Contains a list of all tickers required.
    start: int
        Start date - the format is 'YYYY-MM-DD'.
    end: int
        End date - the format is 'YYYY-MM-DD'.
    period: int
        Use 'd' for daily, 'w' for weekly, 'm' for monthly prices.
        By default, daily prices will be shown.
    _filter: int
        Use 'Open', 'High', 'Low', 'Close', 'Adjusted_close', 'Volume'.
        By default, all columns will be shown.
    group_by: str
        Group by 'ticker' or 'column'. By default value eqaula to "column".

    """
    if isinstance(tickers, str):
        tickers = [tickers]

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(partial(handle_data, start=start, end=end,
                             period=period, filter_=filter_),
                     tickers)

    data = pd.concat(_DFS.values(), axis=1, sort=True, keys=_DFS.keys())

    if group_by == 'column':
        data.columns = data.columns.swaplevel(0, 1)
        data.sort_index(level=0, axis=1, inplace=True)

    return data


if __name__ == "__main__":

    initial_time = time.time()
    start = "2023-01-01"
    end = date.today()
    # r = download("JEDG.LSE", start=start, end=end,
    #              period='m', format_data=True)
    # print(r)

    multi = download_multi(tickers=["JEDG.LSE", "SETP.LSE", "MSFT", "NVDA"],
                           start=start, end=end, period='m')

    print(multi)
    multi.to_pickle("data.pkl")

    print(f"\n Elapsed time: {(time.time() - initial_time):.3} seconds.\n")
