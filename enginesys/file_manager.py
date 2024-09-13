import logging
import os
import shutil


class FileManager:

    def __init__(self, data_path: str):
        """
        Initializes a FileManager object

        Parameters
        ------
        data_path: str
            The path to the main data directory

        """
        
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        logging.info(f"Defined Input folder in: '{self.input_data_path}'")
        os.makedirs(self.output_data_path, exist_ok=True)
        logging.info(f"Defined Output folder in: '{self.output_data_path}'")

    def export_var_plots(
        self, 
        strategy_figs: dict, 
        folder_path: str, 
        to_zip: bool = False, 
        date: str = None,
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
        # try:
        if date:
            figs_path = os.path.join(folder_path, f"riesgo_{date}")
        else:
            figs_path = os.path.join(folder_path, "riesgo")
        
        # Crear la carpeta si no existe
        os.makedirs(figs_path, exist_ok=True)  
        for strategy, fig in strategy_figs.items():
            if date:
                fig_name = f"{strategy.replace(' ', '_').lower()}_var_{date}.png"
            else:
                fig_name = f"{strategy.replace(' ', '_').lower()}_var.png"
            figure_path = os.path.join(figs_path, fig_name)
            print(figure_path)
            fig.write_image(figure_path)
            
        if to_zip:
            shutil.make_archive(figs_path, 'zip', figs_path)
            shutil.rmtree(figs_path)
            figs_path = figs_path + ".zip"
            
        logging.info(f"Plots exported successfully to folder '{figs_path}'")

        # except Exception as e:
        #     logging.error(f"An error occurred while exporting figures: {str(e)}")