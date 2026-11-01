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
RUNNER_SESSION = r"C:\DEV\actions-runner\_work\blog_auto\blog_auto\.agents\skills\publish-to-naver\naver_session.json"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))
sys.path.append(ROOT_DIR)

def load_env():
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(ROOT_DIR, ".env"),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() not in os.environ:
                            os.environ[k.strip()] = v.strip().strip("'\"")
            break

load_env()
NAVER_ID = os.environ.get("NAVER_ID", "jin8191").strip()
NAVER_PW = os.environ.get("NAVER_PASSWORD", "").strip()
NAVER_BLOG_ID = os.environ.get("NAVER_BLOG_ID", "gogo351").strip()

def main():
    print("=" * 65)
    print("🟢 [네이버 스마트 QR 로그인 자동화 엔진 - Playwright Session Builder]")
    print(f"📌 대상 블로그: https://blog.naver.com/{NAVER_BLOG_ID}")
    print(f"📁 세션 저장 파일: {SESSION_FILE}")
    print("=" * 65)
    sys.stdout.flush()

    from telegram_notify import send_telegram_alert, send_telegram_photo

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
        time.sleep(1.5)

        import pyperclip

        # 1. ID / PW 자동 로그인 시도 (비밀번호가 제공된 경우)
        auto_login_attempted = False
        if NAVER_ID and NAVER_PW:
            print("🔑 [ID/PW 자동 로그인] 클립보드 주입 방식으로 로그인 시도...")
            sys.stdout.flush()
            try:
                # ID 입력
                id_input = page.locator("#id")
                id_input.click()
                time.sleep(0.3)
                pyperclip.copy(NAVER_ID)
                page.keyboard.press("Control+V")
                time.sleep(0.5)

                # PW 입력
                pw_input = page.locator("#pw")
                pw_input.click()
                time.sleep(0.3)
                pyperclip.copy(NAVER_PW)
                page.keyboard.press("Control+V")
                time.sleep(0.5)

                # 로그인 버튼 클릭
                login_btn = page.locator("#log\\.login, button.btn_login, button[type='submit']").first
                login_btn.click()
                print("🚀 로그인 버튼 클릭 완료! 응답 대기 중...")
                sys.stdout.flush()
                time.sleep(3)
                auto_login_attempted = True
            except Exception as e:
                print(f"⚠️ ID/PW 입력 중 예외 발생: {e}")

        # 2. 캡차 또는 실패 시 QR 로그인으로 전환
        # 현재 URL 확인
        current_url = page.url
        cookies = context.cookies()
        has_auth = any(c.get("name") == "NID_AUT" for c in cookies)
        has_ses = any(c.get("name") == "NID_SES" for c in cookies)

        if not (has_auth and has_ses):
            # 혹시 2단계 인증이나 캡차가 떴는지 확인
            content = page.content()
            if "2단계 인증" in content or "two-step" in current_url:
                print("📱 [네이버 2단계 인증] 스마트폰 알림 발생! 모바일에서 '예'를 승인해 주세요.")
                qr_img_path = os.path.join(SKILL_DIR, "naver_login_status.png")
                page.screenshot(path=qr_img_path)
                send_telegram_photo(
                    qr_img_path,
                    caption="📱 *[네이버 2단계 인증 요청]*\n\n아이디/비밀번호가 정상 입력되었습니다!\n스마트폰 네이버 앱의 2단계 인증 알림에서 **[예, 저 맞아요]**를 눌러주시면 즉시 로그인이 완료됩니다."
                )
            else:
                # QR 코드 로그인 탭으로 전환 시도
                try:
                    qr_link = page.locator("a:has-text('QR 코드'), #qrcode, a[href*='qrcode']").first
                    if qr_link.is_visible():
                        qr_link.click()
                        print("📱 [QR 코드 로그인] 탭으로 자동 전환 완료!")
                        time.sleep(2)
                        
                        qr_img_path = os.path.join(SKILL_DIR, "naver_qr_live.png")
                        page.screenshot(path=qr_img_path)
                        send_telegram_photo(
                            qr_img_path,
                            caption="📱 *[네이버 실시간 QR 로그인]*\n\n화면의 QR 코드를 **네이버 앱(검색창 옆 렌즈)**으로 스캔 후, 화면에 뜨는 숫자를 눌러주세요!\n로그인 완료 시 세션이 즉시 저장됩니다."
                        )
                except Exception as e:
                    print(f"⚠️ QR 전환 예외: {e}")

        print("\n" + "=" * 65)
        print("👉 모니터 화면에 뜬 QR 코드를 스마트폰 [네이버 앱 렌즈]로 스캔해 주세요.")
        print("👉 (텔레그램으로도 QR 코드가 전송되었습니다)")
        print("👉 로그인이 완료되면 자동으로 감지하여 세션을 영구 저장하고 창이 닫힙니다.")
        print("=" * 65 + "\n")
        sys.stdout.flush()

        start_time = time.time()
        timeout = 300  # 5분 대기
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
                context.storage_state(path=SESSION_FILE)
                # runner workspace에도 세션 즉시 동기화
                if os.path.exists(os.path.dirname(RUNNER_SESSION)):
                    context.storage_state(path=RUNNER_SESSION)
                logged_in = True
                break

        if logged_in:
            print("\n🎉 네이버 로그인 성공 확인!")
            print(f"💾 [네이버 영구 세션 파일 저장 완료] ➔ {SESSION_FILE}")
            sys.stdout.flush()
            send_telegram_alert("🎉 *[네이버 로그인 성공]*\n새로운 로그인 세션이 정상 저장되었습니다!\n오늘자 블로그 3편 자동 발행을 즉시 시작합니다.")
            browser.close()
            return True
        else:
            print("\n❌ 로그인 대기 시간 초과")
            browser.close()
            return False

if __name__ == "__main__":
    main()
