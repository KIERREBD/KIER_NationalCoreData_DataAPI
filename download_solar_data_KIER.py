"""
한국에너지기술연구원 태양에너지 관련 API 서비스
대전시 2021~2022년 데이터 다운로드 스크립트

지원하는 API:
1. 태양에너지 시공간 자원정보 서비스 (일사량 데이터)
2. 태양광 발전량 예측정보 서비스 (발전량 예측 데이터)
"""

import requests
import os
import time
import urllib3
import calendar
import pandas as pd

# API 엔드포인트 (https:// 프로토콜 포함)
BASE_URL_SOLAR_ENERGY = "https://apis.data.go.kr/B551184/SolarGhiService"  # 일사량 데이터
BASE_URL_SOLAR_POWER = "https://apis.data.go.kr/B551184/SolarPvService"    # 발전량 예측 데이터
BASE_URL_SOLAR_ENERGY_realtime = "https://apis.data.go.kr/B551184/SrQtyService"   # 실시간 일사량 데이터 
BASE_URL_ULVRY = "https://apis.data.go.kr/B551184/UlvryService"   # 실시간 홍반자외선 데이터 


# 데이터 저장 디렉토리 (CSV 파일 저장)
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# API 타입 정의
API_TYPE_SOLAR_ENERGY = "solar_energy"  # 태양에너지 시공간 자원정보 서비스
API_TYPE_SOLAR_POWER = "solar_power"    # 태양광 발전량 예측정보 서비스
API_TYPE_SOLAR_ENERGY_realtime = "SOLAR_ENERGY_realtime_predc"          # 위경도 실시간 일사량 데이터 제공 서비스
API_TYPE_ULVRY = "ulvry_predc"          # 위경도 실시간 홍반자외선 데이터 제공 서비스

def download_solar_data(year, month, day, lat, lon, api_type=API_TYPE_SOLAR_ENERGY):
    """
    특정 연도, 월, 좌표의 태양에너지 데이터를 다운로드합니다.
    
    Args:
        year: 연도 (예: 2021)
        month: 월 (1-12)
        day: 일 (1-31)
        lat: 위도
        lon: 경도
        api_type: API 타입 ("solar_energy" 또는 "solar_power")
    
    Returns:
        dict: API 응답 데이터
    """
    # API 타입에 따라 엔드포인트 선택
    if api_type == API_TYPE_SOLAR_ENERGY:
        url = f"{BASE_URL_SOLAR_ENERGY}/getSolarGhiHrInfo"
    elif api_type == API_TYPE_SOLAR_POWER:
        url = f"{BASE_URL_SOLAR_POWER}/getSolarPvHrInfo" 
    elif api_type == API_TYPE_SOLAR_ENERGY_realtime:
        url = f"{BASE_URL_SOLAR_ENERGY_realtime}/getSrQtyPredcInfo" 
    elif api_type == API_TYPE_ULVRY:
        url = f"{BASE_URL_ULVRY}/getUlvryPredcInfo" 
    else:
        return None
    
    params = {
        "serviceKey": SERVICE_KEY,
        "date" : f"{year}{month:02d}{day:02d}",
        "lat": lat,
        "lon": lon,
        "pageNo": 1,
        "numOfRows": 24,
        "type": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30, verify=True)
        response.raise_for_status()
        data = response.json()
        print(data)
        return data
    except Exception as e:
        return None


def parse_api_response(data):
    """API 응답 데이터를 평탄화하여 리스트로 변환"""
    rows = []
    try:
        if 'response' in data and 'body' in data['response']:
            items = data['response']['body'].get('items', {}).get('item', [])
            if not isinstance(items, list):
                items = [items]
            
            for item in items:
                if isinstance(item, dict):
                    rows.append(item)
    except Exception:
        pass
    return rows

