#!/usr/bin/env bash
# Diagnóstico de ApuntIA (FULL-21): salud, disponibilidad de dependencias, métricas y el final
# del registro, en modo local (scripts) o Docker. Los registros ya salen con los datos
# sensibles enmascarados por la aplicación.
#
#   fullstack/scripts/diagnostico.sh [--docker] [--puerto N] [--guardar archivo.txt]
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKER=0 PUERTO="${APUNTIA_PUERTO:-8000}" GUARDAR=""
while [ $# -gt 0 ]; do
    case "$1" in
        --docker) DOCKER=1; shift ;;
        --puerto) PUERTO="$2"; shift 2 ;;
        --guardar) GUARDAR="$2"; shift 2 ;;
        -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; exit 2 ;;
    esac
done
PY="$(command -v python3 || command -v python)"
COMPOSE=(docker compose -f "$RAIZ/fullstack/compose.yaml")

consultar() {  # ruta → JSON con formato (en Docker, desde dentro del contenedor del backend)
    local codigo='import json,sys,urllib.request,urllib.error
url=sys.argv[1]
try:
    r=urllib.request.urlopen(url,timeout=10); c=r.status; d=r.read()
except urllib.error.HTTPError as e:
    c=e.code; d=e.read()
except Exception as e:
    print(f"sin respuesta: {type(e).__name__}"); sys.exit(1)
try: print(f"HTTP {c}"); print(json.dumps(json.loads(d),ensure_ascii=False,indent=2))
except ValueError: print(d.decode(errors="replace")[:500])'
    if [ "$DOCKER" = 1 ]; then "${COMPOSE[@]}" exec -T backend python -c "$codigo" "http://127.0.0.1:8000$1"
    else "$PY" -c "$codigo" "http://127.0.0.1:$PUERTO$1"; fi
}

informe() {
    echo "== ApuntIA · diagnóstico ($( [ "$DOCKER" = 1 ] && echo Docker || echo "local, puerto $PUERTO" )) · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo; echo "== Salud (la aplicación responde): GET /salud"; consultar /salud
    echo; echo "== Disponibilidad de dependencias: GET /api/v2/listo"; consultar /api/v2/listo
    echo; echo "== Métricas (solo desde el propio equipo): GET /api/v2/diagnostico"; consultar /api/v2/diagnostico
    echo; echo "== Últimas líneas del registro"
    if [ "$DOCKER" = 1 ]; then "${COMPOSE[@]}" ps; "${COMPOSE[@]}" logs --no-color --tail 80 backend web
    elif [ -f "$RAIZ/fullstack/.estado/backend.log" ]; then tail -n 80 "$RAIZ/fullstack/.estado/backend.log"
    else echo "(no hay registro: ¿se arrancó con ./iniciar.sh?)"; fi
}

if [ -n "$GUARDAR" ]; then informe > "$GUARDAR" 2>&1; echo "Diagnóstico guardado en $GUARDAR"; else informe; fi
