#!/usr/bin/env bash
# MuscleSense Lab - prepara el entorno de Python en Linux
# (VM local de Claude o contenedor en la nube; tambien sirve en WSL).
#
# Uso:  bash scripts/preparar_linux.sh
#
# El entorno virtual se crea FUERA del proyecto (~/.venvs/musclesense) a proposito:
# un venv de Linux dentro de una carpeta de Windows no sirve en Windows y pesa cientos de MB.
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${MUSCLESENSE_VENV:-$HOME/.venvs/musclesense}"

if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r "$RAIZ/requirements.txt"
"$VENV/bin/python" -m pip check
cd "$RAIZ"
PYTHONDONTWRITEBYTECODE=1 "$VENV/bin/python" -m pytest tests/test_entorno.py -q -p no:cacheprovider
echo "Entorno listo. Activar con:  source $VENV/bin/activate"
