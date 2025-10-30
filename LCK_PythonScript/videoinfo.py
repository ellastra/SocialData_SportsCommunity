import yt_dlp
import pandas as pd

def get_youtube_metadata_ytdlp(video_url):
    """
    yt-dlp를 사용하여 YouTube 영상 메타데이터를 추출하는 함수
    """
    ydl_opts = {
        'quiet': True,  # 로그 출력 최소화
        'no_warnings': True,
        'skip_download': True,  # 다운로드 없이 메타데이터만 추출
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return {
                'url': video_url,
                'title': info.get('title', 'N/A'),
                'upload_date': info.get('upload_date', 'N/A'),
                'duration': info.get('duration', 'N/A'),
                'view_count': info.get('view_count', 'N/A'),
                'uploader': info.get('uploader', 'N/A')
            }
    except Exception as e:
        print(f"Error: {video_url} - {str(e)}")
        return {
            'url': video_url,
            'title': 'ERROR',
            'upload_date': 'ERROR',
            'duration': 'ERROR',
            'view_count': 'ERROR',
            'uploader': 'ERROR'
        }

def scrape_youtube_metadata(csv_file):
    """
    CSV 파일의 YouTube URL들에서 메타데이터를 수집
    """
    # CSV 파일 읽기
    df = pd.read_csv(csv_file, header=None, names=['url'])
    print(f"총 {len(df)}개의 YouTube URL을 처리합니다.\n")
    
    results = []
    
    for i, row in df.iterrows():
        url = row['url']
        print(f"{i+1}/{len(df)} 처리 중: {url}")
        
        metadata = get_youtube_metadata_ytdlp(url)
        results.append(metadata)
        
        if metadata['title'] != 'ERROR':
            print(f"  ✓ 제목: {metadata['title'][:50]}...")
            print(f"  ✓ 날짜: {metadata['upload_date']}")
    
    # DataFrame으로 변환
    result_df = pd.DataFrame(results)
    
    # CSV로 저장
    output_file = 'youtube_metadata.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n데이터가 {output_file}에 저장되었습니다.")
    
    return result_df

# 실행
if __name__ == "__main__":
    results = scrape_youtube_metadata('urls_lck.csv')
    print("\n수집된 데이터 미리보기:")
    print(results.head(10))
