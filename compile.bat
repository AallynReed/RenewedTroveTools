@ECHO OFF
call .\venv\Scripts\activate.bat
echo Compiling Executable
py compile.py bdist_msi
PAUSE