"""
태양광 발전량 예측 모델 스크립트

사용 데이터:
- solar_energy: 일사량 데이터 (feature)
- ASOS: 기상청 지상관측 데이터 (feature)
- solar_power: 태양광 발전량 데이터 (target)

모델:
- LightGBM
- XGBoost

학습/테스트 분할:
- 훈련: 2021년 데이터
- 테스트: 2022년 데이터
"""

import pandas as pd
import numpy as np
import os
import glob
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import lightgbm as lgb
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# 데이터 저장 디렉토리
DATA_DIR = "data"

# ASOS 지점번호 (대전: 133)
ASOS_STN_ID = 133


def resample_hourly(df, datetime_col='datetime', method='mean', start_date=None, end_date=None):
    """
    데이터프레임을 1시간 간격으로 리샘플링 (전체 기간 포함)
    
    Args:
        df: 데이터프레임
        datetime_col: datetime 컬럼명
        method: 리샘플링 방법 ('mean', 'ffill', 'bfill', 'interpolate')
        start_date: 시작 날짜 (None이면 데이터의 최소값 사용)
        end_date: 종료 날짜 (None이면 데이터의 최대값 사용)
    
    Returns:
        resampled_df: 리샘플링된 데이터프레임
    """
    if df.empty:
        return df
    
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.set_index(datetime_col).sort_index()
    
    # 전체 기간 설정
    if start_date is None:
        start_date = df.index.min()
    else:
        start_date = pd.to_datetime(start_date)
    
    if end_date is None:
        end_date = df.index.max()
    else:
        end_date = pd.to_datetime(end_date)
    
    # 전체 기간의 1시간 간격 인덱스 생성
    full_range = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # 인덱스를 전체 범위로 재인덱싱
    df_reindexed = df.reindex(full_range)
    
    # 1시간 간격으로 리샘플링 (이미 1H 간격이므로 주로 결측치 처리)
    if method == 'mean':
        resampled = df_reindexed.resample('1H').mean()
    elif method == 'ffill':
        resampled = df_reindexed.resample('1H').ffill()
    elif method == 'bfill':
        resampled = df_reindexed.resample('1H').bfill()
    elif method == 'interpolate':
        resampled = df_reindexed.resample('1H').interpolate(method='linear')
    else:
        resampled = df_reindexed.resample('1H').mean()
    
    # 인덱스를 컬럼으로 변환
    resampled = resampled.reset_index()
    resampled.rename(columns={'index': 'datetime'}, inplace=True)
    
    return resampled


def load_solar_energy_data(year):
    """solar_energy 데이터 로드 및 1시간 간격으로 리샘플링"""
    files = glob.glob(f"{DATA_DIR}/solar_energy_{year}_*.csv")
    dfs = []
    for file in files:
        df = pd.read_csv(file, encoding='utf-8-sig')
        dfs.append(df)
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        # datetime 생성
        combined_df['datetime'] = pd.to_datetime(combined_df['Date'] + ' ' + combined_df['time'])
        # 전체 연도의 시작과 끝 설정
        start_date = f"{year}-01-01 00:00:00"
        end_date = f"{year}-12-31 23:00:00"
        # 1시간 간격으로 리샘플링 (전체 기간 포함)
        resampled_df = resample_hourly(combined_df, datetime_col='datetime', method='mean', 
                                       start_date=start_date, end_date=end_date)
        return resampled_df
    return pd.DataFrame()


def load_solar_power_data(year):
    """solar_power 데이터 로드 및 1시간 간격으로 리샘플링"""
    files = glob.glob(f"{DATA_DIR}/solar_power_{year}_*.csv")
    dfs = []
    for file in files:
        df = pd.read_csv(file, encoding='utf-8-sig')
        dfs.append(df)
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        # datetime 생성
        combined_df['datetime'] = pd.to_datetime(combined_df['Date'] + ' ' + combined_df['time'])
        # 전체 연도의 시작과 끝 설정
        start_date = f"{year}-01-01 00:00:00"
        end_date = f"{year}-12-31 23:00:00"
        # 1시간 간격으로 리샘플링 (전체 기간 포함)
        resampled_df = resample_hourly(combined_df, datetime_col='datetime', method='mean',
                                       start_date=start_date, end_date=end_date)
        return resampled_df
    return pd.DataFrame()


