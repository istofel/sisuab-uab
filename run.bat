@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
py -3.12 -c "import sys;sys.exit(sys.version_info<(3,11))" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD (
    py -3.11 -c "import sys;sys.exit(sys.version_info<(3,11))" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
)
if not defined PYTHON_CMD (
    python -c "import sys;sys.exit(sys.version_info<(3,11))" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
    echo Python 3.11 ou superior e necessario para iniciar o Importador SisUAB.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 exit /b 1
)
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 exit /b 1
if not exist ".env" copy ".env.example" ".env" >nul
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
if not defined APP_PORT set "APP_PORT=8501"
.venv\Scripts\python.exe -m streamlit run app.py --server.port %APP_PORT%
