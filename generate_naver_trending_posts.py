import os
import sys
import json
import time
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
sys.path.append(ROOT_DIR)

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
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip("'\"")

load_env()
client = genai.Client()

output_dir = os.path.join(ROOT_DIR, "output", "261103_naver_trending")
os.makedirs(output_dir, exist_ok=True)

def render_diagram_card(title, subtitle, badge, steps, output_png_path):
    steps_html = ""
    for idx, s in enumerate(steps, 1):
        steps_html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 18px; background: rgba(255, 255, 255, 0.04); padding: 16px 20px; border-radius: 14px; border-left: 5px solid #38bdf8;">
          <div style="width: 32px; height: 32px; background: #0284c7; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 800; font-size: 16px; margin-right: 18px; color: #ffffff; flex-shrink: 0;">{idx}</div>
          <div style="font-size: 18px; font-weight: 500; color: #f1f5f9; line-height: 1.4;">{s}</div>
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
          <span>Naver Trending Tech Briefing</span>
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

topics = [
    {
        "idx": 1,
        "theme": "네이버 실시간 핫토픽 & 인공지능 검색 혁신",
        "title": "네이버 'AI 탭' 국제표준(ISO 42001) 인증 획득과 에이전틱 AI 검색의 미래",
        "desc": "네이버가 자체 개발한 에이전틱 AI 서비스 'AI 탭'이 국내 최초로 인공지능 경영시스템 국제표준(ISO/IEC 42001) 인증을 획득함. 단순 검색창을 넘어 사용자의 의도를 분석해 대신 업무를 처리하고 예약, 결제, 정보 요약을 자율적으로 수행하는 에이전틱 AI의 신뢰성 및 안전성 확보.",
        "points": [
            "단순 키워드 매칭 검색에서 문제 해결형 에이전트 검색으로의 전환",
            "글로벌 최초 수준의 AI 경영시스템 국제표준(ISO 42001) 획득 배경",
            "사용자 데이터 보안과 환각(Hallucination) 억제 메커니즘",
            "네이버 블로그/쇼핑/예약 생태계와 연동되는 실생활 편익"
        ]
    },
    {
        "idx": 2,
        "theme": "국내 로봇공학 & 휴머노이드 물리 AI 혁신",
        "title": "국내 최초 이족보행 휴머노이드 '데이터 팩토리' 개소와 산업 노동의 대전환",
        "desc": "과학기술정보통신부와 한국기계연구원 등이 주관하여 로봇이 일하는 법을 학습하는 국내 최초 대규모 이족보행 휴머노이드 '데이터 팩토리'를 개소함. 텍스트/이미지 학습을 넘어 실제 물리적 세계에서의 보행, 물건 조작, 균형 제어 데이터를 대량 생산하는 인프라 구축.",
        "points": [
            "두 발로 걷는 인간형 로봇의 가장 큰 난제: 물리적 상호작용 데이터 부족",
            "데이터 팩토리에서 생산되는 모션 캡처 및 촉각/압력 센서 학습 파이프라인",
            "가상 시뮬레이션(Sim2Real)과 실제 공장 환경 데이터의 결합",
            "제조업 강국 대한민국의 산업 현장에 미칠 파급력과 인력 구조 변화"
        ]
    },
    {
        "idx": 3,
        "theme": "국가 첨단 인프라 & 초고성능 슈퍼컴퓨팅",
        "title": "국가 슈퍼컴퓨터 6호기 '한강' 시범서비스 돌입과 대한민국 AI 연산 패권",
        "desc": "한국과학기술정보연구원(KISTI)의 국가 슈퍼컴퓨터 6호기 '한강'이 공식 시범 서비스에 돌입. 기존 5호기(누리온) 대비 압도적인 연산 능력을 갖춘 초고성능 GPU 기반 슈퍼컴퓨터로, 거대언어모델(LLM) 학습, 신약 개발, 기상 이변 예측 등 국가 핵심 연구의 중추 역할 수행.",
        "points": [
            "국가 슈퍼컴퓨터 6호기 '한강'의 스펙과 GPU 클러스터의 압도적 연산력",
            "글로벌 AI 패권 전쟁에서 자체 슈퍼컴퓨팅 인프라가 필수적인 이유",
            "신약 후보물질 발굴 시간 10분의 1 단축 및 기후 재난 예측 정밀도 향상",
            "국내 대학·스타트업·연구기관의 초거대 AI 연구 지원 계획"
        ]
    }
]

log("==================================================================")
log("🚀 네이버 오늘 인기 3대 테크 주제 고품질 블로그 아티클 생성 시작")
log("==================================================================")

