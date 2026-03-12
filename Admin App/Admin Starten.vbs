Set WshShell = CreateObject("WScript.Shell")
' Run python script completely hidden (0)
WshShell.Run "python admin_app.py", 0
Set WshShell = Nothing
