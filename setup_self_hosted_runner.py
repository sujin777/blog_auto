import os
import sys
import time
import zipfile
import platform
import subprocess
import requests
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

RUNNER_DIR = r"C:\DEV\actions-runner"
REPO_OWNER = "sujin777"
REPO_NAME = "blog_auto"
REPO_FULL = f"{REPO_OWNER}/{REPO_NAME}"
GITHUB_URL = f"https://github.com/{REPO_FULL}"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def get_github_pat():
    log("[1/5] Windows Git 자격 증명 관리자에서 GitHub PAT 토큰 탐색 중...")
    try:
        p = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        input_data = f"protocol=https\nhost=github.com\nusername={REPO_OWNER}\n\n"
        out, _ = p.communicate(input=input_data)
        for line in out.strip().split("\n"):
            if line.startswith("password="):
                token = line.split("=", 1)[1].strip()
                log("GitHub PAT 토큰 획득 완료!")
                return token
    except Exception as e:
        log(f"Git Credential Manager 호출 실패: {e}")
    
    # .env 파일 또는 환경 변수 체크
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        log("환경 변수에서 GitHub 토큰 확인 완료!")
        return token
    raise RuntimeError("GitHub PAT 토큰을 찾을 수 없습니다. GitHub 로그인이 필요합니다.")

def get_runner_registration_token(pat):
    log("[2/5] GitHub API로부터 Self-Hosted 러너 등록용 One-Time 토큰 발급 중...")
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{REPO_FULL}/actions/runners/registration-token"
    r = requests.post(url, headers=headers)
    if r.status_code != 201:
        raise RuntimeError(f"러너 등록 토큰 발급 실패 ({r.status_code}): {r.text}")
    data = r.json()
    reg_token = data.get("token")
    expires_at = data.get("expires_at")
    log(f"러너 등록 토큰 획득 성공 (만료 시각: {expires_at})")
    return reg_token

def download_and_extract_runner():
    log(f"[3/5] GitHub Actions 러너 바이너리 준비 ({RUNNER_DIR})...")
    os.makedirs(RUNNER_DIR, exist_ok=True)
    
    config_cmd = os.path.join(RUNNER_DIR, "config.cmd")
    run_cmd = os.path.join(RUNNER_DIR, "run.cmd")
    
    if os.path.exists(config_cmd) and os.path.exists(run_cmd):
        log("이미 러너 바이너리가 설치되어 있습니다. 다운로드를 건너뜁니다.")
        return

    # 최신 Windows x64 러너 다운로드 URL 탐색
    log("최신 Actions Runner 릴리즈 버전 확인 중...")
    zip_path = os.path.join(RUNNER_DIR, "runner.zip")
    download_url = "https://github.com/actions/runner/releases/download/v2.338.2/actions-runner-win-x64-2.338.2.zip"
    try:
        r = requests.get("https://api.github.com/repos/actions/runner/releases/latest", timeout=10)
        if r.status_code == 200:
            for asset in r.json().get("assets", []):
                if "win-x64" in asset.get("name", ""):
                    download_url = asset.get("browser_download_url")
                    break
    except Exception:
        pass

    log(f"러너 다운로드 시작: {download_url}")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r다운로드 진행률: {pct:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="", flush=True)
    print()
    log("압축 해제 중...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(RUNNER_DIR)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    log("러너 바이너리 준비 완료!")

def configure_runner(reg_token):
    log("[4/5] GitHub Actions Self-Hosted 러너 구성(Registration) 시작...")
    hostname = platform.node() or "HOME-PC"
    runner_name = f"{hostname}-domestic-ip"
    
    cmd = [
        os.path.join(RUNNER_DIR, "config.cmd"),
        "--url", GITHUB_URL,
        "--token", reg_token,
        "--name", runner_name,
        "--work", "_work",
        "--labels", "self-hosted,windows,x64,domestic-ip",
        "--unattended",
        "--replace"
    ]
    
    log(f"러너 등록 명령 실행: {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=RUNNER_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(p.stdout)
    if p.returncode != 0:
        log(f"러너 등록 경고 또는 오류 (code {p.returncode}): {p.stderr}")
    else:
        log("GitHub Self-Hosted 러너 등록이 성공적으로 완료되었습니다!")

def start_runner():
    log("[5/5] 러너 백그라운드 구동 활성화...")
    
    # 1. Windows Service 설치 및 구동 시도
    svc_cmd = os.path.join(RUNNER_DIR, "svc.cmd")
    service_installed = False
    if os.path.exists(svc_cmd):
        log("Windows Service 설치 시도 중...")
        p_install = subprocess.run([svc_cmd, "install"], cwd=RUNNER_DIR, capture_output=True, text=True)
        if "Service actions.runner." in p_install.stdout or p_install.returncode == 0:
            log("Windows Service 등록 성공! 서비스 시작 시도...")
            p_start = subprocess.run([svc_cmd, "start"], cwd=RUNNER_DIR, capture_output=True, text=True)
            if p_start.returncode == 0:
                log("GitHub Actions Runner가 Windows Background Service로 영구 기동되었습니다!")
                service_installed = True
            else:
                log(f"서비스 시작 실패: {p_start.stdout} {p_start.stderr}")
        else:
            log(f"서비스 등록에 관리자 권한이 필요할 수 있습니다. (표준 백그라운드 프로세스로 전환합니다)")

    # 2. 서비스 설치가 안 된 경우 (표준 사용자 권한) Windows Scheduled Task 또는 백그라운드 실행
    if not service_installed:
        # 이미 run.cmd 프로세스가 돌고 있는지 확인
        p_check = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Runner.Listener.exe"], capture_output=True, text=True)
        if "Runner.Listener.exe" in p_check.stdout:
            log("Runner.Listener.exe 프로세스가 이미 실행 중입니다.")
        else:
            log("백그라운드 독립 프로세스로 러너 기동 중 (run.cmd)...")
            run_cmd = os.path.join(RUNNER_DIR, "run.cmd")
            # PowerShell Start-Process로 독립 세션 런칭
            ps_cmd = f"Start-Process -FilePath '{run_cmd}' -WorkingDirectory '{RUNNER_DIR}' -WindowStyle Minimized"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd])
            time.sleep(3)
            log("러너 프로세스가 백그라운드에 안착되었습니다.")

def verify_runner_online(pat):
    log("GitHub 서버에서 러너 Online 상태 최종 확인 중...")
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{REPO_FULL}/actions/runners"
    for attempt in range(1, 10):
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            runners = r.json().get("runners", [])
            for runner in runners:
                log(f"발견된 러너: ID={runner.get('id')}, Name={runner.get('name')}, Status={runner.get('status')}, OS={runner.get('os')}")
                if runner.get("status") == "online":
                    log(f"🎉 축하합니다! Self-Hosted 러너 '{runner.get('name')}'가 완벽하게 ONLINE 상태로 연결되었습니다!")
                    return True
        time.sleep(2)
    log("러너가 아직 완전히 Online으로 전환되지 않았을 수 있습니다. 몇 초 후 GitHub Actions에서 확인 가능합니다.")
    return False

def main():
    log("==================================================================")
    log("🚀 GitHub Actions Self-Hosted 러너 1-Click 자동 구축 마법사 시작")
    log("==================================================================")
    pat = get_github_pat()
    reg_token = get_runner_registration_token(pat)
    download_and_extract_runner()
    configure_runner(reg_token)
    start_runner()
    verify_runner_online(pat)
    log("==================================================================")
    log("모든 러너 구축 및 무인 연동 절차가 완료되었습니다!")
    log("==================================================================")

if __name__ == "__main__":
    main()
