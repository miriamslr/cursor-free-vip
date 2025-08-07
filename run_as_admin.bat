@echo off
:: Verifica se está sendo executado como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Executando com privilégios de administrador...
) else (
    echo Solicitando privilégios de administrador...
    powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c cd /d %~dp0 && %~dp0run_as_admin.bat'"
    exit /b
)

:: Navega até o diretório do script
cd /d %~dp0

:: Ativa o ambiente virtual (se existir)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Ambiente virtual não encontrado. Certifique-se de que o ambiente virtual está configurado.
    pause
    exit /b
)

:: Instala as dependências, se necessário
pip install -r requirements.txt

:: Executa o script principal
python main.py

:: Mantém a janela aberta para visualização
pause
