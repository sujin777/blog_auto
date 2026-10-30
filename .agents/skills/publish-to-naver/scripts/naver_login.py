import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SESSION_FILE = os.path.join(SKILL_DIR, "naver_session.json")

def load_env():
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(SKILL_DIR), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(SKILL_DIR)), ".env"),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
            break

load_env()
NAVER_ID = os.environ.get("NAVER_ID", "gogo351").strip()
NAVER_PW = os.environ.get("NAVER_PASSWORD", "").strip()
NAVER_BLOG_ID = os.environ.get("NAVER_BLOG_ID", "gogo351").strip()

def main():
    print("=" * 65)
    print("🟢 [네이버 스마트 로그인 자동화 엔진 - Playwright Session Builder]")
    print(f"📌 대상 블로그: https://blog.naver.com/{NAVER_BLOG_ID}")
    print(f"📁 세션 저장 파일: {SESSION_FILE}")
    print("=" * 65)
    sys.stdout.flush()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        context = browser.new_context(
            no_viewport=True,
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = context.new_page()

        print(f"🌐 네이버 로그인 페이지 접속 중... (계정: {NAVER_ID})")
        sys.stdout.flush()
        page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
        page.bring_to_front()
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # Chromium 창을 최상단으로 활성화
            hwnd = user32.GetForegroundWindow()
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        except Exception:
            pass
        time.sleep(1.5)

        # 1. 자동 입력 (계정 및 비밀번호가 .env에 존재할 경우)
        if NAVER_ID and NAVER_PW:
            print("🤖 .env 계정 정보로 자동 로그인 시도 중...")
            sys.stdout.flush()
            try:
                # 클립보드 주입 방식으로 네이버 보안 캡차 방지
                page.evaluate("""({id, pw}) => {
                    const idEl = document.querySelector('#id');
                    const pwEl = document.querySelector('#pw');
                    if (idEl) idEl.value = id;
                    if (pwEl) pwEl.value = pw;
                }""", {"id": NAVER_ID, "pw": NAVER_PW})
                time.sleep(0.5)

                # 로그인 상태 유지 체크
                try:
                    keep_btn = page.locator("label[for='keep'], .keep_check").first
                    if keep_btn.is_visible():
                        keep_btn.click()
                except Exception:
                    pass

                # 로그인 버튼 클릭
                login_btn = page.locator("button.btn_login, #log\\.login, input[type='submit']").first
                if login_btn.is_visible():
                    login_btn.click()
                    print("🚀 로그인 정보 제출 완료! 2단계 인증 또는 세션 전환 대기 중...")
                    sys.stdout.flush()
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️ 자동 입력 예외: {e}")

        # 2. 실시간 세션 감지 루프 (사용자 직접 로그인, QR코드, 스마트폰 2단계 인증 모두 지원)
        print("\n" + "=" * 65)
        print("👉 화면에 뜬 크롬 브라우저에서 네이버 로그인을 진행해 주세요.")
        print("👉 (아이디/비번 직접 입력 또는 네이버앱 QR코드 스캔 모두 가능합니다)")
        print("👉 로그인이 완료되면 자동으로 감지하여 세션을 영구 저장하고 창이 닫힙니다.")
        print("=" * 65 + "\n")
        sys.stdout.flush()

        start_time = time.time()
        timeout = 600  # 10분 대기
        logged_in = False

        while time.time() - start_time < timeout:
            time.sleep(1.5)

            # 새 기기 등록 팝업 자동 클릭 ("등록" 또는 "등록안함")
            try:
                reg_btn = page.locator("button:has-text('등록'), a:has-text('등록'), #new\\.save").first
                if reg_btn.is_visible():
                    print("👉 [새로운 기기 등록] 버튼 자동 클릭...")
                    reg_btn.click()
                    time.sleep(1)
            except Exception:
                pass

            # 쿠키 확인 (NID_AUT, NID_SES가 있으면 네이버 로그인 성공)
            cookies = context.cookies()
            has_auth = any(c.get("name") == "NID_AUT" for c in cookies)
            has_ses = any(c.get("name") == "NID_SES" for c in cookies)

            current_url = page.url
            url_passed = "nidlogin" not in current_url and ("naver.com" in current_url)

            if (has_auth and has_ses) or (url_passed and "nid.naver.com" not in current_url):
                # 로그인 감지 즉시 0.1초 내에 세션 파일부터 최우선 저장 (창 닫힘 대비)
                context.storage_state(path=SESSION_FILE)
                logged_in = True
                break

        if logged_in:
            print("\n🎉 네이버 로그인 성공 확인!")
            print(f"💾 [1차 세션 즉시 백업 완료] ➔ {SESSION_FILE}")
            sys.stdout.flush()

            try:
                # 내 블로그 쿠키 추가 확보
                print(f"🔍 블로그(https://blog.naver.com/{NAVER_BLOG_ID}) 접속 테스트 중...")
                page.goto(f"https://blog.naver.com/{NAVER_BLOG_ID}", wait_until="domcontentloaded", timeout=8000)
                context.storage_state(path=SESSION_FILE)
            except Exception:
                pass
            print(f"💾 [네이버 영구 세션 파일 저장 완료] ➔ {SESSION_FILE}")
            print("=" * 65)
            print("✅ 네이버 로그인 자동화 세션이 성공적으로 구축되었습니다!")
            print("✅ 이제부터 모든 블로그 포스팅은 로그인 창 없이 100% 무인 자동 발행됩니다.")
            print("=" * 65)
            sys.stdout.flush()
            try:
                browser.close()
            except Exception:
                pass
        else:
            print("\n❌ 로그인 대기 시간 초과")
            browser.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
