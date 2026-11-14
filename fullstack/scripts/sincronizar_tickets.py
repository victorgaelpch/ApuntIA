"""Sincroniza las fichas de fullstack/tickets/ con los Issues de GitHub (FULL-29).

    python fullstack/scripts/sincronizar_tickets.py              # API pública de GitHub
    python fullstack/scripts/sincronizar_tickets.py --offline    # solo el snapshot local
    GITHUB_TOKEN=... python fullstack/scripts/sincronizar_tickets.py   # más límite de peticiones

Qué hace:

- Descarga TODOS los Issues (abiertos y cerrados) del repositorio, paginando con la cabecera
  `Link`. La API de Issues de GitHub también devuelve los Pull Requests: se reconocen por la clave
  `pull_request` y NUNCA generan ficha; se listan aparte en INDICE.md.
- Escribe una ficha por Issue: `<ID>.md` si el título empieza por `[FULL-n]`, `[BACK-n]` o
  `[FRONT-n]`, o `issue-<número>.md` si no tiene identificador. El identificador lógico NO es el
  número de GitHub (`[FULL-29]` es el #93).
- Si dos Issues comparten identificador, no se pisan: el que ya era dueño de `<ID>.md` lo conserva
  y los demás van a `<ID>-issue-<número>.md`; la colisión queda registrada en INDICE.md.
- Dentro de cada ficha solo reescribe el bloque entre `<!-- SINCRONIZADO:INICIO -->` y
  `<!-- SINCRONIZADO:FIN -->`; las notas manuales fuera de él se conservan. La carpeta
  `bitacora/` (registro REAL de sesiones) nunca se toca.
- Guarda el snapshot normalizado en `datos/issues.json`. Si la red, el DNS o la API fallan
  (403/429/5xx), avisa y regenera desde ese snapshot sin inventar fechas.
- Es idempotente: con los mismos datos de GitHub, una segunda ejecución no cambia ningún archivo.

Fechas: GitHub da `created_at`, `updated_at` y `closed_at` en UTC; se muestran también en
America/Mexico_City. Son metadatos del Issue, NO horas de trabajo: el trabajo real solo consta en
`bitacora/`. El token, si se usa, solo se lee de la variable de entorno y nunca se escribe.

Códigos de salida: 0 bien · 1 error de uso o de archivos · 2 sin red/API y sin snapshot ·
3 se usó el snapshot porque la API falló (las fichas pueden estar desactualizadas).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parents[2]
REPO = "victorgaelpch/ApuntIA"
DESTINO = RAIZ / "fullstack" / "tickets"
INICIO, FIN = "<!-- SINCRONIZADO:INICIO -->", "<!-- SINCRONIZADO:FIN -->"
ID_LOGICO = re.compile(r"^\s*\[(FULL|BACK|FRONT)-(\d+)\]", re.I)
AREAS = {"FULL": "Full stack", "BACK": "Backend", "FRONT": "Frontend"}
PLAN = re.compile(r"^- \[[ xX]\] (\d{4}-\d{2}-\d{2}) · (\d{2}:\d{2})[–-](\d{2}:\d{2}) \(America/Mexico_City\): (.+?)\s*$", re.M)
CIERRE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b", re.I)

Respuesta = tuple[int, dict[str, str], bytes]
Transporte = Callable[[str, dict[str, str]], Respuesta]


def zona_cdmx():
    """Zona America/Mexico_City. Sin base IANA (Windows sin el paquete `tzdata`) usa UTC−06:00
    fijo: da el mismo resultado para toda fecha posterior al 30/10/2022, cuando México eliminó el
    horario de verano (todos los Issues del repositorio son de 2026)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/Mexico_City")
    except Exception:  # ZoneInfoNotFoundError o ImportError
        return timezone(timedelta(hours=-6))


ZONA = zona_cdmx()
# Texto fijo para que la salida sea idéntica en Windows y Linux (idempotencia entre equipos).
NOMBRE_ZONA = "America/Mexico_City (UTC−06:00, sin horario de verano desde 2022)"


def a_cdmx(iso: str | None) -> str:
    if not iso:
        return "—"
    utc = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return utc.astimezone(ZONA).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------- descarga


class FalloAPI(Exception):
    """La API no respondió como se esperaba (red, DNS, 403, 429, 5xx, JSON inválido)."""


def transporte_urllib(url: str, cabeceras: dict[str, str]) -> Respuesta:
    peticion = urllib.request.Request(url, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=20) as r:  # noqa: S310 (URL fija de api.github.com)
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read() or b""


