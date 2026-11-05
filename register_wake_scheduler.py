import os
import sys
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = r"c:\DEV\10 month\261025_blog_auto"
RUNNER_BAT = os.path.join(ROOT_DIR, "auto_run.bat")

# auto_run.bat 내용 확인 및 보강
bat_content = f"""@echo off
chcp 65001 > nul
cd /d "{ROOT_DIR}"
python -u auto_pipeline.py >> "{ROOT_DIR}\\daily_scheduler.log" 2>&1
"""

with open(RUNNER_BAT, "w", encoding="utf-8") as f:
    f.write(bat_content)

print(f"📄 [실행 배치 파일 생성 완료] ➔ {RUNNER_BAT}")

# PowerShell 명령어로 Windows 작업 스케줄러 등록 (-WakeToRun 포함)
ps_script = f"""
$Action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "{RUNNER_BAT}"' -WorkingDirectory '{ROOT_DIR}'
$Trigger = New-ScheduledTaskTrigger -Daily -At 06:00AM
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Unregister-ScheduledTask -TaskName "NaverBlogDailyAutoPublish" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "NaverBlogDailyAutoPublish" -Action $Action -Trigger $Trigger -Settings $Settings -Description "매일 아침 06:00 국내 가정용 IP 네이버 블로그 무인 자동 발행 (절전모드 자동해제 및 부팅시 즉시실행)"
Get-ScheduledTask -TaskName "NaverBlogDailyAutoPublish" | Select-Object TaskName, State
"""

p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
print("PowerShell Output:")
print(p.stdout)
if p.stderr:
    print("PowerShell Stderr:", p.stderr)

if p.returncode == 0:
    print("🎉 [Windows 작업 스케줄러 등록 성공!]")
    print("   ⏰ 매일 아침 06:00 정각 실행")
    print("   💡 절전 모드 자동 해제 (-WakeToRun): ON")
    print("   🛡️ 미발행분 부팅 즉시 실행 (-StartWhenAvailable): ON")
else:
    print("⚠️ 스케줄러 등록 실패, 권한 확인 필요")

