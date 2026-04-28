@echo off
setlocal

cd /d "%~dp0"

echo [1/3] Instalando dependencias para app y empaquetado...
".venv311\Scripts\python.exe" -m pip install -r requirements_app.txt
if errorlevel 1 goto :error

echo [2/3] Limpiando builds previos...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist APP_PREDICCIONES_GUI.spec del /q APP_PREDICCIONES_GUI.spec

echo [3/3] Generando ejecutable...
".venv311\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --windowed ^
  --name AppPrediccionesAgua ^
  --collect-all tkinterdnd2 ^
  --add-data "modelo_red_neuronal_agua.keras;." ^
  --add-data "scaler_X.pkl;." ^
  --add-data "scaler_y.pkl;." ^
  APP_PREDICCIONES_GUI.py
if errorlevel 1 goto :error

echo.
echo Ejecutable generado en: dist\AppPrediccionesAgua\AppPrediccionesAgua.exe
echo Comparte la carpeta completa: dist\AppPrediccionesAgua
exit /b 0

:error
echo.
echo Error durante el empaquetado.
exit /b 1
