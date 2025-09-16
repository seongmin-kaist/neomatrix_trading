# strategy.py
import pandas as pd
import numpy as np

def strategy(df: pd.DataFrame, config_dict: dict) -> dict:
    """
    Implements a mean-reversion trading strategy based on Z-scores derived from
    rolling mean and standard deviation, conceptually inspired by the Ornstein-Uhlenbeck process.

    Args:
        df (pd.DataFrame): Price time-series data.
                           Index: datetime
                           Columns: symbols (e.g., BTCUSDT, ETHUSDT, …)
        config_dict (dict): Strategy settings dictionary.
                            Expected structure:
                            {
                                "strategy_config": {
                                    "long_window": int,
                                    "std_window": int,
                                    "entry_zscore": float,
                                    "exit_zscore": float,
                                    "max_weight_per_symbol": float
                                }
                            }

    Returns:
        dict: Weights for each symbol ({symbol: weight}).
              Positive values = Long positions
              Negative values = Short positions
              The absolute sum of all weights must NOT exceed 1.0.
    """
    # Input Validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")
    if df.empty:
        # If no data, return neutral weights.
        return {}

    # Access Strategy Specific Configuration
    strategy_specific_config = config_dict.get("strategy_config", {})
    long_window = strategy_specific_config.get("long_window", 60)
    std_window = strategy_specific_config.get("std_window", 20)
    entry_zscore = strategy_specific_config.get("entry_zscore", 1.5)
    exit_zscore = strategy_specific_config.get("exit_zscore", 0.5)
    max_weight_per_symbol = strategy_specific_config.get("max_weight_per_symbol", 0.1)

    # Validate configuration parameters
    if not isinstance(long_window, int) or long_window <= 0:
        raise ValueError("Config 'long_window' must be a positive integer.")
    if not isinstance(std_window, int) or std_window <= 0:
        raise ValueError("Config 'std_window' must be a positive integer.")
    if long_window < std_window:
        raise ValueError("Config 'long_window' must be greater than or equal to 'std_window'.")
    if not isinstance(entry_zscore, (int, float)) or entry_zscore <= 0:
        raise ValueError("Config 'entry_zscore' must be a positive number.")
    if not isinstance(exit_zscore, (int, float)) or exit_zscore <= 0:
        raise ValueError("Config 'exit_zscore' must be a positive number.")
    if exit_zscore >= entry_zscore:
        raise ValueError("Config 'exit_zscore' must be less than 'entry_zscore'.")
    if not isinstance(max_weight_per_symbol, (int, float)) or not (0 < max_weight_per_symbol <= 1.0):
        raise ValueError("Config 'max_weight_per_symbol' must be a number between 0 (exclusive) and 1 (inclusive).")

    # Ensure enough data for rolling calculations
    required_data_points = max(long_window, std_window)
    if len(df) < required_data_points:
        # Not enough data to calculate indicators, return neutral weights for all symbols
        return {symbol: 0.0 for symbol in df.columns}

    weights = {}
    
    # Iterate over each symbol to calculate signals and determine weights
    for symbol in df.columns:
        prices = df[symbol]

        # Calculate rolling mean, serving as the estimated long-term mean (mu) for mean reversion
        # min_periods ensures that NaN is returned if not enough data points are available
        rolling_mean = prices.rolling(window=long_window, min_periods=long_window).mean().iloc[-1]

        # Calculate rolling standard deviation, serving as a measure of volatility (sigma)
        rolling_std = prices.rolling(window=std_window, min_periods=std_window).std().iloc[-1]

        current_price = prices.iloc[-1]

        # If rolling mean or std cannot be calculated (e.g., not enough data for min_periods)
        # or if std is zero (no price movement), set weight to neutral.
        if pd.isna(rolling_mean) or pd.isna(rolling_std) or rolling_std == 0:
            weights[symbol] = 0.0
            continue

        # Calculate the Z-score: deviation from the mean in terms of standard deviations
        z_score = (current_price - rolling_mean) / rolling_std

        # Determine position based on Z-score thresholds
        if z_score < -entry_zscore:
            # Price is significantly below its mean, indicating an oversold condition.
            # Expect reversion upwards, so go long.
            weights[symbol] = max_weight_per_symbol
        elif z_score > entry_zscore:
            # Price is significantly above its mean, indicating an overbought condition.
            # Expect reversion downwards, so go short.
            weights[symbol] = -max_weight_per_symbol
        elif abs(z_score) < exit_zscore:
            # Price has reverted close to the mean, or is within a neutral zone.
            # Exit any existing position.
            weights[symbol] = 0.0
        else:
            # If the Z-score is between exit_zscore and entry_zscore,
            # the strategy remains neutral or maintains its last position.
            # In a stateless function, this means setting to 0 if no explicit entry/exit signal.
            weights[symbol] = 0.0

    # Normalize weights to ensure the absolute sum does not exceed 1.0
    total_abs_weight = sum(abs(w) for w in weights.values())
    if total_abs_weight > 1.0:
        normalization_factor = 1.0 / total_abs_weight
        for symbol in weights:
            weights[symbol] *= normalization_factor

    return weights