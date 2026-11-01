Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = objWMIService.ExecQuery("Select * from Win32_Process Where (Name = 'python.exe' or Name = 'pythonw.exe') and CommandLine Like '%telegram_commander.py%'")
If colProcesses.Count = 0 Then
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.CurrentDirectory = "C:\DEV\261025_blog_auto"
    WshShell.Run """C:\Users\jin81\AppData\Local\Programs\Python\Python311\python.exe"" ""C:\DEV\261025_blog_auto\telegram_commander.py""", 0, False
End If
