@echo off
setlocal
chcp 65001 > nul
title [AI Blog Runner] 윈도우 무인 스케줄러 등록 마법사

echo ========================================================
echo   ⏰ [AI Blog Runner] 매일 무인 자동 실행 스케줄러 등록
echo ========================================================
echo.
echo 이 스크립트는 매일 지정된 시각에 사용자가 컴퓨터를 직접 조작하지 않아도
echo 백그라운드에서 자동으로 블로그를 수집, 작성, 발행하도록 등록합니다.
echo.
echo (참고: 절전 모드에서도 스스로 깨어나 실행되도록 전원 옵션이 연동됩니다)
echo.

set TASK_NAME=AutoBlogRunnerDaily
set SCRIPT_PATH=c:\DEV\261025_blog_auto\auto_run_complete.bat

set RUN_TIME=08:30
set /p USER_TIME="매일 실행할 시각을 입력하세요 (기본값: 08:30, 24시간 형식): "
if not "%USER_TIME%"=="" set RUN_TIME=%USER_TIME%

echo.
echo [등록 진행 중] 매일 %RUN_TIME% 에 실행되도록 윈도우 작업 스케줄러에 등록합니다...

schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc daily /st %RUN_TIME% /f /rl HIGHEST

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 무인 자동 스케줄러 등록이 성공적으로 완료되었습니다!
    echo   - 작업 이름: %TASK_NAME%
    echo   - 실행 주기: 매일 %RUN_TIME%
    echo   - 실행 대상: %SCRIPT_PATH%
    echo ========================================================
) else (
    echo.
    echo ⚠️ 권한 오류: 관리자 권한으로 실행해야 스케줄러에 등록할 수 있습니다.
    echo 'register_scheduler.bat' 파일을 마우스 우클릭 -> [관리자 권한으로 실행]을 눌러주세요.
)

echo.
pause

