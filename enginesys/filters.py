""" This is where all related to filters is located"""
import os
import logging
import warnings
from typing import Tuple, List, Optional

import pandas as pd
import numpy as np

BASE_DIR = os.getcwd()

def get_asg_ranking() -> pd.DataFrame: return pd.read_excel(os.path.join(BASE_DIR, "data", "rankingASG.xlsx"))
def selected_sectors() -> pd.DataFrame: return pd.read_excel(os.path.join(BASE_DIR, "models", "filter_sectors.xlsx"))

def assign_ranking_asg(df: pd.DataFrame, ranking_df: pd.DataFrame,
                       ranking_column: str = "calificación de sostenibilidad",
                       ticker_asg: str = "ticker",
                       ticker_model: str = "ticker") -> pd.DataFrame:
    """
    Assigns sustainability ratings from ranking_df to df based on the ticker symbol.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the tickers.
    ranking_df : pd.DataFrame
        DataFrame containing the sustainability ratings.
    ranking_column : str
        The column name in ranking_df that contains the sustainability ratings.
    ticker_asg : str
        The column name in ranking_df that contains the ticker symbols.
    ticker_model : str
        The column name in df that contains the ticker symbols.

    Returns
    -------
    pd.DataFrame
        DataFrame with the sustainability ratings assigned.
    """
    try:
        # Ensure the ranking_df index is the ticker column
        if ranking_df.index.name != ticker_asg:
            ranking_df = ranking_df.set_index(ticker_asg)

        # # Drop ticker duplicates in ranking_df to avoid multiple assignments | GENERATES ISSUES
        # ranking_df = ranking_df.drop_duplicates(subset=[ticker_asg], keep='first')
        
        # Merge the dataframes on the ticker columns
        result_df = df.merge(ranking_df[[ranking_column]], left_on=ticker_model, right_index=True, how='left').dropna()

        # Rename the merged column to "RANKING ASG"
        result_df.rename(columns={ranking_column: "ranking_asg"}, inplace=True)
        result_df['ranking_asg'] = result_df['ranking_asg'].astype('int64')


        # Check for missing tickers
        ranking_tickers = list(ranking_df.index)
        df_tickers = list(df[ticker_model])
        not_found = [i for i in df_tickers if not(i in ranking_tickers)]
        if len(not_found) != 0:
            warnings.warn(f"Tickers not found in ASG ranking database: {not_found}")

        # Log success
        logging.info("Sustainability ratings assigned successfully.")
        return result_df

    except Exception as e:
        logging.error(f"An error occurred during the assignment of sustainability ratings: {e}")
        raise

class Filters:
    """
    A class to apply various financial filters on recommendations data.
    """
    def __init__(self, recommendations: pd.DataFrame, filter_sectors: pd.DataFrame) -> None:
        self.recommendations = recommendations
        self.filter_sectors = filter_sectors

    @property
    def filter_sectors(self):
        return self._filter_sectors
    
    @filter_sectors.setter
    def filter_sectors(self, filter_sec: pd.DataFrame):
        self._filter_sectors = filter_sec

    # Build filter ASG (this filter is just read from external source)
    def build_filter_asg(self):
        """
        Implement once there is a clear path for it!!!
        """
        raise ("Not implemented.")

    # Load filter threshold 1.6
    @staticmethod
    def _get_filter_threshold() -> pd.DataFrame: return selected_sectors()

    # Load filter ASG
    @staticmethod
    def _get_filter_asg() -> pd.DataFrame: return get_asg_ranking()

    # Apply filter threshold 1.6
    def filter_threshold(self) -> pd.DataFrame:
        """
        Applies the threshold 1.6 filter on the recommendations data.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the filtered recommendations based on the threshold 1.6 criteria.

        Raises
        ------
        AssertionError
            If no sectors are selected after applying the filter.
        """
        result = pd.merge(self.recommendations, self.filter_sectors, how='left', on=['strategy', 'sector'])
        buy_ = result[(result["side"] == "BUY") & (result["buy"] == 1)]
        sell_ = result[(result["side"] == "SELL") & (result["sell"] == 1)]
        df1 = pd.concat([buy_, sell_], axis=0)
        df1 = df1.drop(["enter", "buy", "sell"], axis=1)
        assert df1.shape[0] != 0, "No sectors were selected, please check the data."
        return df1

    # Apply filter ASG
    def filter_asg(self, column_ranking: str = "ranking_asg",
                   no_ranking_tag: str = 'No reporta') -> pd.DataFrame:
        """
        Applies the ASG filter on the recommendations data.

        Parameters
        ----------
        column_ranking : str, optional
            The name of the column containing the ASG ranking data (default is "ranking_asg").
        no_ranking_tag : str, optional
            The tag used to indicate that a recommendation does not have an ASG ranking
            (default is 'No reporta').

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the filtered recommendations based on the ASG ranking criteria.
        """
        ranking = self._get_filter_asg()
        ticker_asg = assign_ranking_asg(df=self.recommendations, ranking_df=ranking, ticker_model='ticker')
        ticker_asg[column_ranking] = ticker_asg[column_ranking].replace(no_ranking_tag, 0) 
        ticker_asg[column_ranking] = ticker_asg[column_ranking].replace(no_ranking_tag, -1)
        if ticker_asg[column_ranking].dtype == 'O':
            ticker_asg[column_ranking] = ticker_asg[column_ranking].astype('int32')
        mean = round(ticker_asg[column_ranking].mean(), 2)
        selected = "selected"
        if mean >= 3:
            ticker_asg[selected] = 1
        elif mean >= 2:
            ticker_asg[selected] = np.where(ticker_asg[column_ranking].isin([3, 4, 5]), 1, 0)
        elif mean >= 1:
            ticker_asg[selected] = np.where(ticker_asg[column_ranking].isin([4, 5]), 1, 0)
        else:
            ticker_asg[selected] = 0
        filtered = ticker_asg[ticker_asg["selected"] == 1].drop(columns=[selected])
        return filtered


