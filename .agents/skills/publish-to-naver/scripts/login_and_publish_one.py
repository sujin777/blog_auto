import os
import sys
import time
from naver_publish import run, SESSION_FILE, NAVER_BLOG_ID

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 65)
    print("🚀 [네이버 로그인 검증부터 1개 블로그 자동 발행까지 엔드투엔드 파이프라인]")
    print(f"📌 대상 블로그: https://blog.naver.com/{NAVER_BLOG_ID}")
    print("=" * 65)

    # 1. 세션 파일 존재 확인
    if not os.path.exists(SESSION_FILE):
        print(f"❌ 네이버 세션 파일이 없습니다: {SESSION_FILE}")
        print("👉 naver_login.bat을 먼저 실행하여 1회 로그인을 완료해 주세요.")
        sys.exit(1)

    print("🔑 [1단계] 네이버 영구 인증 세션 로드 완료!")
    sys.stdout.flush()

    # 2. 발행할 포스트 선정 (최신 1049 폴더의 1번째 글)
    target_md = os.path.abspath("output/261025_1049/삼성_스마트세탁기_부활_IoT_해킹.md")
    if not os.path.exists(target_md):
        # 대안으로 0745 폴더의 글 탐색
        target_md = os.path.abspath("output/261025_0745/단일_에이전트_루프_아키텍처.md")

    print(f"📝 [2단계] 발행 대상 포스트: {os.path.basename(target_md)}")
    print(f"📁 파일 경로: {target_md}")
    sys.stdout.flush()

    # 3. SmartEditor ONE 자동 발행 실행 (headed 모드로 브라우저 동작 시각화)
    print("\n🌐 [3단계] 스마트에디터 ONE 진입 및 무인 포스팅 시작...")
    print("👉 화면에 열린 브라우저에서 제목, 이미지, 본문 주입 및 최종 발행이 자동으로 진행됩니다!")
    print("=" * 65)
    sys.stdout.flush()

    try:
        run(target_md, publish=True, headless=False)
        print("\n🎉 [완료] 네이버 블로그에 1개 포스트가 성공적으로 공개 발행되었습니다!")
        print(f"🔗 블로그 홈: https://blog.naver.com/{NAVER_BLOG_ID}")
    except Exception as e:
        print(f"\n❌ 발행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
