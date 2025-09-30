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

    # --- 5. Weight Allocation (Normalization) ---
    # The goal is to allocate capital based on signal strength, ensuring the
    # total capital usage (sum of absolute weights) equals 1.0 (or 100%).
    # This fulfills the requirement that the total weight summation is 1.

    # Calculate the sum of the absolute values of all signals. This represents the
    # total "conviction" of the strategy across all selected positions.
    total_abs_signal = np.abs(final_signals).sum()

    # Normalize each signal by dividing by the total absolute signal.
    # This ensures that the sum of the absolute values of the final weights equals 1.
    # Example: If signals are {"BTC": 0.6, "ETH": -0.4}, total_abs_signal is 1.0.
    # The final weights will be {"BTC": 0.6, "ETH": -0.4}.
    # The sum of absolute weights is |0.6| + |-0.4| = 1.0.
    if total_abs_signal > 0:
        weights = final_signals / total_abs_signal
    else:
        # If there are no signals, all weights are zero.
        weights = final_signals * 0

    # The resulting 'weights' dictionary represents a fully invested portfolio
    # where the sum of absolute allocations equals 1.0.

    return weights.to_dict()