def load_asos_data(year, stn_id):
    """ASOS 데이터 로드"""
    files = glob.glob(f"{DATA_DIR}/ASOS_{stn_id}_{year}_*.csv")
    dfs = []
    for file in files:
        df = pd.read_csv(file, encoding='utf-8-sig')
        dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()


def prepare_data(solar_energy_df, solar_power_df, asos_df):
    """
    solar_energy, solar_power, ASOS 데이터를 모두 병합하여 준비
    
    Args:
        solar_energy_df: solar_energy 데이터프레임 (이미 리샘플링됨)
        solar_power_df: solar_power 데이터프레임 (이미 리샘플링됨)
        asos_df: ASOS 데이터프레임
    
    Returns:
        merged_df: 병합된 데이터프레임 (pvAmt 컬럼 포함)
    """
    # solar_energy 데이터 전처리
    if solar_energy_df.empty:
        return pd.DataFrame()
    
    solar_energy_df = solar_energy_df.copy()
    # datetime이 이미 있으므로 확인
    if 'datetime' not in solar_energy_df.columns:
        if 'Date' in solar_energy_df.columns and 'time' in solar_energy_df.columns:
            solar_energy_df['datetime'] = pd.to_datetime(solar_energy_df['Date'] + ' ' + solar_energy_df['time'])
        else:
            return pd.DataFrame()
    
    solar_energy_df['datetime'] = pd.to_datetime(solar_energy_df['datetime'])
    solar_energy_df['hour'] = solar_energy_df['datetime'].dt.hour
    solar_energy_df['day_of_year'] = solar_energy_df['datetime'].dt.dayofyear
    # year, month, day 컬럼이 없으면 생성
    if 'year' not in solar_energy_df.columns:
        solar_energy_df['year'] = solar_energy_df['datetime'].dt.year
    if 'month' not in solar_energy_df.columns:
        solar_energy_df['month'] = solar_energy_df['datetime'].dt.month
    if 'day' not in solar_energy_df.columns:
        solar_energy_df['day'] = solar_energy_df['datetime'].dt.day
    
    # solar_power 데이터 전처리
    if solar_power_df.empty:
        return pd.DataFrame()
    
    solar_power_df = solar_power_df.copy()
    # datetime이 이미 있으므로 확인
    if 'datetime' not in solar_power_df.columns:
        if 'Date' in solar_power_df.columns and 'time' in solar_power_df.columns:
            solar_power_df['datetime'] = pd.to_datetime(solar_power_df['Date'] + ' ' + solar_power_df['time'])
        else:
            return pd.DataFrame()
    
    solar_power_df['datetime'] = pd.to_datetime(solar_power_df['datetime'])
    solar_power_df['hour'] = solar_power_df['datetime'].dt.hour
    solar_power_df['day_of_year'] = solar_power_df['datetime'].dt.dayofyear
    # year, month, day 컬럼이 없으면 생성
    if 'year' not in solar_power_df.columns:
        solar_power_df['year'] = solar_power_df['datetime'].dt.year
    if 'month' not in solar_power_df.columns:
        solar_power_df['month'] = solar_power_df['datetime'].dt.month
    if 'day' not in solar_power_df.columns:
        solar_power_df['day'] = solar_power_df['datetime'].dt.day
    
    # ASOS 데이터 전처리
    if asos_df.empty:
        return pd.DataFrame()
    
    asos_df = asos_df.copy()
    asos_df['datetime'] = pd.to_datetime(asos_df['tm'])
    asos_df['hour'] = asos_df['datetime'].dt.hour
    asos_df['day_of_year'] = asos_df['datetime'].dt.dayofyear
    
    # solar_energy와 ASOS 병합
    merged_df = pd.merge(
        solar_energy_df[['datetime', 'year', 'month', 'day', 'hour', 'day_of_year', 
                         'lat', 'lon', 'ghi', 'cghi']],
        asos_df[['datetime', 'hour', 'day_of_year', 'ta', 'rn', 'ws', 'wd', 'hm', 
                 'pv', 'td', 'pa', 'ps', 'ss', 'icsr']],
        on=['datetime', 'hour', 'day_of_year'],
        how='inner'
    )
    
    # solar_power와 병합 (pvAmt 포함)
    merged_df = pd.merge(
        merged_df,
        solar_power_df[['datetime', 'pvAmt']],
        on='datetime',
        how='inner'
    )
    
    return merged_df


