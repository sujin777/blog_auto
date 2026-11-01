import os
import sys
import json
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram_notify import send_telegram_alert, format_publish_success_message, format_error_message

ROOT_DIR = r"c:\DEV\261025_blog_auto"
folder_path = os.path.join(ROOT_DIR, "output", "261101_0807")

def main():
    print("=" * 65)
    print("🚀 [11월 1일 포스트 3편 네이버 블로그 전체 공개 일괄 자동 발행 시작]")
    print(f"📂 대상 디렉토리: {folder_path}")
    print("=" * 65)
    sys.stdout.flush()

    pub_script = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "scripts", "naver_publish_all.py")
    ret = subprocess.run([
        sys.executable, "-u", pub_script,
        "--dir", folder_path,
        "--publish",
        "--interval", "8"
    ])

    result_json_path = os.path.join(folder_path, "published_results.json")
    published_results = []
    if os.path.exists(result_json_path):
        try:
            with open(result_json_path, "r", encoding="utf-8") as f:
                published_results = json.load(f)
        except Exception as e:
            print(f"결과 JSON 파싱 오류: {e}")

    print("\n" + "=" * 65)
    print(f"📊 발행 결과 ({len(published_results)}개 성공):")
    for r in published_results:
        print(f"  - {r.get('title')}: {r.get('url')}")
    print("=" * 65)
    sys.stdout.flush()

    if published_results:
        raw_data_file = os.path.join(folder_path, "raw_reddit_data.json")
        if os.path.exists(raw_data_file):
            try:
                with open(raw_data_file, "r", encoding="utf-8") as f:
                    raw_posts = json.load(f)
                for idx, r in enumerate(published_results):
                    if idx < len(raw_posts):
                        r["category"] = raw_posts[idx].get("category", "")
                        r["selection_reason"] = raw_posts[idx].get("selection_reason", "")
            except Exception:
                pass
        msg = format_publish_success_message(published_results)
        send_telegram_alert(msg)
        print("📱 [Telegram] 3편 발행 완료 상세 브리핑 발송 완료!")
    else:
        print("⚠️ 발행된 포스트가 없습니다.")

if __name__ == "__main__":
    main()

