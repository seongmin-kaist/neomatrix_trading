from module.data_context import DataContext
import pandas as pd
import numpy as np

def strategy(context: DataContext, config_dict: dict) -> dict:
    weights = {
    'DOGEUSDT': 1.0,
    'XRPUSDT': -1.0,
    }
    return weights
