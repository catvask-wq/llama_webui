@echo off
chcp 65001 >nul
title GGUF Launcher
setlocal EnableExtensions

echo ==============================================
echo    GGUF LAUNCHER - проверка окружения
echo ==============================================
echo.

set "SCRIPT_DIR=%~dp0"

if not exist "%SCRIPT_DIR%launcher.py" (
    echo [ОШИБКА] Рядом с bootstrap.bat не найден файл launcher.py
    echo          Положите оба файла в одну папку и запустите снова.
    pause
    exit /b 1
)

rem ---------- ищем Python ----------

set "PY="

rem python из PATH, но с проверкой, что это НЕ заглушка Microsoft Store
where python >nul 2>nul && python --version >nul 2>nul && set "PY=python"

if not defined PY (
    where py >nul 2>nul && py -3 --version >nul 2>nul && set "PY=py -3"
)

if defined PY goto :have_python

echo [i] Python не найден. Пробую установить автоматически...
echo.

where winget >nul 2>nul
if not errorlevel 1 goto :winget

rem ---------- установка без winget ----------

echo [i] winget не найден. Скачиваю установщик с python.org...
set "INSTALLER=%TEMP%\python-installer.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%INSTALLER%'"
if errorlevel 1 (
    echo [ОШИБКА] Не удалось скачать установщик Python.
    echo          Проверьте интернет или скачайте Python вручную:
    echo          https://www.python.org/downloads/
    echo          При установке отметьте галочку "Add python.exe to PATH".
    pause
    exit /b 1
)
echo [i] Устанавливаю Python, это займёт пару минут...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 (
    echo [ОШИБКА] Установка Python завершилась с ошибкой.
    echo          Без Python работать не могу. Установите вручную:
    echo          https://www.python.org/downloads/
    pause
    exit /b 1
)
goto :find_after_install

rem ---------- установка через winget ----------

:winget
echo [i] Устанавливаю Python через winget, это займёт пару минут...
winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ОШИБКА] winget не смог установить Python.
    echo          Без Python работать не могу. Установите вручную:
    echo          https://www.python.org/downloads/
    pause
    exit /b 1
)

rem ---------- перепроверка после установки ----------

:find_after_install
set "PY="
where python >nul 2>nul && python --version >nul 2>nul && set "PY=python"
if defined PY goto :have_python
where py >nul 2>nul && py -3 --version >nul 2>nul && set "PY=py -3"
if defined PY goto :have_python

rem PATH в текущем окне не обновился - ищем установленный Python руками
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if defined PY goto :have_python
if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"
if defined PY goto :have_python
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if defined PY goto :have_python

echo.
echo [ОШИБКА] Python не удалось найти даже после установки.
echo          Без Python работать не могу. Закройте окно, установите
echo          Python вручную и запустите bootstrap.bat снова:
echo          https://www.python.org/downloads/
pause
exit /b 1

:have_python
echo.
echo [OK] Python найден
echo [i] Запускаю лаунчер...
echo.
%PY% "%SCRIPT_DIR%launcher.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [ОШИБКА] Лаунчер завершился с кодом %RC%.
    echo          Подробности смотрите выше и в файле:
    echo          %SCRIPT_DIR%reports.txt
    pause
)
endlocal