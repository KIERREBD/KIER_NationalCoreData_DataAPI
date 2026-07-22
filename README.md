# 대전시 태양에너지 관련 데이터 다운로드 및 예측 모델

한국에너지기술연구원(KIER)과 외부 기관에서 제공하는 태양에너지 관련 데이터를 다운로드하고, 머신러닝 모델을 활용하여 태양광 발전량을 예측하는 Python 스크립트 모음입니다.

## 📋 지원하는 데이터 소스

### KIER 자체 자료
1. **태양에너지 시공간 자원정보 서비스** (일사량 데이터)
   - 제공 기관: 한국에너지기술연구원(KIER)
   - [API 페이지](https://www.data.go.kr/data/15125092/openapi.do#/)
   - 데이터 기간: 2020년 1월 ~ 2022년 12월
   - 스크립트: `download_solar_data_KIER.py`

2. **태양광 발전량 예측정보 서비스** (발전량 예측 데이터)
   - 제공 기관: 한국에너지기술연구원(KIER)
   - [API 페이지](https://www.data.go.kr/data/15125094/openapi.do)
   - 데이터 기간: 2020년 1월 ~ 2021년 12월
   - 스크립트: `download_solar_data_KIER.py`
   - 참고 문서: `태양광 발전량 예측정보 서비스 소개 (한국에너지기술연구원).pdf`

3. **위경도 실시간 일사량 데이터 제공 서비스** (실시간 일사량 데이터)
   - 제공 기관: 한국에너지기술연구원(KIER)
   - 스크립트: `download_solar_data_KIER.py`

4. **위경도 실시간 홍반자외선 데이터 제공 서비스** (실시간 홍반자외선 데이터)
   - 제공 기관: 한국에너지기술연구원(KIER)
   - 스크립트: `download_solar_data_KIER.py`

5. **천리안2 위성영상 격자 좌표 데이터** (`Ird_LatLon.csv`)
   - 제공 기관: 한국에너지기술연구원(KIER)
   - 설명: 천리안2 위성영상의 격자 중 육상에 대한 부분만 추출한 위경도 위치 데이터
   - 파일 형식: CSV (Lat, Lon 컬럼)
   - 데이터 개수: 약 38만 개의 위경도 좌표
   - 용도: API 호출 시 사용할 수 있는 육상 격자 좌표 목록

### 외부 기관 자료

3. **기상청 ASOS 지상관측 자료**
   - 제공 기관: 기상청(KMA)
   - [API 페이지](https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42&openApiNo=241)
   - 스크립트: `download_asos_data_KMA.py`

4. **ECMWF ERA5 재분석 자료**
   - 제공 기관: ECMWF (European Centre for Medium-Range Weather Forecasts)
   - [CDS 페이지](https://cds.climate.copernicus.eu/)
   - ERA5-Land: 지상 재분석 데이터
   - ERA5: 대기 재분석 데이터
   - 스크립트: `download_era5_data_ECMWF.py`

## 🤖 예측 모델

### 1. 발전량 추정 모델 (`example_estimation_solar_power.py`)
- **목적**: 일사량 및 기상 데이터를 활용한 발전량 추정
- **사용 데이터**: 
  - solar_energy (일사량)
  - ASOS (기상청 지상관측)
  - solar_power (발전량, target)
- **모델**: LightGBM, XGBoost
- **학습/테스트**: 2021년 훈련, 2022년 테스트

### 2. 시계열 예측 모델 (`example_forecast_solar_power.py`)
- **목적**: 과거 발전량 데이터만을 활용한 시계열 예측
- **사용 데이터**: solar_power (단변량 시계열)
- **모델**: ARIMA, LSTM, Transformer
- **학습/테스트**: 2021년 훈련, 2022년 테스트

## 🚀 시작하기

### 설치

```bash
pip install -r requirements.txt
```

### API 키 발급

#### KIER API (공공데이터포털)
1. [공공데이터포털](https://www.data.go.kr)에 회원가입 및 로그인
2. 다음 API 서비스에 활용신청:
   - [태양에너지 시공간 자원정보 서비스](https://www.data.go.kr/data/15125092/openapi.do#/)
   - [태양광 발전량 예측정보 서비스](https://www.data.go.kr/data/15125094/openapi.do)
   - 위경도 실시간 일사량 데이터 제공 서비스
   - 위경도 실시간 홍반자외선 데이터 제공 서비스
3. 발급받은 서비스 키를 `download_solar_data_KIER.py` 파일의 `SERVICE_KEY`에 입력

#### 기상청 API
1. [기상청 API Hub](https://apihub.kma.go.kr/)에서 계정 생성
2. ASOS API: [API 상세 페이지](https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42&openApiNo=241)
3. 발급받은 키를 각 스크립트의 `AUTH_KEY` 또는 `SERVICE_KEY`에 입력

#### ECMWF CDS API
1. [CDS 웹사이트](https://cds.climate.copernicus.eu/)에서 계정 생성
2. API 키를 `~/.cdsapirc` 파일에 설정 (자세한 내용은 `download_era5_data_ECMWF.py` 참고)

### 설정

각 스크립트 파일 상단의 설정 영역에서 API 키와 좌표를 설정하세요:

```python
# download_solar_data_KIER.py
SERVICE_KEY = "YOUR_SERVICE_KEY_HERE"
TARGET_LAT = 36.3504
TARGET_LON = 127.38453

# download_asos_data_KMA.py
SERVICE_KEY = "YOUR_SERVICE_KEY_HERE"
ASOS_STN_ID = 133  # 대전 지점


## 📖 사용 방법

주피터 노트북이나 Python 인터프리터에서 함수를 직접 호출하여 사용합니다:

### 데이터 다운로드

```python
# KIER 태양에너지 데이터 다운로드
from download_solar_data_KIER import (
    download_target_annual_data, 
    download_target_daily_data,
    API_TYPE_SOLAR_ENERGY, 
    API_TYPE_SOLAR_POWER,
    API_TYPE_SOLAR_ENERGY_realtime,
    API_TYPE_ULVRY
)

# 연도 전체 데이터 다운로드 (2021~2022년)
download_target_annual_data(API_TYPE_SOLAR_ENERGY, [2021, 2022], lat=36.349, lon=127.386)
download_target_annual_data(API_TYPE_SOLAR_POWER, [2021, 2022], lat=36.349, lon=127.386)

# 특정 날짜 데이터 다운로드 (실시간 일사량, 홍반자외선)
download_target_daily_data(2026, 1, 20, API_TYPE_SOLAR_ENERGY_realtime, lat=36.349, lon=127.386)
download_target_daily_data(2026, 1, 20, API_TYPE_ULVRY, lat=36.349, lon=127.386)

# 기상청 ASOS 데이터 다운로드
from download_asos_data_KMA import download_asos_data_by_station

download_asos_data_by_station(stn_id=133, start_date='2021-01-01', end_date='2022-12-31')

# ECMWF ERA5 데이터 다운로드
from download_era5_data_ECMWF import download_era5_data

download_era5_data(2021, 1, 1, area=[36.5, 127.3, 36.2, 127.5])
```

### 예측 모델 실행

```python
# 발전량 추정 모델 실행
# example_estimation_solar_power.py 파일을 실행

# 시계열 예측 모델 실행
# example_forecast_solar_power.py 파일을 실행
```

## 📁 출력 파일

`data/` 디렉토리에 CSV 파일로 저장됩니다:

### KIER 데이터
- 연도 전체 데이터 (annual_data 함수):
  - 월별 파일: `solar_energy_2021_01.csv`, `solar_power_2021_01.csv`, ...
  - 전체 요약 파일: `solar_energy_2021_2022_summary.csv`
- 일별 데이터 (daily_data 함수):
  - 일별 파일: `SOLAR_ENERGY_realtime_predc_2026_01_20.csv`, `ulvry_predc_2026_01_20.csv`, ...

### 기상청 데이터
- ASOS: `ASOS_{지점번호}_{연도}_{월}.csv`

### ECMWF 데이터
- ERA5: `era5_land_YYYYMMDD.nc` (NetCDF 형식)

## 📐 응답 칼럼 및 단위

다운로드된 CSV의 주요 칼럼과 단위입니다.

### 일사량 (`solar_energy_*.csv`)

| 칼럼 | 의미 | 단위 |
|---|---|---|
| `Date` / `time` | 날짜(YYYY-MM-DD) / 시각(HH:MM, KST) | — |
| `lat` / `lon` | 위도 / 경도 (WGS84) | degree(°) |
| `ghi` | 수평면 전일사량 (Global Horizontal Irradiance) | **W/m²** (시간 평균) |
| `cghi` | 청천(clear-sky) 수평면 전일사량 (구름 없는 이론 최대) | **W/m²** |

### 발전량 (`solar_power_*.csv`)

| 칼럼 | 의미 | 단위 |
|---|---|---|
| `Date` / `time` | 날짜 / 시각(KST) | — |
| `lat` / `lon` | 위도 / 경도 | degree(°) |
| `pvAmt` | 시간당 예측 발전량 | **MWh (설비용량 1MWp 기준 정규화값, MWh/MWp)** |

> **`pvAmt`** 는 API 입력에 설비용량이 없고 위경도만 받으므로, 특정 발전소의 절대 발전량이 아니라
> **1MWp 설비 기준으로 정규화된 시간당 발전량(MWh/MWp)**입니다. 실제 설비용량 `P[MW]` 를 곱해 환산하세요:
> `발전량[MWh] = pvAmt × P[MW]`.

## 📊 프로젝트 구조 및 파일 목록

크기·라인 수는 2026-07-21 기준.

| 파일 | 라인 | 크기 | 설명 |
|---|--:|--:|---|
| `download_solar_data_KIER.py` | 226 | 8K | KIER 4개 API 다운로드 (일사량·발전량·실시간 일사량·홍반자외선) |
| `download_asos_data_KMA.py` | 163 | 8K | 기상청 ASOS 지상관측 다운로드 |
| `download_era5_data_ECMWF.py` | 128 | 8K | ECMWF ERA5 / ERA5-Land 다운로드 |
| `example_estimation_solar_power.py` | 486 | 16K | 발전량 추정 모델 (LightGBM, XGBoost) |
| `example_forecast_solar_power.py` | 360 | 16K | 시계열 예측 모델 (ARIMA, LSTM, Transformer) |
| `Ird_LatLon.csv` | 383,691 | 14M | 천리안2 위성영상 육상 격자 위경도 (약 38만 점) |
| `requirements.txt` | 10 | 159B | Python 패키지 의존성 |
| `태양광 발전량 예측정보 서비스 소개 (한국에너지기술연구원).pdf` | — | 2.8M | KIER 서비스 소개 문서 |
| `LICENSE` | — | 12K | 라이선스 |
| `README.md` | — | — | 프로젝트 설명서 |

> 📌 다운로드 결과 CSV/NetCDF 는 스크립트 실행 시 `data/` 에 생성됩니다 (저장소에는 포함하지 않음).

## ⚠️ 주의사항

- API 키는 절대 공개하지 마세요
- API 호출 제한:
  - 공공데이터포털: 개발계정 일일 10,000건
  - 기상청 API: 계정별 제한 확인 필요
  - ECMWF CDS: 계정별 제한 확인 필요
- 스크립트에 딜레이를 포함하여 호출 제한을 준수합니다
- 대용량 데이터 다운로드 시 시간이 소요될 수 있습니다

## 🔗 참고 링크

### KIER 자료
- [공공데이터포털 - 태양에너지 시공간 자원정보 서비스](https://www.data.go.kr/data/15125092/openapi.do#/)
- [공공데이터포털 - 태양광 발전량 예측정보 서비스](https://www.data.go.kr/data/15125094/openapi.do)
- [한국에너지기술연구원](https://www.kier.re.kr/)

### 외부 기관 자료
- [기상청 API Hub](https://apihub.kma.go.kr/)
- [기상청 ASOS API 상세](https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42&openApiNo=241)
- [ECMWF CDS](https://cds.climate.copernicus.eu/)
