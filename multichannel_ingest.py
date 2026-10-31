import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def fetch_hacker_news_top():
    log("📰 [Hacker News] 글로벌 1위 최신 엔지니어링 토픽 탐색 중...")
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()
        if not top_ids:
            return None
        
        for story_id in top_ids[:10]:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
            if not item or item.get("type") != "story":
                continue
            
            title = item.get("title", "")
            url = item.get("url", "")
            score = item.get("score", 0)
            by = item.get("by", "anonymous")
            descendants = item.get("descendants", 0)
            
            # 본문 구성 (URL이 있으면 URL 링크 포함, 텍스트가 있으면 포함)
            content = item.get("text", "")
            if not content:
                content = f"글로벌 개발자 커뮤니티 Hacker News에서 추천수 {score}개, 댓글 {descendants}개를 기록하며 1위에 오른 화제의 엔지니어링 토픽입니다. 원문 출처 링크: {url}"
            else:
                content = f"{content}\n\n(참고 링크: {url})"
                
            log(f"  ✓ Hacker News 1위 선정: {title} (추천 {score}개, 작성자 @{by})")
            return {
                "id": str(story_id),
                "title": f"[HackerNews 1위] {title}",
                "author": by,
                "url": url or f"https://news.ycombinator.com/item?id={story_id}",
                "content": content,
                "metrics": {
                    "likes": score,
                    "comments": descendants
                },
                "source": "HackerNews"
            }
    except Exception as e:
        log(f"  ⚠️ Hacker News 수집 중 예외 발생: {e}")
        return None

def run_multichannel_ingest():
    log("=======================================================")
    log("🌐 [2+1 멀티채널 수집기] Reddit(2편) + Hacker News(1편) 가동")
    log("=======================================================")

    # 1. Reddit r/ClaudeAI 최신 인기글 수집 (기존 Apify 스크립트 실행)
    reddit_js = os.path.join(ROOT_DIR, ".agents", "skills", "ingest-reddit-posts", "scripts", "test_reddit.js")
    ret = subprocess.run(["node", reddit_js], cwd=ROOT_DIR)
    if ret.returncode != 0:
        raise RuntimeError("Reddit 데이터 수집 실패")

    # 최신 output 폴더 탐색
    output_dir = os.path.join(ROOT_DIR, "output")
    folders = [f for f in os.listdir(output_dir) if f.startswith("2") and os.path.isdir(os.path.join(output_dir, f))]
    folders.sort(reverse=True)
    if not folders:
        raise RuntimeError("output 폴더를 찾을 수 없습니다.")
    
    latest_folder = os.path.join(output_dir, folders[0])
    raw_json_file = os.path.join(latest_folder, "raw_reddit_data.json")
    
    with open(raw_json_file, "r", encoding="utf-8") as f:
        reddit_posts = json.load(f)

    # Reddit 상위 2개 추출
    top_reddit = reddit_posts[:2]
    for p in top_reddit:
        p["source"] = "Reddit r/ClaudeAI"

    # 2. Hacker News 1위 추출
    hn_post = fetch_hacker_news_top()
    
    # 3. 2 + 1 결합 (총 3개)
    combined = []
    combined.extend(top_reddit)
    if hn_post:
        combined.append(hn_post)
    elif len(reddit_posts) >= 3:
        # HN 수집 실패 시 Reddit 3위 포스트로 대체
        combined.append(reddit_posts[2])

    # 통합 JSON으로 덮어쓰기 저장
    with open(raw_json_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    log(f"✅ 멀티채널 3대 토픽 선별 완료: {latest_folder}")
    for i, p in enumerate(combined, 1):
        log(f"  [{i}] [{p.get('source', 'Reddit')}] {p['title'][:40]}... (추천: {p.get('metrics', {}).get('likes', 0)})")

    return latest_folder

if __name__ == "__main__":
    run_multichannel_ingest()

