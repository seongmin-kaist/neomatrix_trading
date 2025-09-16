# strategy_config.py
strategy_config = {
    "long_window": 60,  # Lookback period for the long-term rolling mean (e.g., 60 minutes for 1 hour mean)
    "std_window": 20,   # Lookback period for the rolling standard deviation used in Z-score calculation
    "entry_zscore": 1.5, # Z-score threshold to enter a position (e.g., 1.5 standard deviations from the mean)
    "exit_zscore": 0.5,  # Z-score threshold to exit a position (e.g., 0.5 standard deviations from the mean)
    "max_weight_per_symbol": 0.1 # Maximum absolute weight allocated to a single symbol before overall normalization
}