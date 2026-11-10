#!/usr/bin/env bash
# Copia de seguridad de los datos de ApuntIA (FULL-23): base de datos + archivos de los
# usuarios en respaldos/apuntia-<fecha>.tar.gz (0600; respaldos/ está en .gitignore).
# Se puede hacer con la aplicación en marcha (copia consistente de SQLite).
#
#   fullstack/scripts/respaldar.sh [--docker] [--destino archivo.tar.gz]
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$RAIZ/back/motori_magenes"
DOCKER=0 DESTINO="$RAIZ/respaldos/apuntia-$(date +%Y%m%d-%H%M%S).tar.gz"
while [ $# -gt 0 ]; do
    case "$1" in
        --docker) DOCKER=1; shift ;;
        --destino) DESTINO="$2"; shift 2 ;;
        -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; exit 2 ;;
    esac
done
mkdir -p "$(dirname "$DESTINO")"
DESTINO="$(cd "$(dirname "$DESTINO")" && pwd)/$(basename "$DESTINO")"
umask 077

if [ "$DOCKER" = 1 ]; then
    COMPOSE=(docker compose -f "$RAIZ/fullstack/compose.yaml")
    "${COMPOSE[@]}" exec -T backend python -m app.datos.respaldo crear /datos /tmp/respaldo.tar.gz
    # /tmp es tmpfs (sistema de solo lectura): «docker cp» no lo ve; se copia por la salida estándar.
    "${COMPOSE[@]}" exec -T backend cat /tmp/respaldo.tar.gz > "$DESTINO"
    "${COMPOSE[@]}" exec -T backend rm -f /tmp/respaldo.tar.gz
    chmod 600 "$DESTINO"
    echo "Copia guardada en $DESTINO"
    exit 0
fi

[ -f "$RAIZ/fullstack/config/.env" ] && DATA_DIR="${DATA_DIR:-$(grep -E '^DATA_DIR=' "$RAIZ/fullstack/config/.env" | cut -d= -f2-)}"
DATA_DIR="${DATA_DIR:-datos}"
case "$DATA_DIR" in /*) ;; *) DATA_DIR="$BACKEND/$DATA_DIR" ;; esac
PY="$BACKEND/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
cd "$BACKEND"
"$PY" -m app.datos.respaldo crear "$DATA_DIR" "$DESTINO"
"$PY" -m app.datos.respaldo verificar "$DESTINO"
