# strategy.py
import pandas as pd
import numpy as np

def strategy(df, config_dict):
    """
    Generates a mean-reversion signal based on historical cumulative returns.

    The signal is the negative of the cumulative return over a lookback period,
    ignoring the most recent 'lag' periods. This strategy sells recent
    winners and buys recent losers.
    """
    # --- Input validation ---
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    if not isinstance(config_dict, dict):
        raise TypeError("config_dict must be a dictionary.")

    # --- Load strategy-specific config ---
    strategy_specific_config = config_dict.get("strategy_config", {})
    # Lookback period in hours for the return calculation
    lookback_hours = strategy_specific_config.get("lookback_hours", 10)
    # Number of recent hours to ignore in the calculation
    lag_hours = strategy_specific_config.get("lag_hours", 1)

    # --- Signal Calculation ---
    signals = {}
    total_window = lookback_hours + lag_hours

    for symbol in df.columns:
        series = df[symbol].dropna()
        # Ensure there's enough data for the calculation
        if len(series) < total_window + 1:
            continue

        # Define the start and end points for the return calculation
        # The end point is `lag_hours` ago from the most recent price
        price_end = series.iloc[-(lag_hours + 1)]
        # The start point is `lookback_hours` before the end point
        price_start = series.iloc[-(total_window + 1)]

        # Avoid division by zero
        if price_start == 0:
            continue
            
        # Calculate the cumulative return over the specified window
        cumulative_return = (price_end / price_start) - 1
        
        # The signal is the negative of the return (mean-reversion)
        signals[symbol] = -cumulative_return

    if not signals:
        return {}
    
    # --- Weight Allocation ---
    # Normalize signals so that the sum of absolute weights equals 1.0
    total_abs_signal = sum(abs(s) for s in signals.values())
    
    # If all signals are zero, return empty weights
    if total_abs_signal == 0:
        return {}

    weights = {s: sig / total_abs_signal for s, sig in signals.items()}

    return weights