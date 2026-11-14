#!/usr/bin/env bash
# Validación de todo ApuntIA con un solo comando (FULL-17). La usa CI y se puede ejecutar en local.
#
#   fullstack/scripts/validar.sh [--rapido | --completo] [--docker] [--informes CARPETA]
#
#   --rapido    (por defecto) pruebas del backend, evaluación del OCR, catálogo y reglas de la
#               interfaz, sintaxis de los scripts y de los workflows. ~1 min.
#   --completo  además: interfaz con API simulada, integración con el backend real (v1 y v2,
#               incluida accesibilidad) y scripts de arranque. ~6 min.
#   --docker    además: construir las imágenes y la prueba de humo de Docker Compose.
#   --informes  guarda informes JUnit (y capturas de la interfaz) en esa carpeta.
#
# Sale con 1 si falla cualquier paso (y sigue con los demás para dar el resumen completo).
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RAIZ"
MODO="rapido" DOCKER=0 INFORMES=""
while [ $# -gt 0 ]; do
    case "$1" in
        --rapido) MODO="rapido"; shift ;;
        --completo) MODO="completo"; shift ;;
        --docker) DOCKER=1; shift ;;
        --informes) INFORMES="${2:?falta la carpeta}"; shift 2 ;;
        -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; exit 2 ;;
    esac
done
PY="${PYTHON:-$(command -v python3 || command -v python)}"
[ -n "$INFORMES" ] && mkdir -p "$INFORMES" && INFORMES="$(cd "$INFORMES" && pwd)"

RESUMEN=() FALLOS=0
paso() {  # nombre, comando...
    local nombre="$1"; shift
    printf '\n\033[1;34m▶ %s\033[0m\n' "$nombre"
    local inicio=$SECONDS
    if "$@"; then RESUMEN+=("✔ $nombre ($((SECONDS - inicio)) s)")
    else RESUMEN+=("✖ $nombre ($((SECONDS - inicio)) s)"); FALLOS=$((FALLOS + 1)); fi
}
junit_node() {  # nombre del informe → opciones de node --test
    [ -n "$INFORMES" ] && echo "--test-reporter=spec --test-reporter-destination=stdout --test-reporter=junit --test-reporter-destination=$INFORMES/$1.xml"
}
junit_py() { [ -n "$INFORMES" ] && echo "--junitxml=$INFORMES/$1.xml"; }

# ------------------------------------------------------------------ rápido
paso "Backend: pytest" bash -c "cd back/motori_magenes && '$PY' -m pytest -p no:cacheprovider $(junit_py backend)"
paso "Servidor IA: pytest con Ollama simulado (BACK-35)" bash -c "'$PY' -m pytest ia_servidor/tests $(junit_py servidor-ia)"
if command -v tesseract >/dev/null 2>&1; then
    paso "Backend: evaluación real del OCR y las fórmulas" bash -c "cd back/motori_magenes && '$PY' -m pytest -p no:cacheprovider -m evaluacion $(junit_py evaluacion)"
    paso "Banco de evaluación: comparación con la línea base (FULL-19)" \
        "$PY" fullstack/evaluacion/evaluar.py --comparar fullstack/evaluacion/linea-base.json --salida "${INFORMES:-fullstack/evaluacion/resultados}"
    paso "Aceptación: escenarios educativos y criterios de rechazo (FULL-24)" \
        "$PY" fullstack/evaluacion/aceptacion.py --salida "${INFORMES:-fullstack/evaluacion/resultados}"
else
    RESUMEN+=("○ Evaluación del OCR omitida: Tesseract no está instalado")
fi
paso "Seguridad: sin secretos en el repositorio ni en su historial" "$PY" fullstack/scripts/buscar_secretos.py
paso "Documentación: enlaces internos, imágenes y documentos huérfanos (FULL-29)" "$PY" fullstack/scripts/comprobar_enlaces.py
paso "Documentación y tickets: pruebas del comprobador y del sincronizador (FULL-29)" bash -c "'$PY' -m unittest discover -s fullstack/tests/docs && '$PY' -m unittest discover -s fullstack/tests/tickets"
paso "Tickets: las fichas coinciden con el snapshot (sincronizador sin red, FULL-29)" bash -c "'$PY' fullstack/scripts/sincronizar_tickets.py --offline && git diff --exit-code -- fullstack/tickets"
paso "Interfaz: catálogo de mensajes y reglas de seguridad" bash -c "node --test $(junit_node catalogo) front/tests/catalogo.test.js"
paso "Sintaxis de los scripts de arranque" bash -c "for s in fullstack/scripts/*.sh iniciar.sh detener.sh; do bash -n \"\$s\" || exit 1; done"
paso "Sintaxis de los workflows y de compose.yaml" "$PY" - <<'PYEOF'
import glob, sys
try:
    import yaml
except ImportError:
    print("PyYAML no está instalado: se omite."); sys.exit(0)
for archivo in glob.glob(".github/workflows/*.yml") + ["fullstack/compose.yaml"]:
    yaml.safe_load(open(archivo, encoding="utf-8"))
    print("ok", archivo)
PYEOF

# ------------------------------------------------------------------ completo
if [ "$MODO" = "completo" ]; then
    paso "Interfaz con API simulada (Playwright)" bash -c "node --test $(junit_node interfaz) front/tests/interfaz.test.js"
    paso "Integración con el backend real (v1, v2, accesibilidad)" bash -c \
        "CAPTURAS='${INFORMES:+$INFORMES/capturas}' node --test --test-concurrency=1 $(junit_node integracion) 'fullstack/tests/integracion/'*.test.js"
    paso "Scripts de arranque y detención" bash -c "node --test $(junit_node scripts) fullstack/tests/scripts/*.test.js"
    paso "Entrega: humo con scripts, reinicio y demostración (FULL-22)" bash -c "node --test --test-name-pattern='scripts|demostración' $(junit_node entrega) fullstack/tests/entrega/entrega.test.js"
fi

# ------------------------------------------------------------------ docker
if [ "$DOCKER" = 1 ]; then
    if docker info >/dev/null 2>&1; then
        paso "Docker: construcción y prueba de humo" bash -c "node --test $(junit_node docker) fullstack/tests/docker/*.test.js"
        paso "Entrega: el mismo humo con Docker, down + up (FULL-22)" bash -c "APUNTIA_DOCKER_SIN_BUILD=1 node --test --test-name-pattern='Docker' $(junit_node entrega-docker) fullstack/tests/entrega/entrega.test.js"
    else
        RESUMEN+=("✖ Docker pedido pero no disponible"); FALLOS=$((FALLOS + 1))
    fi
fi

printf '\n\033[1mResumen (%s%s)\033[0m\n' "$MODO" "$([ "$DOCKER" = 1 ] && echo " + docker")"
printf '  %s\n' "${RESUMEN[@]}"
[ "$FALLOS" -eq 0 ] && { printf '\033[1;32mTodo correcto.\033[0m\n'; exit 0; }
printf '\033[1;31m%d paso(s) fallaron.\033[0m\n' "$FALLOS"
exit 1
