# strategy_config.py

strategy_config = {
    # 1. Price-based mean-reversion core
    "median_lookback": 60,       # 롤링 중간값 계산 기간
    "std_lookback": 60,          # 롤링 표준편차 계산 기간

    # 2. Volume Gate (거래량 필터)
    "volume_z_lookback": 20,       # 총 거래량 z-score 계산 기간
    "volume_z_threshold": 1.5,     # z-score 필터링 임계값

    # 3. Cross-sectional ranking and selection (교차 순위 선정)
    "long_percentile": 0.10,     # 롱 포지션 진입을 위한 하위 순위 백분율
    "short_percentile": 0.10,    # 숏 포지션 진입을 위한 상위 순위 백분율

    # 4. Volatility-targeted sizing (변동성 기반 비중 조절)
    "vol_lookback": 30,          # 수익률 변동성 계산 기간
    "vol_target_scaler": 0.0005, # 목표 변동성에 맞추기 위한 스케일러

    # 5. Risk caps and turnover control (리스크 관리)
    "weight_clip": 0.005,        # 개별 자산의 최대 비중 (0.5%)

    # 5b. Draw-down guard (손실 제한)
    "dd_lookback": 5,            # 손실률 계산 기간
    "dd_threshold": 0.02         # 손실 제한 발동 임계값 (2%)
}