@echo off
setlocal

if not exist .venv (
    py -m venv .venv
)

call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements-build.txt

if not exist assets mkdir assets

for /f "usebackq delims=" %%I in (`py -c "import certifi; print(certifi.where())"`) do set CERTIFI_PEM=%%I
copy /Y "%CERTIFI_PEM%" "assets\cacert.pem" >nul

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

py -m PyInstaller --noconfirm --clean BioLitGraph.spec

echo.
echo Build finished. Open dist\BioLitGraph\BioLitGraph.exe
endlocal
