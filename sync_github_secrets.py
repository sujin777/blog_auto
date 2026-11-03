import os
import sys
import json
import base64
import subprocess
import requests
from nacl import encoding, public

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_OWNER = "sujin777"
REPO_NAME = "blog_auto"
REPO_FULL = f"{REPO_OWNER}/{REPO_NAME}"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_github_pat():
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, _ = p.communicate(f"protocol=https\nhost=github.com\nusername={REPO_OWNER}\n\n")
    for line in out.strip().split("\n"):
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    raise RuntimeError("GitHub PAT 토큰을 찾을 수 없습니다.")

def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    pk = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def main():
    print("=" * 65)
    print("🚀 [Solution B] GitHub Actions 클라우드 무인 구동용 시크릿 자동 동기화")
    print(f"📦 대상 레포지토리: {REPO_FULL}")
    print("=" * 65)

    pat = get_github_pat()
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. 공개키 가져오기
    pk_url = f"https://api.github.com/repos/{REPO_FULL}/actions/secrets/public-key"
    r = requests.get(pk_url, headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"공개키 조회 실패 ({r.status_code}): {r.text}")
    pk_data = r.json()
    key_id = pk_data["key_id"]
    public_key = pk_data["key"]
    print(f"🔑 GitHub 저장소 공개키 획득 완료 (Key ID: {key_id})")

    # 2. 업로드할 시크릿 수집
    secrets = {}
    env_file = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    secrets[k] = v

    session_file = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "naver_session.json")
    if os.path.exists(session_file):
        with open(session_file, "rb") as f:
            session_bytes = f.read()
        secrets["NAVER_SESSION_BASE64"] = base64.b64encode(session_bytes).decode("utf-8")

    print(f"📋 동기화할 시크릿 항목 총 {len(secrets)}개:")
    for k in secrets.keys():
        print(f"  - {k}")

    # 3. 암호화 및 업로드
    for name, value in secrets.items():
        encrypted_val = encrypt_secret(public_key, value)
        put_url = f"https://api.github.com/repos/{REPO_FULL}/actions/secrets/{name}"
        payload = {
            "encrypted_value": encrypted_val,
            "key_id": key_id
        }
        res = requests.put(put_url, headers=headers, json=payload)
        if res.status_code in (201, 204):
            print(f"  ✅ [{name}] 업로드 성공!")
        else:
            print(f"  ⚠️ [{name}] 실패 ({res.status_code}): {res.text}")

    print("=" * 65)
    print("🎉 모든 시크릿이 GitHub Actions 클라우드 환경으로 안전하게 동기화되었습니다!")
    print("=" * 65)

if __name__ == "__main__":
    main()

