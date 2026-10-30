@echo off
title 블로그 파이프라인 자동 실행기

echo ========================================================
echo   [AI Blog Runner] AI 블로그 자동화 파이프라인
echo ========================================================
echo.
echo [1] 전체 자동 실행 (1단계: Reddit 수집 -^> 2단계: 네이버 일괄 발행)
echo [2] 1단계만 실행: Reddit 최신 24시간 인기글 수집 (Ingest)
echo [3] 2단계만 실행: 최근 output 폴더 글 네이버 일괄 자동 발행 (Publish)
echo [4] 대시보드 모니터링 서버 실행 (Dashboard)
echo.
set /p CHOICE="실행할 번호를 입력하세요 (기본값: 1): "
if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="1" goto :ALL
if "%CHOICE%"=="2" goto :INGEST
if "%CHOICE%"=="3" goto :PUBLISH
if "%CHOICE%"=="4" goto :DASHBOARD
goto :ALL

:ALL
echo.
echo ========================================================
echo   [1단계] Reddit 인기 포스트 수집 시작...
echo ========================================================
call node .agents/skills/ingest-reddit-posts/scripts/test_reddit.js
if errorlevel 1 (
    echo.
    echo [경고] Reddit 수집 중 오류가 발생했습니다.
)

echo.
echo ========================================================
echo   [2단계] 네이버 블로그 일괄 자동 발행 시작...
echo ========================================================
call publish_naver_all.bat
goto :FINISH

:INGEST
echo.
echo [실행] Reddit 포스트 수집을 시작합니다...
call node .agents/skills/ingest-reddit-posts/scripts/test_reddit.js
goto :FINISH

:PUBLISH
echo.
echo [실행] 최신 글 네이버 일괄 자동 발행을 시작합니다...
call publish_naver_all.bat
goto :FINISH

:DASHBOARD
echo.
echo [실행] 모니터링 대시보드 서버를 실행합니다...
call node dashboard/server.js
goto :FINISH

:FINISH
echo.
echo ========================================================
echo   모든 작업이 종료되었습니다.
echo ========================================================
pause
