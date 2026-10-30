@echo off
setlocal
title 네이버 로그인 자동화 세션 빌더

echo ============================================================
echo   [Naver Login Session Builder]
echo   대상 블로그: https://blog.naver.com/gogo351
echo.
echo   화면에 브라우저 창이 열립니다.
echo   - 아이디/비번 직접 입력 또는 네이버앱 QR 스캔 시
echo     로그인을 자동 감지하여 세션(naver_session.json)을 저장합니다.
echo ============================================================

python -u .agents\skills\publish-to-naver\scripts\naver_login.py

echo.
pause
