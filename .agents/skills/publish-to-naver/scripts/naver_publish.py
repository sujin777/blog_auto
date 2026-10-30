import argparse
import os
import re
import sys
import time

import markdown
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SESSION_FILE = os.path.join(SKILL_DIR, "naver_session.json")
IMG_RE = re.compile(r"!\[(.*?)\]\((.*?)\)")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_env():
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR))), ".env"),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
            break


load_env()
NAVER_BLOG_ID = os.environ.get("NAVER_BLOG_ID", "").strip() or os.environ.get("NAVER_ID", "").strip()


def parse_markdown(md_file_path):
    with open(md_file_path, "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")

    title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")

    # 태그: '### 태그' 섹션 또는 마지막의 백틱/해시태그 라인
    tags, tag_idx = [], None
    for i, l in enumerate(lines):
        if l.strip() in ("### 태그", "### Tags"):
            tag_idx = i
            break
    search = lines[tag_idx + 1:] if tag_idx is not None else list(reversed(lines))
    for l in search:
        s = l.strip()
        if not s:
            continue
        if "`" in s:
            tags = re.findall(r"`([^`]+)`", s)
        elif s.startswith("#") and not s.startswith("# "):
            tags = [t.lstrip("#").strip() for t in s.split() if t.strip("#")]
        elif "," in s and tag_idx is not None:
            tags = [t.strip() for t in s.split(",") if t.strip()]
        if tags:
            break

    end = tag_idx if tag_idx is not None else len(lines)
    start = next((i + 1 for i, l in enumerate(lines) if l.startswith("# ")), 0)
    body = "\n".join(lines[start:end]).strip()
    return title, body, tags


def split_segments(body, md_dir):
    """본문을 [('html', ...), ('img', abs_path), ...] 순서로 분리"""
    segs, pos = [], 0
    for m in IMG_RE.finditer(body):
        text = body[pos:m.start()].strip()
        if text:
            segs.append(("html", text))
        p = m.group(2)
        abs_p = p if os.path.isabs(p) else os.path.abspath(os.path.join(md_dir, p))
        segs.append(("img", abs_p))
        pos = m.end()
    tail = body[pos:].strip()
    if tail:
        segs.append(("html", tail))
    out = []
    for kind, val in segs:
        if kind == "html":
            val = val.replace("&nbsp;", "")
            html = markdown.markdown(val, extensions=["tables", "fenced_code"])
            out.append(("html", html))
        else:
            out.append((kind, val))
    return out


def paste_html(page, html):
    page.evaluate(
        """async (h) => {
            const item = new ClipboardItem({
                'text/html': new Blob([h], {type: 'text/html'}),
                'text/plain': new Blob([h.replace(/<[^>]+>/g, '')], {type: 'text/plain'})
            });
            await navigator.clipboard.write([item]);
        }""",
        html,
    )
    page.keyboard.press("Control+V")
    page.wait_for_timeout(1200)


def shot(page, name, shots_dir):
    path = os.path.join(shots_dir, name)
    page.screenshot(path=path)
    log(f"📸 {path}")