class FilterThreshold():
    """
    A class to apply the 1.6 filter over ETFs sectors within a DataFrame.

    This class is designed to filter sector data based on specific criteria 
    (such as a threshold of 1.6 on the absolute max/min ratio) and format 
    the data for further processing.
    """
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        pass

    def __repr__(self) -> str:
        return f"<DataFrame with columns {list(self.df.columns)}>"

    @staticmethod
    def format_data(df: pd.DataFrame, strategy_col: str = "estrategia", sector_col: str = "sector", 
                side_col: str = "side", enter_value: int = 1) -> pd.DataFrame:
        """
        Formats the input DataFrame by grouping by 'strategy', 'sector', and 'side', 
        and performing one-hot encoding on the 'side' column.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame containing strategy, sector, and side columns.
        strategy_col : str
            The name of the strategy column in the DataFrame.
        sector_col : str
            The name of the sector column in the DataFrame.
        side_col : str
            The name of the side column in the DataFrame.
        enter_value : int
            The value to assign to the 'enter' column.

        Returns
        -------
        pd.DataFrame
            The formatted DataFrame with columns 'strategy', 'sector', 'enter', 'buy', and 'sell'.
        
        Raises
        ------
        ValueError
            If the required columns are missing from the input DataFrame.
        """
        # Validate that the necessary columns exist
        required_columns = {strategy_col, sector_col, side_col}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        if strategy_col == 'estrategia':
            df = df.rename(columns={strategy_col: 'strategy'})
            strategy_col = 'strategy'

        # Group by 'estrategia', 'sector', and 'side', then count occurrences
        filter_sectors = df.groupby([strategy_col, sector_col, side_col]).size().reset_index(name="count")

        # One-hot encode the 'side' column
        o_h_e = pd.get_dummies(filter_sectors[side_col])

        # Sum 'BUY' and 'SELL' within each 'estrategia' and 'sector'
        filter_sec = pd.concat([filter_sectors.drop(columns=[side_col, "count"]), o_h_e], axis=1)
        filter_sec = filter_sec.groupby([strategy_col, sector_col])[["BUY", "SELL"]].sum().reset_index()

        # Add 'enter' column with value 1
        filter_sec["enter"] = enter_value

        # change label columns
        filter_sec = filter_sec.rename(columns={"BUY": "buy", "SELL": "sell"})

        return filter_sec[[strategy_col, sector_col, "enter", "buy", "sell"]]

    @staticmethod
    def filter_positions(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Separates the DataFrame into buy and sell positions based on the 'side' column.
        """
        buy_df = df[df['side'] == 'BUY']
        sell_df = df[df['side'] == 'SELL']
        return buy_df, sell_df

    @staticmethod
    def filter_condition(df: pd.DataFrame) -> pd.DataFrame:
        """
        Filters the DataFrame based on specific criteria (1.6 threshold).

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the data to be filtered.

        Returns
        -------
        pd.DataFrame or str
            Filtered DataFrame or a message indicating no selection.
        """
        df = df[df["state"] == "CLOSE"]
        if df.empty:
            raise ValueError("Empty DataFrame. No 'CLOSE' values.")
        sector = df["sector"].unique()[0]

        try:
            max_ = df.loc[df["state"] == "CLOSE", "result_dollars"].max()
            min_ = df.loc[df["state"] == "CLOSE", "result_dollars"].min()

            if pd.isna(max_) or pd.isna(min_):
                logging.warning("No CLOSE states found in the DataFrame.")
                return "No CLOSE states found in the DataFrame."

            abs_max_min_ = [abs(max_ / min_) for i in range(df.shape[0])]

            df = df.assign(abs_max_min=abs_max_min_)
            df["aux_filter"] = np.where(df["abs_max_min"] >= 1.6, 1, 0)
            selected_df = df[df["aux_filter"] == 1].rename(columns={"abs_max_min": "criterio de selección"})

            if selected_df.empty:
                logging.warning(f"No rows selected based on the criteria. Sector {sector}")
                return pd.DataFrame()

            selected_df = selected_df.drop(["aux_filter"], axis=1)
            columns = [
                "estrategia", "sector", "symbol", "side", "date_open_next_month", "date_close_next_month",
                "open_price", "close_price", "result_dollars", "state", "criterio de selección"
            ]
            selected_df = selected_df[columns]

            return selected_df
        
        except Exception as e:
            logging.error(f"An error occurred during filtering: {e}")
            return f"An error occurred: {e}"

    def process_file(self) -> pd.DataFrame:
        """
        Orchestrates the steps to process the DataFrame and apply the 1.6 filter.

        This method separates the DataFrame into buy and sell positions, applies the 
        filtering criteria to each, and then concatenates the results.
        """
        buy_df, sell_df = self.filter_positions(self.df)
        selected_buy = self.filter_condition(buy_df)
        selected_sell = self.filter_condition(sell_df)
        
        selected = []
        if isinstance(selected_buy, pd.DataFrame):
            selected.append(selected_buy)
        if isinstance(selected_sell, pd.DataFrame):
            selected.append(selected_sell)
        
        if selected:
            return pd.concat(selected, axis=0)
        else:
            return pd.DataFrame()