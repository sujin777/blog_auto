@echo off
setlocal
chcp 65001 > nul
title [AI Blog Runner] 1-Click 무인 전자동 블로그 파이프라인

echo ========================================================
echo   🚀 [AI Blog Runner] 완전 무인 자동화 파이프라인
echo   - 1단계: Reddit r/ClaudeAI 최신 24시간 인기글 자동 수집
echo   - 2단계: Gemini 3.8 Flash 엔진 기반 고품질 포스트 3편 및 1:1 도해 자동 생성
echo   - 3단계: 네이버 블로그 스마트에디터 ONE 자동 업로드 및 발행
echo ========================================================
echo.

cd /d "c:\DEV\261025_blog_auto"
python -u auto_pipeline.py

echo.
echo ========================================================
echo   작업이 완료되었습니다.
echo ========================================================
pause

