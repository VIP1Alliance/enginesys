import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '..')))

import unittest
import pandas as pd

from enginesys.validator import DataFrameFormatter


class TestDataFrameUtils(unittest.TestCase):
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
        df_cleaned = DataFrameFormatter.remove_unnamed_columns(self.df)
        expected_columns = ["ColumnOne", "COLUMN TWO"]
        self.assertListEqual(list(df_cleaned.columns), expected_columns)

    def test_lower_column_names(self):
        # Test converting column names to lowercase
        df_lower = DataFrameFormatter.lower_column_names(self.df)
        expected_columns = ["columnone", "column two", "unnamed column"]
        self.assertListEqual(list(df_lower.columns), expected_columns)

    def test_spaces_to_underscores(self):
        # Test replacing spaces with underscores
        df_modified = DataFrameFormatter.spaces_to_underscores(self.df)
        expected_columns = ["ColumnOne", "COLUMN_TWO", "Unnamed_Column"]
        self.assertListEqual(list(df_modified.columns), expected_columns)
        
    def test_set_required_columns(self):
        # Test setting required columns
        formatter = DataFrameFormatter()
        required_columns = ["ColumnOne", "COLUMN TWO"]
        formatter.set_required_columns(required_columns)
        self.assertListEqual(formatter.required_columns, required_columns)

    def test_validate_required_columns(self):
        # Test validating required columns
        formatter = DataFrameFormatter()
        required_columns = ["COLUMN TWO", "Unnamed Column", "Column Four"]
        formatter.set_required_columns(required_columns)
        extra_columns, missing_columns = formatter.validate_required_columns(self.df)
        self.assertEqual(extra_columns, set(["ColumnOne"]))
        self.assertEqual(missing_columns, set(["Column Four"]))

    def test_replace_column_names(self):
        # Test replacing column names
        column_dict = {
            "ColumnOne": "NewColumnOne",
            "COLUMN TWO": "NewColumnTwo",
            "Unnamed Column": "NewUnnamedColumn",
        }
        df_renamed = DataFrameFormatter.replace_column_names(self.df, column_dict)
        expected_columns = ["NewColumnOne", "NewColumnTwo", "NewUnnamedColumn"]
        self.assertListEqual(list(df_renamed.columns), expected_columns)


if __name__ == "__main__":
    unittest.main()
