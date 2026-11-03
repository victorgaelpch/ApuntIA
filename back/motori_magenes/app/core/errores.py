"""Errores de la API con la estructura acordada en docs/api.md.

    {"error": {"codigo": "TIPO_NO_PERMITIDO", "mensaje": "..."}}
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Error previsto que se devuelve al cliente con un código estable."""

    def __init__(self, status_code: int, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje


def respuesta_error(status_code: int, codigo: str, mensaje: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"codigo": codigo, "mensaje": mensaje}},
    )


async def manejar_api_error(_: Request, exc: ApiError) -> JSONResponse:
    return respuesta_error(exc.status_code, exc.codigo, exc.mensaje)
