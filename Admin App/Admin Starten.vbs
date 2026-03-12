Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
' Run python script completely hidden (0)
WshShell.Run "python admin_app.py", 0, False
Set WshShell = Nothing
