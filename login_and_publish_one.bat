@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ============================================================
echo   [네이버 로그인부터 1개 블로그 자동 발행까지]
echo   대상 블로그: https://blog.naver.com/gogo351
echo ============================================================
python -u .agents\skills\publish-to-naver\scripts\login_and_publish_one.py
echo.
pause
