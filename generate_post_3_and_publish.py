import os
import sys
import json
import shutil
import time
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from auto_pipeline import load_env, log, generate_with_retry, render_diagram_card
from google import genai

ROOT_DIR = r"c:\DEV\10 month\261025_blog_auto"
folder_path = os.path.join(ROOT_DIR, "output", "261102_1905")
load_env()

def main():
    raw_json_path = os.path.join(folder_path, "raw_reddit_data.json")
    with open(raw_json_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    p = posts[2]  # Post 3
    idx = 3
    source_name = p.get('source', 'HackerNews')
    category_name = p.get('category', '글로벌 IT 엔지니어링 인사이트')

    # 3번 포스트 파일 생성 여부 체크
    md_files = [f for f in os.listdir(folder_path) if f.startswith("post_3") and f.endswith(".md")]
    if not md_files:
        log(f"🚀 [3번 포스트 생성 시작] {p['title'][:35]}...")
        client = genai.Client()
        prompt = f"""
        당신은 대한민국 상위 1% 전문 IT/비즈니스 테크 블로거이자 소프트웨어 아키텍트입니다.
        아래의 [{category_name}] 카테고리 기술 이슈 원본을 분석하여, 공부하는 비개발자나 초보자도 몰입해서 끝까지 읽을 수 있는 최고 품질의 네이버 블로그 기술 포스트를 작성해 주세요.

        [기술 원본 정보]
        - 카테고리: {category_name}
        - 출처: {source_name}
        - 제목: {p['title']}
        - 작성자: @{p.get('author', 'anonymous')}
        - 좋아요/추천수: {p.get('metrics', {}).get('likes', 0)}
        - 본문: {p.get('content', '')}

        [엄격한 작성 규칙]
        1. 메인 제목(#): 대괄호([IT 트렌드] 등) 없이, [독자의 호기심이나 불안을 자극하는 질문형 오프닝] + [구체적 핵심 기술 키워드] + [반전이나 이면 제시]의 3단 바이럴 훅 구조로 작성.
        2. 소제목(##): 섹션 헤더에는 이모지를 일절 배제하고 텍스트만 작성 (예: ## 1. 문제의 본질과 패러다임 변화).
        3. 시각자료 경로 삽입:
           - 메인 제목 직후: ![메인 아트]({idx}_main.png)
           - 본문 중간: ![아키텍처 도해]({idx}_arch.png)
        4. 비개발자 친화적 비유(Analogy): 어려운 기술 용어가 나올 때마다 일상적인 친숙한 개념(택배, 도서관, 지도 등)에 빗댄 비유 설명을 1개 이상 반드시 결합.
        5. 실전 소스코드 전면 배제: Javascript, C, Python 등의 긴 소스코드는 절대 넣지 말고, 정갈한 한글 의사코드(Pseudocode)와 작동 단계 요약 텍스트 상자(```text ... ```)로 대체.
        6. 비교 테이블(Table): 기존 방식 vs 신규 방식 간의 차이점을 명확히 대조하는 Markdown 표를 최소 1개 이상 작성.
        7. 단계 간 여백: 문단이나 단계가 바뀔 때 시각적 호흡을 위해 '&nbsp;' 줄을 삽입.
        8. 태그: 맨 마지막에 1단어 또는 2단어의 간결한 블로그 검색 태그 10개 내외 작성 (예: `#인공지능` `#해커뉴스` `#지식큐레이션` 등).

        [출력 포맷 (반드시 순수 마크다운만 출력)]
        마크다운 시작부터 끝까지 백틱 코드 블록(```markdown)으로 감싸지 말고 순수 마크다운 본문만 그대로 출력하세요.
        """
        res = generate_with_retry(client, prompt, model="gemini-3.1-flash-lite")
        article_md = res.text.strip()

        clean_title = "".join(c for c in p["title"] if c.isalnum() or c in (" ", "_", "-")).strip()
        clean_title = clean_title.replace(" ", "_")[:35]
        folder_name = f"post_{idx}_{clean_title}"
        post_dir = os.path.join(folder_path, folder_name)
        os.makedirs(post_dir, exist_ok=True)

        img1_path = os.path.join(post_dir, f"{idx}_main.png")
        img2_path = os.path.join(post_dir, f"{idx}_arch.png")

        meta_prompt = f"""
        다음 블로그 포스트의 내용을 바탕으로 인포그래픽 카드에 들어갈 정보를 한글로 추출해 주세요:
        {article_md[:1500]}
        
        다음 JSON 포맷으로만 응답하세요:
        {{
          "card1": {{
            "badge": "TECH BRIEFING",
            "title": "한 줄 핵심 제목 (15자 내외)",
            "subtitle": "이 기술이 가져올 핵심 변화 설명 (25자 내외)",
            "steps": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3", "핵심 포인트 4"]
          }},
          "card2": {{
            "badge": "SYSTEM ARCHITECTURE",
            "title": "구조 및 작동 원리 (15자 내외)",
            "subtitle": "어떻게 동작하고 기존과 다른가 (25자 내외)",
            "steps": ["1단계 작동 방식", "2단계 처리 과정", "3단계 데이터 변환", "4단계 최종 결과"]
          }}
        }}
        """
        try:
            m_res = generate_with_retry(client, meta_prompt, model="gemini-3.1-flash-lite")
            m_text = m_res.text.strip()
            if m_text.startswith("```"):
                m_text = m_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            meta = json.loads(m_text)
            c1, c2 = meta["card1"], meta["card2"]
            render_diagram_card(c1["title"], c1["subtitle"], c1["badge"], c1["steps"], img1_path)
            render_diagram_card(c2["title"], c2["subtitle"], c2["badge"], c2["steps"], img2_path)
            log("  🎨 [3/3] 1:1 고해상도 인포그래픽 도해 2장 렌더링 완료")
        except Exception as e:
            log(f"  ⚠️ 도해 생성 실패 (기본 카드로 대체): {e}")
            render_diagram_card("HackerNews Tech", "글로벌 엔지니어링 인사이트", "TECH", ["큐레이션", "데이터 수집", "랭킹 알고리즘", "인터페이스"], img1_path)
            render_diagram_card("Architecture 3", "시스템 구조도", "SYSTEM", ["원문 탐색", "필터링", "가공", "표시"], img2_path)

        # 루트에도 이미지 복사
        shutil.copy2(img1_path, os.path.join(folder_path, f"{idx}_main.png"))
        shutil.copy2(img2_path, os.path.join(folder_path, f"{idx}_arch.png"))

        md_file = os.path.join(folder_path, f"{folder_name}.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(article_md)
        log(f"✅ 3번 포스트 생성 완료: {os.path.basename(md_file)}")

    # 모든 이미지(1, 2, 3)를 folder_path 루트로 최종 동기화
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".png") and ("_main.png" in file_name or "_arch.png" in file_name):
                src = os.path.join(root, file_name)
                dst = os.path.join(folder_path, file_name)
                if src != dst:
                    shutil.copy2(src, dst)

    log("=" * 65)
    log("🚀 [11월 2일자 3편 네이버 블로그 전체 공개 일괄 자동 발행 기동]")
    log("=" * 65)

    pub_script = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "scripts", "naver_publish_all.py")
    ret = subprocess.run([
        sys.executable, "-u", pub_script,
        "--dir", folder_path,
        "--publish",
        "--interval", "8"
    ], cwd=ROOT_DIR)

    from telegram_notify import send_telegram_alert, format_publish_success_message
    result_json = os.path.join(folder_path, "published_results.json")
    if os.path.exists(result_json):
        try:
            with open(result_json, "r", encoding="utf-8") as f:
                results = json.load(f)
            for idx, r in enumerate(results):
                if idx < len(posts):
                    r["category"] = posts[idx].get("category", "")
                    r["selection_reason"] = posts[idx].get("selection_reason", "")
            msg = format_publish_success_message(results)
            send_telegram_alert(msg)
            log("📱 [Telegram] 3편 발행 결과 브리핑 발송 완료!")
        except Exception as e:
            log(f"⚠️ 텔레그램 결과 발송 예외: {e}")

if __name__ == "__main__":
    main()
