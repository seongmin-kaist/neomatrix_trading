# strategy_config.py

strategy_config = {
    # Lookback period (in minutes) for the regression to calculate volatility betas.
    # The paper uses one month of daily data; 1440 minutes approximates one day.
    "beta_lookback_period": 1440,
    
    # Lookback period (in minutes) for calculating the rolling standard deviation
    # of the crypto market return, which serves as our volatility proxy.
    "volatility_lookback": 60,
    
    # Quantile threshold to determine the top and bottom groups for our long-short portfolio.
    # A value of 0.3 means we long the bottom 30% and short the top 30% of assets
    # based on their volatility beta.
    "quantile_threshold": 0.3,
}