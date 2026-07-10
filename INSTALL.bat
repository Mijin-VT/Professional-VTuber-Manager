@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

set "PROGRESS_FILE=%~1"

:: Define pause command (silent if PROGRESS_FILE is defined)
if not "!PROGRESS_FILE!"=="" (
    set "PAUSE_CMD=rem"
) else (
    set "PAUSE_CMD=pause"
)

if not "!PROGRESS_FILE!"=="" echo 0 > "!PROGRESS_FILE!"


echo ===================================================
echo   VT Manager - Dependency and Python Installer
echo ===================================================
echo.

:: 1. Check if running as Administrator (optional but recommended)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrator privileges.
) else (
    echo [WARNING] You are not running as Administrator. If a program installation fails, right-click INSTALL.bat and choose "Run as administrator".
)
echo.

:: 2. Check that winget is available (needed for the system-level installs below)
set "HAS_WINGET=1"
winget --version >nul 2>&1
if !errorLevel! neq 0 (
    set "HAS_WINGET=0"
    echo [WARNING] winget was not found on this system. Automatic installation of Python/FFmpeg/VC++ Redistributable will be skipped.
    echo You can install winget from the "App Installer" package in the Microsoft Store, or install the programs below manually.
    echo.
)

:: 3. Determine Python Command
set "PYTHON_CMD=python"
set "PYTHON_INSTALLED=0"

:: Verify if python is in PATH and meets version requirement (>= 3.10)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is already installed and meets the minimum version requirement (3.10+). Skipping install.
    set "PYTHON_INSTALLED=1"
) else (
    python --version >nul 2>&1
    if !errorLevel! == 0 (
        echo [INFO] Python was detected but it is older than 3.10. An upgrade is required.
    ) else (
        echo [INFO] Python is not installed in PATH.
    )
)

:: 4. Install Python if missing or outdated
if not "!PROGRESS_FILE!"=="" echo 10 > "!PROGRESS_FILE!"
if "%PYTHON_INSTALLED%"=="0" (
    :: Check if local Python installer exists in programs folder
    set "LOCAL_PYTHON_EXE="
    if exist "programs\" (
        for %%f in (programs\python-*.exe) do (
            set "LOCAL_PYTHON_EXE=%%f"
        )
    )

    if not "!LOCAL_PYTHON_EXE!"=="" (
        echo [PROCESS] Found local Python installer: !LOCAL_PYTHON_EXE!
        powershell -Command "Unblock-File -Path '!LOCAL_PYTHON_EXE!'" >nul 2>&1
        echo [PROCESS] Installing Python silently...
        start /wait "" "!LOCAL_PYTHON_EXE!" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        :: Verify if it installed successfully
        set "USER_PYTHON_PATH=%LocalAppData%\Programs\Python\Python312\python.exe"
        set "SYSTEM_PYTHON_PATH=%ProgramFiles%\Python\Python312\python.exe"
        set "SYSTEM_PYTHON_PATH2=%SystemDrive%\Python312\python.exe"
        
        :: Scan common paths for Python versions
        for %%v in (312 313 311 310) do (
            if not "!PYTHON_INSTALLED!"=="1" (
                set "TEST_USER=%LocalAppData%\Programs\Python\Python%%v\python.exe"
                set "TEST_SYS=%ProgramFiles%\Python\Python%%v\python.exe"
                set "TEST_SYS2=%SystemDrive%\Python%%v\python.exe"
                if exist "!TEST_USER!" (
                    set "PYTHON_CMD=!TEST_USER!"
                    set "PYTHON_INSTALLED=1"
                ) else if exist "!TEST_SYS!" (
                    set "PYTHON_CMD=!TEST_SYS!"
                    set "PYTHON_INSTALLED=1"
                ) else if exist "!TEST_SYS2!" (
                    set "PYTHON_CMD=!TEST_SYS2!"
                    set "PYTHON_INSTALLED=1"
                )
            )
        )
    )

    :: If still not installed, fall back to Winget
    if "!PYTHON_INSTALLED!"=="0" (
        if "!HAS_WINGET!"=="0" (
            echo [ERROR] Python 3.10+ is required, no local installer found, and winget is unavailable.
            echo Please download and install Python 3.10+ manually from: https://www.python.org/downloads/
            echo Make sure to check the "Add python.exe to PATH" box during installation.
            !PAUSE_CMD!
            exit /b 1
        )

        echo [PROCESS] Attempting to install Python 3.12 via Winget...
        winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements

        if !errorLevel! == 0 (
            echo [OK] Python 3.12 was installed successfully via Winget.

            set "USER_PYTHON_PATH=%LocalAppData%\Programs\Python\Python312\python.exe"
            set "SYSTEM_PYTHON_PATH=%ProgramFiles%\Python\Python312\python.exe"
            set "SYSTEM_PYTHON_PATH2=%SystemDrive%\Python312\python.exe"

            if exist "!USER_PYTHON_PATH!" (
                set "PYTHON_CMD=!USER_PYTHON_PATH!"
                set "PYTHON_INSTALLED=1"
            ) else if exist "!SYSTEM_PYTHON_PATH!" (
                set "PYTHON_CMD=!SYSTEM_PYTHON_PATH!"
                set "PYTHON_INSTALLED=1"
            ) else if exist "!SYSTEM_PYTHON_PATH2!" (
                set "PYTHON_CMD=!SYSTEM_PYTHON_PATH2!"
                set "PYTHON_INSTALLED=1"
            ) else (
                echo [WARNING] Python was installed but could not be located in common paths.
                echo Please close this window, open a new console, and run INSTALL.bat again.
                !PAUSE_CMD!
                exit /b 1
            )
        ) else (
            echo [ERROR] Python could not be installed automatically.
            echo Please download and install Python 3.10+ manually from: https://www.python.org/downloads/
            echo Make sure to check the "Add python.exe to PATH" box during installation.
            !PAUSE_CMD!
            exit /b 1
        )
    )
)
if not "!PROGRESS_FILE!"=="" echo 25 > "!PROGRESS_FILE!"
echo.

