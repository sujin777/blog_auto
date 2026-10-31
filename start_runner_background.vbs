Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'Runner.Listener.exe'")
If colProcesses.Count = 0 Then
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.CurrentDirectory = "C:\DEV\actions-runner"
    WshShell.Run """C:\DEV\actions-runner\bin\Runner.Listener.exe"" run", 0, False
    WScript.Echo "GitHub Actions Self-Hosted Runner가 백그라운드에서 성공적으로 시작되었습니다!"
Else
    WScript.Echo "GitHub Actions Runner가 이미 정상 실행 중입니다."
End If

