import unittest

import pandas as pd

from enginesys.formatter import Formatter


class TestFormatter(unittest.TestCase):
    def setUp(self):
        # Set up a sample dataframe for testing
        self.df = pd.DataFrame(
            {
                "ColumnOne": [1, 2, 3],
                "COLUMN TWO": [4, 5, 6],
                "Unnamed Column": [7, 8, 9],
            }
        )

    def test_remove_unnamed_columns(self):
        # Test removing unnamed columns
        df_cleaned = Formatter.remove_unnamed_cols(self.df)
        expected_columns = ["ColumnOne", "COLUMN TWO"]
        self.assertListEqual(list(df_cleaned.columns), expected_columns)

    def test_lower_column_names(self):
        # Test converting column names to lowercase
        df_lower = Formatter.lower_column_names(self.df)
        expected_columns = ["columnone", "column two", "unnamed column"]
        self.assertListEqual(list(df_lower.columns), expected_columns)

    def test_spaces_to_underscores(self):
        # Test replacing spaces with underscores
        df_modified = Formatter.spaces_to_underscores(self.df)
        expected_columns = ["ColumnOne", "COLUMN_TWO", "Unnamed_Column"]
        self.assertListEqual(list(df_modified.columns), expected_columns)
        

if __name__ == "__main__":
    unittest.main()
