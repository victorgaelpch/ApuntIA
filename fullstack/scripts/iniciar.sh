#!/usr/bin/env bash
# Arranca ApuntIA sin Docker (FULL-11): comprueba requisitos, prepara el entorno de
# Python, instala dependencias, inicia el backend (que también sirve la interfaz) y
# espera a que responda. Uso (desde cualquier carpeta):
#
#   ./iniciar.sh [--puerto N] [--red] [--sin-navegador] [--sin-venv] [--reinstalar] [--comprobar] [--demo]
#
#   --puerto N       puerto de la aplicación (por defecto APUNTIA_PUERTO o 8000)
#   --red            escuchar en la red local (para abrirla desde el móvil); por defecto solo este equipo
#   --sin-navegador  no abrir el navegador al terminar
#   --sin-venv       usar el Python actual en vez de crear back/motori_magenes/.venv (CI, pruebas)
#   --reinstalar     reinstalar las dependencias aunque no hayan cambiado
#   --comprobar      solo comprobar requisitos y configuración, sin instalar ni arrancar
#   --demo           modo demostración: datos APARTE en fullstack/.demo/ y una cuenta con apuntes sintéticos
#   --demo-nueva     como --demo, pero borra antes fullstack/.demo/ (solo esa carpeta) para empezar de cero
#
# Códigos de salida: 0 bien · 1 requisito ausente · 2 dependencias · 3 puerto ocupado · 4 no arrancó
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND="$RAIZ/back/motori_magenes"
ESTADO="$RAIZ/fullstack/.estado"
CONFIG="$RAIZ/fullstack/config/.env"

azul() { printf '\033[1;34m▶ %s\033[0m\n' "$*"; }
bien() { printf '\033[1;32m✔ %s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m⚠ %s\033[0m\n' "$*"; }
error() { printf '\033[1;31m✖ %s\033[0m\n' "$*" >&2; }

# ------------------------------------------------------------------ opciones
PUERTO_ARG="" RED=0 NAVEGADOR=1 VENV=1 REINSTALAR=0 SOLO_COMPROBAR=0 DEMO=0 DEMO_NUEVA=0
while [ $# -gt 0 ]; do
    case "$1" in
        --puerto) PUERTO_ARG="${2:-}"; shift 2 ;;
        --red) RED=1; shift ;;
        --sin-navegador) NAVEGADOR=0; shift ;;
        --sin-venv) VENV=0; shift ;;
        --reinstalar) REINSTALAR=1; shift ;;
        --comprobar) SOLO_COMPROBAR=1; shift ;;
        --demo) DEMO=1; shift ;;
        --demo-nueva) DEMO=1; DEMO_NUEVA=1; shift ;;
        -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) error "Opción desconocida: $1 (usa --help)"; exit 1 ;;
    esac
done

# ------------------------------------------------------------------ configuración
mkdir -p "$ESTADO"
# Demostración: SIEMPRE en su propia carpeta (manda sobre .env), nunca con los datos reales.
DEMO_DIR="${APUNTIA_DEMO_DIR:-$RAIZ/fullstack/.demo}"
[ "$DEMO" = 1 ] && export DATA_DIR="$DEMO_DIR/datos"
if [ ! -f "$CONFIG" ]; then
    cp "$RAIZ/fullstack/config/.env.example" "$CONFIG"
    bien "Creada la configuración local fullstack/config/.env (puedes editarla)."
fi
# Carga KEY=valor ignorando comentarios; las variables ya definidas en el entorno mandan.
while IFS='=' read -r clave valor; do
    [[ "$clave" =~ ^[A-Z_][A-Z0-9_]*$ ]] || continue
    valor="${valor%$'\r'}"
    [ -n "${!clave+x}" ] || export "$clave=$valor"
done < "$CONFIG"

PUERTO="${PUERTO_ARG:-${APUNTIA_PUERTO:-8000}}"
[[ "$PUERTO" =~ ^[0-9]+$ ]] && [ "$PUERTO" -ge 1024 ] && [ "$PUERTO" -le 65535 ] || { error "Puerto no válido: $PUERTO (usa 1024-65535)."; exit 1; }
HOST="127.0.0.1"; [ "$RED" = 1 ] && HOST="0.0.0.0"
URL="http://localhost:$PUERTO"

# ------------------------------------------------------------------ requisitos
azul "Comprobando requisitos"
PY=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1 && "$candidato" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PY="$(command -v "$candidato")"; break
    fi
