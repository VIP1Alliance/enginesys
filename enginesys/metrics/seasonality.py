import logging

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ======================================================================================= #
# ======================= Methods to calculate the GEA indices ======================== #
# ======================================================================================= #

class SeasonalityMetrics:
    
    def __init__(self, trades_df: pd.DataFrame, vpv_pv: int, investment: int):
        self.trades_df = trades_df      # Trades DataFrame
        self.vpv_pv = vpv_pv            # Variation point value in dollars
        self.investment = investment    # Investment Capital in dollars
    
    @staticmethod
    def gen_one_month_trades_df(trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates a DataFrame containing trades for each month.
        
        Parameters
        ----------
        trades_df: pd.DataFrame
            DataFrame containing trades data.
        
        Returns
        -------
        pd.DataFrame: 
            DataFrame containing trades for each month.
        """
        dfs = []
        for month in range(1, 13):
            if month == 12:
                cond1 = trades_df["date_open_next_month"].dt.month == 12
                cond2 = trades_df["date_close_next_month"].dt.month == 1
                cond3 = trades_df["date_open_next_month"].dt.year + 1 == trades_df["date_close_next_month"].dt.year
            else:
                cond1 = trades_df["date_open_next_month"].dt.month == month
                cond2 = trades_df["date_close_next_month"].dt.month == month + 1
                cond3 = trades_df["date_open_next_month"].dt.year == trades_df["date_close_next_month"].dt.year

            trades_month_df = trades_df[cond1 & cond2 & cond3].copy()
            
            dfs.append(trades_month_df)
        
        one_month_trades_df =  pd.concat(dfs)
        
        return one_month_trades_df

    @staticmethod
    def get_year_metrics(trades_df: pd.DataFrame, vpv_pv: int, investment: int) -> pd.DataFrame:
        """
        Calculate year metrics based on the given trades dataframe.
        
        Parameters
        ----------
        trades_df: pd.DataFrame
            The trades dataframe containing the necessary data.
        vpv_pv: int
            The value per point per volume.
        investment: int
            The total investment amount.
        
        Returns
        -------
        pd.DataFrame
            The calculated year metrics dataframe.
        """

        def get_performance_alg(x):
            """
            Calculates the performance value of a given input.
            """
            return_sum = x.sum()
            performance_val = (return_sum * vpv_pv) / investment
            return performance_val*100

        def get_max_loss(x):
            """
            Calculates the maximum loss value based on the given input.
            """
            loss_value = (x.min() * vpv_pv) / investment
            loss_value  = (x.min() * vpv_pv) / investment
            return loss_value
        
        trades_df["year"] = trades_df["date_open_next_month"].apply(lambda x: x.year)
        trades_df["month"] = trades_df["date_open_next_month"].apply(lambda x: x.month)

        year_metrics = trades_df.groupby(["month", "year"]).agg(
            performance_alg=pd.NamedAgg(column='result_dollars', aggfunc=get_performance_alg),
            max_loss=pd.NamedAgg(column='result_dollars', aggfunc=get_max_loss)
        )
        
        mean_performance = year_metrics.groupby(by="month")["performance_alg"].mean()
        
        trades_df["crp"] = (
            trades_df["result_dollars"]
            >= trades_df["month"].map(mean_performance)
        ).astype(int)
        
        # Crear una nueva columna con los valores a restar basados en 'Category'
        year_metrics["year_crp"] = trades_df.groupby(["month", "year"])["crp"].sum() / 2
        year_metrics["math_expectation"] = np.where(
            year_metrics["performance_alg"] < 0,
            1 - year_metrics["year_crp"],
            year_metrics["year_crp"],
        )
        return year_metrics

    def gen_seasonality(self) -> pd.DataFrame:
        """
        Generates seasonality metrics based on the trades data.
        """
        self.one_month_trades_df = self.gen_one_month_trades_df(self.trades_df)
        self.year_metrics = self.get_year_metrics(
            self.one_month_trades_df, self.vpv_pv, self.investment
        )
        self.seasonality_df = self.year_metrics.groupby(level="month")[
            ["performance_alg", "max_loss", "math_expectation"]
        ].mean()