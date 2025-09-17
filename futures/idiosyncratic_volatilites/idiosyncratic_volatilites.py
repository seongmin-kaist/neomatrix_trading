# strategy.py

import pandas as pd
import numpy as np
import statsmodels.api as sm

def strategy(df, config_dict):
    """
    Implements a long-short strategy based on asset sensitivity to systematic volatility shocks,
    inspired by "The Cross-Section of Volatility and Expected Returns".

    This adaptation is for cryptocurrency markets where a VIX index is unavailable.
    It proxies systematic volatility using the volatility of an equal-weighted crypto market index.

    The strategy is based on the paper's finding that assets with high sensitivity (high beta)
    to volatility shocks tend to have lower future returns. Therefore, this implementation
    shorts the high-beta assets and longs the low-beta assets.

    Args:
        df (pd.DataFrame): Price time-series data with datetime index and symbols as columns.
        config_dict (dict): Dictionary containing strategy settings.

    Returns:
        dict: A dictionary of weights for each symbol, e.g., {"BTCUSDT": 0.1, "ETHUSDT": -0.1}.
              The absolute sum of weights will not exceed 1.0.
    """
    # --- Input Validation ---
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Input 'df' must be a non-empty pandas DataFrame.")
    if not isinstance(config_dict, dict):
        raise TypeError("Input 'config_dict' must be a dictionary.")

    # --- Parameter Extraction ---
    strategy_specific_config = config_dict.get("strategy_config", {})
    beta_lookback_period = strategy_specific_config.get("beta_lookback_period", 1440)
    volatility_lookback = strategy_specific_config.get("volatility_lookback", 60)
    quantile_threshold = strategy_specific_config.get("quantile_threshold", 0.3)

    # --- Data Preparation ---
    # Ensure sufficient data for lookbacks
    if len(df) < beta_lookback_period + volatility_lookback:
        # Not enough data to perform calculations, return no positions
        return {symbol: 0.0 for symbol in df.columns}

    returns = df.pct_change()

    # --- Proxy for Systematic Factors (Crypto Market) ---
    # 1. Create a proxy for the overall market return (equal-weighted)
    market_return = returns.mean(axis=1)
    
    # 2. Create a proxy for market volatility (rolling std dev of market return)
    market_volatility = market_return.rolling(window=volatility_lookback).std()

    # 3. Create a proxy for innovations in market volatility (change in volatility)
    # This is the equivalent of ΔVIX from the paper.
    delta_market_vol = market_volatility.diff()

    # --- Beta Calculation ---
    # For each asset, regress its returns against the market return and volatility innovations
    # to find its sensitivity (beta) to volatility shocks.
    # The regression is: r_asset = α + β_mkt * r_mkt + β_vol * Δvol + ε
    
    betas = []
    regression_data = returns.iloc[-beta_lookback_period:]

    for symbol in regression_data.columns:
        # Prepare data for regression for the current symbol
        y = regression_data[symbol].dropna()
        
        X_df = pd.DataFrame({
            'market_return': market_return.loc[y.index],
            'delta_market_vol': delta_market_vol.loc[y.index]
        })
        
        # Align and drop any rows with missing values
        combined = pd.concat([y, X_df], axis=1).dropna()
        
        # Ensure there is enough data to run a regression
        if len(combined) < 30: # Use a minimum threshold for statistical relevance
            continue

        Y_reg = combined[symbol]
        X_reg = combined[['market_return', 'delta_market_vol']]
        X_reg = sm.add_constant(X_reg)

        try:
            model = sm.OLS(Y_reg, X_reg).fit()
            # Extract the beta for volatility innovations
            vol_beta = model.params.get('delta_market_vol', np.nan)
            if not np.isnan(vol_beta):
                betas.append({'symbol': symbol, 'vol_beta': vol_beta})
        except Exception:
            # Skip if regression fails for any reason
            continue

    if not betas:
        # If no betas could be calculated, return no positions
        return {symbol: 0.0 for symbol in df.columns}

    beta_df = pd.DataFrame(betas)

    # --- Portfolio Construction ---
    # Sort assets based on their volatility beta
    low_beta_cutoff = beta_df['vol_beta'].quantile(quantile_threshold)
    high_beta_cutoff = beta_df['vol_beta'].quantile(1 - quantile_threshold)

    # The paper's finding suggests high-beta assets underperform.
    # So, we long the low-beta assets and short the high-beta assets.
    long_symbols = beta_df[beta_df['vol_beta'] <= low_beta_cutoff]['symbol'].tolist()
    short_symbols = beta_df[beta_df['vol_beta'] >= high_beta_cutoff]['symbol'].tolist()
    
    # --- Weight Allocation ---
    weights = {symbol: 0.0 for symbol in df.columns}
    num_positions = len(long_symbols) + len(short_symbols)

    if num_positions == 0:
        return weights

    # Allocate capital equally across all long and short positions
    weight_per_asset = 1.0 / num_positions

    for symbol in long_symbols:
        weights[symbol] = weight_per_asset
        
    for symbol in short_symbols:
        weights[symbol] = -weight_per_asset
        
    return weights