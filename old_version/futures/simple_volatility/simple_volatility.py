# strategy.py
import pandas as pd
import numpy as np

def strategy(df, config_dict):
    """
    Develops a momentum signal adjusted for volatility.
    The signal is the raw momentum divided by recent volatility.
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
    momentum_lookback = strategy_specific_config.get("momentum_lookback", 60)
    volatility_lookback = strategy_specific_config.get("volatility_lookback", 20)

    # --- Signal Calculation ---
    signals = {}
    
    for symbol in df.columns:
        series = df[symbol].dropna()
        
        # Ensure there's enough data for both momentum and volatility calculations
        if len(series) < momentum_lookback + 1 or len(series) < volatility_lookback + 1:
            continue

        # --- Calculate Raw Momentum ---
        # Momentum is the return over the last `momentum_lookback` hours
        price_now = series.iloc[-1]
        price_then = series.iloc[-(momentum_lookback + 1)]
        
        if price_then == 0:
            continue # Avoid division by zero
        raw_momentum = (price_now / price_then) - 1

        # --- Calculate Volatility ---
        # Volatility is the standard deviation of hourly returns over the last `volatility_lookback` hours
        # We need `volatility_lookback + 1` prices to calculate `volatility_lookback` returns
        recent_prices = series.iloc[-(volatility_lookback + 1):]
        hourly_returns = recent_prices.pct_change().dropna()
        
        # Ensure there are returns to calculate standard deviation on
        if hourly_returns.empty:
            continue
            
        volatility = hourly_returns.std()

        # --- Calculate Final Signal ---
        # The final signal is the momentum adjusted for volatility
        # If volatility is zero, the signal is undefined; we set it to zero to avoid errors
        if volatility > 0:
            signals[symbol] = raw_momentum / volatility
        else:
            signals[symbol] = 0.0

    if not signals:
        return {}
    
    # --- Weight Allocation ---
    # Normalize signals so that the sum of absolute weights equals 1.0
    total_abs_signal = sum(abs(s) for s in signals.values())
    
    if total_abs_signal == 0:
        return {}

    weights = {s: sig / total_abs_signal for s, sig in signals.items()}

    return weights