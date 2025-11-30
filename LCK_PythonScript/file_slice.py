import pandas as pd
import os
import math

def split_csv_file(file_path, num_parts=3):
    """
    큰 CSV 파일을 여러 개의 작은 파일로 분할합니다.
    
    Args:
        file_path (str): 분할할 CSV 파일의 경로
        num_parts (int): 분할할 파일 개수 (기본값: 3)
    """
    # CSV 파일 읽기
    df = pd.read_csv(file_path)
    
    # 전체 행 수
    total_rows = len(df)
    
    # 각 파일당 행 수 계산
    rows_per_file = math.ceil(total_rows / num_parts)
    
    # 파일명과 확장자 분리
    file_dir = os.path.dirname(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # 파일 분할
    for i in range(num_parts):
        start_idx = i * rows_per_file
        end_idx = min((i + 1) * rows_per_file, total_rows)
        
        # 해당 범위의 데이터 추출
        chunk = df.iloc[start_idx:end_idx]
        
        # 새 파일명 생성
        output_file = os.path.join(file_dir, f"{file_name}_{i+1}.csv")
        
        # CSV 파일로 저장
        chunk.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"파일 생성: {output_file} (행 수: {len(chunk)})")

def select_and_split_csv():
    lck_data_folder = "LCK_data"
    
    if not os.path.exists(lck_data_folder):
        print(f"'{lck_data_folder}' 폴더를 찾을 수 없습니다.")
        return
    
    # CSV 파일 목록 가져오기
    csv_files = [f for f in os.listdir(lck_data_folder) if f.endswith('.csv')]
    
    if not csv_files:
        print("CSV 파일을 찾을 수 없습니다.")
        return
    
    # 파일 목록 출력
    print("=== CSV 파일 목록 ===")
    for idx, csv_file in enumerate(csv_files, 1):
        print(f"{idx}. {csv_file}")
    
    # 사용자 입력 받기
    try:
        choice = int(input("\n분할할 파일 번호를 입력하세요: "))
        if 1 <= choice <= len(csv_files):
            selected_file = csv_files[choice - 1]
            file_path = os.path.join(lck_data_folder, selected_file)
            print(f"\n'{selected_file}' 파일을 분할합니다...")
            split_csv_file(file_path, 3) ##### 여기가 설정 부분 #####
        else:
            print("잘못된 번호입니다.")
    except ValueError:
        print("숫자를 입력해주세요.")

if __name__ == "__main__":
    select_and_split_csv()