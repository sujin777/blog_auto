import os
import sys
import json
import time
import subprocess
from datetime import datetime
from google import genai
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def load_env():
    env_file = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

def run_step_1_ingest():
    log("==================================================================")
    log("🚀 [1단계] 스마트 큐레이션 멀티채널(Reddit 4대 + HackerNews 테크) 수집")
    log("==================================================================")
    from multichannel_ingest import run_multichannel_ingest
    return run_multichannel_ingest()

def render_diagram_card(title, subtitle, badge, steps, output_png_path):
    steps_html = ""
    colors = ["#3b82f6", "#f43f5e", "#10b981", "#8b5cf6"]
    for i, s in enumerate(steps[:4], 1):
        c = colors[(i - 1) % len(colors)]
        steps_html += f"""
        <div style='display:flex; align-items:center; margin-bottom:18px; font-size:20px;'>
          <div style='width:44px; height:44px; border-radius:12px; background:{c}; display:flex; align-items:center; justify-content:center; font-weight:800; margin-right:18px; font-size:22px; flex-shrink:0;'>{i}</div>
          <div style='color:#cbd5e1; font-weight:500;'>{s}</div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          margin: 0; padding: 0; background: #0f172a; color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', sans-serif;
          display: flex; justify-content: center; align-items: center; width: 1000px; height: 1000px;
        }}
        .card {{
          width: 860px; height: 860px; background: #1e293b; border-radius: 36px; padding: 60px;
          box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;
          border: 2px solid #334155; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}
        .badge {{
          align-self: flex-start; background: rgba(59, 130, 246, 0.2); color: #60a5fa;
          padding: 8px 20px; border-radius: 9999px; font-weight: 700; font-size: 16px;
          border: 1px solid rgba(59, 130, 246, 0.4); text-transform: uppercase; letter-spacing: 1px;
        }}
        .title {{ font-size: 38px; font-weight: 800; line-height: 1.3; margin: 20px 0 10px 0; }}
        .subtitle {{ font-size: 20px; color: #94a3b8; margin-bottom: 30px; line-height: 1.5; }}
        .steps-box {{ background: #0f172a; border-radius: 24px; padding: 36px; border: 1px solid #1e293b; }}
        .footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #334155; padding-top: 24px; color: #64748b; font-size: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div>
          <div class="badge">{badge}</div>
          <div class="title">{title}</div>
          <div class="subtitle">{subtitle}</div>
          <div class="steps-box">
            {steps_html}
          </div>
        </div>
        <div class="footer">
          <span>AI Tech Architecture Series</span>
          <span>Verified Insight 💡</span>
        </div>
      </div>
    </body>
    </html>
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1000, "height": 1000})
        page.set_content(html)
        page.screenshot(path=output_png_path)
        browser.close()

def generate_with_retry(client, prompt, model="gemini-3.8-flash", max_retries=5, initial_delay=5):
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                log(f"  ⏳ Gemini API 일시 부하 감지 (시도 {attempt}/{max_retries}). {delay}초 후 지수 백오프 재시도...")
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    raise RuntimeError(f"Gemini API 호출이 {max_retries}회 연속 실패했습니다.")

def run_step_2_generate_articles(folder_path):
    log("==================================================================")
    log("🚀 [2단계] Gemini 3.8 Flash 스마트 블로그 아티클 및 1:1 도해 생성")
    log("==================================================================")
    
    raw_json_path = os.path.join(folder_path, "raw_reddit_data.json")
    if not os.path.exists(raw_json_path):
        raise FileNotFoundError(f"수집 데이터가 없습니다: {raw_json_path}")
        
    with open(raw_json_path, "r", encoding="utf-8") as f:
        posts = json.load(f)
        
    client = genai.Client()
    top_posts = posts[:3]
    log(f"총 {len(posts)}개 포스트 중 상위 {len(top_posts)}개 주제 선별 완료")
    
    for idx, p in enumerate(top_posts, 1):
        source_name = p.get('source', 'Reddit')
        category_name = p.get('category', '테크 인사이트')
        log(f"\n[{idx}/{len(top_posts)}] [{category_name}] 주제 생성 중: {p['title'][:40]}...")
        
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
        1. 메인 제목(#): 대괄호([IT 트렌드] 등) 없이, [독자의 호기심이나 불안을 자극하는 질문형 오프닝] + [구체적 핵심 기술 키워드] + [반전이나 이면 제시]의 3단 바이럴 훅 구조로 작성 (예: '내가 첨삭받은 자소서가 AI 글이라고? 클로드의 보이지 않는 워터마크 논란과 그 이면').
        2. 소제목(##): 섹션 헤더에는 이모지(🧠, 💡 등)를 일절 배제하고 텍스트만 작성 (예: ## 1. 문제의 본질과 패러다임 변화).
        3. 시각자료 경로 삽입:
           - 메인 제목 직후: ![메인 아트]({idx}_main.png)
           - 본문 중간: ![아키텍처 도해]({idx}_arch.png)
        4. 비개발자 친화적 비유(Analogy): 어려운 기술 용어나 작동 원리가 나올 때마다 일상적인 친숙한 개념(택배, 주방 요리, 레고 등)에 빗댄 비유 설명을 1개 이상 반드시 결합.
        5. 실전 소스코드 전면 배제: Javascript, C, Python 등의 긴 소스코드는 절대 넣지 말고, 정갈한 한글 의사코드(Pseudocode)와 작동 단계 요약 텍스트 상자(```text ... ```)로 대체.
        6. 비교 테이블(Table): 기존 방식 vs 신규 방식 간의 차이점을 명확히 대조하는 Markdown 표를 최소 1개 이상 작성.
        7. 단계 간 여백: 문단이나 단계가 바뀔 때 시각적 호흡을 위해 '&nbsp;' 줄을 삽입.
        8. 태그: 맨 마지막에 1단어 또는 2단어의 간결한 블로그 검색 태그 10개 내외 작성 (예: `#인공지능` `#클로드` `#생성형AI` `#업무자동화` 등).

        [출력 포맷 (반드시 순수 마크다운만 출력)]
        마크다운 시작부터 끝까지 백틱 코드 블록(```markdown)으로 감싸지 말고 순수 마크다운 본문만 그대로 출력하세요.
        """
        
        res = generate_with_retry(client, prompt, model="gemini-3.8-flash")
        article_md = res.text.strip()
        
        # 파일명 생성
        clean_title = "".join(c for c in p["title"] if c.isalnum() or c in (" ", "_", "-")).strip()
        clean_title = clean_title.replace(" ", "_")[:35]
        folder_name = f"post_{idx}_{clean_title}"
        post_dir = os.path.join(folder_path, folder_name)
        os.makedirs(post_dir, exist_ok=True)
        
        # 2종의 고해상도 인포그래픽 도해 렌더링
        img1_path = os.path.join(post_dir, f"{idx}_main.png")
        img2_path = os.path.join(post_dir, f"{idx}_arch.png")
        
        # 도해 정보 추출 프롬프트
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
            m_res = generate_with_retry(client, meta_prompt, model="gemini-3.8-flash")
            m_text = m_res.text.strip()
            if m_text.startswith("```"):
                m_text = m_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            meta = json.loads(m_text)
            
            c1 = meta["card1"]
            render_diagram_card(c1["title"], c1["subtitle"], c1["badge"], c1["steps"], img1_path)
            
            c2 = meta["card2"]
            render_diagram_card(c2["title"], c2["subtitle"], c2["badge"], c2["steps"], img2_path)
            log(f"  🎨 [{idx}/3] 1:1 고해상도 인포그래픽 도해 2장 렌더링 완료")
        except Exception as e:
            log(f"  ⚠️ 도해 생성 실패 (기본 카드로 대체): {e}")
            render_diagram_card(f"AI Tech Briefing {idx}", "글로벌 테크 트렌드 핵심 분석", "TREND", ["최신 모델 발표", "벤치마크 분석", "생산성 혁신", "향후 전망"], img1_path)
            render_diagram_card(f"Architecture {idx}", "시스템 내부 작동 메커니즘", "SYSTEM", ["입력 데이터 수신", "프롬프트 최적화", "추론 및 가공", "최종 배포"], img2_path)

        # 마크다운 저장
        md_file = os.path.join(folder_path, f"{folder_name}.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(article_md)
        log(f"  ✍️ [{idx}/3] 블로그 포스트 본문 작성 완료 ({len(article_md)}자)")

def run_step_3_publish(folder_path):
    log("==================================================================")
    log("🚀 [3단계] 네이버 블로그 스마트에디터 ONE 자동 발행 기동")
    log("==================================================================")
    pub_script = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "scripts", "naver_publish_all.py")
    ret = subprocess.run([
        sys.executable, "-u", pub_script,
        "--dir", folder_path,
        "--publish",
        "--interval", "8"
    ], cwd=ROOT_DIR)
    
    published_results = []
    result_json_path = os.path.join(folder_path, "published_results.json")
    if os.path.exists(result_json_path):
        try:
            with open(result_json_path, "r", encoding="utf-8") as f:
                published_results = json.load(f)
        except Exception:
            pass
            
    if ret.returncode == 0:
        log("🎉 모든 포스트 네이버 블로그 일괄 자동 발행 성공!")
    else:
        log(f"⚠️ 네이버 발행 스크립트 종료 코드: {ret.returncode}")
        
    return published_results

