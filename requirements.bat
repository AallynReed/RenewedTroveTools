@ECHO OFF
ECHO Launching virtual environment
CALL .\venv\Scripts\activate.bat > nul
ECHO Cleaning up packages
CALL pip freeze > _pip_freeze.txt
FOR /f %%i IN ("_pip_freeze.txt") DO SET size=%%~zi
IF %size% gtr 0 CALL pip uninstall -r _pip_freeze.txt -y > nul
CALL del _pip_freeze.txt > nul
ECHO Installing requirements...
CALL python -m pip install -U pip setuptools -r requirements.txt --no-cache-dir --force-reinstall > nul
ECHO Installed requirements
PAUSE