import os
import sys
import json
import requests
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

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

def send_telegram_alert(message):
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        print("[Telegram] 알림 건너뜀 (TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정)")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("📱 [Telegram] 스마트폰 알림 발송 성공!")
            return True
        else:
            print(f"⚠️ [Telegram] 발송 실패 ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ [Telegram] 알림 발송 예외: {e}")
        return False

def send_telegram_photo(photo_path, caption=""):
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    if not token or not chat_id:
        print("[Telegram] 사진 알림 건너뜀 (토큰 또는 챗ID 미설정)")
        return False
        
    if not os.path.exists(photo_path):
        print(f"⚠️ [Telegram] 사진 파일 없음: {photo_path}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
            res = requests.post(url, data=data, files=files, timeout=15)
        if res.status_code == 200:
            print("📱 [Telegram] 사진 알림 발송 성공!")
            return True
        else:
            print(f"⚠️ [Telegram] 사진 발송 실패 ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ [Telegram] 사진 발송 예외: {e}")
        return False

def format_publish_success_message(published_posts):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    has_scheduled = any(p.get("delay_hours", 0) > 0 or "예약" in p.get("url", "") for p in published_posts)
    header_title = "🚀 *[네이버 블로그 시간차 예약 발행 완료]*" if has_scheduled else "🚀 *[네이버 블로그 일일 무인 발행 완료]*"
    desc_text = f"총 {len(published_posts)}편의 포스트가 지정된 시간차로 네이버 블로그에 예약 등록되었습니다:\n" if has_scheduled else f"총 {len(published_posts)}편의 포스트가 정상 공개 발행되었습니다:\n"

    lines = [
        header_title,
        f"⏰ 작업 일시: {ts}",
        desc_text
    ]
    for i, p in enumerate(published_posts, 1):
        title = p.get("title", f"포스트 {i}")
        url = p.get("url", "#")
        category = p.get("category", "")
        reason = p.get("selection_reason", "")
        delay = p.get("delay_hours", 0)
        target_time = p.get("target_time")
        lines.append(f"*{i}. {title}*")
        if target_time:
            lines.append(f"⏰ 발행 모드: [{target_time}] 네이버 블로그 예약 발행")
        elif delay > 0:
            lines.append(f"⏰ 발행 모드: {delay}시간 후 예약 발행")
        elif "예약" in url:
            lines.append(f"⏰ 발행 모드: {url.split('(')[-1].rstrip(')')}")
        if category:
            lines.append(f"🏷️ 카테고리: {category}")
        if reason:
            lines.append(f"📊 선별 사유: {reason}")
        if "http" in url:
            lines.append(f"👉 [블로그 확인]({url})\n")
        else:
            lines.append(f"📌 {url}\n")
        
    lines.append("🏆 *스마트 큐레이션 엔진 무인 정상 가동 중*")
    return "\n".join(lines)

def format_error_message(error_str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"🚨 *[네이버 블로그 자동 발행 주의 알림]*\n"
        f"⏰ 발생 일시: {ts}\n"
        f"파이프라인 실행 중 다음 상태가 감지되었습니다:\n\n"
        f"```\n{error_str[:300]}\n```\n\n"
        f"👉 조치: 세션 만료 시 QR 코드를 갱신해 주세요."
    )

if __name__ == "__main__":
    test_msg = "🔔 [Blog Auto] 텔레그램 알림 시스템 연동 테스트 성공!\n스마트폰 알림이 정상적으로 수신되었습니다."
    send_telegram_alert(test_msg)
