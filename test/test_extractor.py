import unittest
import pandas as pd
import pandas.testing as pdt
from enginesys.extractor import DataExtractor


class TestDataExtractor(unittest.TestCase):

    def setUp(self):
        self.data_path = "/path/to/data"
        self.extractor = DataExtractor(self.data_path)

    def test_download_eodhd_data(self):
        file_name = "eodhd_data.pickle"
        tickers = ["AAPL", "GOOGL"]
        init_date = "2022-01-01"
        end_date = "2022-01-31"
        period = "m"
        format = "pickle"
        force_download = False

        # Test the download_eodhd_data method
        self.extractor.download_eodhd_data(file_name, tickers, init_date, end_date, period, format, force_download)
        
        # Add assertions here to verify the expected behavior

    def test_download_yahoo_data(self):
        file_name = "yahoo_data.pickle"
        tickers = ["AAPL", "GOOGL"]
        init_date = "2022-01-01"
        end_date = "2022-01-31"
        period = "1mo"
        interval = "1mo"
        format = "pickle"
        force_download = False

        # Test the download_yahoo_data method
        self.extractor.download_yahoo_data(file_name, tickers, init_date, end_date, period, interval, format, force_download)

        # Add assertions here to verify the expected behavior

    def test_read_data(self):
        file_name = "data.pickle"
        format = "pickle"

        # Test the read_data method
        data_df = self.extractor.read_data(file_name, format)

        # Add assertions here to verify the expected behavior

    def test_validate_dt_index(self):
        # Create a sample DataFrame with datetime index
        data_df = pd.DataFrame({"Value": [1, 2, 3]}, index=pd.date_range(start="2022-01-01", periods=3))

        # Test the validate_dt_index method
        validated_df = self.extractor.validate_dt_index(data_df)

        # Add assertions here to verify the expected behavior

    def test_validate_tickers(self):
        # Create a sample DataFrame with tickers column
        data_df = pd.DataFrame({"Ticker": ["AAPL", "GOOGL", "MSFT"], "Value": [1, 2, 3]})

        # Test the validate_tickers method
        self.extractor.validate_tickers(data_df, ["AAPL", "GOOGL"])

        # Add assertions here to verify the expected behavior

    def test_validate_dates(self):
        # Create a sample DataFrame with date column
        data_df = pd.DataFrame({"Value": [1, 2, 3]}, index=pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]))

        # Test the validate_dates method
        validated_data_df = self.extractor.validate_dates(data_df, "2022-01-01", "2022-01-03")
        try:
            pdt.assert_frame_equal(data_df, validated_data_df)
        except AssertionError as e:
            self.fail(f"DataFrames are not equal: {e}")


if __name__ == "__main__":
    unittest.main()