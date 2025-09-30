# ==========================
# Strategy Parameter Settings
# ==========================

hours = [1,2,3]  # momentum periods in hours
strategy_config = {
    "assets": ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BCHUSDT", "LTCUSDT",
               "ADAUSDT", "ETCUSDT", "TRXUSDT", "DOTUSDT", "DOGEUSDT"],
    "window": 180,
    "minutes": [int(i*60) for i in hours],  # convert hours to minutes
    "long_ratio": 0.7,
    "short_ratio": 0.3    
}
