import calendar
import datetime
import logging
import os

import enginesys.eodhd.eodhd as eodhd
import pandas as pd


class DataExtractor:

    def __init__(self, data_path):
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_folder_path, "input")
        self.output_data_path = os.path.join(self.data_folder_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        os.makedirs(self.output_data_path, exist_ok=True)

    def fetch_prices(
        data_path: str,
        tickers: list,
        init_date: str,
        end_date: str,
        period="m",
        download=False,
    ):
        if download:
            self.download_data(data_path, tickers, init_date, end_date, period)
        else:
            self.read_data(data_path, tickers, init_date, end_date)

    def download_data(
        file_name, tickers, init_date, end_date, period="m", full_month=False
    ):
        if full_month:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
            last_day_month = calendar.monthrange(end_date_dt.year, end_date_dt.month)[1]
            end_date_corrected = end_date_dt.replace(day=last_day_month)
            end_date_corrected.strftime("%Y-%m-%d")

        try:
            data = eodhd.download_multi(
                tickers=tickers, start=init_date, end=end_date_corrected, period=period
            )
        except Exception as e:
            logging.error(f"Error downloading data from EODHD API: {e}")

        file_path = os.path.join(self.input_data_path, file_name)
        data.to_pickle(file_path)
        logging.info(f"Data downloaded from EODHD API and saved to file '{file_name}'")

        return data

    def read_data(file_name, format="pickle") -> pd.DataFrame:
        """
        Reads data from a file.
        Args:
            file_name (str): The name of the file to read.
            format (str, optional): The format of the file. Defaults to "pickle".
        Returns:
            pandas.DataFrame: The loaded data.
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the format is not supported.
        """
        file_path = os.join(self.input_data_path, file_name)

        if not os.path.exists(file_path):
            logging.error(
                f"No se encontró el archivo '{file_name}' en la ruta '{self.input_data_path}'"
            )
            return None

        if format == "pickle":
            data = pd.read_pickle(data_path)
        elif format == "excel":
            data = pd.read_excel(data_path)
        elif format == "csv":
            data = pd.read_csv(data_path)
        else:
            logging.error(f"Formato '{format}' no soportado")

        logging.info(f"Se cargaron los datos del archivo '{file_name}'")

        return data

    def validate_dt_index(data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates the index of a DataFrame and converts it to a DatetimeIndex if necessary.

        Parameters:
        - data_df (pd.DataFrame): The DataFrame to be validated.

        Returns:
        - pd.DataFrame: The DataFrame with a validated index.
        """
        if not isinstance(data_df.index, pd.DatetimeIndex):
            logging.warning(
                "The index of the loaded DataFrame is not of type 'datetime'. Converting..."
            )
            if isinstance(data_df.index, pd.PeriodIndex):
                formated_index = data_df.index.to_timestamp()
            elif isinstance(data_df.index, pd.Index):
                formated_index = pd.to_datetime(data_df.index)
            else:
                raise ValueError(
                    "Unable to identify the type of index in the DataFrame"
                )
            data_df.index = formated_index

        return data_df

    def validate_tickers(data_df: pd.DataFrame, tickers: list):

        data_df.columns.names = ["type", "symbol"]
        existing_tickers = list(data_df.columns.get_level_values("symbol").unique())
        missing_tickers = set(tickers) - set(existing_tickers)

        if len(missing_tickers) > 0:
            logging.warning(
                f"Algunos tickers no se encontraron en la fuente de datos:\n"
                f"\tTickers faltantes: {missing_tickers}"
            )

        return data_df

    def validate_dates(data_df, init_date, end_date):
        if data_df.index.min() > pd.to_datetime(init_date):
            logging.warning(
                f"La fecha de inicio solicitada ({init_date}) es anterior a la fecha mínima disponible ({data_df.index.min()})"
            )
        if data_df.index.max() < pd.to_datetime(end_date):
            logging.warning(
                f"La fecha de fin solicitada ({end_date}) es posterior a la fecha máxima disponible ({data_df.index.max()})"
            )
        return data_df
