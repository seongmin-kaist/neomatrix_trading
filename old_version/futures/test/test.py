import numpy as np

def strategy(df, config_dict):

    weights = {'ALTUSDT': np.float64(0.005),
 'COTIUSDT': np.float64(0.005),
 'AUDIOUSDT': np.float64(0.005),
 'LUNCUSDT': np.float64(0.005),
 'USTCUSDT': np.float64(0.005),
 'SNTUSDT': np.float64(0.005),
 'HOTUSDT': np.float64(0.005),
 'XUSDT': np.float64(0.005),
 'MINAUSDT': np.float64(0.005),
 'ETHWUSDT': np.float64(0.005),
 'AUCTIONUSDT': np.float64(0.005),
 'ONEUSDT': np.float64(0.005),
 'TIAUSDT': np.float64(0.005),
 'CAKEUSDT': np.float64(-0.005),
 'XAUTUSDT': np.float64(-0.005),
 'SOLUSDT': np.float64(-0.005),
 'AVAXUSDT': np.float64(-0.004817298503605088),
 'IMXUSDT': np.float64(-0.004192639871291706),
 'BBUSDT': np.float64(-0.0034070451295572456)}

    return weights