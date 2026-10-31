@echo off
chcp 65001 > nul
echo ==================================================================
echo [GitHub Actions Self-Hosted Runner 1-Click 자동 설정]
echo ==================================================================
cd /d "%~dp0"
python setup_self_hosted_runner.py
pause

