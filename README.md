# 🤖 blog_auto - AI Blog Automation Ingestion Engine

> **인공지능 개발 트렌드의 노다지인 r/ClaudeAI 서브레디트에서 실시간 핫 이슈 10개를 긁어모아, 번역 및 딥리서치 질문이 탑재된 `ingest.md` 구조로 빌드해 주는 수집 엔진입니다.**
> 본 프로젝트는 개발 파트너 에이전트(Antigravity)와 유저가 실시간 피드백을 통해 함께 튜닝하며 완성한 고품격 프로덕션 아키텍처를 따르고 있습니다.

---

## 📂 프로젝트 핵심 폴더 구조

```bash
blog_auto/
├── .agents/
│   └── skills/
│       ├── ingest-reddit-posts/
│       │   ├── SKILL.md         # 🌀 Reddit 수집 스킬 정식 명세 가이드
│       │   └── scripts/         # 🛠️ Apify Scraper 제어 및 3단 가공 핵심 엔진
│       │       ├── reddit_posts.js
│       │       └── test_reddit.js
│       ├── deep_research/
│       │   ├── SKILL.md         # 🔬 NotebookLM 기반 병렬 딥리서치 가이드
│       │   └── references/
│       │       └── template_guide.md # 📋 비개발자 친화적 포스팅 레이아웃 가이드
│       └── publish-to-tistory/
│           ├── SKILL.md         # 📝 티스토리 자동 포스팅 스킬 명세 가이드
│           └── scripts/         # 📤 티스토리 자동 기동, 업로더 및 포스팅 스크립트
│               ├── setup_tistory.py
│               ├── upload_images.js
│               └── tistory_publish.py
├── output/                      # 📂 수집 및 리서치 결과물 디렉토리
│   └── {YYMMDD_HHMM}/
│       ├── ingest.md            # 📝 번역과 딥리서치 질문이 탑재된 최종 아웃풋
│       ├── {주제}.md            # ✍️ 최종 생성된 비개발자 친화적 블로그 포스트
│       └── {주제}/              # 🎨 포스트별 생성 삽화 및 학술 도해 패키지
├── logger.js                    # 🎨 컬러 데코레이션 로그 유틸리티
├── history.md                   # 🗓️ 세션별 성과 및 다음 작업 누적 기록 파일
├── plan_checklist.md            # 📋 단계별 개발 체크리스트 마일스톤
├── README.md                    # 📖 본 프로젝트 종합 설명서 (본 파일)
└── AGENTS.md                    # 🧠 에이전트 협업 아키텍처 설계 정리서
```

---

## ⚙️ 핵심 파이프라인 작동 메커니즘

### 1. 차단 우회 및 타겟 채널
* **대상 서브레디트**: `r/ClaudeAI` (`https://www.reddit.com/r/ClaudeAI/top/?t=day`)
* Reddit의 변칙적인 검색창 UI 변경 및 봇 감지 우회를 위해, **Direct Subreddit Top URL**을 타겟으로 잡았습니다.
* `t=day` 옵션을 통해 Reddit 서버 자체에서 지난 24시간 동안 추천수가 가장 뜨거웠던 최고 존엄 인기 글들을 정렬하여 받아옵니다.
* 데이터셋 한도(`maxPostsCount`)는 비용 효율성과 간결함을 위해 정확히 **10개**로 타이트하게 설정되어 있습니다.

### 2. KST(한국 표준시) 기준 정밀 날짜 추적
* Node.js 백엔드 서버 환경의 기본 시간대(UTC)와 한국 시각의 시차(9시간) 오류를 원천 차단하기 위해 **KST 강제 시간 변환 헬퍼**(`getKstDateString`)를 구현했습니다.
* 매 기동 시 로컬 실시간 날짜 기준 어제 날짜(D-1 KST)를 완벽하게 역추적하여 로그를 기록합니다.

### 3. 미디어 필터링
* 텍스트 분석 및 딥리서치의 퀄리티를 위해, 본문 인지가 불가능한 **동영상 포스트(postType이 video이거나 v.redd.it 링크 등)는 수집 단계에서 원천 필터링하여 제외**합니다.

### 4. `ingest.md` 3단 조립 아키텍처
최종 빌드되는 마크다운 포맷은 아래의 3대 핵심 구조로 구성되어 나중에 깊이 있는 테크 딥리서치를 기동하기에 최적의 소스를 제공합니다.
* **🇺🇸 [1] 원본 내용 (Original Content)**: 영문 본문 고스란히 보존.
* **🇰🇷 [2] 한국어 번역 (Korean Translation)**: 매끄럽고 직관적인 기술 번역.
* **🧠 [3] 딥리서치 질문 내용 (Deep-Dive Research Questions)**: 나중에 딥리서치를 활성화할 수 있도록 아래 5대 주제별 구조적 질문 도출 (내용이 빈약할 시 조절).
  1. *기술적 본질 및 아키텍처 검증*
  2. *인사이트*
  3. *트레이드 오프 및 병목 구간 진단*
  4. *미래가치*
  5. *실전 구현 제안*

