"""Investigación opcional con fuentes citables (BACK-18).

Principios (fullstack/docs/api-v2.md §7):
  - Solo con consentimiento explícito por petición Y la preferencia
    `investigacion_permitida` del perfil activada.
  - Al proveedor solo se envían los CONCEPTOS elegidos (palabras clave cortas),
    nunca la foto ni el texto del apunte.
  - Cada ampliación lleva fuente real (URL https de un host fijo, título,
    proveedor, autor, licencia y fecha de consulta). Sin fuente, no hay ampliación.
  - Lo investigado es una PROPUESTA aparte del apunte: el usuario la acepta o
    la rechaza; nunca reemplaza la transcripción. Si contradice el apunte, se
    marca `discrepancia` para que el usuario revise.
  - El contenido externo es dato no confiable: se quita el HTML, se recorta a
    un fragmento breve (cita con atribución, no el artículo) y se descarta si
    contiene instrucciones dirigidas a un asistente (inyección).
  - Sin Internet o con INVESTIGACION_PROVEEDOR=ninguno, todo lo demás funciona.
  - SSRF: el servidor solo consulta las URLs fijas del proveedor; nunca una URL
    recibida del usuario o de la respuesta.
"""

import hashlib
import html
import json
import logging
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date

from app.core import contexto
from app.core.config import settings
from app.datos.apuntes import RepositorioApuntes
from app.services.documento import Ampliacion, Documento, Fuente
from app.services.estructura import DEFINICION, es_ia, estructurar
from app.services.trabajos import ErrorTrabajo, Resultado, Trabajo

logger = logging.getLogger("apuntia.investigacion")

MAX_CONCEPTOS = 8
MAX_FRAGMENTO = 600
USER_AGENT = "ApuntIA/2.0 (proyecto educativo; https://github.com/victorgaelpch/ApuntIA)"
IDIOMAS_WIKIPEDIA = {"es", "en"}

INYECCION = re.compile(
    r"(ignora|ignore|olvida|disregard)\s+(todas\s+|all\s+)?(las\s+|the\s+)?(instrucciones|instructions|previous)"
    r"|(system\s*prompt|you\s+are\s+(an?\s+)?(ai|assistant|chatgpt|claude))"
    r"|(eres\s+un\s+(asistente|modelo))", re.I)


class ProveedorNoDisponible(Exception):
    """El proveedor no responde o está desactivado (no es «sin resultados»)."""


@dataclass
class Hallazgo:
    concepto: str
    titulo: str
    url: str
    fragmento: str
    proveedor: str
    licencia: str
    autor: str


def limpiar_texto(texto: str) -> str:
    """HTML → texto plano breve, sin caracteres de control."""
    texto = re.sub(r"<[^>]*>", " ", texto or "")
    texto = html.unescape(texto)
    texto = "".join(c for c in unicodedata.normalize("NFC", texto) if c in "\n\t" or unicodedata.category(c)[0] != "C")
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) > MAX_FRAGMENTO:  # cita breve: hasta la última frase completa
        corte = texto[:MAX_FRAGMENTO]
        texto = corte[:corte.rfind(". ") + 1] if ". " in corte else corte.rstrip() + "…"
    return texto


def concepto_valido(concepto: str) -> str:
    concepto = re.sub(r"\s+", " ", (concepto or "")).strip()
    if not concepto or len(concepto) > 80 or len(concepto.split()) > 6:
        raise ValueError("Cada concepto debe ser una palabra clave corta (hasta 6 palabras).")
    if re.search(r"[@/\\<>{}]|https?:|www\.|\d{6,}", concepto):
        raise ValueError("Los conceptos no pueden contener direcciones, rutas ni números largos.")
    return concepto


class Proveedor:
    nombre = "base"

    def disponible(self) -> bool:
        return True

    def buscar(self, concepto: str, idioma: str) -> Hallazgo | None:
        raise NotImplementedError


class ProveedorNinguno(Proveedor):
    nombre = "ninguno"

    def disponible(self) -> bool:
        return False

    def buscar(self, concepto, idioma):
        raise ProveedorNoDisponible("La investigación está desactivada en este servidor.")