def main():
    load_env()
    log("🌟 [AI Blog Auto Runner] 스마트 큐레이션 전자동 블로그 파이프라인 시작")
    from telegram_notify import send_telegram_alert, format_publish_success_message, format_error_message
    try:
        latest_folder = run_step_1_ingest()
        run_step_2_generate_articles(latest_folder)
        results = run_step_3_publish(latest_folder)
        log("🏆 전체 무인 파이프라인이 성공적으로 완료되었습니다!")
        
        if results:
            # raw_reddit_data.json에서 카테고리 및 선별 사유 보강
            raw_data_file = os.path.join(latest_folder, "raw_reddit_data.json")
            if os.path.exists(raw_data_file):
                try:
                    with open(raw_data_file, "r", encoding="utf-8") as f:
                        raw_posts = json.load(f)
                    for idx, r in enumerate(results):
                        if idx < len(raw_posts):
                            r["category"] = raw_posts[idx].get("category", "")
                            r["selection_reason"] = raw_posts[idx].get("selection_reason", "")
                except Exception:
                    pass
            msg = format_publish_success_message(results)
            send_telegram_alert(msg)
    except Exception as e:
        err_msg = str(e)
        log(f"❌ 파이프라인 실행 중 오류 발생: {err_msg}")
        send_telegram_alert(format_error_message(err_msg))
        sys.exit(1)

if __name__ == "__main__":
    main()
