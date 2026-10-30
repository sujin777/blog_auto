import argparse
import os
import sys
import time
import re
import json
import base64
import mimetypes
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def load_env():
    # .env 파일 위치를 찾아 환경변수 설정
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            os.environ[key] = val
                break
            except Exception as e:
                print(f"⚠️ 환경 변수 설정 중 오류 발생: {e}")

load_env()
raw_blog_name = os.environ.get("TISTORY_BLOG_NAME", "jini71")
TISTORY_BLOG_NAME = raw_blog_name.replace(".tistory.com", "").strip()

def parse_markdown(md_file_path):
    if not os.path.exists(md_file_path):
        print(f"❌ 마크다운 파일이 존재하지 않습니다: {md_file_path}")
        sys.exit(1)
        
    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.strip().split("\n")
    
    # 1. 제목 파싱 (첫 번째 #으로 시작하는 라인)
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
            
    # 2. 태그 파싱 (### 태그 아래 라인 또는 맨 마지막 부근의 패턴)
    tags = []
    tag_header_idx = -1
    for i, line in enumerate(lines):
        if line.strip() in ["### 태그", "### Tags"]:
            tag_header_idx = i
            break
            
    if tag_header_idx != -1 and tag_header_idx < len(lines) - 1:
        for idx in range(tag_header_idx + 1, len(lines)):
            tag_line = lines[idx].strip()
            if not tag_line:
                continue
            if "`" in tag_line:
                tags = re.findall(r"`([^`]+)`", tag_line)
            elif "," in tag_line:
                tags = [t.strip() for t in tag_line.split(",") if t.strip()]
            elif tag_line.startswith("#"):
                # #태그1 #태그2 형태 파싱
                tags = [t.replace("#", "").strip() for t in tag_line.split() if t.strip()]
            else:
                tags = [tag_line]
            if tags:
                break

    if not tags:
        for line in reversed(lines):
            line_str = line.strip()
            if not line_str:
                continue
            if "`" in line_str and "," in line_str:
                tags = re.findall(r"`([^`]+)`", line_str)
                if tags:
                    break
            elif line_str.startswith("#") and not line_str.startswith("# "):
                # #태그1 #태그2 형태 파싱 (H1 제목인 '# '은 제외해야 함)
                tags = [t.replace("#", "").strip() for t in line_str.split() if t.strip()]
                if tags:
                    break
            elif "," in line_str and not any(line_str.startswith(prefix) for prefix in ["#", "*", "-", "!", ">", "[", "http"]):
                parts = [t.strip() for t in line_str.split(",") if t.strip()]
                if 2 <= len(parts) <= 15 and all(len(p) < 25 for p in parts):
                    tags = parts
                    break

    # 기본 고정 태그 주입 및 중복 제거
    default_tags = ["클로드코드", "안티그래비티", "코덱스", "바이브코딩"]
    clean_tags = []
    for t in tags:
        t_clean = t.strip()
        # 특수문자로만 되어있거나 문장 형태인 것 필터링
        if t_clean and not re.match(r'^[│\s└─>\-]+$', t_clean) and len(t_clean) < 20:
            clean_tags.append(t_clean)
            
    final_tags = default_tags.copy()
    for t in clean_tags:
        if t not in final_tags:
            final_tags.append(t)
            
    tags = final_tags
                
    # 3. 본문 파싱
    tag_header_idx = -1
    for i, line in enumerate(lines):
        if line.strip() in ["### 태그", "### Tags"]:
            tag_header_idx = i
            break
            
    content_lines = lines
    if tag_header_idx != -1:
        content_lines = lines[:tag_header_idx]
        
    first_title_idx = -1
    for i, line in enumerate(content_lines):
        if line.startswith("# "):
            first_title_idx = i
            break
            
    if first_title_idx != -1:
        body_lines = content_lines[first_title_idx + 1:]
    else:
        body_lines = content_lines
        
    body_content = "\n".join(body_lines).strip()
    
    return title, body_content, tags