class _SoloHosts(urllib.request.HTTPRedirectHandler):
    """Redirecciones solo a los mismos hosts fijos y por https (BACK-38: nada de saltos a IPs internas)."""

    def __init__(self, hosts: set[str]):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destino = urllib.parse.urlsplit(newurl)
        if destino.scheme != "https" or (destino.hostname or "") not in self.hosts:
            raise ProveedorNoDisponible("Redirección a un host no permitido.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class ProveedorMediaWiki(Proveedor):
    """API REST pública de un proyecto Wikimedia (contenido CC BY-SA 4.0). Hosts fijos: es/en.<dominio>."""
    nombre = "mediawiki"
    dominio = ""
    autor = ""

    def __init__(self, timeout: float | None = None, abrir=None):
        self.timeout = timeout or settings.investigacion_timeout_s
        self.hosts = {f"{i}.{self.dominio}" for i in IDIOMAS_WIKIPEDIA}
        self._abrir = abrir or urllib.request.build_opener(_SoloHosts(self.hosts)).open

    def _json(self, url: str) -> dict:
        host = urllib.parse.urlsplit(url).hostname or ""
        if not url.startswith("https://") or host not in self.hosts:
            raise ProveedorNoDisponible("URL de proveedor no permitida.")  # defensa en profundidad (SSRF)
        peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with self._abrir(peticion, timeout=self.timeout) as r:
                return json.loads(r.read(512 * 1024).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {}
            raise ProveedorNoDisponible(f"HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProveedorNoDisponible(type(exc).__name__) from None

    def buscar(self, concepto: str, idioma: str) -> Hallazgo | None:
        idioma = idioma if idioma in IDIOMAS_WIKIPEDIA else "es"
        base = f"https://{idioma}.{self.dominio}"
        datos = self._json(f"{base}/w/rest.php/v1/search/page?" + urllib.parse.urlencode({"q": concepto, "limit": 3}))
        for pagina in (datos.get("pages") or [])[:3]:
            clave = str(pagina.get("key") or "")
            if not clave:
                continue
            resumen = self._resumen(base, clave)
            if resumen is None:
                continue
            titulo, fragmento = limpiar_texto(resumen[0] or clave)[:300], limpiar_texto(resumen[1])
            # La URL citada se construye aquí con la clave, no se copia de la respuesta.
            url = f"{base}/wiki/" + urllib.parse.quote(clave, safe="")
            if fragmento:
                return Hallazgo(concepto, titulo, url, fragmento, self.nombre, "CC BY-SA 4.0", self.autor)
        return None

    def _resumen(self, base: str, clave: str) -> tuple[str, str] | None:
        """(título, extracto) de la página, o None si no sirve (desambiguación, vacía…)."""
        resumen = self._json(f"{base}/api/rest_v1/page/summary/" + urllib.parse.quote(clave, safe=""))
        if not resumen or resumen.get("type") != "standard":
            return None
        return str(resumen.get("title") or ""), str(resumen.get("extract") or "")


class ProveedorWikipedia(ProveedorMediaWiki):
    nombre, dominio, autor = "wikipedia", "wikipedia.org", "Colaboradores de Wikipedia"


class ProveedorWikilibros(ProveedorMediaWiki):
    """Libros de texto abiertos (BACK-38): misma API y licencia que Wikipedia, otro host fijo."""
    nombre, dominio, autor = "wikilibros", "wikibooks.org", "Colaboradores de Wikilibros"

    def _resumen(self, base: str, clave: str) -> tuple[str, str] | None:
        # Las páginas de un libro empiezan por secciones y su «summary» REST llega vacío
        # (comprobado el 14/11/2026): se usa TextExtracts en texto plano, sin los títulos «== … ==».
        datos = self._json(f"{base}/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "prop": "extracts", "explaintext": 1, "exchars": 1200, "format": "json",
            "formatversion": 2, "titles": clave}))
        paginas = (datos.get("query") or {}).get("pages") or []
        if not paginas or paginas[0].get("missing"):
            return None
        texto = re.sub(r"^=+[^=\n]*=+\s*$", " ", str(paginas[0].get("extract") or ""), flags=re.M)
        return str(paginas[0].get("title") or ""), texto


class ProveedorCadena(Proveedor):
    """Varias fuentes en orden de preferencia: la primera con resultado gana.

    Si una fuente no responde se prueba la siguiente; solo es «no disponible» si fallan todas.
    """

    def __init__(self, proveedores: list[Proveedor]):
        self.proveedores = proveedores
        self.nombre = "+".join(p.nombre for p in proveedores)

    def disponible(self) -> bool:
        return any(p.disponible() for p in self.proveedores)

    def buscar(self, concepto: str, idioma: str) -> Hallazgo | None:
        fallos = 0
        for p in self.proveedores:
            try:
                hallazgo = p.buscar(concepto, idioma)
            except ProveedorNoDisponible:
                fallos += 1
                continue
            if hallazgo is not None:
                return hallazgo
        if fallos == len(self.proveedores):
            raise ProveedorNoDisponible("Ninguna fuente respondió.")
        return None


PROVEEDORES = {"wikipedia": ProveedorWikipedia, "wikilibros": ProveedorWikilibros}


def crear_proveedor(configuracion: str) -> Proveedor:
    """«wikipedia», «wikilibros», «wikipedia,wikilibros» o «ninguno». Nombres desconocidos: se ignoran."""
    nombres = [n.strip() for n in configuracion.split(",") if n.strip() in PROVEEDORES]
    if not nombres:
        return ProveedorNinguno()
    if len(nombres) == 1:
        return PROVEEDORES[nombres[0]]()
    return ProveedorCadena([PROVEEDORES[n]() for n in dict.fromkeys(nombres)])


_proveedor: Proveedor | None = None
_cache: "OrderedDict[tuple[str, str], tuple[float, Hallazgo | None]]" = OrderedDict()
_cache_lock = threading.Lock()
CACHE_MAX, CACHE_TTL_S = 200, 24 * 3600


def proveedor() -> Proveedor:
    global _proveedor
    if _proveedor is None:
        _proveedor = crear_proveedor(settings.investigacion_proveedor)
    return _proveedor


def usar_proveedor(nuevo: Proveedor | None) -> None:
    """Cambia el proveedor (pruebas o configuración) y vacía la caché."""
    global _proveedor
    _proveedor = nuevo
    with _cache_lock:
        _cache.clear()


def buscar_con_cache(concepto: str, idioma: str) -> Hallazgo | None:
    clave = (idioma, concepto.lower())
    with _cache_lock:
        if clave in _cache and time.time() - _cache[clave][0] < CACHE_TTL_S:
            _cache.move_to_end(clave)
            return _cache[clave][1]
    hallazgo = proveedor().buscar(concepto, idioma)
    with _cache_lock:
        _cache[clave] = (time.time(), hallazgo)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)
    return hallazgo


