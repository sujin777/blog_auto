import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env():
    env_file = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    val = v.strip().strip("'\"")
                    # 환경 변수가 없거나 비어있는 경우 주입
                    if not os.environ.get(k.strip()):
                        os.environ[k.strip()] = val

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

def fetch_korea_naver_news(limit=1):
    log(f"🇰🇷 [네이버 뉴스] 대한민국 IT/과학 헤드라인 핫토픽 {limit}개 탐색 중...")
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get("https://news.naver.com/section/105", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".sa_item._SECTION_HEADLINE")
        if not items:
            items = soup.select(".sa_item")

        for rank, item in enumerate(items[:10], 1):
            title_el = item.select_one(".sa_text_title")
            press_el = item.select_one(".sa_text_press")
            link_el = item.select_one("a.sa_text_title")

            if not title_el or not link_el:
                continue

            title = title_el.get_text(strip=True)
            press = press_el.get_text(strip=True) if press_el else "네이버 IT 뉴스"
            link = link_el.get("href", "")

            # 네이버 기사 상세 본문 가져오기
            content = ""
            try:
                a_res = requests.get(link, headers=headers, timeout=8)
                a_soup = BeautifulSoup(a_res.text, "html.parser")
                art_area = a_soup.select_one("#dic_area, #articleBodyContents, .news_cnt_detail")
                if art_area:
                    content = art_area.get_text("\n", strip=True)
            except Exception:
                pass

            if not content or len(content) < 150:
                lead_el = item.select_one(".sa_text_lede")
                content = lead_el.get_text(strip=True) if lead_el else title

            # AI/테크 관련 핵심 키워드 매칭 우선순위 부여
            news_data = {
                "id": f"naver_news_{rank}",
                "title": f"[국내 테크 1위] {title}",
                "author": press,
                "url": link,
                "content": content,
                "metrics": {
                    "likes": 1000 + rank * 50,
                    "comments": 150 + rank * 10
                },
                "category": "대한민국 최신 IT 핫토픽 & 국내 AI 혁신",
                "source": "NaverNews",
                "selection_reason": f"네이버 뉴스 IT/과학 헤드라인 랭킹 {rank}위 ({press})"
            }
            results.append(news_data)
            log(f"  ✓ 국내 테크 선정: #{rank} [{press}] {title[:35]}...")
            if len(results) >= limit:
                break
    except Exception as e:
        log(f"  ⚠️ 네이버 뉴스 수집 중 예외 발생: {e}")

    if limit == 1:
        return results[0] if results else None
    return results


