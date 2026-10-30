@echo off
setlocal
title 네이버 블로그 수동 포스팅 도구

echo ========================================================
echo   [Naver Blog Manual Publisher Runner]
echo ========================================================
echo.

python publish_manual.py %*

echo.
pause
