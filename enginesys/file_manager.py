import logging
import os
import zipfile
from datetime import datetime

import pandas as pd


class FileManager:

    def __init__(self, data_path: str):
        """
        Initializes a FileManager object

        Parameters
        ------
        data_path: str
            The path to the main data directory

        """
        # Rest of the code...
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        logging.info(f"Defined Input folder in: '{self.input_data_path}'")
        os.makedirs(self.output_data_path, exist_ok=True)
        logging.info(f"Defined Output folder in: '{self.output_data_path}'")

    def export_figures(
        self, strategy_figs: dict, date: str, to_zip: bool = False
    ) -> None:
        """
        Export the given strategy figures to either a folder or a zip file.
        
        Parameters
        ----------
        strategy_figs: dict
            A dictionary containing the strategy names as keys and the corresponding figures as values.
        date: str
            The date in the format "YYYY-MM-DD".
        to_zip: Optional[bool]
            Whether to export the figures to a zip file. Defaults to False.
        
        Returns
        -------
        str:
            The path to the exported folder or zip file.
        
        Raises
        -------
        Exception: 
            If an error occurs while exporting the figures.
        """
        try:
            formated_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d_%m_%Y")
            folder_name = "risk_plots"
            os.makedirs(os.path.join(self.output_data_path, folder_name), exist_ok=True)
            figs_path = os.path.join(
                self.output_data_path, folder_name, f"riesgo_{formated_date}"
            )
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
                return zip_path
            else:
                os.makedirs(figs_path, exist_ok=True)
                for strategy, fig in strategy_figs.items():
                    fig_name = (
                        f"{strategy.replace(' ', '_').lower()}_var_{formated_date}.png"
                    )
                    figure_path = os.path.join(figs_path, fig_name)
                    fig.write_image(figure_path)
                parent_folder, name = os.path.split(os.path.normpath(figs_path))
                rel_folder_path = os.path.join(os.path.basename(parent_folder), name)
                logging.info(
                    f"Plots exported successfully to folder '{rel_folder_path}'"
                )
                return figs_path

        except Exception as e:
            logging.error(f"An error occurred while exporting figures: {str(e)}")

    def export_to_excel(
        self, df: pd.DataFrame, file_name: str, date: str = None, folder_name: str = None
    ) -> None:
        """
        Export the given DataFrame to an Excel file.
        
        Parameters
        ----------
        df: pd.DataFrame
            The DataFrame to be exported.
        file_name: str
            The name of the Excel file.
        date: str
            The date in the format 'YYYY-MM-DD'.
        folder_name: Optional[str]
            The name of the folder to save the file in. Defaults to None.
        
        Returns
        -------
        None
        
        Raises
        -------
        ValueError
            If an error occurs while exporting the data.
        """
        try:
            if date:
                formated_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d_%m_%Y")
                file_name = f"{file_name}_{formated_date}.xlsx"
            else:
                file_name = f"{file_name}.xlsx"

            folder_path = (
                os.path.join(self.output_data_path, folder_name)
                if folder_name
                else self.output_data_path
            )

            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, file_name)
            df.to_excel(file_path)
            logging.info(f"Data exported successfully to file '{file_name}'")
            return folder_path
        except Exception as e:
            raise ValueError(f"An error occurred while exporting data: {str(e)}")
