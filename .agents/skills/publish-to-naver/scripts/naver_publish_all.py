import argparse
import os
import sys
import time
import json
from naver_publish import run

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Naver Blog Batch Publisher")
    parser.add_argument("--dir", required=True, help="Path to output directory (e.g. output/261025_0745)")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default is draft)")
    parser.add_argument("--schedule", action="store_true", help="Enable staggered scheduled publishing (예: 2, 4, 6시간 후 예약 발행)")
    parser.add_argument("--delays", type=str, default="2,4,6", help="Comma-separated delay hours for each post (default: '2,4,6')")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--interval", type=int, default=8, help="Interval seconds between posts (default: 8)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.dir)
    if not os.path.exists(target_dir):
        print(f"❌ 디렉토리가 존재하지 않습니다: {target_dir}")
        sys.exit(1)

    # 딜레이 시간 리스트 파싱
    delay_list = [int(x.strip()) for x in args.delays.split(",") if x.strip().isdigit()]
    if not delay_list:
        delay_list = [2, 4, 6]

    # 포스트 마크다운 파일 탐색 (ingest.md, replaced.md 제외)
    md_files = []
    for f in os.listdir(target_dir):
        if f.endswith(".md") and not f.startswith("ingest") and not f.endswith("_replaced.md"):
            md_files.append(os.path.join(target_dir, f))

    md_files.sort()
    print(f"📋 총 {len(md_files)}개의 포스트 발견:")
    for i, p in enumerate(md_files, 1):
        d_hr = delay_list[i - 1] if args.schedule and i - 1 < len(delay_list) else 0
        mode_label = f"⏰ {d_hr}시간 후 예약 발행" if d_hr > 0 else ("🚀 즉시 발행" if args.publish else "📝 임시저장")
        print(f"  [{i}] {os.path.basename(p)} ➔ {mode_label}")
    print("=" * 60)

    results = []
    for i, md_file in enumerate(md_files, 1):
        d_hr = delay_list[i - 1] if args.schedule and i - 1 < len(delay_list) else 0
        print(f"\n🚀 [{i}/{len(md_files)}] '{os.path.basename(md_file)}' 네이버 블로그 업로드 시작 (지연: {d_hr}시간)...")
        try:
            res = run(md_file, publish=args.publish or (d_hr > 0), headless=not args.headed, delay_hours=d_hr)
            if res and isinstance(res, tuple):
                p_title, p_url = res
                results.append({"title": p_title, "url": p_url, "delay_hours": d_hr})
            print(f"✅ [{i}/{len(md_files)}] 처리 완료!")
        except Exception as e:
            print(f"❌ [{i}/{len(md_files)}] 실패: {e}")

        if i < len(md_files):
            print(f"⏳ 다음 포스트까지 {args.interval}초 대기...")
            time.sleep(args.interval)

    # 결과 JSON 저장
    result_json_path = os.path.join(target_dir, "published_results.json")
    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n🎉 모든 포스트 일괄 업로드 처리가 완료되었습니다!")

if __name__ == "__main__":
    main()
