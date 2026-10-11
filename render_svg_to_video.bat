@echo off
setlocal enabledelayedexpansion
title Pixel2SVG - Render SVG to MP4 Video (Adobe Stock CFR 60 FPS)

echo ==============================================================
echo   🎥 Pixel2SVG - Batch Video Renderer (Adobe Stock Ready)
echo ==============================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak terdeteksi di PATH sistem!
    echo Silakan install Python 3.10+ dan pastikan dicentang 'Add to PATH'.
    pause
    exit /b 1
)

:: Check FFmpeg installation
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] FFmpeg tidak terdeteksi di PATH sistem!
    echo Silakan install FFmpeg dan tambahkan ke PATH.
    pause
    exit /b 1
)

:: Interactive Resolution Prompt
echo Pilih Resolusi Video:
echo   [1] 1080p Full HD (1920x1080) - Standar Adobe Stock [DEFAULT]
echo   [2] 4K Ultra HD   (3840x2160) - Premium Stock
echo   [3] 720p HD       (1280x720)  - File Ringan
set /p RES_CHOICE="Pilihan (1/2/3) [1]: "
if "%RES_CHOICE%"=="" set RES_CHOICE=1
if "%RES_CHOICE%"=="1" set RESOLUTION=1080p
if "%RES_CHOICE%"=="2" set RESOLUTION=4k
if "%RES_CHOICE%"=="3" set RESOLUTION=720p

:: Interactive xLoop Prompt
echo.
echo Pilih Jumlah Loop (xLoop):
echo   [1] 1x Loop
echo   [2] 2x Loops (Rekomendasi Adobe Stock: 15-30s) [DEFAULT]
echo   [3] 3x Loops
echo   [4] 5x Loops
set /p LOOP_CHOICE="Pilihan (1/2/3/4) [2]: "
if "%LOOP_CHOICE%"=="" set LOOP_CHOICE=2
if "%LOOP_CHOICE%"=="1" set LOOPS=1
if "%LOOP_CHOICE%"=="2" set LOOPS=2
if "%LOOP_CHOICE%"=="3" set LOOPS=3
if "%LOOP_CHOICE%"=="4" set LOOPS=5
if not defined LOOPS set LOOPS=%LOOP_CHOICE%

echo.
echo --------------------------------------------------------------
echo   Konfigurasi: Resolusi = %RESOLUTION%, Loop = %LOOPS%x
echo --------------------------------------------------------------
echo.

:: Check if files were dragged and dropped onto the .bat script
if "%~1"=="" (
    echo Tidak ada file yang di-drag-and-drop.
    echo Menjalankan wizard pencarian file di direktori kerja...
    echo.
    python scripts\export_video.py --res %RESOLUTION% --loops %LOOPS%
) else (
    echo Memproses file yang di-drop ke script...
    python scripts\export_video.py --res %RESOLUTION% --loops %LOOPS% %*
)

echo.
echo ==============================================================
echo   Semua tugas render telah selesai!
echo ==============================================================
echo.
pause
