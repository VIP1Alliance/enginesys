""" This is where all related to filters is located"""
import os
import logging
import warnings

import pandas as pd
import numpy as np

# from enginesys.helpers import get_asg_ranking
# from enginesys.helpers import assign_ranking_asg
# from enginesys.helpers import selected_sectorsdf


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
    def __init__(self, recommendations: pd.DataFrame) -> None:
        self.recommendations = recommendations

    # Build filter threshold 1.6
    def build_filter_threshold(self):
        pass

    # Build filter ASG
    def build_filter_asg(self):
        pass

    # Load filter threshold 1.6
    @staticmethod
    def _get_filter_threshold() -> pd.DataFrame: return selected_sectors()

    # Load filter ASG
    @staticmethod
    def _get_filter_asg() -> pd.DataFrame: return get_asg_ranking()

    # Apply filter threshold 1.6
    def filter_threshold(self) -> pd.DataFrame:
        """threshold 1.6 filter here goes function 'filter by sectors' """
        filter_sectors = self._get_filter_threshold()
        result = pd.merge(self.recommendations, filter_sectors, how='left', on=['strategy', 'sector'])
        buy_ = result[(result["side"] == "BUY") & (result["buy"] == 1)]
        sell_ = result[(result["side"] == "SELL") & (result["sell"] == 1)]
        df1 = pd.concat([buy_, sell_], axis=0)
        df1 = df1.drop(["enter", "buy", "sell"], axis=1)
        assert df1.shape[0] != 0, "No sectors were selected, please check the data."
        return df1

    # Apply filter ASG
    def filter_asg(self, column_ranking: str = "ranking_asg",
                   no_ranking_tag: str = 'No reporta') -> pd.DataFrame:
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
