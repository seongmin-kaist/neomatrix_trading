# ==========================
# Strategy Parameter Settings
# ==========================

strategy_config = {
    # List of assets to trade
    "assets": ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BCHUSDT", "LTCUSDT",
               "ADAUSDT", "ETCUSDT", "TRXUSDT", "DOTUSDT", "DOGEUSDT"],

    # --- Signal & Gate Parameters ---
    # Period for calculating the core momentum signal (days)
    "mom_period": 30,
    # Period for calculating the standard deviation of volume (days)
    "vol_std_period": 20,
    # Period for calculating the Z-score of volume volatility (days)
    "vol_z_period": 60,
    # Z-score threshold to define a "calm" market. Trades are allowed if z < threshold.
    "vol_z_threshold": -0.5,
    # Period for calculating the momentum signal's own volatility (days)
    "mom_vol_period": 30,
    
    # --- Risk & Sizing Parameters ---
    # Maximum absolute weight per asset (e.g., 0.005 = 0.5% of portfolio)
    "position_limit": 0.005,
    # Period for smoothing final weights to control turnover (days)
    "smoothing_period": 5,
    # Polarity of the final signal (1 for momentum, -1 for mean-reversion)
    "signal_polarity": 1,
    
    # --- Portfolio Construction ---
    # If True, weights are rank-normalized cross-sectionally.
    # If False, dollar-neutralized weights are used directly.
    "use_rank_normalization": True
}