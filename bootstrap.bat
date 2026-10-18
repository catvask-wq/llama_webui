@echo off
setlocal EnableExtensions DisableDelayedExpansion

title GGUF Launcher

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "LAUNCHER=%SCRIPT_DIR%\launcher.py"
set "LAUNCHER_ARGS=%*"

echo ==============================================
echo             GGUF LAUNCHER
echo ==============================================
echo.

if not exist "%LAUNCHER%" (
    echo [ERROR] launcher.py was not found:
    echo "%LAUNCHER%"
    echo.
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%" >nul 2>nul

if errorlevel 1 (
    echo [ERROR] Cannot access launcher directory.
    pause
    exit /b 1
)

call :find_python

if defined PYTHON goto RUN_LAUNCHER

echo [INFO] Python was not found.
echo [INFO] Trying automatic installation...
echo.

where winget >nul 2>nul

if not errorlevel 1 goto INSTALL_WINGET

goto INSTALL_DIRECT


:INSTALL_WINGET
echo [INFO] Installing Python with winget...
echo.

winget install ^
    --id Python.Python.3.12 ^
    -e ^
    --silent ^
    --accept-package-agreements ^
    --accept-source-agreements

if errorlevel 1 (
    echo.
    echo [ERROR] winget failed to install Python.
    echo.
    echo Install Python manually from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

goto CHECK_AFTER_INSTALL


:INSTALL_DIRECT
echo [INFO] winget was not found.
echo [INFO] Downloading Python installer...
echo.

where powershell >nul 2>nul

if errorlevel 1 (
    echo [ERROR] PowerShell was not found.
    echo.
    echo Install Python manually from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

set "PYTHON_VERSION=3.12.7"
set "INSTALLER=%TEMP%\python-%PYTHON_VERSION%-installer.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
    "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'"

if errorlevel 1 (
    echo [ERROR] Failed to download Python installer.
    echo.
    pause
    exit /b 1
)

if not exist "%INSTALLER%" (
    echo [ERROR] Python installer was not downloaded.
    pause
    exit /b 1
)

echo [INFO] Installing Python...
echo.

"%INSTALLER%" ^
    /quiet ^
    InstallAllUsers=0 ^
    PrependPath=1 ^
    Include_test=0 ^
    Include_launcher=1 ^
    SimpleInstall=1

if errorlevel 1 (
    echo.
    echo [ERROR] Python installation failed.
    echo.
    del "%INSTALLER%" >nul 2>nul
    pause
    exit /b 1
)

del "%INSTALLER%" >nul 2>nul

goto CHECK_AFTER_INSTALL


:CHECK_AFTER_INSTALL
echo.
echo [INFO] Checking Python after installation...
echo.

call :find_python

if defined PYTHON goto RUN_LAUNCHER

if exist "%LocalAppData%\Programs\Python" (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
        if not defined PYTHON if exist "%%D\python.exe" (
            "%%D\python.exe" -c "import sys" >nul 2>nul

            if not errorlevel 1 (
                set "PYTHON=%%D\python.exe"
                set "PYTHON_ARGS="
            )
        )
    )
)

if defined PYTHON goto RUN_LAUNCHER

if exist "%ProgramFiles%\Python*" (
    for /d %%D in ("%ProgramFiles%\Python*") do (
        if not defined PYTHON if exist "%%D\python.exe" (
            "%%D\python.exe" -c "import sys" >nul 2>nul

            if not errorlevel 1 (
                set "PYTHON=%%D\python.exe"
                set "PYTHON_ARGS="
            )
        )
    )
)

if defined PYTHON goto RUN_LAUNCHER

echo.
echo [ERROR] Python could not be found after installation.
echo.
echo Install Python manually from:
echo https://www.python.org/downloads/
echo.
pause
exit /b 1


:RUN_LAUNCHER
echo.
echo [OK] Python found:
echo "%PYTHON%"

if defined PYTHON_ARGS (
    echo [INFO] Python arguments: %PYTHON_ARGS%
)

echo.
echo [INFO] Starting launcher...
echo.

set "PYTHONUNBUFFERED=1"

"%PYTHON%" %PYTHON_ARGS% "%LAUNCHER%" %LAUNCHER_ARGS%

set "RETURN_CODE=%ERRORLEVEL%"

if not "%RETURN_CODE%"=="0" (
    echo.
    echo [ERROR] Launcher exited with code %RETURN_CODE%.
    echo.

    if exist "%SCRIPT_DIR%\reports.txt" (
        echo Report file:
        echo "%SCRIPT_DIR%\reports.txt"
    )

    pause
    endlocal
    exit /b %RETURN_CODE%
)

echo.
echo [OK] Launcher finished successfully.

endlocal
exit /b 0


:find_python
set "PYTHON="
set "PYTHON_ARGS="

for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON (
        echo %%P | findstr /i /c:"WindowsApps" >nul

        if errorlevel 1 (
            "%%P" -c "import sys" >nul 2>nul

            if not errorlevel 1 (
                set "PYTHON=%%P"
                set "PYTHON_ARGS="
            )
        )
    )
)

if defined PYTHON goto :eof

for /f "delims=" %%P in ('where py 2^>nul') do (
    if not defined PYTHON (
        echo %%P | findstr /i /c:"WindowsApps" >nul

        if errorlevel 1 (
            "%%P" -3 -c "import sys" >nul 2>nul

            if not errorlevel 1 (
                set "PYTHON=%%P"
                set "PYTHON_ARGS=-3"
            )
        )
    )
)

goto :eof