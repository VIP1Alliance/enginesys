import logging

import numpy as np
import pandas as pd
from scipy.linalg import eigh
from ..processor import PricesProcessor



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s -asdfasdf %(levelname)s - %(message)s"
)
    
    
class ValueAtRisk:

    def __init__(self, trades_df: pd.DataFrame, prices_df: pd.DataFrame):
        self.tag_prices_df = PricesProcessor.tag_prices(trades_df, prices_df)
        self.trades_df = trades_df
        self.price_variations_df = pd.DataFrame()
        self.strategy_indices_df = pd.DataFrame()
        self.strategies_variation_df = pd.DataFrame()
        self.strategies_metrics_df = pd.DataFrame()
        self.risk_metrics_df = pd.DataFrame()
        self.log_variation_df = pd.DataFrame()

    @staticmethod
    def side_variations(prices_df: pd.DataFrame, side: str = "BUY") -> pd.DataFrame:
        """
        Calculate the variations of prices based on the side (BUY/SELL).

        Parameters
        ----------
        prices_df: pd.DataFrame
            DataFrame containing price data.
        side: str, optional
            Side for variation calculation, either 'BUY' or 'SELL'. Default is 'BUY'.

        Returns
        -------
        pd.DataFrame
            DataFrame with price variations.
        """
        if side == "BUY":
            variations = prices_df / prices_df.shift(1)
        elif side == "SELL":
            variations = prices_df.shift(1) / prices_df
        else:
            raise ValueError("Side must be either 'BUY' or 'SELL'")
        if isinstance(variations, pd.DataFrame):
            variations = variations.sort_index(axis=1)
        return variations[1:]

    @classmethod
    def calculate_variations(cls, prices_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the variations for both BUY and SELL sides.

        Parameters
        ----------
        prices_df: pd.DataFrame
            DataFrame containing price data with multi-index columns for different sides.

        Returns
        -------
        pd.DataFrame
            DataFrame with combined variations for BUY and SELL sides.
        """
        side_columns = prices_df.columns.get_level_values("side")

        if not {"BUY", "SELL"}.issubset(side_columns):
            raise ValueError("prices_df must contain 'BUY' or 'SELL' sides in the columns")

        buy_prices_df = prices_df.loc[:, side_columns == "BUY"]
        sell_prices_df = prices_df.loc[:, side_columns == "SELL"]

        variations_buy = cls.side_variations(buy_prices_df, side="BUY")
        variations_sell = cls.side_variations(sell_prices_df, side="SELL")

        variation_df = pd.concat([variations_buy, variations_sell], axis=1)
        variation_df = variation_df.sort_index(axis=1)
        
        return variation_df

    @staticmethod
    def get_individual_metrics(variations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate individual metrics for the given variations DataFrame.

        Parameters
        ----------
        variations_df: pd.DataFrame
            DataFrame with variations data.

        Returns
        -------
        pd.DataFrame
            DataFrame with individual metrics including Variance, EWMA, and VaR.
        """
        if not isinstance(variations_df, pd.DataFrame):
            raise ValueError("variations_df must be a DataFrame")
        
        if variations_df.empty:
            raise ValueError("variations_df is empty")
        
        if not all(variations_df.dtypes=="float64"):
            raise ValueError("variations_df must contain only numerical values")
        
        # Lambda value
        lambda_ = 0.98

        # Logarithm of the variations
        try:
            log_variations_df = np.log(variations_df).dropna()
        except ValueError as e:
            raise ValueError("Error applying logarithm to variations_df: " + str(e))

        # Weighting factor
        weighting_factor = [lambda_ ** (i) for i in range(len(log_variations_df) - 1, -1, -1)]

        if len(weighting_factor) != len(log_variations_df):
            raise ValueError(
                "Length of weighting_factor does not match the number of rows in log_variations_df"
            )

        # (Weighting factor) X (log_variation)^2 | percentage value
        fpv2 = (log_variations_df**2).mul(weighting_factor, axis=0)

        # Varianza
        variance = pd.Series((1 - lambda_) * fpv2.sum()).rename("Variance")

        # Expected volatility | EWMA
        ewma = pd.Series(np.sqrt(variance)).rename("EWMA")

        # Conditional VaR
        VaR = pd.Series(log_variations_df.quantile(0.05)).rename("VaR")

        return pd.concat([variance, VaR, ewma], axis=1)

    @classmethod
    def get_strategies_var(cls, variations_df: pd.DataFrame) -> dict:
        """
        Calculate Value at Risk (VaR) for each strategy based on the variations DataFrame.

        Parameters
        ----------
        variations_df: pd.DataFrame
            DataFrame with variations data, indexed by strategies.

        Returns
        -------
        dict
            Dictionary with strategies as keys and their VaR values as values.
        """
        if variations_df.columns.get_level_values(0).name != "strategy":
            raise ValueError("variations_df must contain 'strategy' in the columns")

        variations_df = variations_df.droplevel("side", axis=1)

        if variations_df.empty:
            raise ValueError("variations_df is empty after dropping 'side' level")

        individual_metrics_df = cls.get_individual_metrics(variations_df)
        strategies = list(variations_df.columns.get_level_values("strategy").unique())
        strategies_var = {}

        for strategy in strategies:
            if strategy not in individual_metrics_df.index:
                raise ValueError(f"Strategy '{strategy}' not found in individual metrics")

            strategy_metrics_df = individual_metrics_df.loc[strategy]
            n_tickers = len(strategy_metrics_df)
            if n_tickers == 0:
                raise ValueError(f"No tickers found for strategy '{strategy}'")

            # Tickers Weights
            weights = np.array([1 / n_tickers] * n_tickers)

            # Excess Matrix
            excess_matrix = variations_df[strategy] - weights
            var_cov_matrix = excess_matrix.cov()

            # Ensure all columns in var_cov_matrix are in individual_metrics_df
            missing_tickers = set(var_cov_matrix.columns) - set(
                strategy_metrics_df.index
            )
            if missing_tickers:
                raise ValueError(f"Missing tickers in individual metrics: {missing_tickers}")

            for ticker in list(var_cov_matrix.columns):
                var_cov_matrix.at[ticker, ticker] = strategy_metrics_df.loc[ticker, "Variance"]

            # Strategy Variance
            strategy_variance = weights.dot(var_cov_matrix).dot(weights)
            if strategy_variance < 0:
                logging.warning(
                    f"Negative portfolio variance for 'strategy {strategy}', converting covariance matrix to positive semidefinite ..."
                )
                adjusted_var_cov_matrix = cls.make_positive_semidefinite(var_cov_matrix)
                strategy_variance = weights.dot(adjusted_var_cov_matrix).dot(weights)
            
            # Strategy VaR
            strategies_var[strategy] = np.sqrt(strategy_variance)

        return strategies_var

    @staticmethod
    def get_strategy_indices(variations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the index values for each strategy based on variations.

        Parameters
        ----------
        variations_df: pd.DataFrame
            DataFrame with variations data.

        Returns
        -------
        pd.DataFrame
            DataFrame with index values for each strategy.
        """
        if variations_df.columns.get_level_values(0).name != "strategy":
            raise ValueError("variations_df must contain 'strategy' in the columns")

        strategies = variations_df.columns.get_level_values("strategy").unique()
        indices_df = pd.DataFrame()

        for strategy in strategies:
            if strategy not in variations_df.columns.get_level_values("strategy").unique():
                raise ValueError(f"Strategy '{strategy}' not found in variations_df")

            strategy_variations_df = variations_df[strategy].copy()
            if len(strategy_variations_df.columns) == 0:
                raise ValueError(f"No columns found for strategy '{strategy}'")

            strategy_indices = (strategy_variations_df.prod(axis=1)) ** (
                1 / len(strategy_variations_df.columns)
            )
            strategy_indices.iloc[0] = 1

            if indices_df.empty:
                indices_df = pd.DataFrame()

            indices_df[strategy] = strategy_indices.cumprod() * 100

        return indices_df[1:]

    @classmethod
    def get_var_cov_algo_matrix(cls, strategy_indices_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the variance-covariance matrix for the algorithm based on strategy indices.

        Parameters
        ----------
        strategy_indices_df: pd.DataFrame
            DataFrame with strategy indices data.

        Returns
        -------
        pd.DataFrame
            Variance-covariance matrix for the algorithm.
        """
        strategies = list(strategy_indices_df.columns)
        if len(strategies) == 0:
            raise ValueError("No strategies found in strategy_indices_df")

        strats_variation_df = strategy_indices_df / strategy_indices_df.shift(1)
        n_strategies = len(strategies)
        strategy_weights = np.array([1 / n_strategies] * n_strategies)
        excess_matrix_algorithm = strats_variation_df - strategy_weights
        var_cov_algo_matrix = excess_matrix_algorithm.cov()
        strategies_variation_df = cls.side_variations(strategy_indices_df)
        strategy_metrics_df = cls.get_individual_metrics(strategies_variation_df)
        for strategy in strategies:
            if strategy not in strategy_metrics_df.index:
                raise ValueError(
                    f"Strategy '{strategy}' not found in strategy_metrics_df"
                )

            if (
                strategy not in var_cov_algo_matrix.index
                or strategy not in var_cov_algo_matrix.columns
            ):
                raise ValueError(
                    f"Strategy '{strategy}' not found in var_cov_algo_matrix"
                )

            var_cov_algo_matrix.at[strategy, strategy] = strategy_metrics_df.loc[strategy, "Variance"]

        return var_cov_algo_matrix
    
    @staticmethod
    def make_positive_semidefinite(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts a DataFrame into a positive semidefinite matrix by adjusting its eigenvalues.
        Args:
            df (pd.DataFrame): The input DataFrame.
        Returns:
            pd.DataFrame: The adjusted DataFrame with non-negative eigenvalues.
        """
        # Convert DataFrame to a numpy array
        A = df.values
        
        # Performs spectral decomposition
        eigenvalues, eigenvectors = eigh(A)
        
        # Adjust the eigenvalues ​​to be non-negative
        eigenvalues_adjusted = np.maximum(eigenvalues, 0)
        
        # Reconstruct the adjusted matrix
        A_adjusted = eigenvectors @ np.diag(eigenvalues_adjusted) @ eigenvectors.T
        
        # Converts the adjusted array back to a DataFrame
        df_adjusted = pd.DataFrame(A_adjusted, index=df.index, columns=df.columns)
        
        return df_adjusted

    @classmethod
    def var_from_matrix(cls, var_cov_algo_matrix: pd.DataFrame) -> float:
        """
        Calculate the Value at Risk (VaR) from the variance-covariance matrix.

        Parameters
        ----------
        var_cov_algo_matrix: pd.DataFrame
            Variance-covariance matrix for the algorithm.

        Returns
        -------
        float
            Value at Risk (VaR) for the algorithm.
        """
        strategies = list(var_cov_algo_matrix.columns)
        if len(strategies) == 0:
            raise ValueError("No strategies found in var_cov_algo_matrix")

        n_strategies = len(strategies)
        if n_strategies == 0:
            raise ValueError("Number of strategies is zero")

        strategy_weights = np.array([1 / 3] * n_strategies)

        if len(strategy_weights) != var_cov_algo_matrix.shape[0]:
            raise ValueError(
                "Mismatch between number of strategies and dimensions of var_cov_algo_matrix"
            )

        algorithm_variance = strategy_weights.dot(var_cov_algo_matrix).dot(strategy_weights)
        if algorithm_variance < 0:
            logging.warning(
                f"Negative Variance obtained for 'Gea Algorithm', converting covariance matrix to positive semidefinite ..."
            )
            var_cov_matrix_adjusted = cls.make_positive_semidefinite(var_cov_algo_matrix)
            algorithm_variance = strategy_weights.dot(var_cov_matrix_adjusted).dot(strategy_weights)
        
        # Calculate VaR
        algorithm_var = np.sqrt(algorithm_variance)

        return algorithm_var

    @classmethod
    def get_algorithm_var(cls, strategy_indices_df: pd.DataFrame) -> float:
        """
        Calculate the Value at Risk (VaR) for the algorithm using strategy indices.

        Parameters
        ----------
        strategy_indices_df: pd.DataFrame
            DataFrame with index values for strategies.

        Returns
        -------
        float
            Value at Risk (VaR) for the algorithm.
        """
        var_cov_algo_matrix = cls.get_var_cov_algo_matrix(strategy_indices_df)
        algorithm_var = cls.var_from_matrix(var_cov_algo_matrix)
        return algorithm_var

    @staticmethod
    def get_geom_index_alg(strategy_indices_df: pd.DataFrame) -> pd.Series:
        """
        Calculate the geometric index for the algorithm based on strategy indices.

        Parameters
        ----------
        index_strategies: pd.DataFrame
            DataFrame with index values for strategies.

        Returns
        -------
        pd.Series
            Geometric index for the algorithm.
        """
        n_strategies = len(list(strategy_indices_df.columns))
        strategy_weights = np.array([1 / n_strategies] * n_strategies)
        base_value = (strategy_indices_df.iloc[0] * strategy_weights).sum()
        geom_index_alg = 100 * (
            strategy_indices_df.mul(strategy_weights).sum(axis=1) / base_value
        )
        geom_index_alg.rename("geom_index_alg", inplace=True)
        geom_index_alg = pd.DataFrame(geom_index_alg[1:])
        return geom_index_alg
    
    @classmethod
    def get_algorithm_ewma(cls, geom_index_alg: pd.DataFrame) -> float:
        """
        Calculate the Exponentially Weighted Moving Average (EWMA) for the algorithm based on strategy indices.

        Parameters
        ----------
        geom_index_alg: pd.DataFrame
            DataFrame with index values for strategies.

        Returns
        -------
        float
            Exponentially Weighted Moving Average (EWMA) for the algorithm.
        """
        gia_variation = cls.side_variations(geom_index_alg)
        individual_var_strategy = cls.get_individual_metrics(gia_variation)

        if "EWMA" not in individual_var_strategy.columns:
            raise KeyError("EWMA column is missing from individual metrics")
        
        return individual_var_strategy.loc["geom_index_alg", "EWMA"]

    @classmethod
    def get_log_variations(cls, strategy_indices_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate log variations of strategy indices.

        Parameters
        ----------
        strategy_indices_df: pd.DataFrame
            DataFrame with index values for strategies.

        Returns
        -------
        pd.DataFrame
            DataFrame with log variations for each strategy and the algorithm.
        """
        log_variation_df = np.log(strategy_indices_df / strategy_indices_df.shift(1))
        return log_variation_df[1:]

    def calculate_risk_metrics(self) -> pd.DataFrame:
        """
        Generate Value at Risk (VaR) and Exponentially Weighted Moving Average (EWMA) risk results for each strategy and the algorithm.

        Parameters
        ----------
        prices_df: pd.DataFrame
            DataFrame containing price data with multi-index columns for different sides.

        Returns
        -------
        pd.DataFrame
            DataFrame with VaR and EWMA values for each strategy and the algorithm.
        """
        try:
            #Calculate the variations for each asset depending on the side (BUY/SELL)
            self.price_variations_df = self.calculate_variations(self.tag_prices_df)
            logging.info("Price variations calculated successfully")
        except ValueError as e:
            logging.error("Error calculating price variations: " + str(e))
        
        try:
            # Calculate the index values for each strategy based on assets variations
            self.strategy_indices_df = self.get_strategy_indices(self.price_variations_df)
            logging.info("Strategy indices calculated successfully")
        except ValueError as e:
            logging.error("Error calculating strategy indices: " + str(e))

        try:
            # Calculate the variations for each strategy index
            self.strategies_variation_df = self.side_variations(self.strategy_indices_df)
            logging.info("Strategy variations calculated successfully")
        except ValueError as e:
            logging.error("Error calculating strategy variations: " + str(e))
        
        try:
            # Calculate the individual metrics for each strategy
            self.strategies_metrics_df = self.get_individual_metrics(
                self.strategies_variation_df
            )
            logging.info("Individual metrics calculated successfully")
        except ValueError as e:
            logging.error("Error calculating individual metrics: " + str(e))

        try:
            # Calculate value at risk (VaR) for each strategy
            strategies_var = self.get_strategies_var(self.price_variations_df)
        except ValueError as e:
            logging.error("Error calculating strategies VaR: " + str(e))
        
        try:
            # Get the EWMA values for each strategy
            strategies_ewma = self.strategies_metrics_df["EWMA"]

            # Create a DataFrame with the VaR and EWMA for each strategy
            self.risk_metrics_df = pd.DataFrame(columns=["VaR", "EWMA"])
            self.risk_metrics_df.index.name = "strategy"
            for strategy in self.strategy_indices_df.columns:
                if strategy in strategies_var and strategy in strategies_ewma:
                    strategy_var = -strategies_var[strategy]
                    strategy_ewman = strategies_ewma[strategy]
                    self.risk_metrics_df.loc[strategy] = (strategy_var, strategy_ewman)
                else:
                    raise ValueError(f"Missing VaR or EWMA for strategy '{strategy}'")
            logging.info("Risk metrics calculated successfully")
        except ValueError as e:
            logging.error("Error calculating risk metrics: " + str(e))

        try:
            # Calculate the geometric index for the algorithm based on strategy indices
            geom_index_alg = self.get_geom_index_alg(self.strategy_indices_df)
            logging.info("Geometric index for the algorithm calculated successfully")
        except ValueError as e:
            logging.error("Error calculating geometric index for the algorithm: " + str(e))
        
        try:
            # Calculate the VaR and EWMA for the algorithm
            self.risk_metrics_df.loc["Algoritmo GEA"] = (
                -self.get_algorithm_var(self.strategy_indices_df),
                self.get_algorithm_ewma(geom_index_alg),
            )
            logging.info("VaR and EWMA for the algorithm calculated successfully")
        except ValueError as e:
            logging.error("Error calculating VaR and EWMA for the algorithm: " + str(e))
            
        try:
            # Add the geometric index for the algorithm to the strategy indices DataFrame
            self.strategy_indices_df["Algoritmo GEA"] = geom_index_alg
            logging.info("Geometric index for the algorithm added to the strategy indices DataFrame")
        except ValueError as e:
            logging.error("Error adding the geometric index for the algorithm to the strategy indices DataFrame: " + str(e))

        try:
            # Calculate the log variations for each strategy and the algorithm
            self.log_variation_df = self.get_log_variations(self.strategy_indices_df)
            logging.info("Log variations calculated successfully")
        except ValueError as e:
            logging.error("Error calculating log variations: " + str(e))