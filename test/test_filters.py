import unittest
import pandas as pd
from io import StringIO

from enginesys.filters import Filters
from enginesys.filters import FilterThreshold


# Mock the selected_sectors function
def mock_selected_sectors() -> pd.DataFrame:
    data = {
        'strategy': ["strategy1", "strategy1", "strategy2", "strategy2"],
        'sector': ["sector1", "sector2", "sector1", "sector2"],
        'enter': [1, 1, 1, 0],
        'buy': [0, 1, 1, 0],
        'sell': [1, 0, 1, 0]
        }
    return pd.DataFrame(data)

# Mock the get_asg_ranking function and assign_ranking_asg function
def mock_get_asg_ranking():
    data = {'ticker': ['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
            'calificación de sostenibilidad': [4, 3, 5, 1]}
    return pd.DataFrame(data).set_index('ticker')

def mock_assign_ranking_asg(df, ranking_df, ticker_model):
    df['calificación de sostenibilidad'] = df['tickers'].map(ranking_df['calificación de sostenibilidad'])
    return df

class TestFilters(unittest.TestCase):

    def setUp(self):
        data = {
            'strategy': ['strategy1', 'strategy1', 'strategy2', 'strategy2', 'strategy2'],
            'sector': ['sector1', 'sector2', 'sector1', 'sector2', 'sector2'],
            'ticker': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
            'date_open_next_month': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01'],
            'result_dollars': [1.8, 0.5, 2.5, 1.2, 0.3],
            'side': ['BUY', 'SELL', 'BUY', 'SELL', 'BUY'],
            'state': ['CLOSE', 'CLOSE', 'CLOSE', 'CLOSE', 'CLOSE']
        }
        self.df = pd.DataFrame(data)

    def test_filter_asg_df(self):
        filters = Filters(self.df.iloc[:-1,:], pd.DataFrame())
        # Replace the actual functions with the mock functions
        filters._get_filter_asg = mock_get_asg_ranking
        global assign_ranking_asg
        assign_ranking_asg = mock_assign_ranking_asg
        # Expected DataFrame after ASG filtering
        expected1_df = self.df.iloc[:-1]
        expected1_df = expected1_df.assign(ranking_asg=[4, 3, 5, 1])
        # Apply ASG filter
        result_df = filters.filter_asg()
        # Check if the filtered DataFrame matches the expected DataFrame
        pd.testing.assert_frame_equal(result_df.reset_index(drop=True), expected1_df.reset_index(drop=True))

    def test_filter_asg_warning(self):
        filters = Filters(self.df, pd.DataFrame())
        # Replace the actual functions with the mock functions
        filters._get_filter_asg = mock_get_asg_ranking
        global assign_ranking_asg
        assign_ranking_asg = mock_assign_ranking_asg
        with self.assertWarns(UserWarning):
            filters.filter_asg()

    def test_filter_threshold(self):
        filters = Filters(self.df.iloc[:-1,:], pd.DataFrame())
        expected_data = {
            'strategy': {2: 'strategy2'},
            'sector': {2: 'sector1'},
            'ticker': {2: 'MSFT'},
            'date_open_next_month': {2: '2023-01-01'},
            'result_dollars': {2: 2.5},
            'side': {2: 'BUY'},
            'state': {2: 'CLOSE'}
            }
        expected = pd.DataFrame.from_dict(expected_data)
        filters._get_filter_threshold = mock_selected_sectors
        result = filters.filter_threshold()
        pd.testing.assert_frame_equal(result, expected)

class TestFilterThreshold(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.data = {
            'estrategia': ['strategy1', 'strategy1', 'strategy2', 'strategy2'],
            'sector': ['sector1', 'sector1', 'sector2', 'sector2'],
            'side': ['BUY', 'SELL', 'BUY', 'SELL'],
            'state': ['CLOSE', 'CLOSE', 'CLOSE', 'OPEN'],
            'result_dollars': [100, -50, 300, -200],
            'symbol': ['SYM1', 'SYM1', 'SYM2', 'SYM2'],
            'date_open_next_month': ['2023-01-01', '2023-01-01', '2023-02-01', '2023-02-01'],
            'date_close_next_month':['2023-01-31', '2023-01-31', '2023-02-28', '2023-02-28'],
            'open_price': [10, 10, 15, 15],
            'close_price': [12, 8, 18, 12]
        }
        self.df = pd.DataFrame(self.data)

    def test_format_data(self):
        formatted_df = FilterThreshold.format_data(self.df)
        expected_data = {
            'estrategia': ['strategy1', 'strategy2'],
            'sector': ['sector1', 'sector2'],
            'enter': [1, 1],
            'buy': [1, 1],
            'sell': [1, 1]
        }
        expected_df = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(formatted_df, expected_df)

    def test_format_data_missing_columns(self):
        df_missing_cols = self.df.drop(columns=["sector"])
        with self.assertRaises(ValueError) as context:
            FilterThreshold.format_data(df_missing_cols)
        self.assertTrue('Missing required columns' in str(context.exception))

    def test_filter_position(self):
        buy_df, sell_df = FilterThreshold.filter_positions(self.df)
        self.assertEqual(buy_df.shape[0], 2)
        self.assertEqual(sell_df.shape[0], 2)
        self.assertTrue((buy_df['side'] == 'BUY').all())
        self.assertTrue((sell_df['side'] == 'SELL').all())

    def test_filter_conditions(self):
        filtered_df = FilterThreshold.filter_condition(self.df)
        self.assertEqual(filtered_df.shape[0], 3)
        self.assertEqual(filtered_df.iloc[0]['symbol'], 'SYM1')
        self.assertEqual(filtered_df.iloc[0]['criterio de selección'], 6.0)

    def test_filter_condition_no_close(self):
        df_no_close = self.df[self.df["state"] != 'CLOSE']
        with self.assertRaises(ValueError) as context:
            FilterThreshold.filter_condition(df_no_close)
        self.assertTrue('Empty DataFrame' in str(context.exception))

    def test_process_file(self):
        filter_threshold = FilterThreshold(self.df)
        result_df = filter_threshold.process_file()
        self.assertEqual(result_df.shape[0], 2)
        self.assertEqual(result_df.iloc[0]['symbol'], 'SYM1')

if __name__ == '__main__':
    unittest.main()
