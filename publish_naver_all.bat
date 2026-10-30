@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   [Naver Blog SmartEditor ONE Auto Publisher]
echo ========================================================

set LATEST_DIR=
for /f "delims=" %%D in ('dir /b /ad /o-d output\2*') do (
    set "LATEST_DIR=output\%%D"
    goto :found
)

:found
if "%LATEST_DIR%"=="" (
    echo [ERROR] No target folder found in output directory.
    pause
    exit /b 1
)

echo [Target Folder] %LATEST_DIR%
echo.
python .agents/skills/publish-to-naver/scripts/naver_publish_all.py --dir "%LATEST_DIR%" --publish --headed --interval 10
echo.
echo [DONE] All posts processed.
pause
