"""
ECMWF ERA5 재분석 데이터 다운로드 스크립트

지원하는 데이터셋:
- ERA5-Land: 지상 재분석 데이터
- ERA5: 대기 재분석 데이터 (pressure levels)

참고: CDS API 사용을 위해 https://cds.climate.copernicus.eu/ 에서 계정 생성 및 API 키 설정 필요
"""

import cdsapi
import os
import time
import calendar

# 데이터 저장 디렉토리 (NetCDF 파일 저장)
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CDS API 클라이언트 초기화
# CDS API 키는 ~/.cdsapirc 파일에 설정되어 있어야 합니다
c = cdsapi.Client()


def download_era5_land_data(year, month, day, area=None, variables=None, output_path=None):
    """
    특정 날짜의 ERA5-Land 데이터를 다운로드합니다.
    
    Args:
        year: 연도 (예: 2021)
        month: 월 (1-12)
        day: 일 (1-31)
        area: 영역 [북, 서, 남, 동] (예: [43.33, 123.9, 32.93, 131.6])
        variables: 다운로드할 변수 리스트 (None이면 기본 변수 사용)
        output_path: 저장 경로 (None이면 자동 생성)
    
    Returns:
        str: 저장된 파일 경로 또는 None
    """
    if variables is None:
        variables = [
            '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature',
            '2m_temperature', 'forecast_albedo', 'snow_albedo',
            'surface_net_solar_radiation', 'surface_net_thermal_radiation', 'surface_pressure',
        ]
    
    if area is None:
        area = [43.33, 123.9, 32.93, 131.6]  # 한반도 영역 (기본값)
    
    if output_path is None:
        output_path = f"{OUTPUT_DIR}/era5_land_{year}{month:02d}{day:02d}.nc"
    
    request_params = {
        'variable': variables,
        'year': str(year),
        'month': f'{month:02d}',
        'day': f'{day:02d}',
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
        ],
        'format': 'netcdf',
        'area': area,
    }
    
    try:
        print(f"{year}-{month:02d}-{day:02d} 데이터 다운로드 중...", end=" ")
        c.retrieve('reanalysis-era5-land', request_params, output_path)
        print(f"완료 -> {output_path}")
        return output_path
    except Exception as e:
        print(f"실패: {e}")
        return None


def download_era5_data(years=[2021, 2022], area=None, variables=None):
    """
    지정된 연도의 ERA5-Land 데이터를 다운로드합니다.
    
    Args:
        years: 다운로드할 연도 리스트 (기본값: [2021, 2022])
        area: 영역 [북, 서, 남, 동] (예: [43.33, 123.9, 32.93, 131.6])
        variables: 다운로드할 변수 리스트 (None이면 기본 변수 사용)
    """
    if area is None:
        area = [43.33, 123.9, 32.93, 131.6]  # 한반도 영역 (기본값)
    
    downloaded_files = []
    
    # 지정된 연도 데이터 다운로드
    for year in years:
        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            
            for day in range(1, last_day + 1):
                output_path = f"{OUTPUT_DIR}/era5_land_{year}{month:02d}{day:02d}.nc"
                result = download_era5_land_data(year, month, day, area, variables, output_path)
                
                if result:
                    downloaded_files.append(result)
                
                # API 호출 제한을 고려한 딜레이
                time.sleep(1)
    
    print(f"\n총 {len(downloaded_files)}개 파일 다운로드 완료")
    return downloaded_files


# 사용 예시:

# 영역 설정 [북, 서, 남, 동] - 한반도 영역
AREA = [43.33, 123.9, 32.93, 131.6]

# 다운로드할 변수 설정 (None이면 기본 변수 사용)
# VARIABLES = [
#     '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature',
#     '2m_temperature', 'forecast_albedo', 'snow_albedo',
#     'surface_net_solar_radiation', 'surface_net_thermal_radiation', 'surface_pressure',
# ]

# download_era5_data(years=[2021, 2022], area=AREA)
# download_era5_land_data(2021, 1, 1, area=AREA)




