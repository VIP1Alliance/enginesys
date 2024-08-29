import logging

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ===================================================================================== #
# ======================= Methods to calculate the GEA indices ======================== #
# ===================================================================================== #

class AlgorithmIndices:

    def __init__(self):
        pass

    @staticmethod
    def get_gea_indices(trades_df: pd.DataFrame, strategy_weights: dict):
        """
        Calculates a cumulative index for trading strategies based on monthly trade variations.

        This function processes a DataFrame containing various strategies, calculating an index for each and a general weighted index
        based on each strategy's participation. The index reflects the accumulated performance of the strategies.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame with trade data including price variations and strategies.
        date : str, optional
            Name of the column containing the dates for grouping and index calculation, default is 'date'.

        Returns
        -------
        pd.DataFrame
            DataFrame with calculated indices for each strategy and a general index.
        """

        def get_strategy_index(strategy_data):
            """
            Calculates a strategy performance index based on monthly trade variations.
            """
            aux_df = strategy_data.copy()
            trades_by_month = aux_df.groupby("date").size()
            monthly_variation = aux_df.groupby("date")["variation"].prod()
            strategy_index = (monthly_variation ** (1 / trades_by_month)).cumprod()
            return strategy_index

        strategies = trades_df["strategy"].unique()
        indices_df = pd.DataFrame()
        for strategy in strategies:
            strategy_trades = trades_df[trades_df["strategy"] == strategy].copy()
            indices_df[strategy] = get_strategy_index(strategy_trades)

        # TODO: Revisar si es necesario reindexar los DataFrames para evitar dataframes de indices con filas faltantes.
        # Esto evitaría que si existen fechas en las cuales no se puede calcular el indice para alguna de las estrategias
        # se trunque el índice final.

        # Combinar los índices de todos los DataFrames usando un ciclo for
        # first_strategy = indices_df.columns[0]
        # all_dates = indices_df[first_strategy].index  # Empezamos con el índice del primer DataFrame
        # for strategy in indices_df.columns[1:]:
        #     all_dates = all_dates.union(indices_df[first_strategy].index)  # Unimos con el índice del siguiente DataFrame

        # for strategy in strategies:
        #     indices_df[strategy] = indices_df[strategy].reindex(all_dates, fill_value=0)
        
        algorithm_index = 0
        for strategy in strategies:
            algorithm_index += indices_df.get(strategy, 0) * strategy_weights[strategy]
        indices_df["algorithm"] = algorithm_index
        
        return indices_df

    @staticmethod
    def get_benchmark_index(
        prices_df: pd.DataFrame,
        benchmark: str,
    ):
        """
        Calculates the benchmark index based on the given prices DataFrame and benchmark list.

        Parameters
        ----------
        prices_df: pd.DataFrame
            DataFrame containing the prices data.
        benchmark: list
            List of columns to be used as the benchmark. Default is an empty list.

        Returns
        -------
        benchmark_index_df: pd.DataFrame
            DataFrame containing the benchmark index.
        """
        if not benchmark in prices_df.columns:
            raise ValueError("Benchmark not found in prices DataFrame")
        
        benchmark_df = prices_df[benchmark]
        price_ratios = benchmark_df / benchmark_df.shift(1)
        benchmark_index_df = price_ratios.cumprod()

        return benchmark_index_df[1:]