done
if [ -z "$PY" ]; then
    error "Hace falta Python 3.10 o superior. Instálalo desde https://www.python.org/downloads/ (o con el gestor de paquetes) y vuelve a ejecutar."
    exit 1
fi
bien "Python $("$PY" -c 'import platform; print(platform.python_version())') ($PY)"

if command -v tesseract >/dev/null 2>&1; then
    idiomas="$(tesseract --list-langs 2>/dev/null | tail -n +2 | tr '\n' ' ')"
    bien "Tesseract $(tesseract --version 2>&1 | head -1 | awk '{print $2}') (idiomas: ${idiomas:-ninguno})"
    case " $idiomas " in *" spa "*) ;; *) aviso "Falta el idioma español de Tesseract (paquete tesseract-ocr-spa): el texto en español se leerá peor." ;; esac
else
    aviso "Tesseract no está instalado: «Mejorar una foto» funciona, pero los apuntes no se podrán analizar."
    aviso "Instálalo con: sudo apt install tesseract-ocr tesseract-ocr-spa  (macOS: brew install tesseract tesseract-lang)"
fi

# Backend Spring Boot: el repositorio NO tiene uno (ver docs/arranque.md). Si se añade en
# back/<carpeta>/ con mvnw o pom.xml, se detecta y se arranca también.
SPRING=""
for pom in "$RAIZ"/back/*/pom.xml "$RAIZ"/back/*/build.gradle; do
    [ -f "$pom" ] && [ "$(dirname "$pom")" != "$BACKEND" ] && SPRING="$(dirname "$pom")" && break
done
if [ -n "$SPRING" ]; then
    command -v java >/dev/null 2>&1 || { error "Hay un backend Spring Boot en ${SPRING#$RAIZ/} pero falta Java 17 o superior."; exit 1; }
    bien "Spring Boot detectado en ${SPRING#$RAIZ/} ($(java -version 2>&1 | head -1))"
else
    bien "Sin backend Spring Boot en el repositorio: no hace falta Java."
fi

# ¿Puerto libre? Si ya responde ApuntIA, no se arranca otra vez.
if "$PY" - "$URL" <<'PYEOF' 2>/dev/null
import json, sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1] + "/salud", timeout=2) as r:
        sys.exit(0 if json.load(r).get("estado") == "ok" else 1)
except Exception:
    sys.exit(1)
PYEOF
then
    if [ "$DEMO" = 1 ]; then
        error "Ya hay una ApuntIA en marcha en $URL. Detenla primero (./detener.sh) para no mezclar la demostración con tus datos."
        exit 3
    fi
    bien "ApuntIA ya está en marcha en $URL"
    [ "$SOLO_COMPROBAR" = 1 ] && exit 0
    echo "  Ábrela en: $URL/inicio"
    exit 0
fi
if "$PY" -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('127.0.0.1', $PUERTO)) == 0 else 1)"; then
    error "El puerto $PUERTO está ocupado por otro programa. Usa otro: ./iniciar.sh --puerto 8080"
    exit 3
fi
bien "Puerto $PUERTO libre"

if [ "$SOLO_COMPROBAR" = 1 ]; then
    bien "Comprobación terminada: se puede arrancar."
    exit 0
fi

if [ "$DEMO_NUEVA" = 1 ] && [ -d "$DEMO_DIR" ]; then
    # Solo se borra una carpeta creada por el modo demostración (tiene su marca): nunca datos reales.
    if [ ! -f "$DEMO_DIR/.apuntia-demo" ]; then
        error "$DEMO_DIR no es una carpeta de demostración de ApuntIA (le falta .apuntia-demo): no se borra."
        exit 1
    fi
    rm -rf -- "$DEMO_DIR"
    bien "Borrados los datos de demostración anteriores"
fi
if [ "$DEMO" = 1 ]; then
    mkdir -p "$DEMO_DIR" && : > "$DEMO_DIR/.apuntia-demo"
fi

# ------------------------------------------------------------------ entorno de Python
cd "$BACKEND"
if [ "$VENV" = 1 ]; then
    if [ ! -x ".venv/bin/python" ]; then
        azul "Creando el entorno virtual back/motori_magenes/.venv"
        "$PY" -m venv .venv || { error "No se pudo crear el entorno virtual (en Debian/Ubuntu: sudo apt install python3-venv)."; exit 2; }
    fi
    PY="$BACKEND/.venv/bin/python"