for t in topics:
    idx = t["idx"]
    log(f"\n[{idx}/3] [{t['theme']}] 작성 시작: {t['title']}...")

    prompt = f"""
    당신은 대한민국 상위 1% 전문 IT 테크 블로거이자 소프트웨어/시스템 아키텍트입니다.
    네이버 실시간 검색어 및 IT 핫이슈로 가장 뜨겁게 떠오른 아래의 주제를 분석하여, 비개발자나 초보 독자도 흥미진진하게 끝까지 읽을 수 있는 최고 품질의 네이버 블로그 기술 포스트를 작성해 주세요.

    [주제 정보]
    - 카테고리: {t['theme']}
    - 핵심 사건: {t['title']}
    - 상세 개요: {t['desc']}
    - 핵심 논점: {', '.join(t['points'])}

    [엄격한 작성 규칙]
    1. 메인 제목(#): 대괄호([네이버 이슈] 등) 없이, [독자의 호기심이나 궁금증을 자극하는 질문형 오프닝] + [구체적 핵심 기술 키워드] + [반전이나 미래 시사점]의 3단 바이럴 훅 구조로 작성 (예: '# 검색창에 단어만 치던 시대는 끝났다? 네이버 'AI 탭'이 가져올 충격적인 변화와 에이전트의 비밀').
    2. 소제목(##): 섹션 헤더에는 이모지(🧠, 💡 등)를 일절 배제하고 텍스트만 작성 (예: '## 1. 검색의 본질이 바뀌는 패러다임 시프트').
    3. 시각자료 경로 삽입:
       - 메인 제목 직후: ![{t['theme']} 메인]({idx}_main.png)
       - 본문 중간: ![{t['theme']} 도해]({idx}_arch.png)
    4. 비개발자 친화적 비유(Analogy): 어려운 기술 원리가 나올 때마다 일상적인 비유(도서관 사서, 요리 레시피, 택배 배송 등)를 반드시 1개 이상 결합.
    5. 실전 소스코드 전면 배제: Python, C++ 등의 긴 소스코드는 절대 넣지 말고, 직관적인 한글 의사코드(Pseudocode)와 단계 요약 텍스트 상자(```text ... ```)로 대체.
    6. 비교 테이블(Table): 기존 방식 vs 신규 방식 간의 차이점을 명확히 대조하는 Markdown 표를 최소 1개 이상 작성.
    7. 단계 간 여백: 문단이나 단계가 바뀔 때 시각적 호흡을 위해 '&nbsp;' 줄을 삽입.
    8. 태그: 맨 마지막에 1단어 또는 2단어의 간결한 블로그 검색 태그 10개 내외 작성 (예: `#네이버` `#인공지능` `#생성형AI` `#슈퍼컴퓨터` `#로봇` 등).

    [출력 포맷 (반드시 순수 마크다운만 출력)]
    마크다운 시작부터 끝까지 백틱 코드 블록(```markdown)으로 감싸지 말고 순수 마크다운 본문만 그대로 출력하세요.
    """

    res = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
    article_md = res.text.strip()

    # 첫 줄 보정 (# 로 시작하도록)
    lines = article_md.split("\n")
    if lines and not lines[0].startswith("# "):
        lines[0] = f"# {lines[0].lstrip('#').strip()}"
        article_md = "\n".join(lines)

    # 1:1 도해 카드 정보 추출
    meta_prompt = f"""
    다음 블로그 포스트 내용을 바탕으로 인포그래픽 카드에 들어갈 정보를 한글로 추출해 주세요:
    {article_md[:1500]}

    다음 JSON 포맷으로만 응답하세요:
    {{
      "card1": {{
        "badge": "NAVER TREND BRIEFING",
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
    m_res = client.models.generate_content(model="gemini-3.1-flash-lite", contents=meta_prompt)
    m_text = m_res.text.strip()
    if m_text.startswith("```"):
        m_text = m_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
    try:
        meta = json.loads(m_text)
    except Exception:
        meta = {
            "card1": {"badge": "TREND BRIEFING", "title": t["title"][:15], "subtitle": "핵심 기술 트렌드 분석", "steps": t["points"]},
            "card2": {"badge": "SYSTEM ARCHITECTURE", "title": "핵심 프로세스 분석", "subtitle": "작동 메커니즘 단계별 요약", "steps": ["1단계 데이터 수집", "2단계 AI 연산", "3단계 검증", "4단계 실무 적용"]}
        }

    img1_path = os.path.join(output_dir, f"{idx}_main.png")
    img2_path = os.path.join(output_dir, f"{idx}_arch.png")
    c1 = meta["card1"]
    c2 = meta["card2"]
    render_diagram_card(c1["title"], c1["subtitle"], c1["badge"], c1["steps"], img1_path)
    render_diagram_card(c2["title"], c2["subtitle"], c2["badge"], c2["steps"], img2_path)
    log(f"  🎨 [{idx}/3] 1:1 인포그래픽 도해 2장 렌더링 완료")

    md_filename = f"post_{idx}_naver_trending_{idx}.md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(article_md)
    log(f"  ✍️ [{idx}/3] 블로그 포스트 본문 작성 완료 ({len(article_md)}자) ➔ {md_filename}")

log("\n==================================================================")
log("🎉 네이버 인기 주제 블로그 포스트 3편 및 인포그래픽 6장 생성 완료!")
log(f"📁 결과물 저장 경로: {output_dir}")
log("==================================================================")

