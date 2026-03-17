Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
' Run pythonw script (1 allows GUI to show, pythonw prevents console)
WshShell.Run "pythonw.exe admin_app.py", 1, False
Set WshShell = Nothing
