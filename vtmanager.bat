@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Check if python is in PATH and >= 3.10
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if !errorLevel! == 0 (
    start "" pythonw main.py
    exit /b 0
)

:: If not, check local appdata
set "USER_PYTHON=%LocalAppData%\Programs\Python\Python312\pythonw.exe"
if exist "!USER_PYTHON!" (
    start "" "!USER_PYTHON!" main.py
    exit /b 0
)

:: Check Program Files
set "SYSTEM_PYTHON=%ProgramFiles%\Python\Python312\pythonw.exe"
if exist "!SYSTEM_PYTHON!" (
    start "" "!SYSTEM_PYTHON!" main.py
    exit /b 0
)

:: Check System Drive
set "SYSTEM_PYTHON2=%SystemDrive%\Python312\pythonw.exe"
if exist "!SYSTEM_PYTHON2!" (
    start "" "!SYSTEM_PYTHON2!" main.py
    exit /b 0
)

:: Fallback to pythonw in path
start "" pythonw main.py
