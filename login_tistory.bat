@echo off
chcp 65001 > nul
echo ============================================================
echo   티스토리 카카오 로그인 전용 창을 실행합니다.
echo   열리는 브라우저 창에서 카카오 계정으로 1회 로그인해 주세요.
echo   (로그인이 완료되면 세션이 자동 저장되므로 창을 닫으셔도 됩니다)
echo ============================================================
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%USERPROFILE%\tmp\chrome-debug-tistory" "https://www.tistory.com/auth/login"
echo 로그인 완료 후 아무 키나 눌러주세요.
pause