### 5. NotebookLM MCP 기반 병렬 딥리서치 및 비개발자 친화적 포스팅 생성
* **병렬 딥리서치**: `ingest.md`에서 도출된 상위 3개 주요 IT 이슈에 대해 개별 노트북 생성 및 동시 딥리서치 기동.
* **실전 소스코드 배제**: 비개발자 독자의 읽기 피로감을 줄이기 위해 Javascript, Solidity 등의 **실전 소스코드를 전면 삭제**.
* **의사코드(Pseudocode) 대체**: 핵심 비즈니스 로직과 작동 원리는 비개발자도 직관적으로 파악할 수 있는 **한글 의사코드** 및 개념적 비유로 대체 서술.
* **시각 에셋 패키징**: 글의 전문성과 신뢰도를 위해 각 포스트당 1:1 비율의 **일반 삽화 1개 및 학술 도해 3개**를 생성하여 폴더별로 패키징.

---

## 🚀 실행 및 테스트 방법

### 1. 의존성 설치 (Dependencies)
이 프로젝트는 Node.js와 Python(Playwright 제어용)을 함께 활용합니다. 다른 환경에서 새로 다운로드하여 실행할 때는 아래 명령어를 통해 필요한 라이브러리를 모두 설치해 줍니다.

**Node.js 패키지 설치 (npm)**
```bash
npm install
```
(이 명령어를 실행하면 `package.json`에 명시된 `axios`와 `form-data` 라이브러리가 포함된 `node_modules` 폴더가 자동으로 생성되고 설치됩니다.)

**Python 패키지 & Playwright 브라우저 설치**
```bash
pip install playwright
playwright install chromium
```

### 2. 환경 변수 세팅 (`.env`)
프로젝트 루트 경로에 `.env` 파일을 생성하고 아래와 같이 환경 변수를 입력합니다.
```env
APIFY_TOKEN_REDDIT=your_apify_token_here
TISTORY_BLOG_NAME=your_tistory_blog_name
```
- `APIFY_TOKEN_REDDIT`: Apify API 토큰
- `TISTORY_BLOG_NAME`: 티스토리 블로그 서브도메인 이름 (예: `your-blog.tistory.com`인 경우 `your-blog` 입력)

### 통합 실증 러너 구동
터미널에서 아래 명령을 실행하면 자동으로 Apify Scraper가 기동되어 데이터를 폴링하고, 최종 마크다운 아웃풋을 `output` 폴더에 생성합니다.
```bash
node .agents/skills/ingest-reddit-posts/scripts/test_reddit.js
```

### 티스토리 자동 포스팅 파이프라인 구동
1. **디버깅 크롬 기동 및 Tistory 로그인** (최초 1회 로그인 완료 필요):
   ```bash
   python .agents/skills/publish-to-tistory/scripts/setup_tistory.py
   ```
2. **본문 이미지 업로드 및 마크다운 치환** (백엔드 attach API 호출):
   ```bash
   node .agents/skills/publish-to-tistory/scripts/upload_images.js --md-file "output/260602_0106/opus_minebench.md"
   ```
3. **에디터 본문 주입 및 자동 발행** (2, 4, 6시간 후 예약):
   ```bash
   # 1번째 글: 2시간 후 예약 발행
   python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
     --md-file "output/260602_0106/opus_minebench_replaced.md" \
     --image "output/260602_0106/opus_minebench/minebench_illustration.png" \
     --delay-hours 2

   # 2번째 글: 4시간 후 예약 발행
   python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
     --md-file "output/260602_0106/production_ready_ai_replaced.md" \
     --image "output/260602_0106/production_ready_ai/production_ai_illustration.png" \
     --delay-hours 4

   # 3번째 글: 6시간 후 예약 발행
   python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
     --md-file "output/260602_0106/sf_equity_real_estate_replaced.md" \
     --image "output/260602_0106/sf_equity_real_estate/sf_house_equity_illustration.png" \
     --delay-hours 6
   ```

---

## 🤝 라이선스 및 협업 규칙
* 본 프로젝트 내부의 코드를 추가 튜닝하거나 후속 RAG/딥리서치 단계를 개발할 때는 반드시 `history.md`에 누적(Append)하여 이력을 남기고, `.agents/skills/` 폴더 하위의 가이드를 기준으로 기동해 주시기 바랍니다.

---

## 💡 AI 에이전트와 페어 프로그래밍으로 사용하는 방법 (개발 꿀팁)

이 프로젝트는 Antigravity 또는 Claude Code와 같은 AI 개발 파트너 에이전트와 함께 사용할 때 진가를 발휘합니다. 아래처럼 대화창에 간편하게 한마디만 남기면 복잡한 과정 없이 알아서 처리해 줍니다.

### 1. 원클릭 파이프라인 기동하기 (`/auto_blog_pipeline`)
Reddit 수집부터 NotebookLM 병렬 딥리서치, 티스토리 예약 발행까지의 전 과정을 원클릭으로 기동하고 싶을 때는 에이전트 대화창에 다음과 같이 요청해 보세요.
> **"여기서 `/auto_blog_pipeline` 워크플로우 켜서 전체 진행해줘."**
에이전트가 워크플로우 명세를 자동으로 인식하여, 필요한 스크립트들을 순차적 혹은 병렬로 실행하고 최종 결과를 보고해 줍니다.

### 2. 크롤링 타겟 주제 및 채널 손쉽게 바꾸기
만약 수집 타겟 서브레디트나 다른 주제로 변경하고 싶다면, 코드를 직접 고칠 필요 없이 에이전트에게 말로 요청해 보세요.
> **"에피파이에 수집할 서브레디트 주제를 r/ChatGPTCoding으로 바꿀 건데 변경해줘."**
에이전트가 수집 스크립트(`.agents/skills/ingest-reddit-posts/scripts/reddit_posts.js`)의 Payload 구조를 분석하고 안전하게 타겟 주소를 수정해 줍니다.


