@ECHO OFF

CD venv/Scripts

CALL activate.bat

cd ../..

#CALL requirements.bat

CALL py app.py