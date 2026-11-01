import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    import traceback
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log(f"💥 치명적 예외 발생:\n{err}")

sys.excepthook = handle_uncaught_exception

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(ROOT_DIR, "telegram_commander.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    try:
        print(formatted, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_env():
    env_file = os.path.join(ROOT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip("'\"")

load_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
AUTHORIZED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
NAVER_BLOG_ID = os.environ.get("NAVER_BLOG_ID", "gogo351").strip()

# 상태 관리 변수 및 락
pipeline_lock = threading.Lock()
current_pipeline_process = None
is_running_pipeline = False

KEYBOARD = {
    "keyboard": [
        [{"text": "🚀 블로그 자동 작성·발행"}, {"text": "📊 시스템 상태 확인"}],
        [{"text": "📱 네이버 세션 재로그인"}, {"text": "🔗 최근 발행 글 목록"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

def send_message(chat_id, text, reply_markup=KEYBOARD):
    if not TOKEN:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=12)
    except Exception as e:
        log(f"메시지 발송 실패: {e}")

def get_latest_posts_info():
    output_dir = os.path.join(ROOT_DIR, "output")
    if not os.path.exists(output_dir):
        return None, []
    
    folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f)) and f.startswith("26")]
    folders.sort(reverse=True)
    if not folders:
        return None, []
    
    latest_folder = os.path.join(output_dir, folders[0])
    result_json = os.path.join(latest_folder, "published_results.json")
    if os.path.exists(result_json):
        try:
            with open(result_json, "r", encoding="utf-8") as f:
                return folders[0], json.load(f)
        except Exception:
            pass
    return folders[0], []

def check_system_status():
    global is_running_pipeline, current_pipeline_process
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Runner 프로세스 체크
    runner_status = "🔴 중단됨"
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "Get-Process Runner.Listener -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            text=True
        ).strip()
        if out:
            runner_status = f"🟢 정상 가동 중 (PID: {out.split()[0]})"
    except Exception:
        pass

    # 2. 네이버 세션 체크
    session_file = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "naver_session.json")
    session_status = "🔴 세션 파일 없음 (로그인 필요)"
    if os.path.exists(session_file):
        mtime = datetime.fromtimestamp(os.path.getmtime(session_file)).strftime("%m-%d %H:%M")
        size = os.path.getsize(session_file)
        session_status = f"🟢 정상 유효 (갱신: {mtime}, {size}B)"

    # 3. 파이프라인 실행 여부
    pipe_status = "⚪ 유휴 상태 (명령 대기)"
    with pipeline_lock:
        if is_running_pipeline and current_pipeline_process and current_pipeline_process.poll() is None:
            pipe_status = f"🔥 현재 작업 진행 중 (PID: {current_pipeline_process.pid})"

    # 4. 최근 발행 결과
    folder_name, posts = get_latest_posts_info()
    posts_text = ""
    if posts:
        posts_text = f"\n\n📝 *최근 발행된 포스트 ({folder_name})*:\n"
        for i, p in enumerate(posts, 1):
            title = p.get("title", f"포스트 {i}")
            url = p.get("url", "#")
            posts_text += f"{i}. [{title}]({url})\n"
    else:
        posts_text = "\n\n📝 *최근 발행*: 아직 등록된 글이 없습니다."

    status_msg = (
        f"📊 *[블로그 자동화 시스템 상태 브리핑]*\n"
        f"⏰ 현재 시각: `{now_str}` (KST)\n\n"
        f"• 🏃 *GitHub Self-Hosted 러너*: {runner_status}\n"
        f"• 🔑 *네이버 로그인 세션*: {session_status}\n"
        f"• ⚙️ *파이프라인 상태*: {pipe_status}\n"
        f"• 🌐 *타겟 블로그*: [blog.naver.com/{NAVER_BLOG_ID}](https://blog.naver.com/{NAVER_BLOG_ID})"
        f"{posts_text}"
    )
    return status_msg

def run_pipeline_worker(chat_id):
    global current_pipeline_process, is_running_pipeline
    try:
        log("🚀 auto_pipeline.py 백그라운드 구동 시작")
        cmd = [sys.executable, "-u", os.path.join(ROOT_DIR, "auto_pipeline.py")]
        current_pipeline_process = subprocess.Popen(
            cmd,
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        
        stdout, _ = current_pipeline_process.communicate()
        ret = current_pipeline_process.returncode
        
        if ret == 0:
            log("🎉 auto_pipeline.py 정상 종료 완료!")
        else:
            log(f"⚠️ auto_pipeline.py 에러 종료 (코드: {ret})")
            send_message(chat_id, f"⚠️ *[파이프라인 실행 오류]*\n프로세스가 코드 `{ret}` 로 종료되었습니다.\n로그를 확인해 주세요.")
    except Exception as e:
        log(f"파이프라인 쓰레드 예외: {e}")
        send_message(chat_id, f"🚨 *[파이프라인 실행 실패]*\n예외: `{e}`")
    finally:
        with pipeline_lock:
            is_running_pipeline = False
            current_pipeline_process = None

def run_login_worker(chat_id):
    try:
        log("📱 naver_login.py 백그라운드 구동 시작")
        login_script = os.path.join(ROOT_DIR, ".agents", "skills", "publish-to-naver", "scripts", "naver_login.py")
        subprocess.run([sys.executable, "-u", login_script], cwd=ROOT_DIR)
    except Exception as e:
        log(f"로그인 실행 예외: {e}")
        send_message(chat_id, f"⚠️ 네이버 로그인 스크립트 실행 중 예외: `{e}`")

def handle_command(chat_id, text):
    global is_running_pipeline, current_pipeline_process
    raw = text.strip()
    clean = raw.lower()

    log(f"📥 수신된 명령: '{raw}' (From: {chat_id})")

    # 1. 시작 및 도움말
    if clean in ["/start", "/help", "도움말", "help"]:
        msg = (
            "🤖 *[네이버 블로그 무인 자동화 텔레그램 관제 센터]*\n\n"
            "아래 버튼을 터치하거나 메시지를 보내시면 언제 어디서든 제어할 수 있습니다:\n\n"
            "• 🚀 *블로그 자동 작성·발행*: 핫토픽 수집 ➔ 글/도해 생성 ➔ 네이버 전체 공개 자동 발행\n"
            "• 📊 *시스템 상태 확인*: 러너 상태, 네이버 세션, 최근 발행 현황 브리핑\n"
            "• 📱 *네이버 세션 재로그인*: 모바일 네이버 앱용 실시간 QR 코드 즉시 발급\n"
            "• 🔗 *최근 발행 글 목록*: 가장 최근에 발행된 블로그 포스트 링크\n"
            "• 🛑 *중지*: 실행 중인 작업 강제 종료 (`/stop`)"
        )
        send_message(chat_id, msg)
        return

    # 2. 질문형 또는 상태 확인 명령 (우선순위 높음)
    status_keywords = ["상태", "현황", "확인", "/status", "/check", "되었", "했을까", "했어", "올라갔", "결과", "?"]
    if any(k in clean for k in status_keywords) and not ("작성해" in raw or "발행해" in raw or "시작" in raw):
        status_msg = check_system_status()
        send_message(chat_id, status_msg)
        return

    # 3. 블로그 작성 / 발행 명령
    run_keywords = [
        "🚀 블로그 자동 작성·발행", "/run", "/publish",
        "작성해", "발행해", "작성 시작", "발행 시작", "파이프라인 시작",
        "오늘 블로그 작성 해", "블로그 작성 해", "글 써줘"
    ]
    if any(k in raw for k in run_keywords) or clean in ["/run", "/publish"]:
        with pipeline_lock:
            if is_running_pipeline:
                pid_info = f" (PID: `{current_pipeline_process.pid}`)" if current_pipeline_process else ""
                send_message(
                    chat_id,
                    f"⚠️ *현재 블로그 파이프라인이 이미 실행 중입니다.*{pid_info}\n"
                    f"완료될 때까지 잠시만 기다려주시면 자동으로 결과를 알려드립니다."
                )
                return
            is_running_pipeline = True

        send_message(
            chat_id,
            "🚀 *[블로그 자동화 파이프라인 즉시 가동]*\n\n"
            "1️⃣ 글로벌 24시간 핫토픽 스마트 큐레이션 수집\n"
            "2️⃣ 심층 마크다운 기술 아티클 3편 및 인포그래픽 도해 6장 생성\n"
            "3️⃣ 네이버 스마트에디터 ONE 전체 공개 발행\n\n"
            "작업을 시작합니다! 완료되는 즉시 상세 결과 링크를 브리핑해 드립니다."
        )
        t = threading.Thread(target=run_pipeline_worker, args=(chat_id,), daemon=True)
        t.start()
        return

    # 4. 네이버 세션 재로그인 / QR
    if any(k in clean for k in ["로그인", "세션", "qr", "/login", "📱 네이버 세션 재로그인"]):
        send_message(
            chat_id,
            "📱 *[네이버 실시간 QR 로그인 모드 기동]*\n\n"
            "로그인 세션 갱신을 시작합니다.\n"
            "잠시 후 전송되는 QR 코드를 스마트폰 **네이버 앱(검색창 옆 렌즈)**으로 스캔해 주세요!"
        )
        t = threading.Thread(target=run_login_worker, args=(chat_id,), daemon=True)
        t.start()
        return

    # 5. 최근 글 목록
    if any(k in clean for k in ["최근", "링크", "목록", "/latest", "/posts", "🔗 최근 발행 글 목록"]):
        folder_name, posts = get_latest_posts_info()
        if posts:
            msg = f"🔗 *[최근 발행된 포스트 목록 ({folder_name})]*\n\n"
            for i, p in enumerate(posts, 1):
                title = p.get("title", f"포스트 {i}")
                url = p.get("url", "#")
                msg += f"*{i}. {title}*\n👉 [글 보러가기]({url})\n\n"
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "ℹ️ 아직 발행된 글 목록이 없습니다.")
        return

    # 6. 작업 중지
    if any(k in clean for k in ["중지", "멈춰", "취소", "/stop", "/kill"]):
        with pipeline_lock:
            if is_running_pipeline and current_pipeline_process and current_pipeline_process.poll() is None:
                pid = current_pipeline_process.pid
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                    is_running_pipeline = False
                    current_pipeline_process = None
                    send_message(chat_id, f"🛑 *실행 중이던 파이프라인(PID: `{pid}`)을 강제 중지했습니다.*")
                except Exception as e:
                    send_message(chat_id, f"⚠️ 중지 시도 중 예외 발생: `{e}`")
            else:
                send_message(chat_id, "⚪ 현재 실행 중인 파이프라인 작업이 없습니다.")
        return

    # 기타 미인식 메시지
    send_message(
        chat_id,
        f"🤖 수신된 메시지: *'{raw}'*\n\n"
        f"원하시는 동작을 아래 버튼에서 터치해 주세요:\n"
        f"• [🚀 블로그 자동 작성·발행] ➔ 최신 글 수집 및 네이버 발행\n"
        f"• [📊 시스템 상태 확인] ➔ 현재 가동 상태 및 최근 발행 확인\n"
        f"• [📱 네이버 세션 재로그인] ➔ 실시간 QR 코드 재발급\n"
        f"• [🔗 최근 발행 글 목록] ➔ 블로그 링크 조회"
    )

def main():
    log("=" * 65)
    log("🤖 [텔레그램 양방향 원격 관제 엔진 (Telegram Commander) 시작]")
    log(f"📌 인가된 Chat ID: {AUTHORIZED_CHAT_ID}")
    log("=" * 65)

    log("[Check 1] Checking token...")
    if not TOKEN or not AUTHORIZED_CHAT_ID:
        log("❌ 에러: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 설정되지 않았습니다.")
        sys.exit(1)

    log("[Check 2] Getting updates offset...")
    offset = 0
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10)
        log(f"[Check 2-1] getUpdates status: {init_res.status_code}")
        if init_res.status_code == 200:
            existing = init_res.json().get("result", [])
            log(f"[Check 2-2] existing count: {len(existing)}")
            if existing:
                offset = existing[-1].get("update_id", 0) + 1
                log(f"기존 메시지 {len(existing)}개 확인 ➔ 오프셋 {offset} 설정 완료")
    except Exception as e:
        log(f"초기 오프셋 조회 예외: {e}")

    log("[Check 3] Sending welcome message...")
    send_message(
        AUTHORIZED_CHAT_ID,
        "🟢 *[텔레그램 블로그 원격 관제 시스템 활성화 완료]*\n\n"
        "이제 텔레그램 채팅창 아래의 버튼을 터치하거나 원하시는 명령을 보내시면 언제든 원격 제어할 수 있습니다! 🚀"
    )
    log("[Check 4] Entering polling loop...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 20}
            resp = requests.get(url, params=params, timeout=25)
            
            if resp.status_code == 200:
                data = resp.json()
                updates = data.get("result", [])
                for u in updates:
                    offset = u.get("update_id", 0) + 1
                    msg = u.get("message") or u.get("channel_post")
                    if not msg:
                        continue
                    
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "")
                    
                    # 보안 검증: 인가된 유저 ID만 처리
                    if chat_id != str(AUTHORIZED_CHAT_ID):
                        log(f"⚠️ 인가되지 않은 접근 시도 차단 (Chat ID: {chat_id})")
                        send_message(chat_id, "⛔ 인가되지 않은 사용자입니다.", reply_markup=None)
                        continue

                    if text:
                        handle_command(chat_id, text)
            else:
                log(f"⚠️ getUpdates 응답 오류: {resp.status_code}")
                time.sleep(3)

        except requests.exceptions.RequestException:
            time.sleep(2)
        except Exception as e:
            log(f"메인 루프 예외: {e}")
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(os.path.join(ROOT_DIR, "crash.log"), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
