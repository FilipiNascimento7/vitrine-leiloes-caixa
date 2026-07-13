@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Atualizando a vitrine de imoveis da Caixa (Curitiba + RMC)...
echo.
pip install -q -r requirements.txt
python build.py
echo.
echo  Pronto. Abrindo a vitrine...
start "" "docs\vitrine_offline.html"
pause
