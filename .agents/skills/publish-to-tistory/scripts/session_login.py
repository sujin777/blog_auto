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
SESSION_FILE = os.path.join(SKILL_DIR, "tistory_session.json")

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
BLOG_NAME = os.environ.get("TISTORY_BLOG_NAME", "jini71").replace(".tistory.com", "").strip()
KAKAO_EMAIL = os.environ.get("KAKAO_EMAIL", "").strip()
KAKAO_PW = os.environ.get("KAKAO_PASSWORD", "").strip()

def main():
    print("=" * 60)
    print("🔑 [티스토리 영구 세션 생성기 - Playwright Isolated Engine]")
    print(f"📁 세션 저장 위치: {SESSION_FILE}")
    print("=" * 60)
    sys.stdout.flush()

    with sync_playwright() as p:
        # 순수 번들 Chromium 기동 (구글 크롬과 완전 독립되어 100% 확실하게 화면 팝업)
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        print("🌐 티스토리 로그인 페이지로 이동합니다...")
        sys.stdout.flush()
        page.goto("https://www.tistory.com/auth/login")
        time.sleep(1.5)

        # 카카오계정으로 로그인 버튼 클릭
        try:
            kakao_btn = page.locator("a.btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                print("👉 [카카오계정으로 로그인] 버튼 클릭...")
                kakao_btn.click()
                time.sleep(2)
        except Exception:
            pass

        # 자동 입력 시도
        if KAKAO_EMAIL and KAKAO_PW:
            print(f"🤖 .env 계정 정보로 자동 입력 중... ({KAKAO_EMAIL})")
            sys.stdout.flush()
            try:
                id_inp = page.locator('input[name="loginId"], #loginId--1, #loginKey--1, input[type="text"]').first
                if id_inp.is_visible():
                    id_inp.fill(KAKAO_EMAIL)
                    time.sleep(0.3)
                pw_inp = page.locator('input[name="password"], #password--2, input[type="password"]').first
                if pw_inp.is_visible():
                    pw_inp.fill(KAKAO_PW)
                    time.sleep(0.3)
                submit_btn = page.locator('button.btn_g.highlight.submit, button[type="submit"]').first
                if submit_btn.is_visible():
                    submit_btn.click()
                    print("🚀 계정 정보 제출 완료!")
                    sys.stdout.flush()
                    time.sleep(3)
            except Exception as e:
                print(f"⚠️ 자동 입력 예외: {e}")

        print("\n" + "=" * 60)
        print("👉 화면에 뜬 브라우저에서 로그인을 완료해 주세요!")
        print("👉 (보안 캡차나 2단계 인증이 있다면 화면 또는 스마트폰에서 통과해 주세요)")
        print("👉 로그인이 완료되면 자동으로 세션을 영구 저장하고 창이 닫힙니다.")
        print("=" * 60 + "\n")
        sys.stdout.flush()

        # 로그인 감지 루프 (최대 10분 대기)
        start_t = time.time()
        logged_in = False
        while time.time() - start_t < 600:
            time.sleep(1.5)
            curr_url = page.url
            cookies = context.cookies()
            has_session = any(c.get("name") in ["TSSESSION", "TI_SEC", "_T_LOGIN"] for c in cookies)
            url_passed = "tistory.com" in curr_url and "auth/login" not in curr_url and "accounts.kakao.com" not in curr_url

            if has_session or url_passed or "manage" in curr_url:
                logged_in = True
                break

        if logged_in:
            print("\n🎉 카카오/티스토리 로그인 완료 감지!")
            # 글쓰기 페이지 진입 확인
            page.goto(f"https://{BLOG_NAME}.tistory.com/manage/newpost/?type=post")
            time.sleep(3)
            # 영구 세션 파일 저장
            context.storage_state(path=SESSION_FILE)
            print(f"💾 [영구 세션 저장 완료] ➔ {SESSION_FILE}")
            print("✅ 이제부터 모든 글은 100% 무인 자동 발행됩니다!")
            sys.stdout.flush()
            time.sleep(2)
            browser.close()
        else:
            print("\n❌ 로그인 대기 시간 초과")
            browser.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
