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
        os.makedirs(self.input_data_path, exist_ok=True)
        logging.info(f"Defined Input folder in: '{self.input_data_path}'")
        os.makedirs(self.output_data_path, exist_ok=True)
        logging.info(f"Defined Output folder in: '{self.output_data_path}'")
                
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
            folder_name = "risk_plots"
            os.makedirs(os.path.join(self.output_data_path, folder_name), exist_ok=True)
            figs_path = os.path.join(self.output_data_path, folder_name, f"riesgo_{formated_date}")
            if to_zip:
                zip_path = f"{figs_path}.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for strategy, fig in strategy_figs.items():
                        fig_name = f"{strategy.replace(' ', '_').lower()}_var_{formated_date}.png"
                        fig.write_image(fig_name)
                        zipf.write(fig_name)
                        os.remove(fig_name)
                parent_folder, file_name = os.path.split(zip_path)
                rel_file_path = os.path.join(os.path.basename(parent_folder), file_name)
                logging.info(f"Plots exported successfully to file '{rel_file_path}'")
            else:
                os.makedirs(figs_path, exist_ok=True)
                for strategy, fig in strategy_figs.items():
                    fig_name = f"{strategy.replace(' ', '_').lower()}_var_{formated_date}.png"
                    figure_path = os.path.join(figs_path, fig_name)
                    fig.write_image(figure_path)
                parent_folder, name = os.path.split(os.path.normpath(figs_path))
                rel_folder_path = os.path.join(os.path.basename(parent_folder), name)
                logging.info(f"Plots exported successfully to folder '{rel_folder_path}'")
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
            df.to_excel(file_path)
            logging.info(f"Data exported successfully to file '{file_name}'")
        except Exception as e:
            raise ValueError(f"An error occurred while exporting data: {str(e)}")