@ECHO OFF
timeout /t 3 /nobreak
msiexec /a %2 /qb+! TARGETDIR=%1
del /q %3
start %1
pause