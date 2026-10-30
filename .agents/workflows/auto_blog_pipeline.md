---
name: auto_blog_pipeline
description: r/ClaudeAI 인기 포스트 수집(ingest-reddit-posts), 상위 주제별 병렬 딥리서치 및 블로그 포스트 생성(deep_research), 그리고 네이버 블로그(SmartEditor ONE) 자동 포스팅 및 발행(publish-to-naver)을 하나로 연결하는 엔드투엔드 블로그 자동화 파이프라인 워크플로우입니다.
---

# 🤖 AI 블로그 자동화 파이프라인 (auto_blog_pipeline)

이 워크플로우는 Reddit에서 최신 인기 포스트를 수집하고, AI 심층 리서치(Deep Research)를 수행하여 고품질 포스트를 제작한 뒤, **네이버 블로그(SmartEditor ONE)**에 자동으로 이미지를 업로드하고 본문을 발행하는 전체 파이프라인을 끊김 없이 연속으로 실행하기 위한 명세서입니다. (티스토리 듀얼 지원)

---

## 🌀 1. 파이프라인 단계별 흐름 (Pipeline Flow)

```mermaid
graph TD
    A["1단계: Reddit 포스트 수집<br>(/ingest-reddit-posts)"] -->|ingest.md & 폴더 생성| B["2단계: 병렬 딥리서치 & 포스트 생성<br>(/deep_research)"]
    B -->|{주제}.md & {주제}/ 이미지 폴더 생성| C["3단계: 네이버 블로그 자동 업로드 & 포스트 발행<br>(/publish-to-naver)"]
    C -->|완료| D["🎉 최종 네이버 블로그 즉시/임시저장 발행 완료"]
```

---

## 🛠️ 2. 상세 실행 가이드 (Execution Roadmap)

### Phase 1: Reddit 최신 인기글 수집 (`/ingest-reddit-posts`)
1. **타겟 수집**: 지난 24시간 동안 r/ClaudeAI 서브레디트에서 가장 반응이 뜨거웠던 상위 10개 포스트를 크롤링합니다.
2. **폴더 생성**: 수집 시각을 기준으로 `output/{YYMMDD_HHMM}` 형태의 폴더를 생성합니다.
3. **가공 및 저장**: 원문 수집과 함께 한국어 번역 및 5대 핵심 질문을 구성하여 `output/{YYMMDD_HHMM}/ingest.md` 파일로 저장합니다.
4. **실행 명령**:
   ```bash
   node .agents/skills/ingest-reddit-posts/scripts/test_reddit.js
   ```

### Phase 2: 병렬 딥리서치 및 콘텐츠 빌드 (`/deep_research`)
1. **주제 선정**: 수집된 `ingest.md` 내용 중 가장 파급력이 크고 블로깅하기 적합한 **상위 3개 핵심 주제**를 선별합니다.
2. **NotebookLM 기반 딥리서치**: 각 주제별로 가상 노트북을 생성한 후 `mode="deep"`, `source="web"`으로 병렬 딥리서치를 기동합니다.
3. **콘텐츠 생성**: 비개발자 친화적인 톤앤매너 규칙(실전 소스코드 배제, 의사코드 및 비교 테이블 활용)을 준수하며 `{주제}.md` 포스트를 집필하고, 필요한 본문 삽화 및 학술 도해 이미지를 생성하여 `{주제}/` 하위 경로에 패키징합니다.
   * 저장 경로: `output/{YYMMDD_HHMM}/{주제}.md`
   * 이미지 경로: `output/{YYMMDD_HHMM}/{주제}/{이미지_이름}.png`

### Phase 3: 네이버 블로그 자동 업로드 및 발행 (`/publish-to-naver`)
1. **사전 준비**: 1회용 브라우저 세션을 실행하여 네이버 로그인 및 세션 파일(`naver_session.json`)을 적재합니다. (최초 1회만 수행)
   ```bash
   naver_login.bat
   # 또는 python .agents/skills/publish-to-naver/scripts/naver_login.py
   ```
2. **SmartEditor ONE 자동 본문 주입 및 이미지 첨부 발행**:
   각 포스트별 마크다운을 네이버 에디터용 HTML로 변환하여 주입하고, 로컬 다이어그램 삽화들을 `file_chooser`로 자동 첨부한 뒤 태그 입력 및 최종 공개 발행을 수행합니다.
   ```bash
   # 예시: 1번째 주제 발행 (--publish 옵션 시 즉시 공개 발행, 미지정 시 임시저장)
   python .agents/skills/publish-to-naver/scripts/naver_publish.py \
     --md-file "output/{YYMMDD_HHMM}/{주제}.md" \
     --publish --headed

   # 예시: 2번째 주제 발행
   python .agents/skills/publish-to-naver/scripts/naver_publish.py \
     --md-file "output/{YYMMDD_HHMM}/{주제}.md" \
     --publish --headed

   # 예시: 3번째 주제 발행
   python .agents/skills/publish-to-naver/scripts/naver_publish.py \
     --md-file "output/{YYMMDD_HHMM}/{주제}.md" \
     --publish --headed
   ```

> **참고**: 티스토리 블로그 발행을 원하는 경우 `.agents/skills/publish-to-tistory` 스킬을 사용하여 듀얼 발행도 가능합니다.

---

## 📏 3. 파이프라인 무결성 체크리스트 (Verification)
- [ ] `ingest.md`가 정상적으로 빌드되었고 한글 번역 및 딥리서치 질문이 풍부하게 들어가 있는가?
- [ ] 딥리서치 결과로 생성된 `{주제}.md`에 비개발자 가이드라인(소스코드 배제, 의사코드 대체, 학술 도해 포함)이 충실히 적용되었는가?
- [ ] 각 주제별 폴더에 생성된 시각자료 이미지 파일들이 마크다운 내 이미지 링크 경로와 칼같이 일치하는가?
- [ ] 디버깅용 크롬 브라우저(Port 9223)가 정상 작동 중이며 티스토리 로그인이 유지되어 있는가?
- [ ] 포스트들의 예약 발행 간격(딜레이 시간)이 겹치지 않도록 적절히 분산 설계되었는가?
