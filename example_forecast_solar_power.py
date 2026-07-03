"""
태양광 발전량 시계열 예측 모델 스크립트

사용 데이터:
- solar_power: 태양광 발전량 데이터 (target, 단변량 시계열)

모델:
- ARIMA: 시계열 자기회귀 모델
- LSTM: 장단기 메모리 신경망
- Transformer: 일반 Transformer 모델

학습/테스트 분할:
- 훈련: 2020년 데이터
- 테스트: 2021년 데이터
"""

import pandas as pd
import numpy as np
import os
import glob
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from darts import TimeSeries
from darts.models import ARIMA, RNNModel, TransformerModel
from darts.dataprocessing.transformers import Scaler, MissingValuesFiller
from darts.metrics import mae, rmse, mape

# 데이터 저장 디렉토리
DATA_DIR = "data"


def resample_hourly(df, datetime_col='datetime', method='mean', start_date=None, end_date=None):
    """
    데이터프레임을 1시간 간격으로 리샘플링 (전체 기간 포함)
    """
    if df.empty:
        return df
    
    df = df.copy()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.set_index(datetime_col).sort_index()
    
    if start_date is None:
        start_date = df.index.min()
    else:
        start_date = pd.to_datetime(start_date)
    
    if end_date is None:
        end_date = df.index.max()
    else:
        end_date = pd.to_datetime(end_date)
    
    full_range = pd.date_range(start=start_date, end=end_date, freq='1H')
    df_reindexed = df.reindex(full_range)
    
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
    
    resampled = resampled.reset_index()
    resampled.rename(columns={'index': 'datetime'}, inplace=True)
    
    return resampled


def load_solar_power_data(year):
    """solar_power 데이터 로드 및 1시간 간격으로 리샘플링"""
    files = glob.glob(f"{DATA_DIR}/solar_power_{year}_*.csv")
    dfs = []
    for file in files:
        df = pd.read_csv(file, encoding='utf-8-sig')
        dfs.append(df)
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df['datetime'] = pd.to_datetime(combined_df['Date'] + ' ' + combined_df['time'])
        start_date = f"{year}-01-01 00:00:00"
        end_date = f"{year}-12-31 23:00:00"
        resampled_df = resample_hourly(combined_df, datetime_col='datetime', method='mean',
                                       start_date=start_date, end_date=end_date)
        return resampled_df
    return pd.DataFrame()


def prepare_model_data(year):
    """특정 연도의 모델 학습/예측용 데이터 준비"""
    print(f"\n{year}년 데이터 로딩 중...")
    
    solar_power_df = load_solar_power_data(year)
    
    print(f"  solar_power: {len(solar_power_df)}행")
    
    if solar_power_df.empty:
        print(f"  경고: {year}년 데이터가 비어있습니다.")
        return pd.DataFrame()
    
    # datetime 컬럼이 없으면 생성
    if 'datetime' not in solar_power_df.columns:
        if 'Date' in solar_power_df.columns and 'time' in solar_power_df.columns:
            solar_power_df['datetime'] = pd.to_datetime(solar_power_df['Date'] + ' ' + solar_power_df['time'])
        else:
            print(f"  오류: datetime 컬럼을 생성할 수 없습니다.")
            return pd.DataFrame()
    
    # 필요한 컬럼만 선택
    result_df = solar_power_df[['datetime', 'pvAmt']].copy()
    
    print(f"  데이터 준비 완료: {len(result_df)}행")
    
    return result_df


