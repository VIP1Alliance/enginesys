import logging
import os
import zipfile
from datetime import datetime

import pandas as pd


class FileManager:
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        logging.info(f"FileManager created with data_path: {data_path}")
        os.makedirs(self.input_data_path, exist_ok=True)
        logging.info(f"Input data path: {self.input_data_path}")
        os.makedirs(self.output_data_path, exist_ok=True)
        logging.info(f"Output data path: {self.output_data_path}")
                
    def read_data(self, file_name: str, format: str ="pickle") -> pd.DataFrame:
        """
        Reads data from a file.
        
        Parameters
        ----------
        file_name: str
            The name of the file to read.
        format: str, optional
            The format of the file. Defaults to "pickle".
        
        Returns
        -------
        pandas.DataFrame: 
            The loaded data.
        
        Raises:
        -------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the format is not supported.
        """
        file_path = os.path.join(self.input_data_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_name}' was not found in the path '{self.input_data_path}'")
        if format == "pickle":
            data = pd.read_pickle(file_path)
        elif format == "excel":
            data = pd.read_excel(file_path)
        elif format == "csv":
            data = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported format: '{format}'")

        logging.info(f"Data loaded from file '{file_name}'")

        return data

    def export_figures(self, strategy_figs: dict, date: str, to_zip: bool = False) -> None:
        try:
            formated_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d_%m_%Y")
            os.makedirs(os.path.join(self.output_data_path, "risk_plots"), exist_ok=True)
            figures_path = os.path.join(self.output_data_path, "risk_plots", f"riesgo_{formated_date}")
            if to_zip:
                zip_path = f"{figures_path}.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for strategy, fig in strategy_figs.items():
                        fig_name = f"{strategy.replace(' ', '_').lower()}_var_{formated_date}.png"
                        fig.write_image(fig_name)
                        zipf.write(fig_name)
                        os.remove(fig_name)
            else:
                os.makedirs(figures_path, exist_ok=True)
                for strategy, fig in strategy_figs.items():
                    fig_name = f"{strategy.replace(' ', '_').lower()}_var_{formated_date}.png"
                    figure_path = os.path.join(figures_path, fig_name)
                    fig.write_image(figure_path)
            logging.info(f"Figures exported successfully to {figures_path}")
        except Exception as e:
            logging.error(f"An error occurred while exporting figures: {str(e)}")
    
    def export_to_excel(self, df: pd.DataFrame, file_name: str, date: str, folder_name: str = None) -> None:
        try:
            formated_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d_%m_%Y")
            file_name = f"{file_name}_{formated_date}.xlsx"
            if folder_name:
                os.makedirs(os.path.join(self.output_data_path, folder_name), exist_ok=True)
                file_name = os.path.join(folder_name, file_name)
            file_path = os.path.join(self.output_data_path, file_name)
            df.to_excel(file_path, index=False)
            logging.info(f"Data exported successfully to {file_path}")
        except Exception as e:
            raise ValueError(f"An error occurred while exporting data: {str(e)}")