$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = "$desktop\Smart Search Pro.lnk"

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "C:\Program Files\Python313\pythonw.exe"
$Shortcut.Arguments = '"C:\Users\ramos\.local\bin\smart_search\app.py"'
$Shortcut.WorkingDirectory = "C:\Users\ramos\.local\bin\smart_search"
$Shortcut.Description = "Smart Search Pro - Advanced File Search"
$Shortcut.Save()

Write-Host "Shortcut created at: $shortcutPath"