def train_and_evaluate_forecast_models(train_df, test_df):
    """
    ARIMA, LSTM, Transformer 모델 학습 및 평가 (단변량 시계열)
    
    Args:
        train_df: 훈련 데이터 (datetime, pvAmt 컬럼 포함)
        test_df: 테스트 데이터 (datetime, pvAmt 컬럼 포함)
    
    Returns:
        dict: 모델 결과 딕셔너리
    """
    # 데이터 준비
    train_df = train_df.dropna(subset=['pvAmt']).copy()
    test_df = test_df.dropna(subset=['pvAmt']).copy()
    
    # datetime을 인덱스로 설정
    train_df = train_df.set_index('datetime').sort_index()
    test_df = test_df.set_index('datetime').sort_index()
    
    # Target 시계열 생성 (단변량)
    train_target = TimeSeries.from_dataframe(train_df[['pvAmt']], freq='H')
    test_target = TimeSeries.from_dataframe(test_df[['pvAmt']], freq='H')
    
    # 결측치 처리
    filler = MissingValuesFiller(fill='auto')
    train_target = filler.transform(train_target)
    test_target = filler.transform(test_target)
    
    # 정규화
    target_scaler = Scaler()
    train_target_scaled = target_scaler.fit_transform(train_target)
    test_target_scaled = target_scaler.transform(test_target)
    
    print(f"\n훈련 데이터: {len(train_target_scaled)}행")
    print(f"테스트 데이터: {len(test_target_scaled)}행")
    
    results = {}
    
    # 예측 길이 설정 (24시간)
    forecast_horizon = 24
    
    # ARIMA 모델
    print("\n" + "="*60)
    print("ARIMA 모델 학습 중...")
    print("="*60)
    
    try:
        arima_model = ARIMA(p=24, d=1, q=24, seasonal=True)
        arima_model.fit(train_target_scaled)
        
        # 예측
        arima_forecast = arima_model.predict(len(test_target_scaled))
        arima_forecast = target_scaler.inverse_transform(arima_forecast)
        
        # 평가
        test_target_values = test_target.values().flatten()
        arima_pred_values = arima_forecast.values().flatten()
        
        # 길이 맞추기
        min_len = min(len(test_target_values), len(arima_pred_values))
        test_target_values = test_target_values[:min_len]
        arima_pred_values = arima_pred_values[:min_len]
        
        arima_rmse = np.sqrt(mean_squared_error(test_target_values, arima_pred_values))
        arima_mae = mean_absolute_error(test_target_values, arima_pred_values)
        arima_r2 = r2_score(test_target_values, arima_pred_values)
        
        results['arima'] = {
            'model': arima_model,
            'test_rmse': arima_rmse,
            'test_mae': arima_mae,
            'test_r2': arima_r2,
            'y_test_pred': arima_pred_values
        }
        
        print(f"테스트 RMSE: {arima_rmse:.4f}")
        print(f"테스트 MAE: {arima_mae:.4f}")
        print(f"테스트 R²: {arima_r2:.4f}")
    except Exception as e:
        print(f"ARIMA 모델 오류: {e}")
        results['arima'] = None
    
    # LSTM 모델
    print("\n" + "="*60)
    print("LSTM 모델 학습 중...")
    print("="*60)
    
    try:
        lstm_model = RNNModel(
            model='LSTM',
            input_chunk_length=24,
            output_chunk_length=forecast_horizon,
            n_rnn_layers=2,
            dropout=0.1,
            n_epochs=50,
            random_state=42,
            verbose=False
        )
        
        lstm_model.fit(
            series=train_target_scaled,
            verbose=False
        )
        
        # 예측
        lstm_forecast = lstm_model.predict(
            n=len(test_target_scaled)
        )
        lstm_forecast = target_scaler.inverse_transform(lstm_forecast)
        
        # 평가
        test_target_values = test_target.values().flatten()
        lstm_pred_values = lstm_forecast.values().flatten()
        
        min_len = min(len(test_target_values), len(lstm_pred_values))
        test_target_values = test_target_values[:min_len]
        lstm_pred_values = lstm_pred_values[:min_len]
        
        lstm_rmse = np.sqrt(mean_squared_error(test_target_values, lstm_pred_values))
        lstm_mae = mean_absolute_error(test_target_values, lstm_pred_values)
        lstm_r2 = r2_score(test_target_values, lstm_pred_values)
        
        results['lstm'] = {
            'model': lstm_model,
            'test_rmse': lstm_rmse,
            'test_mae': lstm_mae,
            'test_r2': lstm_r2,
            'y_test_pred': lstm_pred_values
        }
        
        print(f"테스트 RMSE: {lstm_rmse:.4f}")
        print(f"테스트 MAE: {lstm_mae:.4f}")
        print(f"테스트 R²: {lstm_r2:.4f}")
    except Exception as e:
        print(f"LSTM 모델 오류: {e}")
        results['lstm'] = None
    
    # Transformer 모델
    print("\n" + "="*60)
    print("Transformer 모델 학습 중...")
    print("="*60)
    
    try:
        transformer_model = TransformerModel(
            input_chunk_length=24,
            output_chunk_length=forecast_horizon,
            d_model=64,
            nhead=4,
            num_encoder_layers=3,
            num_decoder_layers=3,
            dim_feedforward=256,
            dropout=0.1,
            activation='relu',
            n_epochs=50,
            random_state=42,
            verbose=False
        )
        
        transformer_model.fit(
            series=train_target_scaled,
            verbose=False
        )
        
        # 예측
        transformer_forecast = transformer_model.predict(
            n=len(test_target_scaled)
        )
        transformer_forecast = target_scaler.inverse_transform(transformer_forecast)
        
        # 평가
        test_target_values = test_target.values().flatten()
        transformer_pred_values = transformer_forecast.values().flatten()
        
        min_len = min(len(test_target_values), len(transformer_pred_values))
        test_target_values = test_target_values[:min_len]
        transformer_pred_values = transformer_pred_values[:min_len]
        
        transformer_rmse = np.sqrt(mean_squared_error(test_target_values, transformer_pred_values))
        transformer_mae = mean_absolute_error(test_target_values, transformer_pred_values)
        transformer_r2 = r2_score(test_target_values, transformer_pred_values)
        
        results['transformer'] = {
            'model': transformer_model,
            'test_rmse': transformer_rmse,
            'test_mae': transformer_mae,
            'test_r2': transformer_r2,
            'y_test_pred': transformer_pred_values
        }
        
        print(f"테스트 RMSE: {transformer_rmse:.4f}")
        print(f"테스트 MAE: {transformer_mae:.4f}")
        print(f"테스트 R²: {transformer_r2:.4f}")
    except Exception as e:
        print(f"Transformer 모델 오류: {e}")
        import traceback
        traceback.print_exc()
        results['transformer'] = None
    
    return results


