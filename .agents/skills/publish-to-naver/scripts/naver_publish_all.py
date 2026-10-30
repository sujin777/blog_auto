import argparse
import os
import sys
import time
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
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--interval", type=int, default=15, help="Interval seconds between posts (default: 15)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.dir)
    if not os.path.exists(target_dir):
        print(f"❌ 디렉토리가 존재하지 않습니다: {target_dir}")
        sys.exit(1)

    # 포스트 마크다운 파일 탐색 (ingest.md, replaced.md 제외)
    md_files = []
    for f in os.listdir(target_dir):
        if f.endswith(".md") and not f.startswith("ingest") and not f.endswith("_replaced.md"):
            md_files.append(os.path.join(target_dir, f))

    md_files.sort()
    print(f"📋 총 {len(md_files)}개의 포스트 발견:")
    for i, p in enumerate(md_files, 1):
        print(f"  [{i}] {os.path.basename(p)}")
    print("=" * 60)

    for i, md_file in enumerate(md_files, 1):
        print(f"\n🚀 [{i}/{len(md_files)}] '{os.path.basename(md_file)}' 네이버 블로그 업로드 시작...")
        try:
            run(md_file, publish=args.publish, headless=not args.headed)
            print(f"✅ [{i}/{len(md_files)}] 처리 완료!")
        except Exception as e:
            print(f"❌ [{i}/{len(md_files)}] 실패: {e}")

        if i < len(md_files):
            print(f"⏳ 다음 포스트까지 {args.interval}초 대기...")
            time.sleep(args.interval)

    print("\n🎉 모든 포스트 일괄 업로드 처리가 완료되었습니다!")

if __name__ == "__main__":
    main()
