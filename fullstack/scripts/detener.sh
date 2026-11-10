#!/usr/bin/env bash
# Detiene lo que arrancó iniciar.sh (FULL-11). Solo termina procesos cuyo PID está en
# fullstack/.estado/ Y que siguen siendo de ApuntIA (uvicorn main:app o Spring Boot):
# si el sistema reutilizó el número para otro programa, no lo toca.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ESTADO="$RAIZ/fullstack/.estado"

bien() { printf '\033[1;32m✔ %s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m⚠ %s\033[0m\n' "$*"; }

es_de_apuntia() {  # pid, patrón esperado en la línea de órdenes
    local pid="$1" patron="$2" linea=""
    if [ -r "/proc/$pid/cmdline" ]; then linea="$(tr '\0' ' ' < "/proc/$pid/cmdline")"
    else linea="$(ps -o command= -p "$pid" 2>/dev/null || true)"; fi
    [[ "$linea" == *$patron* ]]
}

detener() {  # nombre, patrón
    local nombre="$1" patron="$2" archivo="$ESTADO/$1.pid" pid
    [ -f "$archivo" ] || return 0
    pid="$(cat "$archivo")"
    if ! kill -0 "$pid" 2>/dev/null; then
        aviso "$nombre no estaba en marcha."
    elif ! es_de_apuntia "$pid" "$patron"; then
        aviso "El proceso $pid ya no es de ApuntIA: no se toca."
    else
        kill -TERM "$pid" 2>/dev/null
        for _ in $(seq 1 40); do kill -0 "$pid" 2>/dev/null || break; sleep 0.25; done
        if kill -0 "$pid" 2>/dev/null; then
            aviso "$nombre no terminó en 10 s: se fuerza."
            kill -KILL "$pid" 2>/dev/null
        fi
        bien "$nombre detenido."
    fi
    rm -f "$archivo"
}

[ -d "$ESTADO" ] && ls "$ESTADO"/*.pid >/dev/null 2>&1 || { bien "ApuntIA no estaba en marcha."; exit 0; }
detener backend "uvicorn main:app"
detener spring "spring-boot"
detener spring "bootRun"
exit 0
