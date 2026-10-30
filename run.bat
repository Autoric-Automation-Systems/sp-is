@echo off
rem Launcher do SP-IS para Windows: duplo clique para abrir o aplicativo.
rem Na primeira execucao cria o .venv e instala as dependencias.
setlocal
title SP-IS - Smart Plant Inspection System
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto :deps

echo [SP-IS] Primeira execucao: criando o ambiente virtual .venv...
python --version >nul 2>nul
if not errorlevel 1 (
    python -m venv .venv
) else (
    py -3 --version >nul 2>nul
    if errorlevel 1 goto :no_python
    py -3 -m venv .venv
)
if errorlevel 1 goto :fail
if not exist "%VENV_PY%" goto :no_python

:deps
"%VENV_PY%" -c "import customtkinter, cv2, numpy, PIL, psutil" >nul 2>nul
if errorlevel 1 (
    echo [SP-IS] Instalando dependencias do requirements.txt...
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
)

echo [SP-IS] Iniciando o aplicativo. Feche esta janela para encerrar.
echo.
"%VENV_PY%" app.py
if errorlevel 1 (
    echo.
    echo [SP-IS] O aplicativo terminou com erro. Veja as mensagens acima.
    pause
)
exit /b 0

:no_python
echo.
echo [SP-IS] Python 3 nao encontrado.
echo         Instale em https://www.python.org/downloads/ e marque
echo         "Add python.exe to PATH" durante a instalacao.
echo.
pause
exit /b 1

:fail
echo.
echo [SP-IS] Falha ao preparar o ambiente. Veja as mensagens acima.
echo.
pause
exit /b 1