def run(md_file, publish=False, headless=True):
    title, body, tags = parse_markdown(md_file)
    md_dir = os.path.dirname(os.path.abspath(md_file))
    shots_dir = os.path.join(md_dir, "naver_shots")
    os.makedirs(shots_dir, exist_ok=True)
    segments = split_segments(body, md_dir)

    log(f"블로그 ID: {NAVER_BLOG_ID} | 모드: {'발행' if publish else '임시저장'}")
    log(f"제목: {title}")
    log(f"태그 {len(tags)}개: {', '.join(tags[:10])}")
    log(f"본문 세그먼트: {sum(1 for s in segments if s[0]=='html')}개 텍스트 / "
        f"{sum(1 for s in segments if s[0]=='img')}개 이미지")

    if not os.path.exists(SESSION_FILE):
        log(f"❌ 세션 파일 없음: {SESSION_FILE} → naver_login.bat 먼저 실행")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1600, "height": 1000},
            permissions=["clipboard-read", "clipboard-write"],
        )
        page = context.new_page()
        page.on("dialog", lambda d: d.dismiss())

        try:
            log("글쓰기 페이지 진입...")
            page.goto(f"https://blog.naver.com/{NAVER_BLOG_ID}/postwrite", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            if "nidlogin" in page.url or "nid.naver.com" in page.url:
                log("🔑 세션 만료 감지 → 만료 쿠키 초기화 후 현재 브라우저 창에서 로그인 대기 중...")
                context.clear_cookies()
                page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
                page.bring_to_front()
                login_wait_start = time.time()
                while time.time() - login_wait_start < 600:
                    page.wait_for_timeout(1000)
                    try:
                        reg_btn = page.locator("button:has-text('등록'), a:has-text('등록'), #new\\.save").first
                        if reg_btn.is_visible():
                            reg_btn.click()
                            page.wait_for_timeout(800)
                    except Exception:
                        pass
                    cookies = context.cookies()
                    has_auth = any(c.get("name") == "NID_AUT" for c in cookies)
                    has_ses = any(c.get("name") == "NID_SES" for c in cookies)
                    if has_auth and has_ses and "nidlogin" not in page.url and "nid.naver.com" not in page.url:
                        context.storage_state(path=SESSION_FILE)
                        log(f"💾 로그인 감지 및 영구 세션 갱신 완료 ({SESSION_FILE})")
                        break
                page.goto(f"https://blog.naver.com/{NAVER_BLOG_ID}/postwrite", wait_until="domcontentloaded")

            page.wait_for_selector(".se-documentTitle", timeout=30000)
            page.wait_for_timeout(2500)

            # 임시저장 이어쓰기 팝업 → 취소
            cancel = page.locator(".se-popup-button-cancel")
            if cancel.count() and cancel.first.is_visible():
                cancel.first.click()
                log("임시저장 팝업 → [취소]")
                page.wait_for_timeout(800)
            help_close = page.locator(".se-help-panel-close-button")
            if help_close.count() and help_close.first.is_visible():
                help_close.first.click()
                log("도움말 패널 닫기")
                page.wait_for_timeout(500)

            # 제목
            page.locator(".se-documentTitle").first.click()
            page.keyboard.insert_text(title)
            log("제목 입력 완료")

            # 본문
            page.locator(".se-section-text, .se-component.se-text").first.click()
            page.wait_for_timeout(500)
            for i, (kind, val) in enumerate(segments, 1):
                if kind == "html":
                    paste_html(page, val)
                    log(f"  [{i}/{len(segments)}] 텍스트 블록 붙여넣기 ({len(val)}자 HTML)")
                else:
                    if not os.path.exists(val):
                        log(f"  [{i}/{len(segments)}] ⚠️ 이미지 없음, 건너뜀: {val}")
                        continue
                    with page.expect_file_chooser(timeout=15000) as fc:
                        page.locator("button.se-image-toolbar-button, button[data-name='image']").first.click()
                    fc.value.set_files(val)
                    page.wait_for_timeout(4000)
                    page.keyboard.press("End")
                    log(f"  [{i}/{len(segments)}] 이미지 업로드: {os.path.basename(val)}")
            shot(page, "01_body_done.png", shots_dir)

            if not publish:
                save_btn = page.locator("button[class*='save_btn']")
                save_btn.first.click()
                page.wait_for_timeout(3000)
                shot(page, "02_draft_saved.png", shots_dir)
                log("✅ 임시저장 완료 (블로그 > 글쓰기 > 임시저장 목록에서 확인 가능)")
                return

            # 발행 레이어
            page.locator("button[class*='publish_btn']").first.click()
            page.wait_for_timeout(2000)
            shot(page, "02_publish_layer.png", shots_dir)

            tag_input = page.locator("input[class*='tag_input'], input[placeholder*='태그']")
            if tags and tag_input.count():
                for t in tags[:10]:
                    tag_input.first.click()
                    page.keyboard.insert_text(t)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(250)
                log(f"태그 {min(len(tags), 10)}개 입력")

            page.locator("button[class*='confirm_btn']").first.click()
            page.wait_for_timeout(5000)
            shot(page, "03_published.png", shots_dir)
            log(f"🎉 발행 완료 → {page.url}")
        except Exception as e:
            log(f"❌ 에러: {e}")
            try:
                shot(page, "99_error.png", shots_dir)
            except Exception:
                pass
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Naver Blog SmartEditor ONE Publisher")
    ap.add_argument("--md-file", required=True)
    ap.add_argument("--image", required=False, help="(호환용, 미사용: 본문 첫 이미지가 대표이미지가 됨)")
    ap.add_argument("--publish", action="store_true", help="실제 발행 (기본은 임시저장)")
    ap.add_argument("--headed", action="store_true", help="브라우저 화면 표시")
    a = ap.parse_args()
    run(a.md_file, publish=a.publish, headless=not a.headed)