# ------------------------------------------------------------------ conceptos y contraste

def conceptos_sugeridos(doc: Documento) -> list[str]:
    """Candidatos para investigar, sacados del propio apunte (el usuario elige).

    BACK-38: solo de bloques confirmados; una propuesta del servidor IA sin revisar ni corregir
    puede estar mal leída y no debe decidir qué se busca fuera.
    """
    confirmados = [b for b in doc.bloques if not (es_ia(b) and not b.revisado and not b.editado)]
    e = estructurar(doc.model_copy(update={"bloques": confirmados}))
    vistos, salida = set(), []
    for c in [g["concepto"] for g in e.glosario] + [s.titulo for s in e.secciones if s.titulo != "Contenido"] \
            + e.conceptos:
        try:
            c = concepto_valido(c)
        except ValueError:
            continue
        if c.lower() not in vistos:
            vistos.add(c.lower())
            salida.append(c)
    return salida[:12]


NUMERO = re.compile(r"\b\d+(?:[.,]\d+)?\b")


def discrepancia(doc: Documento, concepto: str, fragmento: str) -> str | None:
    """Señala cifras distintas entre lo que el apunte dice del concepto y la fuente.

    Heurística conservadora: compara solo números (años, valores) de las
    frases del apunte que nombran el concepto. Nunca cambia el apunte.
    """
    frases = [f.strip() for b in doc.bloques for f in re.split(r"(?<=[.!?])\s+|\n", b.texto or "")
              if concepto.lower() in f.lower()]
    del_apunte = {n for f in frases for n in NUMERO.findall(f)}
    de_fuente = set(NUMERO.findall(fragmento))
    if del_apunte and de_fuente and not (del_apunte & de_fuente):
        return (f"El apunte menciona {', '.join(sorted(del_apunte))} y la fuente "
                f"{', '.join(sorted(de_fuente)[:5])}. Revisa cuál es correcto antes de aceptar.")
    for b in doc.bloques:  # definiciones del apunte que niegan lo que dice la fuente («X no es …»)
        for linea in (b.texto or "").split("\n"):
            m = DEFINICION.match(linea.strip())
            if m and m.group(1).strip().lower() == concepto.lower() and re.search(r"\bno\s+(es|son)\b", linea, re.I):
                return "El apunte define este concepto en negativo; compara con la fuente antes de aceptar."
    return None


