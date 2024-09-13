import logging
from datetime import datetime

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
from datetime import timedelta


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MarketManager:

    def __init__(self):
        pass
    
    @staticmethod
    def check_market_status(market_name: str, date: datetime, time_zone: str) -> str:
        market_cal = mcal.get_calendar(market_name)
        valid_days = market_cal.valid_days(
            start_date=date.replace(day=1),
            end_date=date.replace(day=1, month=date.month + 1) - timedelta(days=1),
        )
        is_business_day = date.date() in valid_days.date

        if is_business_day:
            
            time_zone = "America/Bogota"
            market_schedule = market_cal.schedule(start_date=date, end_date=date, tz=time_zone)

            date_ts = pd.Timestamp(date, tz=time_zone)
            
            if date_ts < market_schedule.loc[date.strftime("%Y-%m-%d"), "market_open"]:
                market_status = "Not Opened"
            elif date_ts >= market_schedule.loc[date.strftime("%Y-%m-%d"), "market_close"]:
                market_status = "Closed"
            else:
                market_status = "Opened"
                
        else:
            raise ValueError(f"The date '{date.date()}' is not a business day in '{market_name}'")

        return market_status

    @staticmethod
    def get_holidays_market(market_name: str, start_date: str, end_date: str):
        market_cal = mcal.get_calendar(market_name)
        all_holidays = market_cal.holidays().holidays
        holidays_in_range = [
            holiday
            for holiday in all_holidays
            if np.datetime64(start_date) <= holiday <= np.datetime64(end_date)
        ]
        return pd.DatetimeIndex(holidays_in_range)
