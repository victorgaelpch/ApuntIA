"""Entrada de documentos de varias páginas (BACK-11).

Acepta de 1 a MAX_PAGINAS fotos, en orden, cada una de tipo «pizarron» o
«cuaderno». Cada foto pasa por la MISMA validación que POST /analisis (firma
binaria, tamaño, megapíxeles, decodificación). Si alguna falla, la petición se
rechaza entera sin guardar nada y el error indica qué página falló y por qué,
para que el usuario quite solo esa (las demás no se pierden en el cliente).
"""

from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import settings
from app.core.errores import ApiError
from app.services.validacion import ImagenRecibida, validar_imagen

TIPOS_FUENTE = ("pizarron", "cuaderno")


@dataclass
class PaginaRecibida:
    orden: int
    tipo_fuente: str
    imagen: ImagenRecibida


class ErrorPaginas(ApiError):
    """Error con el detalle de cada página que falló."""

    def __init__(self, detalles: list[dict]):
        n = len(detalles)
        super().__init__(400, detalles[0]["codigo"] if n == 1 else "PAGINAS_INVALIDAS",
                         f"{n} página(s) no son válidas: " + "; ".join(
                             f"página {d['pagina']}: {d['mensaje']}" for d in detalles[:5]))
        self.detalles = detalles


def validar_paginas(archivos: list[UploadFile] | None, tipos: list[str] | None) -> list[PaginaRecibida]:
    archivos = [a for a in (archivos or []) if a is not None]
    if not archivos:
        raise ApiError(400, "ARCHIVO_AUSENTE", "Añade al menos una foto en el campo «paginas».")
    if len(archivos) > settings.max_paginas:
        raise ApiError(400, "DEMASIADAS_PAGINAS", f"Puedes subir hasta {settings.max_paginas} páginas por apunte.")
    tipos = list(tipos or [])
    if len(tipos) == 1 and len(archivos) > 1:
        tipos = tipos * len(archivos)  # un solo tipo vale para todas
    if len(tipos) != len(archivos):
        raise ApiError(400, "DATOS_INVALIDOS", "Indica un tipo (pizarron o cuaderno) por página.")

    paginas, detalles = [], []
    for i, (archivo, tipo) in enumerate(zip(archivos, tipos), start=1):
        if tipo not in TIPOS_FUENTE:
            detalles.append({"pagina": i, "codigo": "DATOS_INVALIDOS",
                             "mensaje": "el tipo debe ser «pizarron» o «cuaderno»"})
            continue
        try:
            paginas.append(PaginaRecibida(i, tipo, validar_imagen(archivo)))
        except ApiError as exc:
            detalles.append({"pagina": i, "codigo": exc.codigo, "mensaje": exc.mensaje})
    if detalles:
        raise ErrorPaginas(detalles)
    return paginas
