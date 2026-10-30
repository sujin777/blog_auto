@echo off
setlocal
title 블로그 자동화 컨트롤 타워

:MENU
cls
echo ========================================================
echo   [AI Blog Runner] 블로그 통합 실행 메뉴
echo ========================================================
echo.
echo  [1] Reddit 24시간 인기글 수집 (npm run ingest)
echo  [2] 최근 글 네이버 일괄 자동 발행 (npm run publish)
echo  [3] 네이버 수동 포스팅 도구 (publish_manual.bat)
echo  [4] 모니터링 대시보드 웹 서버 실행 (npm run dashboard)
echo  [5] 전체 자동화 원클릭 실행 (auto_run.bat)
echo  [0] 프로그램 종료
echo.
echo ========================================================

set SEL=
set /p SEL="실행할 번호를 입력하세요 (0~5): "

if "%SEL%"=="" goto :MENU
if "%SEL%"=="1" goto :INGEST
if "%SEL%"=="2" goto :PUBLISH
if "%SEL%"=="3" goto :MANUAL
if "%SEL%"=="4" goto :DASHBOARD
if "%SEL%"=="5" goto :AUTO
if "%SEL%"=="0" goto :EXIT

echo.
echo [오류] 잘못된 번호입니다. 0~5 사이의 번호를 입력해주세요.
pause
goto :MENU

:INGEST
echo.
echo ========================================================
echo   [실행] Reddit 24시간 인기글 수집 시작...
echo ========================================================
call npm run ingest
goto :FINISH

:PUBLISH
echo.
echo ========================================================
echo   [실행] 최근 글 네이버 일괄 자동 발행 시작...
echo ========================================================
call npm run publish
goto :FINISH

:MANUAL
echo.
echo ========================================================
echo   [실행] 네이버 수동 포스팅 도구 실행...
echo ========================================================
call publish_manual.bat
goto :FINISH

:DASHBOARD
echo.
echo ========================================================
echo   [실행] 대시보드 서버 실행 (http://localhost:3000)...
echo ========================================================
call npm run dashboard
goto :FINISH

:AUTO
echo.
echo ========================================================
echo   [실행] 전체 자동화 파이프라인 실행...
echo ========================================================
call auto_run.bat
goto :FINISH

:FINISH
echo.
echo ========================================================
echo   선택한 작업이 완료되었습니다.
echo ========================================================
pause
goto :MENU

:EXIT
echo.
echo 블로그 자동화 프로그램을 종료합니다.
exit /b 0
