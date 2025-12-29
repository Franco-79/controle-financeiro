@echo off
:: Entra na pasta onde este arquivo está salvo
cd /d "%~dp0"

:: Executa o comando do Streamlit
echo Iniciando o Controle Financeiro...
python -m streamlit run app.py

:: Se der erro, pausa para ler o que aconteceu
pause