def run(md_file, image_file, delay_hours):
    title, body, tags = parse_markdown(md_file)
    md_dir = os.path.dirname(md_file)
    
    print(f"📝 마크다운 파싱 결과:")
    print(f"  - 제목: {title}")
    print(f"  - 태그 ({len(tags)}개): {', '.join(tags)}")
    print(f"  - 본문 크기: {len(body)} 자")
    
    with sync_playwright() as p:
        print("🔌 브라우저 세션 연결 중...")
        context = None
        session_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tistory_session.json")
        
        # 1. 영구 세션 파일이 존재하면 즉시 로드 (100% 무인 자동화 모드)
        if os.path.exists(session_file):
            print(f"✨ [영구 세션 감지] {session_file} 로드 중...")
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(storage_state=session_file, no_viewport=True)
            print("🚀 저장된 카카오/티스토리 세션으로 즉시 진입합니다! (로그인 생략)")
        else:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9223")
                contexts = browser.contexts
                context = contexts[0] if contexts else browser.new_context()
                print("  - 기존 9223 디버깅 포트에 연결 성공")
            except Exception:
                profile_path = os.path.expanduser("~/tmp/chrome-debug-tistory")
                print(f"  - 9223 포트 미발견. 전용 프로필({profile_path})로 Chrome 직접 기동...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=profile_path,
                    headless=False,
                    channel="chrome",
                    args=[
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized"
                    ],
                    no_viewport=True
                )
        
        # 기존 탭들 중 티스토리 도메인을 열고 있는 탭이 있다면 재사용
        page = None
        for p_tab in context.pages:
            if "tistory.com" in p_tab.url:
                page = p_tab
                print(f"♻️ 기존 티스토리 탭 재사용: {page.url}")
                break
                
        if not page:
            page = context.new_page()
            print("🆕 새 탭 생성")
        
        # 1. 페이지 로딩 즉시 경고창(임시저장 팝업 등) 자동 승인/취소 핸들러 등록
        def handle_dialog(dialog):
            print(f"💬 다이얼로그 감지: {dialog.message}")
            try:
                if "저장된 글" in dialog.message or "저장된" in dialog.message or "이어서" in dialog.message:
                    dialog.dismiss() # '취소'를 눌러 임시저장 본문을 무시하고 새 글로 시작
                    print("  - 임시저장 글 불러오기 취소 (새 글 작성 시작)")
                else:
                    dialog.accept() # 작성 모드 변경 등의 경고창은 '확인'을 눌러야 마크다운 모드로 전환됨!
                    print("  - 다이얼로그 허용(accept)")
            except Exception as d_err:
                print(f"  - 다이얼로그 처리 중 에러 발생 (이미 처리되었을 수 있음): {d_err}")
                
        page.on("dialog", handle_dialog)
        
        try:
            print("🌐 티스토리 글쓰기 페이지로 이동 중...")
            page.goto(f"https://{TISTORY_BLOG_NAME}.tistory.com/manage/newpost/?type=post&returnURL=%2Fmanage%2Fposts%2F")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 카카오/티스토리 로그인 리다이렉트 감지 시 대기
            if any(k in page.url for k in ["auth", "login", "kakao"]):
                print("🔑 티스토리 로그인이 필요합니다. 화면에 열린 창에서 카카오 계정으로 로그인해 주세요...")
                # 팝업 탭 리스너 등록
                popup_page = None
                def on_page(new_p):
                    nonlocal popup_page
                    popup_page = new_p
                    print(f"📑 새 탭/팝업 감지: {new_p.url}")
                context.on("page", on_page)
                
                try:
                    kakao_btn = page.locator("a.btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
                    if kakao_btn.is_visible():
                        print("👉 [카카오계정으로 로그인] 버튼 자동 클릭...")
                        kakao_btn.click()
                        time.sleep(2)
                except Exception:
                    pass
                
                # 로그인 대상 페이지 결정 (팝업이 떴으면 팝업, 아니면 메인)
                target_p = popup_page if popup_page else page
                
                # .env에 카카오 계정 정보가 설정되어 있는 경우 자동 로그인 입력 수행
                kakao_email = os.environ.get("KAKAO_EMAIL", "").strip()
                kakao_pw = os.environ.get("KAKAO_PASSWORD", "").strip()
                if kakao_email and kakao_pw:
                    print(f"🤖 .env 계정 정보로 카카오 자동 로그인 시도 중... ({kakao_email})")
                    try:
                        time.sleep(1.5)
                        # 혹시 팝업이 늦게 떴을 수 있으니 재확인
                        target_p = popup_page if popup_page else page
                        target_p.wait_for_load_state("domcontentloaded")
                        
                        id_inp = target_p.locator('input[name="loginId"], #loginId--1, #loginKey--1, input[type="text"]').first
                        if id_inp.is_visible():
                            id_inp.fill(kakao_email)
                            time.sleep(0.3)
                        pw_inp = target_p.locator('input[name="password"], #password--2, input[type="password"]').first
                        if pw_inp.is_visible():
                            pw_inp.fill(kakao_pw)
                            time.sleep(0.3)
                        submit_btn = target_p.locator('button.btn_g.highlight.submit, button[type="submit"]').first
                        if submit_btn.is_visible():
                            submit_btn.click()
                            print("🚀 로그인 정보 제출 완료! 세션 전환 대기 중...")
                            time.sleep(3)
                            
                        # 스크린샷 저장
                        try:
                            target_p.screenshot(path="output/login_debug.png")
                            print(f"📸 현재 로그인 화면 스크린샷 저장: output/login_debug.png (URL: {target_p.url})")
                        except Exception:
                            pass
                            
                        # 캡차 자동 해결 시도
                        try:
                            time.sleep(1)
                            body_text = target_p.content()
                            if "DKAPTCHA" in body_text or "문제에 답해 주세요" in body_text or "지도에서 눌러주세요" in body_text:
                                print("🧩 카카오 지도 보안 캡차 감지! 자동 해결을 시도합니다...")
                                time.sleep(1)
                                if "새마을방앗간" in body_text:
                                    print("👉 '새마을방앗간' 마커 좌표 (1085, 450) 클릭 시도...")
                                    target_p.mouse.click(1085, 450)
                                    time.sleep(1)
                                elif "화장실" in body_text:
                                    print("👉 '화장실' 마커 좌표 (920, 370) 클릭 시도...")
                                    target_p.mouse.click(920, 370)
                                    time.sleep(1)
                                elif "S-OIL" in body_text or "s-oil" in body_text.lower():
                                    print("👉 'S-OIL' 마커 좌표 (830, 330) 클릭 시도...")
                                    target_p.mouse.click(830, 330)
                                    time.sleep(1)
                                elif "일산종합상사" in body_text:
                                    print("👉 '일산종합상사' 마커 좌표 (1050, 340) 클릭 시도...")
                                    target_p.mouse.click(1050, 340)
                                    time.sleep(1)
                                    
                                submit_cap = target_p.locator('button:has-text("답변 제출"), button:has-text("제출")').first
                                if submit_cap.is_visible():
                                    submit_cap.click()
                                    print("🚀 캡차 답변 제출 클릭 완료!")
                                    time.sleep(3)
                                    target_p.screenshot(path="output/login_debug.png")
                        except Exception as cap_err:
                            print(f"⚠️ 캡차 처리 중 오류: {cap_err}")
                            
                        # 추가 버튼 처리: '다음에 변경' 또는 '계속하기' 또는 '동의'
                        time.sleep(2)
                        target_p = popup_page if popup_page else page
                        for extra_sel in [
                            "button:has-text('다음에')", "a:has-text('다음에 변경')",
                            "button:has-text('동의하고 계속하기')", "button:has-text('동의')",
                            "button:has-text('확인')", "button.btn_confirm"
                        ]:
                            try:
                                extra_btn = target_p.locator(extra_sel).first
                                if extra_btn.is_visible():
                                    print(f"👉 추가 확인 버튼 감지 및 자동 클릭: {extra_sel}")
                                    extra_btn.click()
                                    time.sleep(2)
                                    target_p.screenshot(path="output/login_debug.png")
                            except Exception:
                                pass
                    except Exception as al_err:
                        print(f"⚠️ 자동 로그인 필드 입력 중 오류: {al_err}")
                
                # 쿠키 및 세션 실시간 감지 (최대 180초)
                login_success = False
                start_wait = time.time()
                while time.time() - start_wait < 180:
                    time.sleep(2)
                    # 스크린샷 갱신
                    try:
                        active_p = popup_page if popup_page else page
                        active_p.screenshot(path="output/login_debug.png")
                    except Exception:
                        pass
                    # 활성 탭 URL 또는 쿠키 검사
                    current_urls = [p_curr.url for p_curr in context.pages]
                    cookies = context.cookies()
                    has_session = any(c.get("name") in ["TSSESSION", "TI_SEC", "_T_LOGIN"] for c in cookies)
                    url_passed = any("manage" in u or ("tistory.com" in u and "login" not in u and "kakao" not in u) for u in current_urls)
                    
                    if has_session or url_passed:
                        print("✓ 카카오 로그인 성공 감지! 글쓰기 페이지로 다시 이동합니다...")
                        login_success = True
                        break
                        
                if not login_success:
                    print("❌ 로그인 대기 시간 초과로 작업을 중단합니다.")
                    return
                    
                page.goto(f"https://{TISTORY_BLOG_NAME}.tistory.com/manage/newpost/?type=post&returnURL=%2Fmanage%2Fposts%2F")
                page.wait_for_load_state("networkidle")
                time.sleep(2)
            
            # [동적 업로드] 본문 로컬 이미지 수집 및 브라우저 세션 다이렉트 업로드/치환 로직
            image_pattern = r'!\[(.*?)\]\((.*?)\)'
            matches = re.findall(image_pattern, body)
            
            # 필터링: 외부 URL 제외한 로컬 이미지 경로만 골라내기
            local_images = []
            for alt, img_path in matches:
                if not img_path.startswith("http://") and not img_path.startswith("https://"):
                    local_images.append((alt, img_path))
            
            if local_images:
                print(f"📡 본문 내 로컬 이미지 {len(local_images)}개 감지. 브라우저 세션 다이렉트 업로드 및 치환 기동...")
                for alt, img_path in local_images:
                    abs_img_path = img_path
                    if not os.path.isabs(img_path):
                        abs_img_path = os.path.abspath(os.path.join(md_dir, img_path))
                    
                    if not os.path.exists(abs_img_path):
                        print(f"⚠️ 경고: 이미지 파일을 찾을 수 없습니다: {abs_img_path}")
                        continue
                        
                    # base64 변환
                    mime_type, _ = mimetypes.guess_type(abs_img_path)
                    if not mime_type:
                        mime_type = "image/png"
                    with open(abs_img_path, "rb") as img_f:
                        base64_data = base64.b64encode(img_f.read()).decode("utf-8")
                    data_uri = f"data:{mime_type};base64,{base64_data}"
                    filename = os.path.basename(abs_img_path)
                    
                    print(f"📤 업로드 중: {filename}...")
                    
                    # 브라우저 내부 fetch() API 호출
                    upload_js = """
                    async (args) => {
                        const dataUri = args[0];
                        const fname = args[1];
                        const parts = dataUri.split(',');
                        const mime = parts[0].match(/:(.*?);/)[1];
                        const bstr = atob(parts[1]);
                        let n = bstr.length;
                        const u8arr = new Uint8Array(n);
                        while (n--) {
                            u8arr[n] = bstr.charCodeAt(n);
                        }
                        const blob = new Blob([u8arr], { type: mime });
                        const file = new File([blob], fname, { type: mime });
                        
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        const uploadRes = await fetch('/manage/post/attach.json', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (uploadRes.status === 200) {
                            return await uploadRes.json();
                        }
                        throw new Error('Upload failed with status ' + uploadRes.status);
                    }
                    """
                    try:
                        res_data = page.evaluate(upload_js, [data_uri, filename])
                        key = res_data.get("key")
                        fname = res_data.get("filename")
                        if key and fname:
                            tistory_tag = f'[##_Image|kage@{key}/{fname}|alignCenter|width="100%"|_##]'
                            # 본문 마크다운 치환
                            body = body.replace(f"![{alt}]({img_path})", tistory_tag)
                            print(f"  └─ ✅ 성공! 치환 태그: {tistory_tag}")
                        else:
                            print(f"  └─ ❌ 업로드 실패 (응답 데이터 누락): {res_data}")
                    except Exception as upload_err:
                        print(f"  └─ ❌ 브라우저 업로드 에러: {upload_err}")
            
            # 파일 백업본 저장 (치환 결과 확인용)
            try:
                replaced_backup_path = md_file.replace(".md", "_replaced.md")
                # 마크다운 원래 헤더(# 제목)를 복원해서 저장
                with open(replaced_backup_path, "w", encoding="utf-8") as f_backup:
                    f_backup.write(f"# {title}\n\n{body}")
                print(f"💾 치환 완료 마크다운 백업본 생성 완료: {replaced_backup_path}")
            except Exception as backup_err:
                print(f"⚠️ 백업본 생성 실패: {backup_err}")

            
            # 2. 카테고리 선택
            print("🔬 카테고리 '🔬 Deep Research : AI & 자동화' 선택 중...")
            page.locator("#category-btn").click()
            time.sleep(0.5)
            
            target_cat = page.locator('#category-list .mce-menu-item:has-text("Deep Research")').first
            if target_cat.is_visible():
                target_cat.click()
                print("✅ 카테고리 선택 완료")
            else:
                print("⚠️ 카테고리를 찾을 수 없습니다. 기본값으로 진행합니다.")
            time.sleep(0.5)
            
            # 3. 마크다운 모드로 전환
            print("🔄 에디터 모드를 '마크다운'으로 전환 중...")
            page.locator("#editor-mode-layer-btn-open").click()
            time.sleep(0.5)
            
            markdown_item = page.locator("#editor-mode-markdown").first
            if markdown_item.is_visible():
                markdown_item.click()
                print("✅ 마크다운 모드 전환 완료")
            else:
                print("❌ 마크다운 메뉴를 클릭할 수 없습니다.")
                sys.exit(1)
            time.sleep(2)
            
            # 4. 제목 및 본문 입력
            print("✍️ 제목 입력 중...")
            page.locator("#post-title-inp").fill(title)
            time.sleep(0.5)
            
            print("✍️ 본문 입력 중...")
            body_textarea = page.locator('textarea:visible:not(#post-title-inp)').first
            body_textarea.fill(body)
            time.sleep(1.0)
            
            # 본문이 길어져 태그창이 숨겨질 수 있으므로 강제 스크롤 다운 수행
            print("📜 태그 입력을 위해 하단으로 스크롤 중...")
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
            except Exception as scroll_err:
                print(f"  - 스크롤 실패 경고: {scroll_err}")
            
            # 5. 태그 입력
            print("🏷️ 태그 입력 중...")
            tag_input = page.locator("#tagText").first
            try:
                tag_input.scroll_into_view_if_needed(timeout=5000)
            except Exception:
                pass
            
            # fill 대신 focus & keyboard.type 우회 기법 적용
            for tag in tags:
                try:
                    # 강제로 포커스를 맞추고 텍스트 타이핑
                    page.focus("#tagText", timeout=3000)
                    page.keyboard.type(tag)
                    page.keyboard.press("Enter")
                    print(f"  - 태그 입력 성공 (type): {tag}")
                except Exception as tag_err:
                    print(f"  - 일반 포커스 실패로 evaluate 기반 입력 시도: {tag_err}")
                    # 최종 evaluate 백업
                    page.evaluate("""([t]) => {
                        const ti = document.querySelector('#tagText');
                        if (ti) {
                            ti.value = t;
                            ti.dispatchEvent(new Event('input', { bubbles: true }));
                            ti.dispatchEvent(new Event('change', { bubbles: true }));
                            // 엔터 키다운 이벤트 시뮬레이션
                            const ke = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter', keyCode: 13, which: 13 });
                            ti.dispatchEvent(ke);
                            const ku = new KeyboardEvent('keyup', { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter', keyCode: 13, which: 13 });
                            ti.dispatchEvent(ku);
                        }
                    }""", [tag])
                    print(f"  - 태그 입력 성공 (evaluate): {tag}")
                time.sleep(0.3)
            print("✅ 태그 입력 완료")
            time.sleep(0.5)
            
            # 6. 완료 버튼 클릭 (발행 레이어 팝업)
            print("🔔 완료 버튼 클릭...")
            page.locator("#publish-layer-btn").click()
            time.sleep(1.5)
            
            # 7. 대표이미지 업로드
            if image_file:
                abs_image_path = os.path.abspath(image_file)
                if os.path.exists(abs_image_path):
                    print(f"🖼️ 대표 이미지 업로드 중... ({abs_image_path})")
                    file_input = page.locator('.layer_body input[type="file"]').first
                    
                    with page.expect_response("**/attach.json") as response_info:
                        file_input.set_input_files(abs_image_path)
                    
                    resp = response_info.value
                    if resp.status == 200:
                        print("✅ 대표 이미지 업로드 완료")
                    else:
                        print(f"⚠️ 대표 이미지 업로드 HTTP 에러: {resp.status}")
                else:
                    print(f"⚠️ 이미지를 찾을 수 없어 건너뜜: {abs_image_path}")
            
            # 8. 발행일 예약 설정 (필요시)
            if delay_hours > 0:
                print(f"⏰ {delay_hours}시간 후 예약 발행 세팅 중...")
                page.locator('button.btn_date:has-text("예약")').click()
                time.sleep(0.5)
                
                js_time_str = page.evaluate("""() => {
                    const d = new Date();
                    const offset = d.getTimezoneOffset() * 60000;
                    return (new Date(d - offset)).toISOString().slice(0, 19).replace('T', ' ');
                }""")
                current_dt = datetime.strptime(js_time_str, "%Y-%m-%d %H:%M:%S")
                target_dt = current_dt + timedelta(hours=delay_hours)
                
                if target_dt.date() != current_dt.date():
                    print("⚠️ 주의: 예약 시간이 다음날로 넘어갑니다. 달력 UI 에러 예방을 위해 오늘 밤 23시 55분으로 예약을 자동 복원합니다.")
                    target_dt = current_dt.replace(hour=23, minute=55)
                
                
                target_hour = target_dt.hour
                target_minute = target_dt.minute
                
                print(f"🎯 예약 시간 설정: {target_dt.strftime('%Y-%m-%d %H:%M')}")
                page.locator("#dateHour").fill(str(target_hour))
                time.sleep(0.2)
                page.locator("#dateMinute").fill(str(target_minute))
                time.sleep(0.5)
            else:
                print("🚀 즉시 발행 세팅...")
                page.locator('button.btn_date:has-text("현재")').click()
                time.sleep(0.5)
                
            # 9. 최종 발행 버튼 클릭
            print("🚀 최종 발행 버튼 클릭!")
            page.locator("#publish-btn").click()
            time.sleep(5)
            print("🎉 포스팅 발행 프로세스 완료!")
            
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
        finally:
            try:
                if 'browser' in locals() and browser:
                    browser.close()
                elif 'context' in locals() and context:
                    context.close()
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tistory Markdown Publisher via Playwright")
    parser.add_argument("--md-file", required=True, help="Path to the markdown post file")
    parser.add_argument("--image", required=False, help="Path to the cover image file")
    parser.add_argument("--delay-hours", type=int, default=0, help="Delay in hours for scheduling (0 for immediate)")
    args = parser.parse_args()
    
    run(args.md_file, args.image, args.delay_hours)
