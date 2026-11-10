#!/usr/bin/env bash
# Restaura una copia de seguridad de ApuntIA (FULL-23). Con la aplicación PARADA.
# Verifica la copia (SHA-256 e integridad) antes de tocar nada; si ya hay datos, exige
# --forzar y los aparta (no los borra). Si la copia es de una versión anterior, aplica
# las migraciones que falten.
#
#   fullstack/scripts/restaurar.sh copia.tar.gz [--forzar] [--docker]
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$RAIZ/back/motori_magenes"
COPIA="" FORZAR="" DOCKER=0
while [ $# -gt 0 ]; do
    case "$1" in
        --forzar) FORZAR="--forzar"; shift ;;
        --docker) DOCKER=1; shift ;;
        -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) echo "Opción desconocida: $1" >&2; exit 2 ;;
        *) COPIA="$1"; shift ;;
    esac
done
[ -f "$COPIA" ] || { echo "Indica la copia: restaurar.sh respaldos/apuntia-AAAAMMDD-HHMMSS.tar.gz" >&2; exit 2; }
COPIA="$(cd "$(dirname "$COPIA")" && pwd)/$(basename "$COPIA")"

if [ "$DOCKER" = 1 ]; then
    COMPOSE=(docker compose -f "$RAIZ/fullstack/compose.yaml")
    echo "Parando los servicios para restaurar…"
    "${COMPOSE[@]}" stop web backend
    # La copia (0600, del usuario del equipo) entra por la entrada estándar: el contenedor
    # corre con otro usuario y no podría leerla montada.
    "${COMPOSE[@]}" run --rm --no-deps -T backend sh -c \
        "cat > /tmp/copia.tar.gz && python -m app.datos.respaldo restaurar /tmp/copia.tar.gz /datos $FORZAR" < "$COPIA"
    "${COMPOSE[@]}" up -d --no-build --wait
    echo "Restaurado y en marcha."
    exit 0
fi

PID="$RAIZ/fullstack/.estado/backend.pid"
if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then
    echo "ApuntIA está en marcha: detenla primero con ./detener.sh" >&2
    exit 1
fi
[ -f "$RAIZ/fullstack/config/.env" ] && DATA_DIR="${DATA_DIR:-$(grep -E '^DATA_DIR=' "$RAIZ/fullstack/config/.env" | cut -d= -f2-)}"
DATA_DIR="${DATA_DIR:-datos}"
case "$DATA_DIR" in /*) ;; *) DATA_DIR="$BACKEND/$DATA_DIR" ;; esac
PY="$BACKEND/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
cd "$BACKEND"
"$PY" -m app.datos.respaldo restaurar "$COPIA" "$DATA_DIR" $FORZAR
echo "Arráncala con ./iniciar.sh"
