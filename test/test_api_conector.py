import unittest

import pandas as pd
import pandas.testing as pdt

from enginesys.api_connector import APIConnector


class TestAPIConnector(unittest.TestCase):

    def setUp(self):
        self.data_path = "/path/to/data"
        self.extractor = APIConnector(self.data_path)
        self.data_df = pd.DataFrame({"Value": [1, 2, 3]}, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))
        self.prices_df = pd.DataFrame({
            "AAPL": [100.0, 105.0, 110.0],
            "GOOGL": [2000.0, 2050.0, 2100.0]
        }, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))

    def test_validate_interval_dates(self):
        # Test the validate_interval_dates method
        validated_data_df = self.extractor.validate_interval_dates(self.data_df, "2022-01-01", "2022-01-03")
        try:
            pdt.assert_frame_equal(self.data_df, validated_data_df)
        except AssertionError as e:
            self.fail(f"DataFrames are not equal: {e}")

    def test_validate_date_prices(self):
        # Test the validate_date_prices method
        missing_prices_tickers = self.extractor.validate_date_prices(self.prices_df, "2022-01-03")

        # Add assertions here to verify the expected behavior
        self.assertEqual(missing_prices_tickers, [])

        # Test with missing prices
        prices_df_missing_prices = pd.DataFrame({
            "GOOGL": [100.0, 105.0, None],
            "AAPL": [2000.0, None, 2100.0]
        }, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))
        missing_prices_tickers = self.extractor.validate_date_prices(prices_df_missing_prices, "2022-01-03")
        self.assertEqual(missing_prices_tickers, ["GOOGL"])

        # Test with zero prices
        prices_df_zero_prices = pd.DataFrame({
            "AAPL": [100.0, 105.0, 0.0],
            "GOOGL": [2000.0, 0.0, 2100.0]
        }, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))
        missing_prices_tickers = self.extractor.validate_date_prices(prices_df_zero_prices, "2022-01-03")
        self.assertEqual(missing_prices_tickers, ["AAPL"])

        # Test with missing and zero prices
        prices_df_missing_zero_prices = pd.DataFrame({
            "AAPL": [100.0, None, 0.0],
            "GOOGL": [2000.0, 0.0, None]
        }, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))
        missing_prices_tickers = self.extractor.validate_date_prices(prices_df_missing_zero_prices, "2022-01-03")
        self.assertEqual(missing_prices_tickers, ["AAPL", "GOOGL"])

        # Test with no prices for the given date
        prices_df_no_prices = pd.DataFrame({
            "AAPL": [100.0, 105.0, 110.0],
            "GOOGL": [2000.0, 2050.0, 2100.0]
        }, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-04"]))
        with self.assertRaises(ValueError):
            self.extractor.validate_date_prices(prices_df_no_prices, "2022-01-03")


if __name__ == "__main__":
    unittest.main()