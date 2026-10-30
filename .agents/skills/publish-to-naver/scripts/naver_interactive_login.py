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
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

def main():
    print("=" * 65)
    print("🟢 [네이버 영구 세션 생성기 - 화면 직접 로그인 모드]")
    print(f"📁 세션 저장 위치: {SESSION_FILE}")
    print("=" * 65)
    print("👉 화면에 뜬 브라우저 창에서 평소처럼 네이버 로그인을 진행해 주세요.")
    print("👉 로그인이 완료되면 자동으로 세션을 감지하여 영구 저장하고 창이 닫힙니다.")
    print("=" * 65)
    sys.stdout.flush()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        print("🌐 네이버 로그인 페이지로 이동합니다...")
        sys.stdout.flush()
        page.goto("https://nid.naver.com/nidlogin.login")

        # 로그인 감지 루프 (최대 10분)
        start_t = time.time()
        logged_in = False
        naver_id = ""

        while time.time() - start_t < 600:
            time.sleep(1.5)
            cookies = context.cookies()
            has_auth = any(c.get("name") == "NID_AUT" for c in cookies)
            has_ses = any(c.get("name") == "NID_SES" for c in cookies)

            # 네이버 ID 추출 시도
            for c in cookies:
                if c.get("name") == "NID_AUT":
                    # NID_AUT 쿠키가 있으면 로그인 성공
                    pass

            if has_auth and has_ses:
                logged_in = True
                break

        if logged_in:
            print("\n🎉 네이버 로그인 성공 감지!")
            sys.stdout.flush()

            # 블로그 관리자 홈으로 이동하여 최종 블로그 ID 확인
            page.goto("https://section.blog.naver.com/")
            time.sleep(3)

            # 영구 세션 파일 저장
            context.storage_state(path=SESSION_FILE)
            print(f"💾 [영구 세션 저장 완료] ➔ {SESSION_FILE}")
            
            # 페이지에서 사용자 블로그 주소/ID 추출 시도
            try:
                user_blog_link = page.locator("a.user_blog, a[href*='blog.naver.com']").first
                if user_blog_link.is_visible():
                    href = user_blog_link.get_attribute("href")
                    if "blog.naver.com/" in href:
                        naver_id = href.split("blog.naver.com/")[1].split("/")[0].split("?")[0]
                        print(f"📌 감지된 네이버 블로그 ID: {naver_id}")
            except Exception:
                pass

            # .env 파일에 NAVER_BLOG_ID 자동 업데이트 (발견된 경우)
            if naver_id and os.path.exists(ENV_FILE):
                try:
                    with open(ENV_FILE, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    with open(ENV_FILE, "w", encoding="utf-8") as f:
                        for l in lines:
                            if l.startswith("NAVER_BLOG_ID="):
                                f.write(f"NAVER_BLOG_ID={naver_id}\n")
                            elif l.startswith("NAVER_ID=") and not l.strip().split("=")[1]:
                                f.write(f"NAVER_ID={naver_id}\n")
                            else:
                                f.write(l)
                    print(f"📝 .env에 NAVER_BLOG_ID={naver_id} 자동 설정 완료!")
                except Exception as ee:
                    print(f"⚠️ .env 업데이트 예외: {ee}")

            print("✅ 이제부터 모든 네이버 블로그 글은 100% 무인 자동 발행됩니다!")
            sys.stdout.flush()
            time.sleep(2)
            browser.close()
        else:
            print("\n❌ 로그인 대기 시간 초과")
            browser.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