fi
huella="$(cat requirements.txt constraints.txt 2>/dev/null | "$PY" -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())')"
marca="$ESTADO/requisitos-$( [ "$VENV" = 1 ] && echo venv || echo sistema ).sha256"
if [ "$REINSTALAR" = 1 ] || [ ! -f "$marca" ] || [ "$(cat "$marca")" != "$huella" ]; then
    azul "Instalando dependencias de Python (puede tardar unos minutos la primera vez)"
    restricciones=(); [ -f constraints.txt ] && restricciones=(-c constraints.txt)
    if ! "$PY" -m pip install --disable-pip-version-check -q -r requirements.txt "${restricciones[@]}"; then
        error "Falló la instalación de dependencias. Revisa tu conexión y vuelve a ejecutar con --reinstalar."
        exit 2
    fi
    echo "$huella" > "$marca"
fi
"$PY" -c "import fastapi, uvicorn, cv2, reportlab" 2>/dev/null || { error "Faltan módulos (fastapi, uvicorn, opencv, reportlab). Ejecuta con --reinstalar."; exit 2; }
bien "Dependencias listas"

# ------------------------------------------------------------------ arranque
iniciar_en_segundo_plano() {  # nombre, carpeta, comando...
    local nombre="$1" carpeta="$2"; shift 2
    # «cd» va aparte: si el «&» abarcara «cd && …», $! sería un subshell y no el servidor.
    ( cd "$carpeta" || exit 1
      nohup "$@" > "$ESTADO/$nombre.log" 2>&1 &
      echo $! > "$ESTADO/$nombre.pid" )
}

if [ -n "$SPRING" ]; then
    azul "Iniciando Spring Boot"
    if [ -x "$SPRING/mvnw" ]; then iniciar_en_segundo_plano spring "$SPRING" ./mvnw -q spring-boot:run
    elif [ -x "$SPRING/gradlew" ]; then iniciar_en_segundo_plano spring "$SPRING" ./gradlew -q bootRun
    else error "Spring Boot sin Maven/Gradle Wrapper (mvnw o gradlew): añádelo para no exigir Maven instalado."; exit 1; fi
fi

azul "Iniciando ApuntIA en $URL"
export APUNTIA_PUERTO="$PUERTO"
iniciar_en_segundo_plano backend "$BACKEND" "$PY" -m uvicorn main:app --host "$HOST" --port "$PUERTO"

# Espera activa a /salud (sin «sleep» ciego), máximo 60 s.
if ! "$PY" - "$URL" "$(cat "$ESTADO/backend.pid")" <<'PYEOF'
import json, os, sys, time, urllib.request
url, pid = sys.argv[1], int(sys.argv[2])
fin = time.time() + 60
while time.time() < fin:
    try:
        os.kill(pid, 0)
    except OSError:
        sys.exit(1)          # el proceso terminó: error de arranque
    try:
        with urllib.request.urlopen(url + "/salud", timeout=2) as r:
            if json.load(r).get("estado") == "ok":
                sys.exit(0)
    except Exception:
        time.sleep(0.5)
sys.exit(1)
PYEOF
then
    error "ApuntIA no arrancó. Últimas líneas de fullstack/.estado/backend.log:"
    tail -n 20 "$ESTADO/backend.log" >&2 || true
    exit 4
fi

bien "ApuntIA está lista"
if [ "$DEMO" = 1 ]; then
    azul "Preparando la demostración (datos sintéticos, aparte de los reales)"
    (cd "$BACKEND" && "$PY" "$RAIZ/fullstack/scripts/demo.py" "$URL") || aviso "No se pudieron crear los datos de demostración: la aplicación sigue en marcha."
fi
echo
echo "  Mejorar una foto (sin cuenta):  $URL/inicio"
echo "  Apuntes con cuenta:             $URL/front/apuntes.html"
echo "  Documentación de la API:        $URL/docs"
[ "$RED" = 1 ] && echo "  Desde el móvil (misma red):     http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PUERTO/inicio"
echo "  Registro del servidor:          fullstack/.estado/backend.log"
echo "  Para detenerla:                 ./detener.sh"

if [ "$NAVEGADOR" = 1 ]; then
    if command -v xdg-open >/dev/null 2>&1 && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then xdg-open "$URL/inicio" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ]; then open "$URL/inicio" || true
    fi
fi
