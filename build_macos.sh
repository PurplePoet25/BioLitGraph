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

rm -rf build dist

python -m PyInstaller --noconfirm --clean BioLitGraph.spec

echo
echo "Build finished. Open dist/BioLitGraph.app"
