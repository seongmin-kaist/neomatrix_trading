# strategy.py

import requests
import pandas as pd
import time
from datetime import datetime
import numpy as np

def strategy(df, config_dict):
    
    data_url = "https://crypto.fin.cloud.ainode.ai/a71eaf04-802f-40be-93c2-5bee2548f4db/get/info/coin"
    response = requests.get(data_url)
    data = response.json()

    symbols = []
    for item in data['data']:
        symbols.append(item['coin_nm'] + 'USDT')

    def get_bitget_history_ohlcv(symbols, days_to_fetch, granularity='1D', product_type='umcbl'):
        """
        Bitget API를 사용하여 여러 종목의 일봉 OHLCV 데이터를 가져옵니다.
        API의 200개 제한을 해결하기 위한 페이지네이션 로직을 포함합니다.

        Args:
            symbols (list): 데이터를 가져올 심볼 리스트 (예: ['BTCUSDT', 'ETHUSDT'])
            days_to_fetch (int): 가져올 데이터의 날짜 수 (예: 500)
            granularity (str): 캔들 주기 ('1D'는 일봉)
            product_type (str): 상품 타입 ('umcbl'은 USDT 선물)

        Returns:
            pandas.DataFrame: MultiIndex 컬럼을 가진 OHLCV 데이터프레임.
                            (레벨 0: 심볼, 레벨 1: o, h, l, c, v 등)
        """
        base_url = "https://api.bitget.com"
        endpoint = "/api/v2/mix/market/history-candles"
        url = base_url + endpoint

        all_symbols_data = []

        for symbol in symbols:
            
            all_candles = []
            # Bitget은 endTime을 기준으로 과거 데이터를 조회하므로, 현재 시간부터 시작
            end_time_ms = int(datetime.now().timestamp() * 1000)

            while len(all_candles) < days_to_fetch:
                params = {
                    'symbol': symbol,
                    'granularity': granularity,
                    'productType': product_type,
                    'limit': 200,  # API 최대 요청 개수
                    'endTime': end_time_ms
                }

                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
                    data = response.json()

                    if data.get('code') != '00000':
                        # print(f"[{symbol}] API 오류: {data.get('msg')}")
                        break

                    candles = data.get('data', [])
                    if not candles:
                        # print(f"[{symbol}] 더 이상 데이터가 없습니다.")
                        break
                    
                    # 중복 저장을 막기 위해 기존 데이터와 겹치지 않는 부분만 추가
                    new_candles = [c for c in candles if c not in all_candles]
                    all_candles.extend(new_candles)

                    # 가장 오래된 데이터의 타임스탬프를 다음 요청의 endTime으로 설정
                    oldest_ts = int(candles[0][0])
                    end_time_ms = oldest_ts - 1 # 1ms를 빼서 중복 조회 방지
                    
                    # API 속도 제한을 피하기 위한 약간의 대기 시간
                    time.sleep(0.2) 

                except requests.exceptions.RequestException as e:
                    break
            
            if not all_candles:
                continue
            
            # 수집된 데이터를 DataFrame으로 변환
            df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'base_volume', 'volume'])
            
            # 필요한 컬럼만 선택하고 데이터 타입 변환
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df = df.astype(float)
            
            # 타임스탬프를 날짜/시간 인덱스로 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 전략에서 요구하는 MultiIndex 컬럼 형식으로 변경
            df.columns = pd.MultiIndex.from_product([[symbol], df.columns])
            
            all_symbols_data.append(df)
        
        if not all_symbols_data:
            return None

        # 모든 종목의 데이터프레임을 하나로 병합
        final_df = pd.concat(all_symbols_data, axis=1)
        
        # 데이터를 시간순으로 정렬하고 요청한 날짜만큼만 반환
        final_df.sort_index(inplace=True)
        return final_df.tail(days_to_fetch)
    
    target_symbols = symbols
    # target_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT']

    days = 60
    df = get_bitget_history_ohlcv(symbols=target_symbols, days_to_fetch=days)

    """
    Expected df format:
    - Index: datetime
    - Columns: pandas MultiIndex with level 0 as symbol (e.g., 'BTCUSDT') and
               level 1 as metric (e.g., 'close', 'volume').
    """
    # --- Input validation ---
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("Input DataFrame 'df' is empty.")
    if not isinstance(config_dict, dict):
        raise TypeError("'config_dict' must be a dictionary.")
    
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("Input DataFrame 'df' must have MultiIndex columns.")

    # --- Load strategy-specific config ---
    strategy_specific_config = config_dict.get("strategy_config", {})
    median_lookback = strategy_specific_config.get("median_lookback", 60)
    std_lookback = strategy_specific_config.get("std_lookback", 60)
    volume_z_lookback = strategy_specific_config.get("volume_z_lookback", 20)
    volume_z_threshold = strategy_specific_config.get("volume_z_threshold", 1.5)
    long_percentile = strategy_specific_config.get("long_percentile", 0.10)
    short_percentile = strategy_specific_config.get("short_percentile", 0.10)
    vol_lookback = strategy_specific_config.get("vol_lookback", 30)
    vol_target_scaler = strategy_specific_config.get("vol_target_scaler", 0.0005)
    weight_clip = strategy_specific_config.get("weight_clip", 0.005)
    dd_lookback = strategy_specific_config.get("dd_lookback", 5)
    dd_threshold = strategy_specific_config.get("dd_threshold", 0.02)


    # --- Signal Calculation ---
    symbols = df.columns.get_level_values(0).unique()
    final_z_scores = {}

    for symbol in symbols:
        try:
            close_prices = df[(symbol, 'close')].ffill()
            total_volume = df[(symbol, 'volume')].ffill()
        except KeyError:
            continue
        

        min_required_data = max(median_lookback, std_lookback, vol_lookback, volume_z_lookback)
        if len(close_prices.dropna()) < min_required_data or len(total_volume.dropna()) < min_required_data:
            continue

        # 1. Price-based mean-reversion core
        median_price = close_prices.rolling(window=median_lookback).median()
        std_price = close_prices.rolling(window=std_lookback).std().replace(0, np.nan)
        z_price = (close_prices - median_price) / std_price

        # 2. Volume gate
        mean_volume = total_volume.rolling(window=volume_z_lookback).mean()
        std_volume = total_volume.rolling(window=volume_z_lookback).std().replace(0, np.nan)
        z_volume = (total_volume - mean_volume) / std_volume
        
        gated_z_price = z_price.where(z_volume.abs() < volume_z_threshold, 0)
        
        if pd.notna(gated_z_price.iloc[-1]):
            final_z_scores[symbol] = gated_z_price.iloc[-1]
            
    if not final_z_scores:
        return {}
        
    # --- Cross-sectional ranking and selection ---
    z_series = pd.Series(final_z_scores).dropna()
    if z_series.empty:
        return {}

    ranks = z_series.rank(pct=True)
    raw_weights = 0.5 - ranks

    long_candidates = raw_weights[ranks <= long_percentile]
    short_candidates = raw_weights[ranks >= (1.0 - short_percentile)]
    selected_raw_weights = pd.concat([long_candidates, short_candidates])
    
    if selected_raw_weights.empty:
        return {}

    # --- Volatility-targeted sizing & Risk Caps ---
    final_weights = {}
    for symbol, raw_weight in selected_raw_weights.items():
        close_prices = df[(symbol, 'close')].ffill()
        daily_returns = close_prices.pct_change(1)
        
        vol_30 = daily_returns.rolling(window=vol_lookback).std().iloc[-1]
        vol_30_safe = max(vol_30, 1e-6) if pd.notna(vol_30) else 1e-6
        
        vol_scale = vol_target_scaler / vol_30_safe
        scaled_weight = raw_weight * vol_scale
        
        final_weights[symbol] = np.clip(scaled_weight, -weight_clip, weight_clip)

    if not final_weights:
        return {}

    # --- Drawdown Guard (Stateless Proxy) ---
    recent_returns = df.xs('close', axis=1, level=1).pct_change().iloc[-(dd_lookback):]
    
    if not recent_returns.empty:
        simulated_pnl = pd.Series(0.0, index=recent_returns.index)
        for symbol, weight in final_weights.items():
            if symbol in recent_returns.columns:
                simulated_pnl += recent_returns[symbol].fillna(0) * weight
        
        equity_curve = (1 + simulated_pnl).cumprod()
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max
        
        if not drawdown.empty and drawdown.min() < -dd_threshold:
            for symbol in final_weights:
                final_weights[symbol] /= 2.0

    # --- Final Normalization ---
    total_abs_weight = sum(abs(w) for w in final_weights.values())
    if total_abs_weight > 1.0:
        for symbol, weight in final_weights.items():
            final_weights[symbol] = weight / total_abs_weight
            
    return final_weights