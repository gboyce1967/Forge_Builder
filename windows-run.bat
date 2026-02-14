@echo off
REM Forge Builder Launcher for Windows
REM Installs requirements and runs the script

echo ========================================
echo    Forge Builder - Setup ^& Launch
echo ========================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.6+ from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Verify Python version
python --version 2>&1 | findstr /R "Python 3\." >nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 is required.
    echo         Install Python 3.6+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [*] Using: %%i

REM Check for pip
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip is not installed.
    echo         Run: python -m ensurepip --upgrade
    pause
    exit /b 1
)

REM Install requirements
echo [*] Checking dependencies...
python -c "import reportlab" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] Installing reportlab...
    python -m pip install --user reportlab
) else (
    echo [*] reportlab already installed
)

echo.
echo [*] Launching Forge Designer...
echo ========================================
echo.

REM Run the script, passing through any arguments
python "%~dp0ForgeDesigner.py" %*

pause
