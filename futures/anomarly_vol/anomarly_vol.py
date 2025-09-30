# strategy.py
import pandas as pd
import numpy as np
from module.data_context import DataContext # Import the necessary module

def strategy(context: DataContext, config_dict: dict) -> dict:
    """
    Implements the Micro-structure Volatility Anomaly strategy with position limits.

    This version correctly fetches historical data using the DataContext module before
    applying the trading logic.
    - It fetches data for a pre-defined asset list.
    - It selects the top N long and top N short candidates based on the signal.
    - It shorts assets with unusually high recent volatility (mean-reversion).
    - It longs assets with unusually low recent volatility.
    """
    # --- 1. Configuration Extraction ---
    strategy_params = config_dict.get("strategy_config", {})
    assets = strategy_params.get("assets", [])
    short_vol_window = strategy_params.get("short_vol_window", 20)
    long_vol_window = strategy_params.get("long_vol_window", 60)
    clip_threshold = strategy_params.get("clip_threshold", 2.0)
    max_positions = strategy_params.get("max_positions", 6)

    if not assets:
        return {} # Exit if no assets are specified

    # --- 2. Data Fetching ---
    # The total lookback period required is the sum of the two volatility windows.
    # We add a small buffer to ensure enough data for rolling calculations.
    total_lookback = short_vol_window + long_vol_window + 5
    
    hist = context.get_history(
        assets=assets,
        window=total_lookback,
        frequency="1m",
        fields=["close"]
    )

    # Exit if no historical data is returned
    if hist.empty:
        return {}

    # Pivot the data to have datetime as index and assets as columns
    df = hist["close"].unstack(level=0)
    
    # Ensure all required assets are present after unstacking
    tradable_assets = [asset for asset in assets if asset in df.columns]
    if not tradable_assets:
        return {}
    df_filtered = df[tradable_assets]


    # --- 3. Strategy Logic ---
    # Step 1: Compute 1-minute percentage returns.
    returns = df_filtered.pct_change(1)

    # Step 2: Calculate short-term realized volatility.
    vol_short = returns.rolling(window=short_vol_window, min_periods=short_vol_window).std()

    # Step 3: Calculate the medium-term volatility benchmark.
    vol_long = vol_short.rolling(window=long_vol_window, min_periods=long_vol_window).mean()

    # Step 4: Form a volatility-relative signal (z-score like measure).
    epsilon = 1e-10
    zvol = (vol_short - vol_long) / (vol_long + epsilon)

    # Step 5: Generate the final trading signal (inverted for mean-reversion).
    signal = -zvol

    # Step 6: Clip the raw signal.
    signal_clipped = signal.clip(-clip_threshold, clip_threshold)

    # --- 4. Position Selection ---
    latest_signal = signal_clipped.iloc[-1].dropna()

    if latest_signal.empty:
        return {}

    # Sort signals to find the strongest long (positive) and short (negative) candidates.
    sorted_signals = latest_signal.sort_values(ascending=False)
    
    num_longs = max_positions // 2
    num_shorts = max_positions - num_longs
    
    long_candidates = sorted_signals[sorted_signals > 0].head(num_longs)
    short_candidates = sorted_signals[sorted_signals < 0].tail(num_shorts)
    
    final_signals = pd.concat([long_candidates, short_candidates])

    if final_signals.empty:
        return {}

    # --- 5. Weight Allocation ---
    total_abs_signal = np.abs(final_signals).sum()

    if total_abs_signal > 0:
        weights = final_signals / total_abs_signal
    else:
        weights = final_signals * 0

    return weights.to_dict()