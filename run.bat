@echo off
REM =====================================================
REM Script chay ung dung Quan ly Ban hang
REM =====================================================

echo.
echo ========================================
echo   KHOI DONG UNG DUNG QUAN LY BAN HANG
echo ========================================
echo.

REM Chuyen den thu muc src
cd /d "%~dp0src"

REM Chay ung dung Python
python main_form.py

REM Tam dung de xem loi (neu co)
if errorlevel 1 (
    echo.
    echo ========================================
    echo   CO LOI XAY RA! Vui long kiem tra.
    echo ========================================
    pause
)
