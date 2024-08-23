import logging
import stat

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
pd.DataFrame()

# ======================================================================================= #
# ======================= Functions to calculate the GEA indices ======================== #
# ======================================================================================= #

class TradeProcessor:

    @staticmethod
    def split_trades_monthly(trades_df: pd.DataFrame, open_date_column: str, close_date_column: str):
        """
        Splits trades in the given DataFrame into monthly intervals based on the open and close dates.

        Parameters
        ----------
        trades_df : pd.DataFrame
            The DataFrame containing the trades data.
        open_date_column : str
            The name of the column in trades_df that represents the open date of each trade.
        close_date_column : str
            The name of the column in trades_df that represents the close date of each trade.

        Returns
        -------
        pd.DataFrame
            A new DataFrame with the trades split into monthly intervals.
        """

        aux_df = trades_df.copy()

        def months_by_trade(row):
            months = pd.date_range(
                start=row[open_date_column],
                end=row[close_date_column],
                freq="MS",
            )[:-1]
            return months

        aux_df.insert(0, "date", aux_df.apply(months_by_trade, axis=1))
        splitted_trades_df = aux_df.explode("date", ignore_index=True)
        return splitted_trades_df
    
    @staticmethod
    def get_prices(prices_df: pd.DataFrame, tickers: list, dates: list) -> tuple:
            """
            Extract close and open prices for given tickers and dates. If a price is not found, it is set to None.

            Parameters
            ----------
            prices_df : pd.DataFrame
                DataFrame containing adjusted close prices with dates as indices and tickers as columns.
            tickers : list
                List of ticker symbols.
            dates : list
                List of dates in 'YYYY-MM-DD' format.

            Returns
            -------
            tuple
                Two lists containing the close and open prices respectively.
            """
            open_prices = []
            close_prices = []

            for ticker, date in zip(tickers, dates):
                try:
                    close_date = date
                    open_date = date - relativedelta(months=1)
                    open_price = prices_df.loc[open_date, ticker]
                    close_price = prices_df.loc[close_date, ticker]
                except KeyError as e:
                    logging.error(
                        f"Ticker price ({ticker}) for date ({close_date}) was not found in the price table: Error: {e}"
                    )
                    open_price, close_price = None, None

                open_prices.append(open_price)
                close_prices.append(close_price)

            return open_prices, close_prices

    @classmethod
    def assing_prices(
        cls, trades_df: pd.DataFrame, prices_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add columns with open and close prices to each trade based on the trade date and ticker symbol. 
        If a price is not found, it is set to None.

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame containing trade information.
        prices_df : pd.DataFrame
            DataFrame containing price information.
        pd.DataFrame
            DataFrame with trade information and corresponding open and close prices.

        Returns
        -------
        pd.DataFrame
            A copy of the Trades DataFrame with the Open and Close price columns added.
        """

        trades_df = trades_df.copy()
        open_prices, close_prices = cls.get_prices(
            prices_df, tickers=trades_df["ticker"], dates=trades_df["date"]
        )

        trades_df = trades_df.assign(open_price=open_prices, close_price=close_prices)

        return trades_df

    @staticmethod
    def compute_variations(trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add column with the variation rate for each trade based on the open and close prices and the trade side.

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame containing trade data with open and close prices.

        Returns
        -------
        pd.DataFrame
            DataFrame with the variation rate for each trade.
        """
        trades_df = trades_df.copy()

        # Rule to assign variation rate according to the value of "side"
        trades_df["variation"] = np.where(
            trades_df["side"] == "SELL",
            trades_df["open_price"] / trades_df["close_price"],
            trades_df["close_price"] / trades_df["open_price"],
        )

        return trades_df

    @staticmethod
    def assign_weights(
        trades_df: pd.DataFrame,
        strategy_weights: dict,
        total_investment: float,
    ) -> pd.DataFrame:
        """
        Calculate the weights for each trade based on the strategy weights and the total investment amount.
        The weights are calculated based on the number of trades per month for each strategy. 
        The global and local weights are also calculated.

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame containing trade data with strategy information.
        strategy_weights : dict
            Dictionary containing the strategy weights.
        total_investment : float
            Total investment amount in USD.

        Returns
        -------
        pd.DataFrame
            DataFrame with the weights assigned to each trade.
        """
        # Generate montly data for each strategy.
        strategy_trades_dfs = []
        for strategy in trades_df["strategy"].unique():
            strategy_trades_df = trades_df[trades_df["strategy"] == strategy].copy()
            strategy_weight = strategy_weights[strategy]

            # Investment for strategy
            strategy_investment = total_investment * strategy_weight

            # Trades per month
            trades_by_month = strategy_trades_df.groupby("date").size()

            # Add global and local weights columns
            strategy_trades_df["assignation"] = strategy_trades_df["date"].apply(
                lambda x: strategy_investment / trades_by_month[x]
            )
            strategy_trades_df["weight_by_strategy(%)"] = strategy_trades_df[
                "date"
            ].apply(lambda x: 100 / trades_by_month[x])
            strategy_trades_df["weight_by_portfolio(%)"] = strategy_trades_df[
                "weight_by_strategy(%)"
            ].apply(lambda x: strategy_weight * x)

            strategy_trades_df = strategy_trades_df.sort_values(
                by=["date", "sector"]
            ).reset_index(drop=True)

            strategy_trades_dfs.append(strategy_trades_df)

        trades_and_weights_df = pd.concat(strategy_trades_dfs, axis=0)

        return trades_and_weights_df

    def gen_monthly_trades_dataset(
        self,
        trades_df: pd.DataFrame,
        prices_df: pd.DataFrame,
        strategy_weights: dict,
        investment: float,
        init_date: str,
        end_date: str,
        open_date_column: str,
        close_date_column: str,
    ) -> pd.DataFrame:
        """
        Generate a monthly trades dataset based on the given parameters. The dataset will contain the 
        trades data, prices data, strategy weights, investment amount, and date range for filtering trades. 
        The dataset will be used to calculate the monthly performance of the trading strategies.

        Parameters
        ----------
        trades_df : pd.DataFrame
            DataFrame containing trades data.
        prices_df : pd.DataFrame
            DataFrame containing prices data.
        strategy_weights : dict
            Dictionary containing strategy weights.
        investment : float
            Total investment amount in USD.
        init_date : str
            Initial date for filtering trades.
        end_date : str
            End date for filtering trades.
        open_date_column : str
            Column name for open date in trades_df.
        close_date_column : str
            Column name for close date in trades_df.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the generated monthly trades dataset.
        """
        monthly_trades_df = self.split_trades_monthly(trades_df, open_date_column, close_date_column)
        logging.info(f"Monthly trades dataset generated with {len(monthly_trades_df)} trades.")
        monthly_trades_df = monthly_trades_df[(monthly_trades_df["date"] >= init_date) & (monthly_trades_df["date"] <= end_date)]
        monthly_trades_df = self.assing_prices(monthly_trades_df, prices_df)
        logging.info(f"Prices assigned to the trades dataframe.")
        monthly_trades_df = self.compute_variations(monthly_trades_df)
        logging.info(f"Variations computed for the trades dataframe.")
        monthly_trades_df = self.assign_weights(monthly_trades_df, strategy_weights, investment)
        logging.info(f"Weights assigned to the trades dataframe.")
        monthly_trades_df = monthly_trades_df.reset_index(drop=True)
        return monthly_trades_df

    @staticmethod
    def truncate_by_period(
        data: pd.DataFrame,
        date_column_name: str = "",
        period_type="year",
        n_periods=0,
        last_date=None,
    ) -> pd.DataFrame:
        """
        Truncates a DataFrame by a given number of periods. The period type can be either 'year' or 'month'. The last date to include in the truncated DataFrame can be provided.

        Parameters
        ----------
        data: pd.DataFrame
            The DataFrame to be truncated.
        date_column_name: str, optional
            The name of the date column in the DataFrame. If not provided, the index column will be used as the date column. Defaults to "".
        period_type: str, optional
            The type of period to truncate by. Should be either 'year' or 'month'. Defaults to "year".
        n_periods: int, optional
            The number of periods to truncate. Defaults to 0.
        last_date: str, optional
            The last date to include in the truncated DataFrame. If not provided, the maximum date in the date column will be used. Defaults to None.

        Returns
        -------
        pd.DataFrame
            The truncated DataFrame.
        """
        if date_column_name:
            date_column = data[date_column_name]
        else:
            index_name = data.index.name
            data = data.reset_index()
            date_column = data[index_name]

        if last_date:
            if last_date in date_column.values:
                data = data[date_column <= last_date]
            else:
                raise ValueError(f"Last date '{last_date}' is not in the date column")
        else:
            last_date = date_column.max()

        if period_type in ["year", "month"]:
            months_multiplier = 1 if period_type == "month" else 12
        else:
            raise ValueError("Period type should be either 'year' or 'month'")

        total_mounths = n_periods * months_multiplier
        new_init_date = last_date - pd.DateOffset(months=total_mounths)
        truncated_data = data[date_column >= new_init_date]

        if not date_column_name:
            truncated_data = truncated_data.set_index(index_name)

        truncated_data = truncated_data.reset_index(drop=True)
        return truncated_data
    
    
class PricesProcessor:
    
    @staticmethod
    def fill_missing_prices(prices_df1, prices_df2):
        """
        Fill missing prices in prices_df1 with corresponding values from prices_df2.
        Missing prices are identified as zeros and NaNs in prices_df1.
        
        Parameters
        ----------
        prices_df1: pd.DataFrame
            The DataFrame containing prices with missing values.
        prices_df2: pd.DataFrame
            The DataFrame containing prices to fill the missing values.
        
        Returns
        -------
        DataFrame: 
            The DataFrame with missing prices filled using values from prices_df2.
        """
        
        # Fill missing prices in prices_df1 with corresponding values from prices_df2
        filled_prices_df1 = prices_df1.replace(0, np.nan).fillna(prices_df2)

        return filled_prices_df1