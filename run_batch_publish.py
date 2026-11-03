import os
import sys
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "scripts"))

from naver_publish import run
from telegram_notify import send_telegram_alert, format_publish_success_message

target_dir = os.path.join(ROOT_DIR, "output", "261102_1905")

md_files = [
    os.path.join(target_dir, f)
    for f in sorted(os.listdir(target_dir))
    if f.startswith("post_") and f.endswith(".md")
]

print(f"📋 발행 대상 포스트 총 {len(md_files)}편:")
for i, f in enumerate(md_files, 1):
    print(f"  [{i}] {os.path.basename(f)}")
print("=" * 60)
sys.stdout.flush()

results = []
for i, md_file in enumerate(md_files, 1):
    print(f"\n🚀 [{i}/{len(md_files)}] '{os.path.basename(md_file)}' 네이버 블로그 업로드 시작...")
    sys.stdout.flush()
    try:
        res = run(md_file, publish=True, headless=True)
        if res and isinstance(res, tuple):
            p_title, p_url = res
            results.append({"title": p_title, "url": p_url})
            print(f"✅ [{i}/{len(md_files)}] 업로드 및 발행 성공! URL: {p_url}")
        else:
            print(f"⚠️ [{i}/{len(md_files)}] 발행 반환값 확인 필요: {res}")
    except Exception as e:
        print(f"❌ [{i}/{len(md_files)}] 실패: {e}")
    sys.stdout.flush()

    if i < len(md_files):
        print(f"⏳ 다음 포스트 업로드까지 8초 대기 중...")
        sys.stdout.flush()
        time.sleep(8)

# 결과 저장
result_json_path = os.path.join(target_dir, "published_results.json")
with open(result_json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n🎉 네이버 블로그 3편 전체 발행 완료!")
sys.stdout.flush()

if results:
    msg = format_publish_success_message(results)
    send_telegram_alert(msg)
    print("📱 [Telegram] 3편 발행 결과 브리핑 전송 완료!")
else:
    print("⚠️ 성공한 포스트가 없어 텔레그램 알림을 건너뜁니다.")

