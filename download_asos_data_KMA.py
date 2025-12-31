"""
기상청 ASOS (지상관측) 자료 다운로드 스크립트
(https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42&openApiNo=241)

지원하는 API:
- 기상청 ASOS 시간별 자료 (AsosHourlyInfoService)
"""

import requests
import os
import time
import calendar
import pandas as pd

# API 엔드포인트
BASE_URL_ASOS = "http://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"

# 데이터 저장 디렉토리 (CSV 파일 저장)
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_asos_data(year, month, stn_id):
    """
    특정 연도, 월, 지점의 ASOS 데이터를 다운로드합니다.
    
    Args:
        year: 연도 (예: 2021)
        month: 월 (1-12)
        stn_id: 지점번호
    
    Returns:
        dict: API 응답 데이터
    """
    url = BASE_URL_ASOS
    
    # 다음 달 시작일 계산
    if month < 12:
        end_year = year
        end_month = month + 1
        end_day = 1
    else:
        end_year = year + 1
        end_month = 1
        end_day = 1
    
    params = {
        'serviceKey': SERVICE_KEY,
        'pageNo': '1',
        'numOfRows': '999',
        'dataType': 'json',
        'dataCd': 'ASOS',
        'dateCd': 'HR',
        'startDt': f'{year}{month:02d}01',
        'startHh': '00',
        'endDt': f'{end_year}{end_month:02d}{end_day:02d}',
        'endHh': '23',
        'stnIds': str(stn_id)
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
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


def download_asos_data_by_station(stn_id, years=[2021, 2022]):
    """
    특정 지점의 지정된 연도 전체 데이터를 다운로드하고 CSV로 저장합니다.
    
    Args:
        stn_id: 지점번호 (기상청 ASOS 지점번호)
        years: 다운로드할 연도 리스트 (기본값: [2021, 2022])
    """
    display_name = f"지점{stn_id}"
    
    all_rows = []
    
    # 지정된 연도 데이터 다운로드
    for year in years:
        for month in range(1, 13):
            print(f"{display_name} {year}-{month:02d} 데이터 다운로드 중...", end=" ")
            data = download_asos_data(year, month, stn_id)
            
            if data:
                rows = parse_api_response(data)
                row_count = len(rows)
                if row_count > 0:
                    for row in rows:
                        row['year'] = year
                        row['month'] = month
                        all_rows.append(row)
                    print(f"완료 ({row_count}행)")
                else:
                    print("실패 (행 0개)")
            else:
                print("실패")
            
            time.sleep(0.5)
            
            # 월별 CSV 파일 저장
            month_rows = [r for r in all_rows if r.get('year') == year and r.get('month') == month]
            if month_rows:
                filename = f"{OUTPUT_DIR}/ASOS_{stn_id}_{year}_{month:02d}.csv"
                df = pd.DataFrame(month_rows)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"{display_name} {year}-{month:02d} 저장 완료 ({len(month_rows)}행)")
    
    # 전체 데이터를 하나의 CSV 파일로도 저장
    if all_rows:
        year_range = f"{years[0]}_{years[-1]}"
        summary_filename = f"{OUTPUT_DIR}/ASOS_{stn_id}_{year_range}_summary.csv"
        df = pd.DataFrame(all_rows)
        df.to_csv(summary_filename, index=False, encoding='utf-8-sig')
        print(f"{display_name} 전체 데이터 저장 완료: {summary_filename} ({len(all_rows)}행)")
    
    return all_rows


def download_asos_data_multiple_stations(stn_ids, years=[2021, 2022]):
    """
    여러 지점의 데이터를 다운로드합니다.
    
    Args:
        stn_ids: 지점번호 리스트
        years: 다운로드할 연도 리스트 (기본값: [2021, 2022])
    """
    for stn_id in stn_ids:
        print(f"\n{'='*60}")
        print(f"지점{stn_id} 데이터 다운로드 시작")
        print(f"{'='*60}")
        download_asos_data_by_station(stn_id=stn_id, years=years)
        print()


# 사용 예시:

# 기상청에서 발급받은 서비스 키를 입력하세요
SERVICE_KEY = "YOUR_SERVICE_KEY_HERE"

# download_asos_data_by_station(stn_id=108, years=[2021, 2022])  # 서울
# download_asos_data_by_station(stn_id=133, years=[2021, 2022])  # 대전
# download_asos_data_multiple_stations(stn_ids=[108, 133], years=[2021, 2022])  # 여러 지점
