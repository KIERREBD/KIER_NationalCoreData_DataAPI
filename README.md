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

## 📊 프로젝트 구조

```
public2025_KIERREBD_github/
├── download_solar_data_KIER.py      # KIER 태양에너지 데이터 다운로드
├── download_asos_data_KMA.py        # 기상청 ASOS 데이터 다운로드
├── download_era5_data_ECMWF.py     # ECMWF ERA5 데이터 다운로드
├── example_estimation_solar_power.py    # 발전량 추정 모델 (LightGBM, XGBoost)
├── example_forecast_solar_power.py      # 시계열 예측 모델 (ARIMA, LSTM, Transformer)
├── README.md                        # 프로젝트 설명서
├── requirements.txt                 # Python 패키지 의존성
├── 태양광 발전량 예측정보 서비스 소개 (한국에너지기술연구원).pdf  # KIER 서비스 소개 문서
└── data/                            # 다운로드된 데이터 (자동 생성)
    ├── solar_energy_*.csv
    ├── solar_power_*.csv
    ├── ASOS_*.csv
    └── era5_*.nc

```

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
