---
name: publish-to-tistory
description: Playwright를 사용하여 마크다운 포스트와 이미지를 로컬 크롬 디버깅 포트(9223)를 통해 티스토리에 자동 업로드 및 즉시/예약 발행하는 스킬입니다.
---

# 📝 티스토리 자동 포스팅 스킬 (publish-to-tistory)

이 스킬은 작성된 마크다운 초안과 썸네일 이미지를 사용하여 본인의 티스토리 블로그(`https://{your-blog-name}.tistory.com/`)에 자동으로 포스팅하거나 예약 발행하는 역할을 수행합니다.

## 1. 사전 요구사항 (Requirements)
* **환경 변수 세팅**: 프로젝트 루트의 `.env` 파일에 `TISTORY_BLOG_NAME` 값을 설정해야 합니다. (예: `nam-ai.tistory.com`인 경우 `nam-ai` 입력)
  ```env
  TISTORY_BLOG_NAME=your-blog-name
  ```
* **Node.js 패키지**: `axios`, `form-data` 설치 (`npm install`)
* **Playwright**: `playwright` 라이브러리가 필요합니다. (`pip install playwright`)
* **디버깅 브라우저 기동**: `python .agents/skills/publish-to-tistory/scripts/setup_tistory.py` 스크립트를 사전에 실행하여 디버깅 포트 **9223**으로 구동 중이어야 하며, 해당 크롬 브라우저 상에서 티스토리에 로그인이 완료되어 있어야 합니다.

## 2. 사용 방법 (Usage)

티스토리 포스팅은 **[1단계] 이미지 업로드 & 본문 치환**과 **[2단계] 에디터 자동 발행**의 2단계로 진행됩니다.

### [1번째 글: 2시간 후 예약 발행 예시]
```bash
# 1단계: 본문 이미지 다이렉트 업로드 및 치환
node .agents/skills/publish-to-tistory/scripts/upload_images.js --md-file "output/260602_0106/opus_minebench.md"

# 2단계: 에디터 본문 주입 및 대표 이미지 업로드하여 2시간 후 예약 발행
python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
  --md-file "output/260602_0106/opus_minebench_replaced.md" \
  --image "output/260602_0106/opus_minebench/minebench_illustration.png" \
  --delay-hours 2
```

### [2번째 글: 4시간 후 예약 발행 예시]
```bash
# 1단계: 본문 이미지 다이렉트 업로드 및 치환
node .agents/skills/publish-to-tistory/scripts/upload_images.js --md-file "output/260602_0106/production_ready_ai.md"

# 2단계: 에디터 본문 주입 및 4시간 후 예약 발행
python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
  --md-file "output/260602_0106/production_ready_ai_replaced.md" \
  --image "output/260602_0106/production_ready_ai/production_ai_illustration.png" \
  --delay-hours 4
```

### [3번째 글: 6시간 후 예약 발행 예시]
```bash
# 1단계: 본문 이미지 다이렉트 업로드 및 치환
node .agents/skills/publish-to-tistory/scripts/upload_images.js --md-file "output/260602_0106/sf_equity_real_estate.md"

# 2단계: 에디터 본문 주입 및 6시간 후 예약 발행
python .agents/skills/publish-to-tistory/scripts/tistory_publish.py \
  --md-file "output/260602_0106/sf_equity_real_estate_replaced.md" \
  --image "output/260602_0106/sf_equity_real_estate/sf_house_equity_illustration.png" \
  --delay-hours 6
```

## 3. 핵심 자동화 로직
1. **이미지 사전 업로드 (Axios)**: `.agents/skills/publish-to-tistory/scripts/upload_images.js`에서 본문 내 로컬 이미지 경로를 정규식으로 수집해 Tistory attach API로 다이렉트 업로드합니다. 반환된 key 정보로 `[##_Image|kage@...|_##]` 카카오 CDN 치환 태그를 만들어 본문 내용을 사전에 변경해 둡니다.
2. **CDP 연결**: `127.0.0.1:9223`으로 디버깅 크롬 세션에 연결합니다.
3. **글쓰기 페이지 이동**: 블로그 관리자 글쓰기 주소로 진입합니다. (이때 생성되는 임시저장 불러오기 팝업 등은 브라우저 대화상자 핸들러를 통해 자동으로 취소 처리됩니다.)
4. **카테고리**: `🔬 Deep Research : AI & 자동화` 카테고리를 선택합니다.
5. **마크다운 모드 전환**: 상단 에디터 툴바에서 모드를 마크다운으로 전환하고 경고 팝업이 뜨면 확인(Confirm)합니다.
6. **제목 & 본문 입력**: 치환 완료된 마크다운 파일 첫 행을 제목으로 파싱하여 입력하고, 나머지 본문을 본문 영역에 붙여넣습니다.
7. **태그 입력**: 파일 하단에서 태그 목록을 추출하여 태그 입력란에 하나씩 입력 후 엔터를 쳐서 등록합니다.
8. **모달 및 대표이미지 업로드**: 완료 버튼을 누르고 나타나는 발행 팝업에서 대표이미지(썸네일) 영역을 클릭해 지정된 이미지를 업로드합니다.
9. **예약 설정 및 발행**: 즉시 발행의 경우 `현재`를, 예약의 경우 `예약`을 누르고 날짜 및 시/분을 계산해 셋팅한 뒤 최종 `공개 발행` 버튼을 누릅니다.
