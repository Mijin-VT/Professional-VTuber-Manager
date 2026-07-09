@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Check if python is in PATH and >= 3.10
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if !errorLevel! == 0 (
    python debug_run.py
    exit /b 0
)

:: If not, check local appdata
set "USER_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "!USER_PYTHON!" (
    "!USER_PYTHON!" debug_run.py
    exit /b 0
)

:: Check Program Files
set "SYSTEM_PYTHON=%ProgramFiles%\Python\Python312\python.exe"
if exist "!SYSTEM_PYTHON!" (
    "!SYSTEM_PYTHON!" debug_run.py
    exit /b 0
)

:: Check System Drive
set "SYSTEM_PYTHON2=%SystemDrive%\Python312\python.exe"
if exist "!SYSTEM_PYTHON2!" (
    "!SYSTEM_PYTHON2!" debug_run.py
    exit /b 0
)

:: Fallback to python in path
python debug_run.py
