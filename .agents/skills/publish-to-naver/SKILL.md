---
name: publish-to-naver
description: Playwright를 사용하여 네이버 스마트에디터 ONE(SmartEditor ONE)에 마크다운 기반 고품질 기술 포스트와 이미지를 자동 업로드하고 즉시/예약 발행하는 스킬입니다.
---

# 🟢 네이버 블로그 자동 포스팅 스킬 (publish-to-naver)

이 스킬은 작성된 블로그 콘텐츠와 이미지 에셋들을 **네이버 블로그(`https://blog.naver.com/{NAVER_BLOG_ID}`)**의 스마트에디터 ONE에 자동으로 업로드하고 즉시 발행하거나 예약 포스팅하는 역할을 수행합니다.

## 1. 사전 요구사항 (Requirements)
* **환경 변수 세팅**: `.env` 파일에 네이버 계정 정보를 설정해야 합니다.
  ```env
  NAVER_ID=your_naver_id
  NAVER_PASSWORD=your_naver_password
  NAVER_BLOG_ID=your_naver_blog_id (보통 NAVER_ID와 동일)
  ```
* **Python 라이브러리**: `playwright`, `pyperclip` 필요 (`pip install playwright pyperclip`)
* **영구 세션 파일**: 최초 1회 `python .agents/skills/publish-to-naver/scripts/naver_login.py`를 실행하여 캡차를 우회하고 `naver_session.json`을 저장해야 합니다.

## 2. 사용 방법 (Usage)

### [단일 포스트 즉시 발행 예시]
```bash
python .agents/skills/publish-to-naver/scripts/naver_publish.py \
  --md-file "output/261025_0745/단일_에이전트_루프_아키텍처.md" \
  --image "output/261025_0745/단일_에이전트_루프_아키텍처/single_agent_main.jpg"
```

## 3. 핵심 아키텍처
1. **클립보드 방식 캡차 우회 (`naver_login.py`)**: 키로거 방지 보안을 우회하여 `Ctrl+C ➔ Ctrl+V`로 로그인 후 `storage_state="naver_session.json"` 저장.
2. **스마트에디터 ONE 블록 주입 (`naver_publish.py`)**:
   - 팝업(도움말, 임시저장) 자동 취소 처리
   - 제목 입력란 타겟팅 및 키워드 주입
   - 본문 단락 블록, 인용구 블록, 소제목 서식 자동 적용
   - 로컬 이미지 파일들을 에디터에 순차 업로드
   - 태그 입력 및 최종 발행 버튼 클릭
