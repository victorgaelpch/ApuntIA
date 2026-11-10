"""Interfaz web servida desde el mismo origen que la API (FRONT-11).

Las páginas con cuenta usan una cookie de sesión HttpOnly que el navegador solo
envía a su propio origen, así que la interfaz se sirve desde FastAPI:

  GET /inicio      → index.html (mejorar una foto y presentación)
  GET /front/...   → páginas, estilos y scripts de la carpeta front/

`GET /` sigue devolviendo {"message": "Hola Mundo"} (contrato v1). Solo se
sirven archivos de la interfaz: ni las pruebas ni nada fuera de front/.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from app.core.config import settings

EXTENSIONES = {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico"}
# La maqueta de diseño (FRONT-01) usa estilos en línea que la CSP de la interfaz no permite
# y datos de ejemplo: no forma parte de la aplicación servida.
EXCLUIDOS = {"maqueta.html", "js/index.js", "css/index.css.map"}


class EstaticosInterfaz(StaticFiles):
    """StaticFiles que solo entrega recursos de la interfaz (no tests/ ni README)."""

    async def get_response(self, path, scope):
        partes = Path(path).parts
        if ((partes and partes[0] in ("tests", "node_modules")) or Path(path).suffix.lower() not in EXTENSIONES
                or Path(path).as_posix() in EXCLUIDOS):
            from starlette.exceptions import HTTPException
            raise HTTPException(status_code=404)
        respuesta = await super().get_response(path, scope)
        respuesta.headers["Cache-Control"] = "no-cache"
        return respuesta


def registrar(app: FastAPI) -> None:
    carpeta = Path(settings.front_dir) if settings.front_dir else None
    if not carpeta or not carpeta.is_dir():
        return
    inicio = Path(settings.pagina_inicio)

    if inicio.is_file():
        @app.get("/inicio", include_in_schema=False)
        def pagina_inicio():
            return FileResponse(inicio, media_type="text/html", headers={"Cache-Control": "no-cache"})

    @app.get("/front", include_in_schema=False)
    @app.get("/front/", include_in_schema=False)
    def raiz_interfaz():
        return RedirectResponse("/front/apuntes.html")

    app.mount("/front", EstaticosInterfaz(directory=carpeta), name="interfaz")
