@ECHO OFF
taskkill /im RenewedTroveTools.exe /F
taskkill /im flet.exe /F
msiexec /i %2 /qb+! TARGETDIR=%1
del /q %3
start %1
pause