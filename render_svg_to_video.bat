@echo off
setlocal enabledelayedexpansion
title Pixel2SVG - Render SVG to Video (Adobe Stock CFR 60 FPS)

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
echo   [1] 1080p Full HD (1920x1080) - Standar Adobe Stock / Broadcast [DEFAULT]
echo   [2] 4K Ultra HD   (3840x2160) - Premium UHD (Vektor Murni, Tajam Tanpa Stretch)
echo   [3] 720p HD       (1280x720)  - File Ringan / Draft Cepat
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

:: Interactive Quality / Codec Profile Prompt
echo.
echo Pilih Profil Kualitas Encoder:
echo   [1] Pristine Master (H.264 CRF 10 + Animation Tune + Full Range) [DEFAULT]
echo   [2] High Quality    (H.264 CRF 14 + Animation Tune)
echo   [3] Apple ProRes 422 HQ (.MOV) - 10-Bit Broadcast Master Uncompressed
set /p QUAL_CHOICE="Pilihan (1/2/3) [1]: "
if "%QUAL_CHOICE%"=="" set QUAL_CHOICE=1
if "%QUAL_CHOICE%"=="1" (
    set CODEC_PARAM=--codec h264 --crf 10
    set QUAL_LABEL=H.264 CRF 10 (Pristine Master)
)
if "%QUAL_CHOICE%"=="2" (
    set CODEC_PARAM=--codec h264 --crf 14
    set QUAL_LABEL=H.264 CRF 14 (High Quality)
)
if "%QUAL_CHOICE%"=="3" (
    set CODEC_PARAM=--codec prores
    set QUAL_LABEL=Apple ProRes 422 HQ 10-Bit (.MOV)
)

echo.
echo --------------------------------------------------------------
echo   Konfigurasi : Resolusi = %RESOLUTION%, Loop = %LOOPS%x
echo   Kualitas    : %QUAL_LABEL%
echo --------------------------------------------------------------
echo.

:: Check if files were dragged and dropped onto the .bat script
if "%~1"=="" (
    echo Tidak ada file yang di-drag-and-drop.
    echo Menjalankan wizard pencarian file di direktori kerja...
    echo.
    python scripts\export_video.py --res %RESOLUTION% --loops %LOOPS% %CODEC_PARAM%
) else (
    echo Memproses file yang di-drop ke script...
    python scripts\export_video.py --res %RESOLUTION% --loops %LOOPS% %CODEC_PARAM% %*
)

echo.
echo ==============================================================
echo   Semua tugas render telah selesai!
echo ==============================================================
echo.
pause
