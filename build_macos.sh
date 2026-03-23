#!/usr/bin/env bash
set -e

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

mkdir -p assets
cp "$(python -c 'import certifi; print(certifi.where())')" assets/cacert.pem

python -m PyInstaller --noconfirm --clean --windowed --name BioLitGraph \
  --icon assets/icons/biolitgraph_icon.icns \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --add-data "data:data" \
  --add-data "assets:assets" \
  launcher.py

echo
echo "Build finished. Open dist/BioLitGraph.app"
