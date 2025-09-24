# strategy_config.py

strategy_config_params = {
  "rebalancing_config": {
    "rebalancing_interval_hours": 72, ## Rebalancing cycle (choose between 6, 12, 24, and 72 hours)
  },
  "strategy_config": {
    "momentum_lookback": 60,   # Lookback period in hours for the raw momentum calculation
    "volatility_lookback": 20  # Lookback period in hours for the volatility calculation
  }
}