@echo off
REM Karnak Timing Analysis - Environment Activation Script
REM This script activates the Python virtual environment and shows usage instructions

echo.
echo ========================================
echo  KARNAK TIMING ANALYSIS ENVIRONMENT
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "karnak_timing_env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv karnak_timing_env
    echo Then install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate the virtual environment
echo Activating Python virtual environment...
call karnak_timing_env\Scripts\activate.bat

echo.
echo ✅ Virtual environment activated!
echo.
echo Available commands:
echo   python extract_karnak_logs.py karnak --timing-only
echo   python karnak_timing_analyzer.py karnak_logs.txt --all
echo   python run_analysis.py
echo.
echo To deactivate: deactivate
echo.
echo ========================================

REM Keep the environment active
cmd /k