def download_target_annual_data(api_type=API_TYPE_SOLAR_ENERGY, years=[2021, 2022], lat=None, lon=None):
    """
    대상지의 지정된 연도 전체 데이터를 다운로드하고 CSV로 저장합니다.
    
    Args:
        api_type: API 타입 ("solar_energy" 또는 "solar_power")
        years: 다운로드할 연도 리스트 (기본값: [2021, 2022])
        lat: 위도
        lon: 경도
    """
    if lat is None:
        lat = TARGET_LAT
    if lon is None:
        lon = TARGET_LON
    
    prefix = "solar_energy" 
    if api_type is not None : 
        prefix = api_type
    else : 
        prefix = "solar_power"
        
    all_rows = []
    
    # 지정된 연도 데이터 다운로드
    for year in years:
        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            
            for day in range(1, last_day + 1):
                print(f"{year}-{month:02d}-{day:02d} 데이터 다운로드 중...", end=" ")
                data = download_solar_data(year, month, day, lat, lon, api_type)
                
                if data:
                    rows = parse_api_response(data)
                    row_count = len(rows)
                    if row_count > 0:
                        for row in rows:
                            row['year'] = year
                            row['month'] = month
                            row['day'] = day
                            all_rows.append(row)
                        print(f"완료 ({row_count}행)")
                    else:
                        print("실패 (행 0개)")
                else:
                    print("실패")
                            
            # 월별 CSV 파일 저장
            month_rows = [r for r in all_rows if r.get('year') == year and r.get('month') == month]
            if month_rows:
                filename = f"{OUTPUT_DIR}/{prefix}_{year}_{month:02d}.csv"
                df = pd.DataFrame(month_rows)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"{year}-{month:02d} 저장 완료 ({len(month_rows)}행)")
    
    # 전체 데이터를 하나의 CSV 파일로도 저장
    if all_rows:
        year_range = f"{years[0]}_{years[-1]}"
        summary_filename = f"{OUTPUT_DIR}/{prefix}_{year_range}_summary.csv"
        df = pd.DataFrame(all_rows)
        df.to_csv(summary_filename, index=False, encoding='utf-8-sig')
        print(f"전체 데이터 저장 완료: {summary_filename} ({len(all_rows)}행)")
    
    return all_rows

def download_target_daily_data(year, month, day, api_type=API_TYPE_SOLAR_ENERGY, lat=None, lon=None):
    """
    특정 날짜의 데이터를 다운로드하고 CSV로 저장합니다.
    
    Args:
        year: 연도 (예: 2026)
        month: 월 (1-12)
        day: 일 (1-31)
        api_type: API 타입
        lat: 위도
        lon: 경도
    
    Returns:
        list: 다운로드된 데이터 행 리스트
    """
    if lat is None:
        lat = TARGET_LAT
    if lon is None:
        lon = TARGET_LON
    
    prefix = "solar_energy" 
    if api_type is not None : 
        prefix = api_type
    else : 
        prefix = "solar_power"
    
    print(f"{year}-{month:02d}-{day:02d} 데이터 다운로드 중...", end=" ")
    data = download_solar_data(year, month, day, lat, lon, api_type)
    
    rows = []
    if data:
        rows = parse_api_response(data)
        row_count = len(rows)
        if row_count > 0:
            for row in rows:
                row['year'] = year
                row['month'] = month
                row['day'] = day
            filename = f"{OUTPUT_DIR}/{prefix}_{year}_{month:02d}_{day:02d}.csv"
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"완료 ({row_count}행) - 저장: {filename}")
        else:
            print("실패 (행 0개)")
    else:
        print("실패")
    
    return rows


# 사용 예시:

# 공공데이터포털에서 발급받은 서비스 키를 입력하세요 (Decoding 일반 인증키)
SERVICE_KEY = "YOUR_SERVICE_KEY_HERE"

# 대상지 좌표 (위도, 경도) - 예시는 대전시
TARGET_LAT = 36.349
TARGET_LON = 127.386

download_target_annual_data(API_TYPE_SOLAR_ENERGY, [2021, 2022], lat=TARGET_LAT, lon=TARGET_LON)
download_target_annual_data(API_TYPE_SOLAR_POWER, [2021, 2022], lat=TARGET_LAT, lon=TARGET_LON)
# 실시간 일사량, 홍반자외선 추가 (1월 20일 하루만 다운로드)
download_target_daily_data(2026, 1, 20, API_TYPE_SOLAR_ENERGY_realtime, lat=TARGET_LAT, lon=TARGET_LON)
download_target_daily_data(2026, 1, 20, API_TYPE_ULVRY, lat=TARGET_LAT, lon=TARGET_LON)

