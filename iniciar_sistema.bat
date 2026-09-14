@echo off
title Sistema Cuidado Articular y Movimiento

cd /d "%~dp0"

echo ==========================================
echo  Iniciando sistema Cuidado Articular
echo ==========================================
echo.

if not exist "app.py" (
    echo ERROR: No se encontro app.py en esta carpeta.
    echo Verifica que este archivo este dentro de la carpeta principal del proyecto.
    pause
    exit /b
)

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: No se encontro el entorno virtual venv.
    echo Primero debes crear o copiar el entorno virtual del proyecto.
    pause
    exit /b
)

call "venv\Scripts\activate.bat"

echo Entorno virtual activado.
echo Abriendo la aplicacion...
echo.

streamlit run app.py

pause