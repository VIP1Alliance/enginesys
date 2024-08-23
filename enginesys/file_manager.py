import os
import zipfile
from datetime import datetime


class FileManager:
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.input_data_path = os.path.join(self.data_path, "input")
        self.output_data_path = os.path.join(self.data_path, "output")

        os.makedirs(data_path, exist_ok=True)
        os.makedirs(self.input_data_path, exist_ok=True)
        os.makedirs(self.output_data_path, exist_ok=True)

    def export_figures(self, strategy_figs: dict, date: str, to_zip: bool = False) -> None:
        date_formated = datetime.strptime(date, "%Y-%m-%d").strftime("%d_%m_%Y")
        os.makedirs(os.path.join(self.output_data_path, "risk_plots"), exist_ok=True)
        figures_path = os.path.join(self.output_data_path, "risk_plots", f"riesgo_{date_formated}")
        if to_zip:
            zip_path = f"{figures_path}.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for strategy, fig in strategy_figs.items():
                    fig_name = f"{strategy.replace(' ', '_').lower()}_var_{date_formated}.png"
                    fig.write_image(fig_name)
                    zipf.write(fig_name)
                    os.remove(fig_name)
        else:
            os.makedirs(figures_path, exist_ok=True)
            for strategy, fig in strategy_figs.items():
                fig_name = f"{strategy.replace(' ', '_').lower()}_var_{date_formated}.png"
                figure_path = os.path.join(figures_path, fig_name)
                fig.write_image(figure_path)