:: 5. Verify and Install FFmpeg (required by pydub for audio processing)
ffmpeg -version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] FFmpeg is already installed in PATH. Skipping install.
) else (
    echo [INFO] FFmpeg was not detected in PATH.
    if "!HAS_WINGET!"=="1" (
        echo [PROCESS] Attempting to install FFmpeg via Winget...
        winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
        if !errorLevel! == 0 (
            echo [OK] FFmpeg was installed successfully.
            set "PATH=%PATH%;%ProgramFiles%\FFmpeg\bin"
        ) else (
            echo [WARNING] FFmpeg could not be installed automatically.
            echo Some audio processing features might be limited. You can install it manually from: https://ffmpeg.org/
        )
    ) else (
        echo [WARNING] winget is unavailable, skipping automatic FFmpeg install. Get it manually from: https://ffmpeg.org/
    )
)
if not "!PROGRESS_FILE!"=="" echo 45 > "!PROGRESS_FILE!"
echo.

:: 6. Verify and Install MSVC++ Redistributable (required for llama.cpp / Whisper native binaries)
if exist "%windir%\System32\vcruntime140.dll" (
    echo [OK] Microsoft Visual C++ Redistributable is already installed. Skipping install.
) else (
    echo [INFO] Microsoft Visual C++ Redistributable was not detected.
    if "!HAS_WINGET!"=="1" (
        echo [PROCESS] Attempting to install Microsoft Visual C++ Redistributable via Winget...
        winget install --id Microsoft.VCRedist.2015+.x64 -e --silent --accept-source-agreements --accept-package-agreements
        if !errorLevel! == 0 (
            echo [OK] Microsoft Visual C++ Redistributable was installed successfully.
        ) else (
            echo [WARNING] Microsoft Visual C++ Redistributable could not be installed automatically.
            echo Local llama-server or Whisper inference might fail to run. You can download it manually from Microsoft.
        )
    ) else (
        echo [WARNING] winget is unavailable, skipping automatic VC++ Redistributable install. Get it manually from Microsoft's website.
    )
)
if not "!PROGRESS_FILE!"=="" echo 60 > "!PROGRESS_FILE!"
echo.

