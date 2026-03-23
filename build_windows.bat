@echo off
setlocal

if not exist .venv (
    py -m venv .venv
)
call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements-build.txt

py -m PyInstaller --noconfirm --clean --windowed --name BioLitGraph ^
  --icon assets\icons\biolitgraph_icon.ico ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --add-data "data;data" ^
  launcher.py

echo.
echo Build finished. Open dist\BioLitGraph\BioLitGraph.exe
endlocal