def prepare_model_data(year, stn_id):
    """특정 연도의 모델 학습/예측용 데이터 준비"""
    print(f"\n{year}년 데이터 로딩 중...")
    
    # 데이터 로드
    solar_energy_df = load_solar_energy_data(year)
    solar_power_df = load_solar_power_data(year)
    asos_df = load_asos_data(year, stn_id)
    
    print(f"  solar_energy: {len(solar_energy_df)}행")
    print(f"  solar_power: {len(solar_power_df)}행")
    print(f"  ASOS: {len(asos_df)}행")
    
    if solar_energy_df.empty or solar_power_df.empty or asos_df.empty:
        print(f"  경고: {year}년 데이터가 비어있습니다.")
        return pd.DataFrame()
    
    # 모든 데이터 병합 (pvAmt 포함)
    merged_df = prepare_data(solar_energy_df, solar_power_df, asos_df)
    
    print(f"  병합 완료: {len(merged_df)}행")
    
    return merged_df


def get_feature_columns():
    """
    사용할 feature 컬럼 리스트 반환
    
    변수 설명:
    - 시간 관련:
      * month: 월 (1-12)
      * day: 일 (1-31)
      * hour: 시간 (0-23)
      * day_of_year: 연중 일수 (1-365/366)
    
    - 위치 정보:
      * lat: 위도
      * lon: 경도
    
    - 일사량 데이터 (solar_energy):
      * ghi: 전천일사량 (Global Horizontal Irradiance)
      * cghi: 누적 전천일사량 (Cumulative Global Horizontal Irradiance)
    
    - 기상청 ASOS 데이터 (출처: https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42&openApiNo=241):
      * ta: 기온(°C) - 종관기상관측 지점의 기온
      * rn: 강수량(mm) - 관측 시간 동안의 강수량
      * ws: 풍속(m/s) - 풍속
      * wd: 풍향(16방위) - 풍향 (0-360도 또는 16방위)
      * hm: 습도(%) - 상대습도
      * pv: 증기압(hPa) - 수증기압
      * td: 이슬점온도(°C) - 이슬점온도
      * pa: 현지기압(hPa) - 관측 지점의 기압
      * ps: 해면기압(hPa) - 해수면으로 환산한 기압
      * ss: 일조(hr) - 일조시간
      * icsr: 일사(MJ/m²) - 일사량
    """
    return [
        'month', 'day', 'hour', 'day_of_year',
        'lat', 'lon',
        'ghi', 'cghi',
        'ta', 'rn', 'ws', 'wd', 'hm', 'pv', 'td', 'pa', 'ps', 'ss', 'icsr'
    ]


