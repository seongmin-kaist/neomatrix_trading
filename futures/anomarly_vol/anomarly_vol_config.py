# strategy_config.py

strategy_config = {
    "assets": ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
                        'TONUSDT', 'DOGEUSDT', 'ADAUSDT', 'TRXUSDT', 'AVAXUSDT',
                        'DOTUSDT', 'BCHUSDT', 'LTCUSDT', 'NEARUSDT', 'KASUSDT',
                        'ICPUSDT', 'XLMUSDT', 'ETCUSDT', 'APTUSDT', 'FETUSDT',
                        'FILUSDT', 'STXUSDT', 'ATOMUSDT', 'HBARUSDT', 'VETUSDT',
                        'SUIUSDT', 'ARUSDT', 'THETAUSDT', 'RUNEUSDT', 'ALGOUSDT',
                        'COREUSDT', 'FLOWUSDT', 'BSVUSDT', 'SEIUSDT', 'EGLDUSDT',
                        'XTZUSDT', 'NEOUSDT', 'CFXUSDT', 'MINAUSDT', 'IOTAUSDT',
                        'LUNCUSDT', 'CKBUSDT', 'IOTXUSDT', 'KSMUSDT', 'DYMUSDT',
                        'ZILUSDT', 'CELOUSDT', 'QTUMUSDT', 'RVNUSDT', 'ONEUSDT',
                        'ONTUSDT', 'ICXUSDT', 'BBUSDT', 'COTIUSDT', 'SXPUSDT',
                        'LSKUSDT', 'NTRNUSDT', 'TAIKOUSDT', 'WAXPUSDT', 'IOSTUSDT',
                        'XVGUSDT', 'NKNUSDT', 'BEAMUSDT', 'MEMEUSDT', 'JUPUSDT',
                        'ARBUSDT', 'GTCUSDT'],
    # Defines the lookback period (in minutes) for calculating short-term volatility.
    # This parameter captures the most recent price fluctuation intensity.
    "short_vol_window": 20,

    # Defines the lookback period (in minutes) for the medium-term volatility benchmark.
    # This acts as the baseline to which the short-term volatility is compared.
    "long_vol_window": 60,

    # Sets the maximum absolute value for the raw signal before normalization.
    # This helps to mitigate the impact of extreme volatility spikes on position sizing.
    "clip_threshold": 2.0
}