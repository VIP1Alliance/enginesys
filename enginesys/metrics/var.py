import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

class ValueAtRisk:

    def get_strategy_variations(trades_month_df, adjusted_close):
        variation_df = {}
        for strategy in trades_month_df["strategy"].unique():
            trades_month_strategy_df = trades_month_df[trades_month_df["strategy"] == strategy]
            tickers_buy = list(trades_month_strategy_df["ticker"][trades_month_strategy_df["side"] == "BUY"].unique())
            tickers_sell = list(trades_month_strategy_df["ticker"][trades_month_strategy_df["side"] == "SELL"].unique())
            return_buy = adjusted_close[tickers_buy].shift(-1) / adjusted_close[tickers_buy]
            return_sell = adjusted_close[tickers_sell] / adjusted_close[tickers_sell].shift(-1)
            variation_strat_df = pd.concat([return_buy, return_sell], axis=1).dropna()
            variation_df[strategy] = variation_strat_df.dropna()
        return variation_df

    def get_individual_metrics(trades_month_df, adjusted_close):
        individual_metrics_df= helpers.VaR_daily(adjusted_close, trades_month_df)
        individual_metrics_df["strategy"] = list(trades_month_df["strategy"])
        return individual_metrics_df

    # def get_strategies_var(individual_metrics_df, price_variations_df, tickers_by_strategy):
    #     strategies_var = {}
    #     for strategy in individual_metrics_df["strategy"].unique():
    #         metrics_df = individual_metrics_df[individual_metrics_df["strategy"] == strategy]
    #         tickers = tickers_by_strategy[strategy]
    #         n_tickers= len(tickers)
    #         # Tickers Weights
    #         weights = np.array([1/n_tickers]*n_tickers)
    #         # Excess Matrix
    #         excess_matrix = price_variations_df[strategy] - weights
    #         var_cov_matrix = excess_matrix.cov()
    #         for ticker in list(var_cov_matrix.columns):
    #             var_cov_matrix.at[ticker, ticker] = metrics_df.loc[ticker, "Varianza"]
    #         # Strategy Variance
    #         # TODO: Check if the matrix multiplication is correct. Negative values are being returned
    #         portfolio_variance = weights.dot(var_cov_matrix).dot(weights)
    #         if portfolio_variance < 0:
    #             logging.warning(f"Negative portfolio variance for 'strategy {strategy}'")
    #             strategies_var[strategy] = np.nan
    #         else:
    #         # Strategy VaR
    #             strategy_var = np.sqrt(portfolio_variance)
    #             strategies_var[strategy] = strategy_var
    #     return strategies_var

    # def compute_individual_index(variations_df, strategy):
    #     temp_df = variations_df[strategy].copy()
    #     temp_df["product_variations"] = (temp_df.prod(axis=1))**(1/len(temp_df.columns))
    #     temp_df.at[temp_df.index[0], 'product_variations'] = 1
    #     index_strategy = (temp_df["product_variations"].cumprod()*100)
    #     return index_strategy

    # def get_index_strategies(trades_month_df, price_variations_df):
    #     index_strategies = pd.DataFrame()
    #     strategies = list(trades_month_df["strategy"].unique())
    #     for strategy in strategies:
    #         index_strategies[strategy] = compute_individual_index(price_variations_df, strategy)  
    #     index_strategies = index_strategies[1:]
    #     return index_strategies

    # def get_strategies_metrics(index_strategies):
    #     strategies = list(index_strategies.columns)
    #     index_side = pd.DataFrame({"ticker": strategies, "side": ["BUY"] * len(strategies)})
    #     individual_strategy_metrics = helpers.VaR_daily(prices_df=index_strategies, trades_df=index_side)
    #     return individual_strategy_metrics

    # def get_var_cov_algo_matrix(index_strategies):
    #     strategies = list(index_strategies.columns)
    #     strats_variation_df = index_strategies.shift(-1)/index_strategies
    #     n_strategies = len(strategies)
    #     strategy_weights  = np.array([1/n_strategies]*n_strategies)
    #     excess_matrix_algorithm = strats_variation_df - strategy_weights
    #     var_cov_algo_matrix = excess_matrix_algorithm.cov()
    #     individual_strategy_metrics = get_strategies_metrics(index_strategies)
    #     for strategy in strategies:
    #         var_cov_algo_matrix.at[strategy, strategy] = individual_strategy_metrics.loc[strategy, "Varianza"]
    #     return var_cov_algo_matrix

    # def var_from_matrix(var_cov_algo_matrix):
    #     strategies = list(var_cov_algo_matrix.columns)
    #     n_strategies = len(strategies)
    #     strategy_weights  = np.array([1/3]*n_strategies)
    #     algorithm_variance = strategy_weights.dot(var_cov_algo_matrix).dot(strategy_weights)
    #     if algorithm_variance < 0:
    #         logging.warning(f"Negative Variance obtained for 'Gea Algorithm'")
    #         algorithm_var = np.nan
    #     else:
    #     # Strategy VaR
    #         algorithm_var = np.sqrt(algorithm_variance)
    #     return algorithm_var

    # def get_algorithm_var(index_strategies):
    #     var_cov_algo_matrix =  get_var_cov_algo_matrix(index_strategies)
    #     algorithm_var = var_from_matrix(var_cov_algo_matrix)
    #     return algorithm_var

    # def get_geometric_index_algorithm(index_strategies):
    #     n_strategies = len(list(index_strategies.columns))
    #     strategy_weights  = np.array([1/n_strategies]*n_strategies)
    #     base_value = (index_strategies.iloc[0]*strategy_weights).sum()
    #     geometric_index_algorithm = (index_strategies.mul(strategy_weights).sum(axis=1) / base_value) * 100
    #     geometric_index_algorithm = pd.DataFrame(geometric_index_algorithm[1:])
    #     geometric_index_algorithm.rename(columns={0: "geometric_index_alg"}, inplace=True)
    #     return geometric_index_algorithm

    # def get_algorithm_ewma(index_strategies):
    #     geometric_index_algorithm = get_geometric_index_algorithm(index_strategies)
    #     geo_index_side = pd.DataFrame({"ticker": ["geometric_index_alg"], "side": ["BUY"]})
    #     individual_var_strategy = helpers.VaR_daily(prices_df=geometric_index_algorithm, trades_df=geo_index_side)
    #     return individual_var_strategy.loc["geometric_index_alg", "EWMA"]

    # def generate_risk_results(trades_month_df, adjusted_close):
    #     tickers_by_strategy = trades_month_df.groupby("strategy")["ticker"].apply(list).to_dict()
    #     price_variations_df = calculate_variations(trades_month_df, adjusted_close)
    #     index_strategies_df = get_index_strategies(trades_month_df, price_variations_df)
    #     individual_metrics_df = get_individual_metrics(trades_month_df, adjusted_close)
    #     strategies_metrics_df = get_strategies_metrics(index_strategies_df)
    #     strategies_var = get_strategies_var(individual_metrics_df, price_variations_df, tickers_by_strategy)
    #     strategies_ewma = strategies_metrics_df["EWMA"]
    #     # Calculate the VaR and EWMA for each strategy
    #     var_ewma_values_df = pd.DataFrame(columns=["VaR", "EWMA"])
    #     for strategy in index_strategies_df.columns:
    #         strategy_var = -strategies_var[strategy]
    #         strategy_ewman = strategies_ewma[strategy]
    #         var_ewma_values_df.loc[strategy] = (strategy_var, strategy_ewman)
    #     # Calculate the VaR and EWMA for the algorithm
    #     var_ewma_values_df.loc["Algoritmo GEA"] = (-get_algorithm_var(index_strategies_df), get_algorithm_ewma(index_strategies_df))
    #     return var_ewma_values_df

    # def get_log_variations(trades_month_df, adjusted_close):
    #     price_variations_df = calculate_variations(trades_month_df, adjusted_close)
    #     indices_df = get_index_strategies(trades_month_df, price_variations_df)
    #     geometric_index_algorithm = get_geometric_index_algorithm(indices_df)["geometric_index_alg"]
    #     indices_df["Algoritmo GEA"] = geometric_index_algorithm
    #     log_variation_df = np.log(indices_df.shift(-1)/indices_df)[:-1]
    #     return log_variation_df