def fetch_hacker_news_top_tech(limit=1):
    log(f"📰 [Hacker News] 상위 20개 핫토픽 중 IT/소프트웨어 테크 아티클 {limit}개 탐색 중...")
    results = []
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()
        if not top_ids:
            return results if limit > 1 else None
        
        for rank, story_id in enumerate(top_ids[:20], 1):
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
            if not item or item.get("type") != "story":
                continue
            
            title = item.get("title", "")
            url = item.get("url", "")
            score = item.get("score", 0)
            by = item.get("by", "anonymous")
            descendants = item.get("descendants", 0)
            
            if not is_tech_story(title, url) and rank > 3:
                continue

            content = item.get("text", "")
            if not content:
                content = f"글로벌 개발자 커뮤니티 Hacker News에서 추천수 {score}개, 댓글 {descendants}개를 기록하며 랭킹 {rank}위에 오른 화제의 엔지니어링 토픽입니다. 원문 출처 링크: {url}"
            else:
                content = f"{content}\n\n(참고 링크: {url})"
                
            story_data = {
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
            results.append(story_data)
            log(f"  ✓ Hacker News 테크 선정: #{rank} {title} (추천 {score}개, 댓글 {descendants}개)")
            if len(results) >= limit:
                break
    except Exception as e:
        log(f"  ⚠️ Hacker News 수집 중 예외 발생: {e}")

    if limit == 1:
        return results[0] if results else None
    return results

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

def categorize_and_select(korea_post, scored_posts, hn_post):
    log("🧠 [3대 테마 밸런스 선별] 1:한국 최신 IT 핫이슈 / 2:글로벌 AI 모델·실용팁 / 3:엔지니어링 인사이트")
    
    selected = []

    # Slot 1: 대한민국 최신 인기 IT 이슈 & 국내 AI 혁신
    if korea_post:
        korea_post["category"] = "대한민국 최신 IT 핫토픽 & 국내 AI 혁신"
        selected.append(korea_post)

    # Slot 2: 글로벌 AI 실생활/업무 활용 팁 & 최신 모델 (Reddit 1위)
    if scored_posts:
        reddit_top = scored_posts[0]["post"]
        reddit_top["category"] = "글로벌 AI 모델 혁신 & 실무 활용 팁"
        reddit_top["selection_reason"] = scored_posts[0]["reason"]
        selected.append(reddit_top)

    # Slot 3: 글로벌 IT 엔지니어링 인사이트 (Hacker News 1위)
    if hn_post:
        hn_post["category"] = "글로벌 IT 엔지니어링 인사이트"
        selected.append(hn_post)

    # 3개 미달 시 안전 보충 로직
    if len(selected) < 3:
        for item in scored_posts[1:]:
            p = item["post"]
            if not any(s.get("url") == p.get("url") for s in selected):
                p["category"] = "글로벌 테크 트렌드 분석"
                p["selection_reason"] = item["reason"]
                selected.append(p)
                if len(selected) >= 3:
                    break

    if len(selected) < 3:
        hn_extras = fetch_hacker_news_top_tech(limit=3)
        for h in hn_extras:
            if not any(s.get("url") == h.get("url") for s in selected):
                h["category"] = "글로벌 IT 엔지니어링 인사이트"
                selected.append(h)
                if len(selected) >= 3:
                    break

    return selected[:3]

def run_multichannel_ingest():
    log("==================================================================")
    log("🌐 [스마트 멀티채널 수집기] 국내 네이버 IT 뉴스 + Reddit AI + Hacker News")
    log("==================================================================")

    load_env()
    output_dir = os.path.join(ROOT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    # 1. 대한민국 실시간 인기 네이버 IT/과학 뉴스 수집
    korea_post = fetch_korea_naver_news(limit=1)

    # 2. Reddit 4대 메이저 AI 커뮤니티 수집 (Apify Scraper)
    reddit_js = os.path.join(ROOT_DIR, ".agents", "skills", "ingest-reddit-posts", "scripts", "test_reddit.js")
    try:
        ret = subprocess.run(["node", reddit_js], cwd=ROOT_DIR, env=os.environ.copy())
        if ret.returncode != 0:
            log(f"⚠️ Reddit 수집 스크립트 비정상 종료 (코드: {ret.returncode})")
    except Exception as e:
        log(f"⚠️ Reddit 스크립트 실행 예외: {e}")

    now_str = datetime.now().strftime("%y%m%d_%H%M")
    folders = [f for f in os.listdir(output_dir) if f.startswith("2") and os.path.isdir(os.path.join(output_dir, f))]
    folders.sort(reverse=True)
    
    if not folders or not folders[0].startswith(datetime.now().strftime("%y%m%d")):
        latest_folder = os.path.join(output_dir, now_str)
        os.makedirs(latest_folder, exist_ok=True)
    else:
        latest_folder = os.path.join(output_dir, folders[0])
    
    raw_json_file = os.path.join(latest_folder, "raw_reddit_data.json")
    
    reddit_posts = []
    if os.path.exists(raw_json_file):
        try:
            with open(raw_json_file, "r", encoding="utf-8") as f:
                reddit_posts = json.load(f)
        except Exception as e:
            log(f"⚠️ raw_reddit_data.json 읽기 실패: {e}")

    log(f"📥 수집된 원본 Reddit 글: {len(reddit_posts)}개")

    # 3. 바이럴 인게이지먼트 복합 스코어링 및 노이즈 필터링
    scored_posts = []
    for p in reddit_posts:
        score, reason, kws = calculate_virality_score(p)
        if score > 0:
            scored_posts.append({
                "score": score,
                "reason": reason,
                "post": p
            })

    scored_posts.sort(key=lambda x: x["score"], reverse=True)
    log(f"📊 노이즈 필터 통과 고품질 포스트: {len(scored_posts)}개")

    # 4. Hacker News 상위 테크 아티클 수집
    hn_post = fetch_hacker_news_top_tech(limit=1)

    # 5. 3대 카테고리 밸런스 강제 배분 (한국 테크 1 + Reddit AI 1 + Hacker News 1)
    final_selected = categorize_and_select(korea_post, scored_posts, hn_post)

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