def siguiente(enlace: str | None) -> str | None:
    """URL rel="next" de una cabecera Link de GitHub."""
    for parte in (enlace or "").split(","):
        m = re.match(r'\s*<([^>]+)>;\s*rel="next"', parte)
        if m:
            return m.group(1)
    return None


def descargar(repo: str, transporte: Transporte, token: str | None = None,
              espera: Callable[[float], None] = time.sleep, max_paginas: int = 50) -> list[dict]:
    cabeceras = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "apuntia-sincronizar-tickets"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    url: str | None = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&sort=created&direction=asc"
    todos: list[dict] = []
    for _ in range(max_paginas):
        if url is None:
            return todos
        for intento in (1, 2):  # un único reintento, y solo si la espera es corta
            try:
                estado, cab, cuerpo = transporte(url, cabeceras)
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                raise FalloAPI(f"sin conexión con api.github.com ({type(e).__name__})") from None
            if estado == 200:
                break
            limite = estado == 429 or (estado == 403 and cab.get("x-ratelimit-remaining") == "0")
            pausa = float(cab.get("retry-after", "0") or 0)
            if limite and intento == 1 and 0 < pausa <= 60:
                espera(pausa)
                continue
            motivo = "límite de peticiones agotado (usa GITHUB_TOKEN o espera)" if limite else f"HTTP {estado}"
            raise FalloAPI(f"la API de GitHub respondió {motivo}")
        try:
            pagina = json.loads(cuerpo.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise FalloAPI("la API devolvió algo que no es JSON") from None
        if not isinstance(pagina, list):
            raise FalloAPI("respuesta inesperada de la API (no es una lista)")
        todos.extend(pagina)
        url = siguiente(cab.get("link"))
    raise FalloAPI(f"más de {max_paginas} páginas: se detiene para no entrar en un bucle")


# ---------------------------------------------------------------------------- modelo


def normalizar(crudo: dict) -> dict:
    """Solo los campos públicos que se usan (sin cuerpo completo ni datos de usuarios)."""
    pr = crudo.get("pull_request")
    cuerpo = crudo.get("body") or ""
    return {
        "numero": crudo["number"],
        "titulo": (crudo.get("title") or "").strip(),
        "url": crudo.get("html_url", ""),
        "es_pr": pr is not None,
        "pr_fusionado_en": (pr or {}).get("merged_at"),
        "estado": crudo.get("state", ""),
        "motivo_estado": crudo.get("state_reason"),
        "etiquetas": sorted(e["name"] if isinstance(e, dict) else str(e) for e in crudo.get("labels") or []),
        "responsables": sorted(a["login"] for a in crudo.get("assignees") or [] if a and a.get("login")),
        "autor": (crudo.get("user") or {}).get("login"),
        "created_at": crudo.get("created_at"),
        "updated_at": crudo.get("updated_at"),
        "closed_at": crudo.get("closed_at"),
        "dependencias": extraer_dependencias(cuerpo),
        "plan": [list(m) for m in PLAN.findall(cuerpo)],
        "cierra": sorted({int(n) for n in CIERRE.findall(cuerpo)}) if pr is not None else [],
    }


def extraer_dependencias(cuerpo: str) -> str | None:
    m = re.search(r"^##\s*Dependencias\s*\n+(.+?)(?:\n\s*\n|\n#)", cuerpo, re.M | re.S)
    if m:
        return " ".join(m.group(1).split())
    m = re.search(r"^DEPENDENCIAS:\s*(.+)$", cuerpo, re.M)
    return m.group(1).strip() if m else None


def id_logico(titulo: str) -> str | None:
    m = ID_LOGICO.match(titulo)
    return f"{m.group(1).upper()}-{m.group(2)}" if m else None  # tal cual: [BACK-01] → BACK-01


@dataclass
class Ficha:
    issue: dict
    ident: str | None
    archivo: str


def dueno_actual(destino: Path, nombre: str) -> int | None:
    ruta = destino / nombre
    if not ruta.exists():
        return None
    m = re.search(r"\| Número en GitHub \| \[#(\d+)\]", ruta.read_text(encoding="utf-8"))
    return int(m.group(1)) if m else None


def asignar_archivos(issues: list[dict], destino: Path) -> tuple[list[Ficha], dict[str, list[int]]]:
    por_id: dict[str, list[dict]] = {}
    fichas: list[Ficha] = []
    for i in issues:
        ident = id_logico(i["titulo"])
        if ident:
            por_id.setdefault(ident, []).append(i)
        else:
            fichas.append(Ficha(i, None, f"issue-{i['numero']}.md"))
    colisiones: dict[str, list[int]] = {}
    for ident, grupo in por_id.items():
        if len(grupo) == 1:
            fichas.append(Ficha(grupo[0], ident, f"{ident}.md"))
            continue
        numeros = sorted(g["numero"] for g in grupo)
        colisiones[ident] = numeros
        dueno = dueno_actual(destino, f"{ident}.md")
        dueno = dueno if dueno in numeros else numeros[0]
        for g in grupo:
            nombre = f"{ident}.md" if g["numero"] == dueno else f"{ident}-issue-{g['numero']}.md"
            fichas.append(Ficha(g, ident, nombre))
    fichas.sort(key=lambda f: f.issue["numero"])
    return fichas, colisiones


# ---------------------------------------------------------------------------- escritura


def celda(texto: object) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def utc(iso: str | None) -> str:
    return iso.replace("T", " ").replace("Z", " UTC") if iso else "—"


def estado_legible(i: dict) -> str:
    if i["estado"] == "open":
        return "Abierto"
    return {"completed": "Cerrado (completado)", "not_planned": "Cerrado (no planificado)",
            "duplicate": "Cerrado (duplicado)"}.get(i.get("motivo_estado") or "", "Cerrado")


def area(ident: str | None, etiquetas: list[str]) -> str:
    if ident:
        return AREAS[ident.split("-")[0]]
    return ", ".join(etiquetas) or "sin área (sin identificador ni etiqueta)"


def bloque_sincronizado(f: Ficha, prs: list[dict], destino: Path, fuente: str) -> str:
    i = f.issue
    ident = f.ident or "sin identificador lógico"
    bitacora = destino / "bitacora" / f"{f.ident or 'issue-' + str(i['numero'])}.md"
    if bitacora.exists():
        sesiones = len(re.findall(r"^\s*-\s*\[?[ xX]?\]?\s*Sesión real:\s*\d{4}-\d{2}-\d{2}", bitacora.read_text(encoding="utf-8"), re.M))
        registro = f"[bitacora/{bitacora.name}](bitacora/{bitacora.name}) — {sesiones} sesión(es) real(es) registrada(s)"
    else:
        registro = "no registrada (no hay archivo en `bitacora/`; no se estima ni se deduce de las fechas de GitHub)"
    vinculados = [p for p in prs if i["numero"] in p["cierra"]]
    evidencia = " · ".join(
        f"[PR #{p['numero']}]({p['url']}) ({'fusionado ' + a_cdmx(p['pr_fusionado_en']) if p['pr_fusionado_en'] else 'sin fusionar'})"
        for p in vinculados) or "ningún PR declara «Closes #%d»" % i["numero"]
    plan = "\n".join(f"| {d} | {a}–{b} | {celda(t)} |" for d, a, b, t in i["plan"])
    plan_txt = ("| Fecha | Horario (CDMX) | Actividad prevista |\n|-------|----------------|--------------------|\n" + plan
                if plan else "Sin sesiones planificadas en la descripción del Issue.")
    return f"""{INICIO}
<!-- Bloque generado por fullstack/scripts/sincronizar_tickets.py: no editar a mano (se reescribe). -->

# {celda(ident)} — {celda(i['titulo'])}

| Campo | Valor |
|-------|-------|
| Identificador lógico | {celda(ident)} |
| Número en GitHub | [#{i['numero']}]({i['url']}) |
| Área | {celda(area(f.ident, i['etiquetas']))} |
| Etiquetas | {celda(', '.join(i['etiquetas']) or 'sin etiqueta')} |
| Responsable(s) | {celda(', '.join(i['responsables']) or 'sin asignar')} |
| Estado | {estado_legible(i)} |
| Dependencias | {celda(i['dependencias'] or 'no declaradas en el Issue')} |
| `created_at` | {utc(i['created_at'])} · {a_cdmx(i['created_at'])} (CDMX) |
| `updated_at` | {utc(i['updated_at'])} · {a_cdmx(i['updated_at'])} (CDMX) |
| `closed_at` | {utc(i['closed_at'])}{' · ' + a_cdmx(i['closed_at']) + ' (CDMX)' if i['closed_at'] else ' (abierto)'} |

Origen de los datos: {fuente}. Zona horaria: {NOMBRE_ZONA}. Las fechas de GitHub son metadatos
del Issue (creación, última modificación, cierre), **no** horas de trabajo.

## FECHA PLANIFICADA (propuesta, no es trabajo realizado)

{plan_txt}

## REGISTRO REAL

{registro}

## EVIDENCIA

{evidencia}
{FIN}"""


NOTAS_INICIALES = """
## Notas manuales

_Esta sección y todo lo que esté fuera del bloque sincronizado se conserva al volver a sincronizar._
"""


def escribir_si_cambia(ruta: Path, contenido: str) -> bool:
    if ruta.exists() and ruta.read_text(encoding="utf-8") == contenido:
        return False
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return True


def escribir_ficha(destino: Path, f: Ficha, prs: list[dict], fuente: str) -> bool:
    ruta = destino / f.archivo
    bloque = bloque_sincronizado(f, prs, destino, fuente)
    if ruta.exists():
        actual = ruta.read_text(encoding="utf-8")
        if INICIO in actual and FIN in actual:
            antes, resto = actual.split(INICIO, 1)
            despues = resto.split(FIN, 1)[1]
            nuevo = antes + bloque + despues
        else:  # ficha manual previa sin marcas: no se pierde, se conserva debajo
            nuevo = bloque + "\n\n## Contenido manual anterior\n\n" + actual
    else:
        nuevo = bloque + "\n" + NOTAS_INICIALES
    return escribir_si_cambia(ruta, nuevo)


def ids_planificados(destino: Path) -> list[str]:
    ruta = destino / "cronograma-planeado.md"
    if not ruta.exists():
        return []
    return sorted(set(re.findall(r"^\|\s*((?:FULL|BACK|FRONT)-\d+)\s*\|", ruta.read_text(encoding="utf-8"), re.M)))


def indice(fichas: list[Ficha], prs: list[dict], colisiones: dict[str, list[int]], destino: Path,
           obtenido_en: str, fuente: str) -> str:
    def clave(f: Ficha):
        if f.ident:
            pref, n = f.ident.split("-")
            return (0, pref, int(n), f.issue["numero"])
        return (1, "", 0, f.issue["numero"])

    filas = "\n".join(
        f"| {celda(f.ident or '—')} | [#{f.issue['numero']}]({f.issue['url']}) | {celda(f.issue['titulo'])} | "
        f"{celda(area(f.ident, f.issue['etiquetas']))} | {estado_legible(f.issue)} | "
        f"{celda(', '.join(f.issue['responsables']) or 'sin asignar')} | {a_cdmx(f.issue['created_at'])} | "
        f"{a_cdmx(f.issue['closed_at'])} | [{f.archivo}]({f.archivo}) |"
        for f in sorted(fichas, key=clave))
    abiertos = sum(f.issue["estado"] == "open" for f in fichas)
    col = "\n".join(f"- `{k}` lo usan los Issues {', '.join('#' + str(n) for n in v)}: cada uno tiene su ficha; "
                    "resolver contra el número y la URL reales." for k, v in sorted(colisiones.items()))
    ids_issues = {f.ident for f in fichas if f.ident}
    prs_con_id = [(p, id_logico(p["titulo"])) for p in prs if id_logico(p["titulo"])]
    col_pr = "\n".join(f"- [PR #{p['numero']}]({p['url']}) usa el prefijo `[{k}]` en su título; es un Pull Request, "
                       f"no el Issue {k}." for p, k in prs_con_id if k in ids_issues)
    faltan = [k for k in ids_planificados(destino) if k not in ids_issues]
    faltan_txt = "\n".join(f"- `{k}`: está en el [cronograma planificado](cronograma-planeado.md) pero no existe "
                           "ningún Issue con ese identificador en GitHub." for k in faltan)
    filas_pr = "\n".join(
        f"| [#{p['numero']}]({p['url']}) | {celda(p['titulo'])} | "
        f"{'Fusionado ' + a_cdmx(p['pr_fusionado_en']) if p['pr_fusionado_en'] else ('Abierto' if p['estado'] == 'open' else 'Cerrado sin fusionar')} | "
        f"{', '.join('#' + str(n) for n in p['cierra']) or '—'} |" for p in sorted(prs, key=lambda p: p["numero"]))
    return f"""# Índice de tickets de ApuntIA

<!-- Archivo generado por fullstack/scripts/sincronizar_tickets.py: no editar a mano. -->

Datos obtenidos el **{a_cdmx(obtenido_en)} (CDMX)** de {fuente}. Zona horaria: {NOMBRE_ZONA}.
{len(fichas)} Issues ({abiertos} abiertos, {len(fichas) - abiertos} cerrados) y {len(prs)} Pull Requests.
Las fechas son las de GitHub (creación y cierre), no horas de trabajo: el trabajo real está en
cada ficha, sección «REGISTRO REAL».

## Issues

| ID lógico | GitHub | Título | Área | Estado | Responsable(s) | Creado (CDMX) | Cerrado (CDMX) | Ficha |
|-----------|--------|--------|------|--------|----------------|---------------|----------------|-------|
{filas}

## Colisiones e incoherencias detectadas

{col or "- Ningún identificador lógico lo comparten dos Issues."}
{col_pr}
{faltan_txt}

## Pull Requests (no son Issues: no tienen ficha)

La API de Issues de GitHub los devuelve mezclados; se listan aquí solo como evidencia.

| PR | Título | Estado | Declara cerrar |
|----|--------|--------|----------------|
{filas_pr}
"""


# ---------------------------------------------------------------------------- orquestación


def cargar_snapshot(ruta: Path) -> dict | None:
    if not ruta.exists():
        return None
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos.get("issues"), list) else None
    except (json.JSONDecodeError, AttributeError):
        return None