# 사용 예시:

print("="*60)
print("태양광 발전량 시계열 예측 모델 학습 및 평가")
print("="*60)

# 데이터 준비
train_df = prepare_model_data(2020)
test_df = prepare_model_data(2021)

if train_df.empty or test_df.empty:
    print("\n오류: 훈련 또는 테스트 데이터가 비어있습니다.")

# 모델 학습 및 평가
results = train_and_evaluate_forecast_models(train_df, test_df)

# 결과 요약
print("\n" + "="*60)
print("결과 요약")
print("="*60)

if results.get('arima'):
    print("\nARIMA:")
    print(f"  테스트 RMSE: {results['arima']['test_rmse']:.4f}")
    print(f"  테스트 MAE: {results['arima']['test_mae']:.4f}")
    print(f"  테스트 R²: {results['arima']['test_r2']:.4f}")

if results.get('lstm'):
    print("\nLSTM:")
    print(f"  테스트 RMSE: {results['lstm']['test_rmse']:.4f}")
    print(f"  테스트 MAE: {results['lstm']['test_mae']:.4f}")
    print(f"  테스트 R²: {results['lstm']['test_r2']:.4f}")

if results.get('transformer'):
    print("\nTransformer:")
    print(f"  테스트 RMSE: {results['transformer']['test_rmse']:.4f}")
    print(f"  테스트 MAE: {results['transformer']['test_mae']:.4f}")
    print(f"  테스트 R²: {results['transformer']['test_r2']:.4f}")

