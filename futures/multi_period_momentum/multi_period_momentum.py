from module.data_context import DataContext
import pandas as pd

def strategy(context: DataContext, config_dict: dict) -> dict:
    """
    Hourly momentum strategy with configurable long/short ratio.
    periods in config are automatically in minutes.
    """
    # Load strategy configuration
    strategy_params = config_dict.get("strategy_config", {})
    assets = strategy_params.get("assets", [])
    window = strategy_params.get("window", 180)  # window in minutes
    periods = strategy_params.get("minutes", [60, 120, 180])  # already in minutes
    long_ratio = strategy_params.get("long_ratio", 0.7)
    short_ratio = strategy_params.get("short_ratio", 0.3)

    # Fetch historical price data at 1-minute frequency
    hist = context.get_history(
        assets=assets,
        window=window + max(periods),
        frequency="1m",
        fields=["close"]
    )

    if hist.empty:
        return {}

    # Pivot to have index=datetime, columns=asset
    df = hist["close"].unstack(level=0)

    # Calculate momentum for each asset
    momentum = {}
    for col in df.columns:
        col_momentum = 0
        for p in periods:
            if len(df) > p:
                first_price = df[col].iloc[-p-1]
                last_price = df[col].iloc[-1]
                if first_price != 0:
                    col_momentum += (last_price / first_price) - 1
        momentum[col] = col_momentum / len(periods)

    # Separate long and short
    longs = {k: v for k, v in momentum.items() if v > 0}
    shorts = {k: v for k, v in momentum.items() if v < 0}

    # Normalize weights
    weights = {}
    total_long = sum(longs.values())
    total_short = -sum(shorts.values())
    for k, v in longs.items():
        weights[k] = (v / total_long) * long_ratio if total_long != 0 else 0
    for k, v in shorts.items():
        weights[k] = (v / total_short) * short_ratio if total_short != 0 else 0

    # Ensure total absolute weight ≤ 1
    abs_sum = sum(abs(w) for w in weights.values())
    if abs_sum > 1.0:
        scale = 1.0 / abs_sum
        for k in weights:
            weights[k] *= scale

    return weights
