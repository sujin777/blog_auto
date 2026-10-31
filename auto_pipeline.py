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
    log("=======================================================")
    log("🚀 [1단계] 2+1 멀티채널(Reddit 2편 + HackerNews 1편) 트렌드 수집")
    log("=======================================================")
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

    html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset='utf-8'>
    <style>
      body {{ margin:0; width:1000px; height:1000px; display:flex; flex-direction:column; justify-content:center; align-items:center; background:linear-gradient(135deg, #090d16 0%, #171c2d 50%, #1f1b3c 100%); font-family:'Malgun Gothic', -apple-system, sans-serif; color:white; }}
      .badge {{ background:rgba(244,63,94,0.15); border:1px solid #f43f5e; color:#fda4af; padding:8px 22px; border-radius:999px; font-weight:700; font-size:18px; margin-bottom:24px; text-transform:uppercase; letter-spacing:2px; }}
      .title {{ font-size:38px; font-weight:800; text-align:center; max-width:860px; line-height:1.4; margin-bottom:16px; text-shadow:0 4px 20px rgba(0,0,0,0.6); }}
      .subtitle {{ font-size:20px; color:#94a3b8; text-align:center; max-width:800px; line-height:1.5; margin-bottom:34px; }}
      .box {{ background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.12); border-radius:24px; padding:36px; width:800px; box-shadow:0 20px 50px rgba(0,0,0,0.4); backdrop-filter:blur(10px); }}
    </style>
    </head>
    <body>
      <div class='badge'>{badge}</div>
      <div class='title'>{title}</div>
      <div class='subtitle'>{subtitle}</div>
      <div class='box'>
        {steps_html}
      </div>
    </body>
    </html>"""

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page(viewport={"width": 1000, "height": 1000})
        page.set_content(html)
        page.screenshot(path=output_png_path)
        b.close()

def generate_with_retry(client, prompt, model="gemini-3.8-flash", max_retries=5, initial_delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except Exception as e:
            err_str = str(e)
            if attempt < max_retries and any(k in err_str for k in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded"]):
                delay = initial_delay * (2 ** (attempt - 1))
                log(f"⚠️ Gemini API 일시적 부하 발생 ({err_str[:60]})... {delay}초 대기 후 재시도 ({attempt}/{max_retries})")
                time.sleep(delay)
            else:
                log(f"❌ Gemini API 오류: {err_str}")
                raise

def run_step_2_generate_articles(folder_path):
    log("=======================================================")
    log("🤖 [2단계] Gemini 3.8 Flash 엔진 기반 포스트 및 도해 자동 생성")
    log("=======================================================")
    
    raw_json_file = os.path.join(folder_path, "raw_reddit_data.json")
    if not os.path.exists(raw_json_file):
        raise RuntimeError("raw_reddit_data.json 파일 부재")
        
    with open(raw_json_file, "r", encoding="utf-8") as f:
        posts = json.load(f)
        
    client = genai.Client()
    
    # 상위 3개 선별
    top_posts = posts[:3]
    log(f"총 {len(posts)}개 포스트 중 상위 {len(top_posts)}개 주제 선별 완료")
    
    for idx, p in enumerate(top_posts, 1):
        source_name = p.get('source', 'Reddit')
        log(f"\n[{idx}/{len(top_posts)}] [{source_name}] 주제 생성 중: {p['title'][:40]}...")
        
        prompt = f"""
        당신은 상위 1% 전문 IT/비즈니스 테크 블로거이자 소프트웨어 아키텍트입니다.
        아래의 {source_name} 인기 기술 이슈 원본을 분석하여, 공부하는 비개발자나 초보자도 몰입해서 끝까지 읽을 수 있는 최고 품질의 네이버 블로그 기술 포스트를 작성해 주세요.

        [기술 원본 정보]
        - 출처: {source_name}
        - 제목: {p['title']}
        - 작성자: @{p.get('author', 'anonymous')}
        - 좋아요/추천수: {p.get('metrics', {}).get('likes', 0)}
        - 본문: {p.get('content', '')}

        [엄격한 작성 규칙]
        1. 메인 제목(#): 대괄호([IT 트렌드] 등) 없이 독자의 호기심을 자극하는 매력적이고 완성도 높은 한글 제목으로 작성.
        2. 소제목(##): 섹션 헤더에는 이모지(🧠, 💡 등)를 일절 배제하고 텍스트만 작성 (예: ## 1. 문제의 본질과 패러다임 변화).
        3. 시각자료 경로 삽입:
           - 메인 제목 직후: ![메인 아트]({idx}_main.png)
           - 본문 중간: ![아키텍처 도해]({idx}_arch.png)
        4. 비개발자 친화적 비유(Analogy): 어려운 기술 용어나 작동 원리가 나올 때마다 일상적인 친숙한 개념(택배, 주방 요리, 레고 등)에 빗댄 비유 설명을 1개 이상 반드시 결합.
        5. 실전 소스코드 전면 배제: Javascript, C, Python 등의 긴 소스코드는 절대 넣지 말고, 정갈한 한글 의사코드(Pseudocode)와 작동 단계 요약 텍스트 상자(```text ... ```)로 대체.
        6. 비교 테이블(Table): 기존 방식 vs 신규 방식 간의 차이점을 명확히 대조하는 Markdown 표를 최소 1개 이상 작성.
        7. 단계 간 여백: 문단이나 단계가 바뀔 때 시각적 호흡을 위해 '&nbsp;' 줄을 삽입.
        8. 태그: 맨 마지막에 1단어 또는 2단어의 간결한 블로그 검색 태그 10개 내외 작성 (예: `#인공지능` `#클로드` `#테크트렌드` 등).

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
        [포스트 내용 일부]
        {article_md[:1500]}

        [출력 JSON 규격]
        {{
          "badge": "짧은 영문 카테고리 (예: AUTONOMOUS AI / CYBERSECURITY)",
          "title": "한 줄 메인 타이틀 (30자 이내)",
          "subtitle": "설명 서브타이틀 (40자 이내)",
          "steps": [
            "1단계: 핵심 요약 (40자 이내)",
            "2단계: 핵심 요약 (40자 이내)",
            "3단계: 핵심 요약 (40자 이내)",
            "4단계: 핵심 요약 (40자 이내)"
          ]
        }}
        오직 순수 JSON만 출력하세요.
        """
        meta_res = generate_with_retry(client, meta_prompt, model="gemini-3.8-flash")
        meta_json_str = meta_res.text.strip().replace("```json", "").replace("```", "").strip()
        try:
            meta = json.loads(meta_json_str)
        except Exception:
            meta = {
                "badge": "TECH INSIGHT",
                "title": p["title"][:30],
                "subtitle": "최첨단 AI 트렌드 및 실무 아키텍처 분석",
                "steps": [
                    "핵심 원리: 시스템 동작 메커니즘 분석",
                    "실전 적용: 비개발자 친화적 워크플로우 구축",
                    "트레이드오프: 비용 및 리소스 최적화",
                    "미래 가치: 차세대 산업 생태계 파급력"
                ]
            }
            
        # 메인 카드 & 아키텍처 카드 렌더링
        render_diagram_card(meta["title"], meta["subtitle"], meta["badge"], meta["steps"], img1_path)
        render_diagram_card(f"{meta['title']} 구조도", "엔지니어링 파이프라인 및 실행 단계", "ARCHITECTURE", meta["steps"], img2_path)
        log(f"  📸 고해상도 1:1 도해 2종 렌더링 완료 ({os.path.basename(img1_path)}, {os.path.basename(img2_path)})")
        
        # 마크다운 저장 (이미지 경로를 하위 폴더 기준으로 설정)
        article_md = article_md.replace(f"({idx}_main.png)", f"({folder_name}/{idx}_main.png)")
        article_md = article_md.replace(f"({idx}_arch.png)", f"({folder_name}/{idx}_arch.png)")
        
        md_file_path = os.path.join(folder_path, f"{folder_name}.md")
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(article_md)
        log(f"  💾 마크다운 포스트 저장 완료: {os.path.basename(md_file_path)}")

def run_step_3_publish(folder_path):
    log("=======================================================")
    log("🚀 [3단계] 네이버 블로그 스마트에디터 ONE 자동 발행 기동")
    log("=======================================================")
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
    log("🌟 [AI Blog Auto Runner] 무인 전자동 블로그 파이프라인 시작")
    from telegram_notify import send_telegram_alert, format_publish_success_message, format_error_message
    try:
        latest_folder = run_step_1_ingest()
        run_step_2_generate_articles(latest_folder)
        results = run_step_3_publish(latest_folder)
        log("🏆 전체 무인 파이프라인이 성공적으로 완료되었습니다!")
        
        if results:
            msg = format_publish_success_message(results)
            send_telegram_alert(msg)
    except Exception as e:
        err_msg = str(e)
        log(f"❌ 파이프라인 실행 중 오류 발생: {err_msg}")
        send_telegram_alert(format_error_message(err_msg))
        sys.exit(1)

if __name__ == "__main__":
    main()
