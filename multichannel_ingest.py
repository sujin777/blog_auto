import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 네이버 상위 노출 20대 핵심 테크 키워드 사전
TECH_KEYWORDS = [
    "chatgpt", "챗gpt", "클로드", "claude", "생성형 ai", "생성형ai",
    "인공지능", "프롬프트", "업무 자동화", "자동화", "바이브 코딩", "vibe coding",
    "llm", "딥시크", "deepseek", "오픈ai", "openai", "앤트로픽", "anthropic",
    "코딩 에이전트", "ai 에이전트", "ai 툴", "파이썬 자동화", "머신러닝"
]

# Hacker News 테크/소프트웨어 필터 키워드
HN_TECH_KEYWORDS = [
    "ai", "llm", "gpt", "model", "software", "code", "programming", "python",
    "rust", "linux", "compiler", "database", "security", "cloud", "api", "gpu",
    "algorithm", "open source", "developer", "engine", "tech", "web", "server",
    "apple", "google", "microsoft", "meta", "nvidia", "silicon", "framework"
]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def is_tech_story(title, url):
    combined = (title + " " + url).lower()
    return any(kw in combined for kw in HN_TECH_KEYWORDS)

def fetch_hacker_news_top_tech():
    log("📰 [Hacker News] 상위 15개 핫토픽 중 IT/소프트웨어/기술 최상위 아티클 탐색 중...")
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()
        if not top_ids:
            return None
        
        for rank, story_id in enumerate(top_ids[:15], 1):
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
            if not item or item.get("type") != "story":
                continue
            
            title = item.get("title", "")
            url = item.get("url", "")
            score = item.get("score", 0)
            by = item.get("by", "anonymous")
            descendants = item.get("descendants", 0)
            
            # 테크/소프트웨어/엔지니어링 필터 적용
            if not is_tech_story(title, url) and rank > 3:
                # 3위 이내라도 순수 비IT면 스킵
                continue

            content = item.get("text", "")
            if not content:
                content = f"글로벌 개발자 커뮤니티 Hacker News에서 추천수 {score}개, 댓글 {descendants}개를 기록하며 랭킹 {rank}위에 오른 화제의 엔지니어링 토픽입니다. 원문 출처 링크: {url}"
            else:
                content = f"{content}\n\n(참고 링크: {url})"
                
            log(f"  ✓ Hacker News 테크 1위 선정: #{rank} {title} (추천 {score}개, 댓글 {descendants}개)")
            return {
                "id": str(story_id),
                "title": f"[HackerNews {rank}위] {title}",
                "author": by,
                "url": url or f"https://news.ycombinator.com/item?id={story_id}",
                "content": content,
                "metrics": {
                    "likes": score,
                    "comments": descendants
                },
                "category": "글로벌 IT 엔지니어링 인사이트",
                "source": "HackerNews",
                "selection_reason": f"Hacker News 테크 랭킹 {rank}위 (추천 {score}개, 댓글 {descendants}개)"
            }
    except Exception as e:
        log(f"  ⚠️ Hacker News 수집 중 예외 발생: {e}")
        return None

def calculate_virality_score(post):
    upvotes = post.get("metrics", {}).get("likes", 0)
    comments = post.get("metrics", {}).get("comments", 0)
    content = post.get("content", "")
    title = post.get("title", "")
    full_text = (title + " " + content).lower()
    content_len = len(content)

    # 1. 노이즈 필터링: 150자 미만 단순 단문/짤방 탈락 (단, 추천수 500개 이상 초압도적 글은 예외 허용)
    if content_len < 150 and upvotes < 500:
        return -1.0, "본문 분량 부족 (< 150자)", []

    # 2. 기본 바이럴 스코어: 추천수(40%) + 댓글 토론 열기(30%) + 정보 텍스트 밀도(30%)
    # 텍스트 밀도는 최대 1200자 기준 정규화
    text_density_score = min(content_len, 1200) / 1200.0 * 30.0
    base_score = (upvotes * 0.4) + (comments * 0.3) + text_density_score

    # 3. 네이버 20대 인기 테크 키워드 매칭 부스팅 (+20%)
    matched_kws = [kw for kw in TECH_KEYWORDS if kw in full_text]
    keyword_bonus = 0.0
    if matched_kws:
        keyword_bonus = base_score * 0.20

    final_score = base_score + keyword_bonus
    reason = f"추천 {upvotes}개, 댓글 {comments}개"
    if matched_kws:
        reason += f" + 네이버 '{matched_kws[0]}' 키워드 매칭(+20% 부스팅)"

    return final_score, reason, matched_kws