def _id_ampliacion(concepto: str, url: str) -> str:
    return "a" + hashlib.sha256(f"{concepto.lower()}|{url}".encode()).hexdigest()[:16]


# ------------------------------------------------------------------ trabajo «investigacion»

def manejar_investigacion(trabajo: Trabajo) -> Resultado:
    ctx = contexto.obtener()
    repo = RepositorioApuntes(ctx.bd, ctx.almacen)
    conceptos = trabajo.parametros.get("conceptos") or []
    idioma = trabajo.parametros.get("idioma") or "es"
    doc = repo.documento(trabajo.usuario_id, trabajo.apunte_id)
    hallazgos, sin_resultado, descartados, fallidos = [], [], [], []
    inicio = time.monotonic()
    for i, concepto in enumerate(conceptos):
        trabajo.avance("investigando", int(5 + 85 * i / max(1, len(conceptos))))
        try:
            h = buscar_con_cache(concepto, idioma)
        except ProveedorNoDisponible:
            fallidos.append(concepto)
            continue
        if h is None:
            sin_resultado.append(concepto)
        elif INYECCION.search(h.fragmento) or INYECCION.search(h.titulo):
            descartados.append(concepto)  # la página intenta dar órdenes: no se usa
        else:
            hallazgos.append(h)
    # Métricas técnicas, sin los conceptos (pueden ser privados).
    logger.info("Investigación %s: %d conceptos, %d con fuente, %d sin resultado, %d descartados, %d fallos, %.0f ms",
                trabajo.id, len(conceptos), len(hallazgos), len(sin_resultado), len(descartados), len(fallidos),
                (time.monotonic() - inicio) * 1000)
    if fallidos and len(fallidos) == len(conceptos):
        raise ErrorTrabajo("INVESTIGACION_NO_DISPONIBLE",
                           "No se pudo consultar la fuente externa. Tu apunte sigue intacto; inténtalo más tarde.")

    trabajo.avance("investigando", 95)
    consultado = date.today().isoformat()
    for _ in range(3):  # se añade sobre la versión MÁS RECIENTE para no pisar ediciones
        actual = repo.obtener(trabajo.usuario_id, trabajo.apunte_id, con_documento=False)["version"]
        doc = repo.documento(trabajo.usuario_id, trabajo.apunte_id)
        existentes = {a.id for a in doc.ampliaciones}
        nuevas = []
        for h in hallazgos:
            aid = _id_ampliacion(h.concepto, h.url)
            if aid in existentes:
                continue
            nuevas.append(Ampliacion(
                id=aid, concepto=h.concepto, texto=h.fragmento, estado="propuesta",
                fuente=Fuente(titulo=h.titulo, url=h.url, proveedor=h.proveedor, consultado=consultado,
                              licencia=h.licencia, autor=h.autor),
                discrepancia=discrepancia(doc, h.concepto, h.fragmento)))
        version = actual
        if nuevas:
            try:
                version = repo.nueva_version(trabajo.usuario_id, trabajo.apunte_id,
                                             doc.model_copy(update={"ampliaciones": doc.ampliaciones + nuevas}),
                                             "investigacion", version_esperada=actual)
            except Exception as exc:  # noqa: BLE001
                if getattr(exc, "codigo", "") == "CONFLICTO_VERSION":
                    continue
                raise
        break
    else:
        raise ErrorTrabajo("CONFLICTO_VERSION", "El apunte cambió mientras se investigaba. Vuelve a intentarlo.")
    resumen = {"version": version, "propuestas": len(nuevas), "sin_resultado": len(sin_resultado),
               "descartados": len(descartados), "fallidos": len(fallidos),
               "discrepancias": sum(a.discrepancia is not None for a in nuevas)}
    if fallidos:
        return Resultado("parcial", resumen, "Algunos conceptos no se pudieron consultar; el resto está listo.")
    if not hallazgos:
        resumen["aviso"] = "No se encontraron fuentes fiables para esos conceptos."
    return Resultado("completado", resumen)


@contexto.al_iniciar
def _registrar(ctx) -> None:
    ctx.trabajos.registrar("investigacion", manejar_investigacion)