def train_and_evaluate_models(train_df, test_df):
    """
    LightGBM과 XGBoost 모델 학습 및 평가
    
    Args:
        train_df: 훈련 데이터
        test_df: 테스트 데이터
    
    Returns:
        dict: 모델 결과 딕셔너리
    """
    # Feature와 target 분리
    feature_cols = get_feature_columns()
    
    # 결측치 처리
    train_df = train_df.dropna(subset=feature_cols + ['pvAmt']).copy()
    test_df = test_df.dropna(subset=feature_cols + ['pvAmt']).copy()
    
    # pop으로 target 분리
    y_train = train_df.pop('pvAmt')
    y_test = test_df.pop('pvAmt')
    
    X_train = train_df[feature_cols]
    X_test = test_df[feature_cols]
    
    print(f"\n훈련 데이터: {len(X_train)}행")
    print(f"테스트 데이터: {len(X_test)}행")
    
    results = {}
    
    # LightGBM 모델
    print("\n" + "="*60)
    print("LightGBM 모델 학습 중...")
    print("="*60)
    
    lgb_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [5, 10, 15, 20],
        'learning_rate': [0.01, 0.05, 0.1],
        'num_leaves': [31, 50, 100],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0],
    }
    
    lgb_model = lgb.LGBMRegressor(random_state=42, verbose=-1)
    lgb_random = RandomizedSearchCV(
        estimator=lgb_model,
        param_distributions=lgb_params,
        n_iter=20,
        cv=5,
        scoring='neg_mean_squared_error',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    lgb_random.fit(X_train, y_train)
    lgb_best = lgb_random.best_estimator_
    
    # 예측
    y_train_pred = lgb_best.predict(X_train)
    y_test_pred = lgb_best.predict(X_test)
    
    # 평가
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    results['lgb'] = {
        'model': lgb_best,
        'best_params': lgb_random.best_params_,
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'y_test_pred': y_test_pred
    }
    
    # print(f"\n최적 파라미터: {lgb_random.best_params_}")
    # print(f"훈련 RMSE: {train_rmse:.4f}")
    # print(f"테스트 RMSE: {test_rmse:.4f}")
    # print(f"훈련 MAE: {train_mae:.4f}")
    # print(f"테스트 MAE: {test_mae:.4f}")
    # print(f"훈련 R²: {train_r2:.4f}")
    # print(f"테스트 R²: {test_r2:.4f}")
    
    # XGBoost 모델
    print("\n" + "="*60)
    print("XGBoost 모델 학습 중...")
    print("="*60)
    
    xgb_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [5, 10, 15, 20],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0],
        'gamma': [0, 0.1, 0.2],
    }
    
    xgb_model = xgb.XGBRegressor(random_state=42, verbosity=0)
    xgb_random = RandomizedSearchCV(
        estimator=xgb_model,
        param_distributions=xgb_params,
        n_iter=20,
        cv=5,
        scoring='neg_mean_squared_error',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    xgb_random.fit(X_train, y_train)
    xgb_best = xgb_random.best_estimator_
    
    # 예측
    y_train_pred = xgb_best.predict(X_train)
    y_test_pred = xgb_best.predict(X_test)
    
    # 평가
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    results['xgb'] = {
        'model': xgb_best,
        'best_params': xgb_random.best_params_,
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'y_test_pred': y_test_pred
    }
    
    # print(f"\n최적 파라미터: {xgb_random.best_params_}")
    # print(f"훈련 RMSE: {train_rmse:.4f}")
    # print(f"테스트 RMSE: {test_rmse:.4f}")
    # print(f"훈련 MAE: {train_mae:.4f}")
    # print(f"테스트 MAE: {test_mae:.4f}")
    # print(f"훈련 R²: {train_r2:.4f}")
    # print(f"테스트 R²: {test_r2:.4f}")
    
    return results


# 사용 예시:

print("="*60)
print("태양광 발전량 예측 모델 학습 및 평가")
print("="*60)

# 데이터 준비
train_df = prepare_model_data(2021, ASOS_STN_ID)
test_df = prepare_model_data(2022, ASOS_STN_ID)

if train_df.empty or test_df.empty:
    print("\n오류: 훈련 또는 테스트 데이터가 비어있습니다.")

# 모델 학습 및 평가
results = train_and_evaluate_models(train_df, test_df)

# 결과 요약
print("\n" + "="*60)
print("결과 요약")
print("="*60)
print("\nLightGBM:")
print(f"  테스트 RMSE: {results['lgb']['test_rmse']:.4f}")
print(f"  테스트 MAE: {results['lgb']['test_mae']:.4f}")
print(f"  테스트 R²: {results['lgb']['test_r2']:.4f}")

print("\nXGBoost:")
print(f"  테스트 RMSE: {results['xgb']['test_rmse']:.4f}")
print(f"  테스트 MAE: {results['xgb']['test_mae']:.4f}")
print(f"  테스트 R²: {results['xgb']['test_r2']:.4f}")



