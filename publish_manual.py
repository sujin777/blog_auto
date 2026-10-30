import os
import sys
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 60)
    print("  🚀 [네이버 블로그 수동 포스팅 & 발행 러너]")
    print("=" * 60)

    target_file = None

    # 1. 커맨드라인 인자 (또는 드래그 앤 드롭 파일) 확인
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        target_file = os.path.abspath(sys.argv[1])
        print(f"\n[선택된 파일]: {target_file}")
    else:
        # 2. output 디렉토리 내 마크다운 파일 탐색
        output_dir = os.path.abspath("output")
        md_files = []
        if os.path.exists(output_dir):
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(".md") and f != "ingest.md":
                        rel_path = os.path.relpath(os.path.join(root, f), os.getcwd())
                        mtime = os.path.getmtime(os.path.join(root, f))
                        md_files.append((rel_path, mtime))

        md_files.sort(key=lambda x: x[1], reverse=True)

        if not md_files:
            print("\n[알림] output 디렉토리에 발행할 수 있는 마크다운 파일이 없습니다.")
            target_file = input("발행할 마크다운 파일의 전체 경로를 직접 입력하세요: ").strip().strip('"\'')
            if not os.path.exists(target_file):
                print(f"[에러] 파일을 찾을 수 없습니다: {target_file}")
                return
        else:
            print("\n[발행 가능한 최신 포스트 목록]:")
            for idx, (path, _) in enumerate(md_files[:10], 1):
                print(f"  [{idx}] {path}")
            print("  [0] 파일 경로 직접 입력")

            while True:
                choice = input("\n발행할 번호를 선택하세요 (기본값: 1): ").strip()
                if choice == "" or choice == "1":
                    target_file = md_files[0][0]
                    break
                elif choice == "0":
                    target_file = input("마크다운 파일 경로: ").strip().strip('"\'')
                    if os.path.exists(target_file):
                        break
                    print("존재하지 않는 파일입니다. 다시 입력하세요.")
                else:
                    try:
                        c_idx = int(choice)
                        if 1 <= c_idx <= len(md_files):
                            target_file = md_files[c_idx - 1][0]
                            break
                        print("유효한 번호를 입력하세요.")
                    except ValueError:
                        print("숫자를 입력하세요.")

    print(f"\n>> 최종 선택 파일: {target_file}")

    # 3. 발행 모드 선택
    print("\n[발행 모드 선택]")
    print("  [1] 즉시 공개 발행 (네이버 블로그에 바로 공개)")
    print("  [2] 임시 저장 (블로그 에디터에 저장해 두고 직접 검토 후 발행)")
    m_choice = input("선택 (기본값: 1): ").strip()
    is_publish = (m_choice != "2")

    # 4. 발행 스크립트 실행
    publish_script = os.path.join(".agents", "skills", "publish-to-naver", "scripts", "naver_publish.py")
    cmd = [sys.executable, publish_script, "--md-file", target_file, "--headed"]
    if is_publish:
        cmd.append("--publish")

    print(f"\n[실행 중] 스마트에디터 ONE 브라우저를 띄워 포스팅을 진행합니다...")
    try:
        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            print("\n" + "=" * 60)
            print("  🎉 수동 포스팅 작업이 성공적으로 완료되었습니다!")
            print("=" * 60)
        else:
            print(f"\n[오류] 발행 스크립트가 코드 {ret.returncode}로 종료되었습니다.")
    except Exception as e:
        print(f"\n[실행 에러]: {e}")

if __name__ == "__main__":
    main()
