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

def main():
    profile_path = os.path.expanduser("~/tmp/chrome-debug-tistory")
    os.makedirs(profile_path, exist_ok=True)
    
    print(f"🚀 티스토리 로그인 전용 브라우저를 기동합니다...")
    print(f"📁 프로필 경로: {profile_path}")
    print("=" * 60)
    print("👉 화면에 열린 크롬 창에서 [카카오계정으로 로그인]을 진행해 주세요.")
    print("👉 로그인이 완료되면 자동으로 감지하여 세션을 영구 저장합니다.")
    print("=" * 60)
    sys.stdout.flush()

    with sync_playwright() as p:
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
        
        page = context.pages[0] if context.pages else context.new_page()
        print("🌐 티스토리 로그인 페이지 접속 중...")
        sys.stdout.flush()
        page.goto("https://www.tistory.com/auth/login")
        time.sleep(1.5)
        
        # 카카오계정으로 로그인 버튼 자동 클릭
        try:
            kakao_btn = page.locator("a.btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                print("👉 카카오계정으로 로그인 버튼 자동 클릭...")
                kakao_btn.click()
        except Exception:
            pass
            
        print("⏳ 카카오 계정 로그인 대기 중 (최대 10분)...")
        print("👉 아이디/비밀번호 입력 또는 QR코드 스캔으로 로그인해 주세요.")
        sys.stdout.flush()
        
        # 사용자가 로그인을 완료하여 tistory.com 메인이나 관리자 페이지로 이동할 때까지 대기
        logged_in = False
        start_time = time.time()
        timeout = 600 # 10분 대기
        
        while time.time() - start_time < timeout:
            current_url = page.url
            # 로그인 완료 판별: auth/login이 아니고 tistory.com 메인 또는 manage 페이지일 때
            if "tistory.com" in current_url and "auth/login" not in current_url and "accounts.kakao.com" not in current_url:
                try:
                    cookies = context.cookies()
                    has_session = any("TSSESSION" in c["name"] or "TI_SEC" in c["name"] for c in cookies)
                    if has_session or "manage" in current_url:
                        logged_in = True
                        break
                except Exception:
                    pass
            time.sleep(1)
            
        if logged_in:
            print("\n🎉 카카오 로그인 감지 성공!")
            print("💾 세션 및 쿠키를 안전하게 디스크에 저장합니다...")
            sys.stdout.flush()
            time.sleep(2)
            context.close()
            print("✅ 로그인 세션 저장 완료! 이제 티스토리 자동 발행이 가능합니다.")
        else:
            print("\n⚠️ 로그인 대기 시간(5분)이 초과되었습니다.")
            context.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