def sincronizar(destino: Path = DESTINO, repo: str = REPO, transporte: Transporte | None = transporte_urllib,
                token: str | None = None, ahora: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                salida=print, espera: Callable[[float], None] = time.sleep) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "datos").mkdir(exist_ok=True)
    ruta_snap = destino / "datos" / "issues.json"
    snapshot = cargar_snapshot(ruta_snap)
    codigo = 0
    if transporte is None:
        if snapshot is None:
            salida("ERROR: modo sin conexión y no hay snapshot en datos/issues.json.")
            return 2
        items, obtenido_en = snapshot["issues"], snapshot["obtenido_en"]
        salida(f"Sin conexión: se usa el snapshot del {a_cdmx(obtenido_en)} (CDMX).")
    else:
        try:
            items = sorted((normalizar(c) for c in descargar(repo, transporte, token, espera)), key=lambda x: x["numero"])
            # Idempotencia: si GitHub no cambió, se conserva la fecha de la consulta anterior.
            obtenido_en = (snapshot["obtenido_en"] if snapshot and snapshot["issues"] == items
                           else ahora().strftime("%Y-%m-%dT%H:%M:%SZ"))
        except FalloAPI as e:
            if snapshot is None:
                salida(f"ERROR: {e}. No hay snapshot local: no se genera nada (no se inventan datos). Reintenta más tarde.")
                return 2
            salida(f"AVISO: {e}. Se regenera desde el snapshot del {a_cdmx(snapshot['obtenido_en'])} (CDMX); "
                   "puede estar desactualizado. Vuelve a ejecutar cuando haya conexión.")
            items, obtenido_en, codigo = snapshot["issues"], snapshot["obtenido_en"], 3
    fuente = (f"la API REST de GitHub (`GET /repos/{repo}/issues?state=all`), snapshot "
              f"[`datos/issues.json`](datos/issues.json)")
    issues = [i for i in items if not i["es_pr"]]
    prs = [i for i in items if i["es_pr"]]
    fichas, colisiones = asignar_archivos(issues, destino)
    cambiados = 0
    cambiados += escribir_si_cambia(ruta_snap, json.dumps(
        {"repositorio": repo, "obtenido_en": obtenido_en, "issues": items}, ensure_ascii=False, indent=1) + "\n")
    for f in fichas:
        cambiados += escribir_ficha(destino, f, prs, fuente)
    cambiados += escribir_si_cambia(destino / "INDICE.md", indice(fichas, prs, colisiones, destino, obtenido_en, fuente))
    salida(f"{len(issues)} Issues y {len(prs)} PRs; {len(colisiones)} colisión(es); {cambiados} archivo(s) actualizado(s).")
    return codigo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--offline", action="store_true", help="no consultar GitHub: regenerar desde datos/issues.json")
    p.add_argument("--repo", default=REPO, help=f"owner/nombre (por defecto {REPO})")
    p.add_argument("--destino", type=Path, default=DESTINO, help="carpeta de tickets")
    a = p.parse_args(argv)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", a.repo):
        print("ERROR: --repo debe tener la forma owner/nombre.")
        return 1
    token = os.environ.get("GITHUB_TOKEN") or None
    return sincronizar(a.destino, a.repo, None if a.offline else transporte_urllib, token)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
