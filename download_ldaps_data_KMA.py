"""
기상청 LDAPS (Local Data Assimilation and Prediction System) 데이터 다운로드 스크립트

LDAPS는 기상청의 지역 수치예보 모델로, 특정 좌표의 기상 예보 데이터를 제공합니다.
"""

import requests
import os
import time
import urllib3
import pandas as pd
from datetime import date, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 엔드포인트
BASE_URL_LDAPS = "https://apihub.kma.go.kr/api/typ06/url/um_grib_pt_tmfc.php"
BASE_PARAMS = "group=UMKR&nwp=N512"

# 데이터 저장 디렉토리 (CSV 파일 저장)
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# LDAPS 변수 목록 (기본 변수)
DEFAULT_VARS = [
    'TMP', 'RH', 'TDSWS', 'SWDIR', 'NDNLW', 'VLCDC',
    'LCDC', 'MCDC', 'HCDC', 'TCAR', 'TCAM', 'VIS',
    'LHTFL', 'PRMSL', 'TCTH', 'PRES'
]

# 변수 테이블 파일 경로
DATA_BASE_DIR = "data_base"
VARS_TABLE_FILE = f"{DATA_BASE_DIR}/ldaps_api_varn.csv"


def create_default_vars_table(file_path):
    """
    기본 LDAPS 변수 매핑 테이블 파일을 생성합니다.
    
    Args:
        file_path: 생성할 파일 경로
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    default_data = {
        'var_name': ['TMP', 'RH', 'TDSWS', 'SWDIR', 'NDNLW', 'VLCDC',
                     'LCDC', 'MCDC', 'HCDC', 'TCAR', 'TCAM', 'VIS',
                     'LHTFL', 'PRMSL', 'TCTH', 'PRES'],
        'varn': ['TMP', 'RH', 'TDSWS', 'SWDIR', 'NDNLW', 'VLCDC',
                 'LCDC', 'MCDC', 'HCDC', 'TCAR', 'TCAM', 'VIS',
                 'LHTFL', 'PRMSL', 'TCTH', 'PRES']
    }
    
    df = pd.DataFrame(default_data)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"기본 변수 테이블 파일 생성: {file_path}")


def load_ldaps_vars_table(file_path=None):
    """
    LDAPS 변수 매핑 테이블을 로드합니다.
    파일이 없으면 기본값으로 파일을 생성합니다.
    
    Args:
        file_path: CSV 파일 경로 (None이면 기본 경로 사용)
    
    Returns:
        pd.DataFrame: 변수 매핑 테이블
    """
    if file_path is None:
        file_path = VARS_TABLE_FILE
    
    if os.path.exists(file_path):
        try:
            vars_table = pd.read_csv(file_path)
            # var_name과 varn 컬럼이 있는지 확인
            if 'var_name' in vars_table.columns and 'varn' in vars_table.columns:
                return vars_table
            else:
                print(f"경고: {file_path}에 필요한 컬럼(var_name, varn)이 없습니다. 기본 파일을 생성합니다.")
                create_default_vars_table(file_path)
                return pd.read_csv(file_path)
        except Exception as e:
            print(f"경고: {file_path} 로드 실패: {e}. 기본 파일을 생성합니다.")
            create_default_vars_table(file_path)
            return pd.read_csv(file_path)
    else:
        print(f"변수 테이블 파일이 없습니다. 기본 파일을 생성합니다: {file_path}")
        create_default_vars_table(file_path)
        return pd.read_csv(file_path)


# 변수 테이블 로드 (파일이 없으면 생성)
LDAPS_VARS_TABLE = load_ldaps_vars_table()


def download_ldaps_file(file_url):
    """
    LDAPS API에서 데이터를 다운로드합니다.
    
    Args:
        file_url: 다운로드할 URL
    
    Returns:
        list: 파싱된 데이터 행 리스트 또는 None
    """
    session = requests.Session()
    
    retries = Retry(
        total=5,
        backoff_factor=3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        response = session.get(file_url, timeout=30, verify=False)
        response.raise_for_status()
        data = response.text.strip().split('\n')
        rows = [line.split() for line in data]
        return rows
    except requests.exceptions.RequestException as e:
        return None


def download_ldaps_data(init_time, lat, lon, vars_list=None, auth_key=None):
    """
    특정 초기 시간과 좌표의 LDAPS 데이터를 다운로드합니다.
    
    Args:
        init_time: 초기 시간 (YYYYMMDDHH 형식, 예: '2021010118')
        lat: 위도
        lon: 경도
        vars_list: 다운로드할 변수 리스트 (None이면 기본 변수 사용)
        vars_table: 변수명과 varn 매핑 테이블 (pd.DataFrame, None이면 LDAPS_VARS_TABLE 사용)
        auth_key: 인증 키 (None이면 AUTH_KEY 사용)
    
    Returns:
        pd.DataFrame: 다운로드된 데이터프레임
    """
    if vars_list is None:
        vars_list = DEFAULT_VARS
    
    vars_table = LDAPS_VARS_TABLE
    
    if auth_key is None:
        auth_key = AUTH_KEY
    
    # 예보 시간대 (0-48시간, 1시간 간격)
    data_times = pd.date_range(
        start=pd.to_datetime(init_time, format="%Y%m%d%H"),
        periods=49,
        freq="1h"
    )
    
    data = pd.DataFrame()
    data['INITIAL_TIME'] = init_time
    data['FORECAST_TIME'] = data_times.strftime("%Y%m%d%H")
    
    for var in vars_list:
        # vars_table이 있으면 varn 코드 사용, 없으면 변수명 그대로 사용
        varn = vars_table[vars_table['var_name'].str.strip() == var]['varn'].iloc[0]
        
        # TMP 변수는 level=15 필요
        if var == 'TMP':
            url = f'{BASE_URL_LDAPS}?{BASE_PARAMS}&data=U&varn={varn}&level=15&tmfc={init_time}&ef=0,48,1&lon={lon}&lat={lat}&authKey={auth_key}'
        else:
            url = f'{BASE_URL_LDAPS}?{BASE_PARAMS}&data=U&varn={varn}&tmfc={init_time}&ef=0,48,1&lon={lon}&lat={lat}&authKey={auth_key}'
        
        rows_varn = download_ldaps_file(url)
        
        if rows_varn and len(rows_varn) > 0:
            try:
                rows_varn_pd = pd.DataFrame(rows_varn)
                # API 응답 형식: INITIAL_TIME FORECAST_TIME varn (빈 컬럼) 값
                if len(rows_varn_pd.columns) >= 5:
                    rows_varn_pd.columns = ['INITIAL_TIME', 'FORECAST_TIME', 'varn', '', var]
                    rows_varn_pd = rows_varn_pd[['FORECAST_TIME', var]]
                    # 값 컬럼을 숫자로 변환
                    rows_varn_pd[var] = pd.to_numeric(rows_varn_pd[var], errors='coerce')
                    data = data.merge(rows_varn_pd, on='FORECAST_TIME', how='left')
                elif len(rows_varn_pd.columns) == 5:
                    # 컬럼 수가 정확히 5개인 경우
                    rows_varn_pd.columns = ['INITIAL_TIME', 'FORECAST_TIME', 'varn', '', var]
                    rows_varn_pd = rows_varn_pd[['FORECAST_TIME', var]]
                    rows_varn_pd[var] = pd.to_numeric(rows_varn_pd[var], errors='coerce')
                    data = data.merge(rows_varn_pd, on='FORECAST_TIME', how='left')
            except Exception as e:
                print(f"  변수 {var} 파싱 오류: {e}")
                print(f"    응답 행 수: {len(rows_varn)}, 컬럼 수: {len(rows_varn[0]) if rows_varn else 0}")
        
        time.sleep(0.5)  # API 호출 제한 고려
    
    data['INITIAL_TIME'] = init_time
    return data


def download_ldaps_data_by_date_range(start_date, end_date, lat, lon, vars_list=None, auth_key=None):
    """
    지정된 날짜 범위의 LDAPS 데이터를 다운로드합니다.
    
    Args:
        start_date: 시작 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        end_date: 종료 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        lat: 위도
        lon: 경도
        vars_list: 다운로드할 변수 리스트 (None이면 기본 변수 사용)
        auth_key: 인증 키 (None이면 AUTH_KEY 사용)
    
    Returns:
        dict: 날짜별 데이터프레임 딕셔너리
    """
    vars_table = LDAPS_VARS_TABLE
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()
    
    results = {}
    current_date = start_date
    year = current_date.year
    month = current_date.month
    
    while current_date <= end_date:
        init_time = current_date.strftime("%Y%m%d") + '18'  # 18시 초기값
        current_year = init_time[0:4]
        current_month = init_time[4:6]
        
        # 연도나 월이 바뀌면 업데이트
        if current_year != str(year) or current_month != f"{month:02d}":
            year = int(current_year)
            month = int(current_month)
        
        print(f"{init_time} 데이터 다운로드 중...", end=" ")
        
        data = download_ldaps_data(init_time, lat, lon, vars_list, auth_key)
        
        if not data.empty and len(data.columns) > 2:  # INITIAL_TIME, FORECAST_TIME 외에 변수가 있는지 확인
            # 파일명 형식: LDAPS_{위도}_{경도}_{연도}_{월}.csv
            filename = f"{OUTPUT_DIR}/LDAPS_{lat}_{lon}_{year}_{month:02d}.csv"
            
            # 기존 파일이 있으면 병합, 없으면 새로 생성
            if os.path.exists(filename):
                existing_data = pd.read_csv(filename, encoding='utf-8-sig')
                # 같은 INITIAL_TIME이 있으면 스킵
                if init_time not in existing_data['INITIAL_TIME'].values:
                    combined_data = pd.concat([existing_data, data], ignore_index=True)
                    combined_data.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"완료 (추가) -> {filename} ({len(data)}행)")
                else:
                    print(f"스킵 (이미 존재) -> {filename}")
            else:
                data.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"완료 -> {filename} ({len(data)}행)")
            
            results[init_time] = data
        else:
            print("실패 (데이터 없음)")
        
        current_date += timedelta(days=1)
    
    return results


# 사용 예시:

# 기상청 API Hub에서 발급받은 인증 키를 입력하세요
AUTH_KEY = "YOUR_AUTH_KEY_HERE"

# 대상지 좌표 (위도, 경도)
TARGET_LAT = 36.3504
TARGET_LON = 127.38453

# 외부 파일에서 변수 테이블 로드 (선택사항)
# LDAPS_VARS_TABLE = load_ldaps_vars_table('ldaps_api_varn.csv')
# download_ldaps_data_by_date_range('2025-01-01', '2025-01-10', TARGET_LAT, TARGET_LON, vars_list=DEFAULT_VARS, auth_key=AUTH_KEY)