:: 7. Verify and Install Git LFS
git lfs --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Git LFS is already installed. Skipping install.
) else (
    echo [INFO] Git LFS was not detected in PATH.
    echo [PROCESS] Downloading Git LFS installer from https://git-lfs.com...
    set "LFS_URL=https://github.com/git-lfs/git-lfs/releases/download/v3.6.0/git-lfs-windows-v3.6.0.exe"
    set "LFS_INSTALLER=%TEMP%\git-lfs-installer.exe"
    
    curl -L -s -o "!LFS_INSTALLER!" "!LFS_URL!"
    if not exist "!LFS_INSTALLER!" (
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '!LFS_URL!' -OutFile '!LFS_INSTALLER!'" >nul 2>&1
    )
    
    if exist "!LFS_INSTALLER!" (
        powershell -Command "Unblock-File -Path '!LFS_INSTALLER!'" >nul 2>&1
        echo [PROCESS] Installing Git LFS silently...
        "!LFS_INSTALLER!" /SILENT /NORESTART
        del "!LFS_INSTALLER!" >nul 2>&1
        
        :: Refresh PATH locally for the current session to include common Git/Git LFS locations
        set "PATH=%PATH%;%ProgramFiles%\Git\cmd;%ProgramFiles%\Git\bin;%ProgramFiles%\Git LFS;%LocalAppData%\Programs\Git LFS"
        
        git lfs --version >nul 2>&1
        if !errorLevel! == 0 (
            echo [OK] Git LFS was installed successfully.
        ) else (
            echo [WARNING] Git LFS was installed but is not yet in PATH. You may need to restart your terminal.
        )
    ) else (
        echo [WARNING] Could not download Git LFS from git-lfs.com.
        if "!HAS_WINGET!"=="1" (
            echo [PROCESS] Attempting to install Git LFS via Winget...
            winget install --id GitHub.GitLFS -e --silent --accept-source-agreements --accept-package-agreements
            if !errorLevel! == 0 (
                :: Refresh PATH locally
                set "PATH=%PATH%;%ProgramFiles%\Git\cmd;%ProgramFiles%\Git\bin;%ProgramFiles%\Git LFS;%LocalAppData%\Programs\Git LFS"
                echo [OK] Git LFS was installed successfully via Winget.
            ) else (
                echo [WARNING] Git LFS installation via Winget failed.
            )
        ) else (
            echo [WARNING] Winget is unavailable. Please install Git LFS manually from https://git-lfs.com
        )
    )
)
if not "!PROGRESS_FILE!"=="" echo 75 > "!PROGRESS_FILE!"

:: Activate Git LFS in the background
echo [PROCESS] Activating Git LFS in the background...
start /b cmd /c "git lfs install" >nul 2>&1
echo [OK] Git LFS activation command triggered in the background.
echo.

:: 8. Informational GPU check (does not install drivers automatically — CUDA DLLs already ship in .\bin)
nvidia-smi >nul 2>&1
if !errorLevel! == 0 (
    echo [OK] NVIDIA GPU driver detected. GPU-accelerated inference will be available.
) else (
    echo [INFO] No NVIDIA GPU driver detected. VT Manager will run in CPU-only mode.
    echo If you have an NVIDIA GPU, install the latest driver from https://www.nvidia.com/drivers for faster inference.
)
echo.

echo [PROCESS] Using Python at: %PYTHON_CMD%
echo.

:: 9. Upgrade Pip
echo [PROCESS] Upgrading pip...
"%PYTHON_CMD%" -m pip install --upgrade pip
if !errorLevel! neq 0 (
    echo [WARNING] Error upgrading pip, continuing with library installation...
)
if not "!PROGRESS_FILE!"=="" echo 80 > "!PROGRESS_FILE!"
echo.

:: 10. Install every package listed in requirements.txt, skipping the ones already installed
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found next to INSTALL.bat. Cannot continue.
    !PAUSE_CMD!
    exit /b 1
)

echo [PROCESS] Checking Python packages from requirements.txt...
echo.

for /f "usebackq delims=" %%L in ("requirements.txt") do (
    set "rawline=%%L"
    set "line=!rawline: =!"

    if not "!line!"=="" if "!line:~0,1!" neq "#" (
        set "pkgname=!line!"
        for /f "tokens=1 delims==<>! [" %%p in ("!line!") do set "pkgname=%%p"

        "%PYTHON_CMD%" -m pip show !pkgname! >nul 2>&1
        if !errorLevel! == 0 (
            echo [OK] !pkgname! is already installed. Skipping.
        ) else (
            echo [PROCESS] Installing !rawline! ...
            "%PYTHON_CMD%" -m pip install "!rawline!"
            if !errorLevel! neq 0 (
                echo [WARNING] Failed to install !pkgname!. VT Manager may run with that feature disabled.
            ) else (
                echo [OK] !pkgname! installed successfully.
            )
        )
    )
)
if not "!PROGRESS_FILE!"=="" echo 95 > "!PROGRESS_FILE!"
echo.

:: 11. Final verification of core libraries needed just to launch the app window
echo [PROCESS] Verifying core libraries...
"%PYTHON_CMD%" -c "import customtkinter, requests, psutil, jinja2, websocket; print('Core libraries: OK')" >nul 2>&1
if !errorLevel! == 0 (
    echo [OK] All core libraries were successfully installed and verified!
    echo.
    echo ===================================================
    echo   Installation completed successfully.
    echo   You can start the application using:
    echo   python main.py   or   python debug_run.py
    echo ===================================================
    if not "!PROGRESS_FILE!"=="" echo 100 > "!PROGRESS_FILE!"
) else (
    echo [WARNING] Core library verification failed. Check the messages above for the package that failed to install.
    echo Voice, memory, and web-search features are optional — VT Manager will still launch without them,
    echo but core libraries (CustomTkinter, requests, psutil, jinja2, websocket-client) are required.
    exit /b 2
)

echo.
!PAUSE_CMD!
exit /b 0
