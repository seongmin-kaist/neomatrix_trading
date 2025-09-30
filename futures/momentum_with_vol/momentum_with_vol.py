from module.data_context import DataContext
import pandas as pd
import numpy as np

def strategy(context: DataContext, config_dict: dict) -> dict:
    """
    Implements a daily momentum strategy gated by low volume volatility.

    The strategy operates based on the following logic:
    1.  **Weekly Rebalancing:** Trades are only executed on the first day of the week (Monday).
    2.  **Momentum Signal:** A 30-day price return is used as the core signal.
    3.  **Flow-Stress Gate:** Trading is only enabled when the Z-score of recent volume
        volatility is unusually low, indicating a 'calm' market.
    4.  **Volatility Scaling:** The momentum signal is scaled by its own recent volatility.
    5.  **Risk Controls:**
        - Positions are capped at a small percentage of the portfolio.
        - Weights are smoothed over time to reduce turnover.
        - The final portfolio is made dollar-neutral (longs equal shorts).
        - Optionally, weights can be rank-normalized across assets.
    
    NOTE: Portfolio-level drawdown guards and automatic signal polarity checks
    are not implemented as they require historical portfolio equity data and
    backtesting capabilities, which are outside the scope of this function.
    Polarity can be manually inverted via the config file.
    """
    # Load strategy configuration
    strategy_params = config_dict.get("strategy_config", {})
    assets = strategy_params.get("assets", [])
    mom_period = strategy_params.get("mom_period", 30)
    vol_std_period = strategy_params.get("vol_std_period", 20)
    vol_z_period = strategy_params.get("vol_z_period", 60)
    vol_z_threshold = strategy_params.get("vol_z_threshold", -0.5)
    mom_vol_period = strategy_params.get("mom_vol_period", 30)
    position_limit = strategy_params.get("position_limit", 0.005)
    smoothing_period = strategy_params.get("smoothing_period", 5)
    use_rank_normalization = strategy_params.get("use_rank_normalization", True)
    signal_polarity = strategy_params.get("signal_polarity", 1)

    # Determine the required lookback window for historical data
    window = vol_z_period + vol_std_period + 5

    # Fetch daily historical price and volume data
    hist = context.get_history(
        assets=assets,
        window=window,
        frequency="1d",
        fields=["close", "volume"]
    )

    if hist.empty or len(hist.index.get_level_values('datetime').unique()) < window:
        return {}

    # --- Weekly Rebalancing Gate (FIXED) ---
    # Get the most recent timestamp from the fetched historical data
    latest_timestamp = hist.index.get_level_values('datetime')[-1]
    # Check if it's Monday (weekday() == 0). If not, hold positions by returning empty weights.
    if latest_timestamp.weekday() != 0:
        return {}

    # Pivot dataframes to have assets as columns and datetime as index
    close_df = hist["close"].unstack(level=0)
    volume_df = hist["volume"].unstack(level=0)

    # --- 1. Core Price Signal (Momentum) ---
    momentum = (close_df / close_df.shift(mom_period)) - 1

    # --- 2. Flow-Stress Gate ---
    volume_std = volume_df.rolling(window=vol_std_period, min_periods=vol_std_period).std()
    vol_z_mean = volume_std.rolling(window=vol_z_period, min_periods=vol_z_period).mean()
    vol_z_std = volume_std.rolling(window=vol_z_period, min_periods=vol_z_period).std()
    volume_z_score = (volume_std - vol_z_mean) / vol_z_std
    gate = (volume_z_score < vol_z_threshold).astype(int)

    # --- 3. Volatility-Scaled Sizing ---
    momentum_vol = momentum.rolling(window=mom_vol_period, min_periods=mom_vol_period).std()
    raw_weight = (momentum * gate) / momentum_vol
    raw_weight.replace([np.inf, -np.inf], np.nan, inplace=True)
    raw_weight.fillna(0, inplace=True)

    # --- 4. Risk Caps & Turnover Control ---
    clipped_weight = raw_weight.clip(-position_limit, position_limit)
    smooth_weight = clipped_weight.ewm(span=smoothing_period, adjust=False).mean()

    # --- 5. Cross-sectional Neutralization & Final Polishing ---
    neutral_weight = smooth_weight.sub(smooth_weight.mean(axis=1), axis=0)
    
    final_weight_df = neutral_weight
    if use_rank_normalization:
        ranked_weight = neutral_weight.rank(axis=1, pct=True)
        final_weight_df = ranked_weight - 0.5

    # --- 6. Final Weight Generation ---
    latest_weights = final_weight_df.iloc[-1]
    latest_weights *= signal_polarity
    latest_weights.fillna(0, inplace=True)

    total_abs_weight = latest_weights.abs().sum()
    if total_abs_weight > 1.0:
        latest_weights = latest_weights / total_abs_weight

    return latest_weights.to_dict()