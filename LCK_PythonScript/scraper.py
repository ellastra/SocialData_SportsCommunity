# 개별 파일로만 저장하는 더 간단한 버전
from chat_downloader import ChatDownloader
from pathlib import Path
import json
import pandas as pd

# 여러 개의 YouTube URL 리스트
urls_file = pd.read_csv('urls_lck.csv', header=None)
urls = urls_file[0].tolist()

downloader = ChatDownloader()

for i, url in enumerate(urls):
    try:
        print(f"Processing URL {i+1}/{len(urls)}: {url}")
        chat = downloader.get_chat(url)
        
        out = []
        for msg in chat:
            out.append({
                "time_text": msg.get("time_text"),
                "timestamp": msg.get("timestamp"),
                "author": msg.get("author", {}).get("id"),
                "message": msg.get("message"),
                "amount": msg.get("money", {}).get("text"),   # superchat (if any)
            })
        
        # 파일명을 video_id 또는 순서 번호로 설정
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else f"video_{i+1}"
        filename = f"chat_{video_id}.json"
        
        Path(filename).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {len(out)} messages to {filename}")
        
    except Exception as e:
        print(f"Error processing {url}: {e}")
        continue
    