def categorize_and_select(scored_posts, hn_post):
    log("🧠 [3대 테마 밸런스 선별] 실용 팁 / 최신 모델 테크 / 글로벌 인사이트 배분 중...")
    
    # 테마 키워드 정의
    practical_keywords = ["tip", "prompt", "workflow", "how to", "use case", "automation", "guide", "free", "tricks", "productivity", "팁", "활용", "작성", "방법"]
    frontier_keywords = ["model", "claude", "gpt", "openai", "anthropic", "deepseek", "release", "benchmark", "update", "reasoning", "opus", "sonnet", "o3", "모델", "출시", "업데이트"]

    slot1 = None # 실생활/업무 AI 생산성 및 활용 팁
    slot2 = None # 최신 AI 모델 & 기술 혁신
    slot3 = hn_post # 글로벌 IT 엔지니어링 인사이트

    # 1차 분류: 실용 팁 및 생산성 포스트 탐색
    for item in scored_posts:
        post = item["post"]
        text = (post["title"] + " " + post["content"]).lower()
        if any(kw in text for kw in practical_keywords):
            slot1 = post
            slot1["category"] = "실생활/업무 AI 생산성 및 꿀팁"
            slot1["selection_reason"] = item["reason"] + " (실용 팁 테마 매칭)"
            break
            
    # 실용 팁 슬롯이 비었으면 최고 득점 글 1위 배정
    if not slot1 and scored_posts:
        slot1 = scored_posts[0]["post"]
        slot1["category"] = "실생활/업무 AI 생산성 및 꿀팁"
        slot1["selection_reason"] = scored_posts[0]["reason"]

    # 2차 분류: 최신 AI 모델 & 기술 혁신 포스트 탐색 (slot1 제외)
    for item in scored_posts:
        post = item["post"]
        if post["url"] == slot1["url"]:
            continue
        text = (post["title"] + " " + post["content"]).lower()
        if any(kw in text for kw in frontier_keywords):
            slot2 = post
            slot2["category"] = "최신 AI 모델 및 빅테크 기술 혁신"
            slot2["selection_reason"] = item["reason"] + " (빅테크 AI 혁신 매칭)"
            break

    # 최신 모델 슬롯이 비었으면 다음 순위 최고 득점 글 배정
    if not slot2:
        for item in scored_posts:
            if item["post"]["url"] != slot1["url"]:
                slot2 = item["post"]
                slot2["category"] = "최신 AI 모델 및 빅테크 기술 혁신"
                slot2["selection_reason"] = item["reason"]
                break

    selected = [slot1, slot2]
    if slot3:
        selected.append(slot3)
    elif len(scored_posts) >= 3:
        # HN 부재 시 Reddit 3위 배정
        remaining = [item["post"] for item in scored_posts if item["post"]["url"] not in [slot1["url"], slot2["url"]]]
        if remaining:
            fallback = remaining[0]
            fallback["category"] = "글로벌 IT 엔지니어링 인사이트"
            fallback["selection_reason"] = "Reddit 종합 인기 3위"
            selected.append(fallback)

    return selected

def run_multichannel_ingest():
    log("==================================================================")
    log("🌐 [스마트 큐레이션 수집기] Reddit 4대 커뮤니티 + Hacker News 테크")
    log("==================================================================")

    # 1. Reddit 4대 메이저 AI 커뮤니티 수집 (Apify Scraper)
    reddit_js = os.path.join(ROOT_DIR, ".agents", "skills", "ingest-reddit-posts", "scripts", "test_reddit.js")
    ret = subprocess.run(["node", reddit_js], cwd=ROOT_DIR)
    if ret.returncode != 0:
        raise RuntimeError("Reddit 4대 커뮤니티 데이터 수집 실패")

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

    log(f"📥 수집된 원본 Reddit 글: {len(reddit_posts)}개")

    # 2. 바이럴 인게이지먼트 복합 스코어링 및 노이즈 필터링
    scored_posts = []
    for p in reddit_posts:
        score, reason, kws = calculate_virality_score(p)
        if score > 0:
            scored_posts.append({
                "score": score,
                "reason": reason,
                "post": p
            })
        else:
            log(f"  [노이즈 제외] {p['title'][:35]}... ({reason})")

    # 점수 높은 순으로 정렬
    scored_posts.sort(key=lambda x: x["score"], reverse=True)
    log(f"📊 노이즈 필터 통과 고품질 포스트: {len(scored_posts)}개")

    # 3. Hacker News 상위 테크 아티클 수집
    hn_post = fetch_hacker_news_top_tech()

    # 4. 3대 카테고리 밸런스 강제 배분
    final_selected = categorize_and_select(scored_posts, hn_post)

    # 통합 JSON으로 덮어쓰기 저장 (선별 사유 및 카테고리 메타데이터 포함)
    with open(raw_json_file, "w", encoding="utf-8") as f:
        json.dump(final_selected, f, ensure_ascii=False, indent=2)

    log(f"✅ 스마트 3대 테마 선별 완료: {latest_folder}")
    for i, p in enumerate(final_selected, 1):
        log(f"  [{i}] [{p.get('category', '일반')}] {p['title'][:38]}...")
        log(f"      ㄴ 선별 사유: {p.get('selection_reason', '인기 스코어 상위')}")

    return latest_folder

if __name__ == "__main__":
    run_multichannel_ingest()
