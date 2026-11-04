@echo off
chcp 65001 > nul
cd /d "c:\DEV\261025_blog_auto"
python -u auto_pipeline.py >> "c:\DEV\261025_blog_auto\daily_scheduler.log" 2>&1
