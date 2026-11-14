"""Catálogo de errores del servidor IA. Todas las respuestas de error tienen la forma

    {"error": {"codigo": "...", "mensaje": "...", "reintentable": true|false, "id_correlacion": "..."}}

`reintentable` dice al cliente (BACK-37) si tiene sentido volver a intentarlo más tarde sin
cambiar la petición. El mensaje es público; el detalle técnico solo va al log, sin contenido
de la imagen.
"""

from __future__ import annotations

# codigo: (estado HTTP, reintentable, mensaje público)
CATALOGO: dict[str, tuple[int, bool, str]] = {
    "IMAGEN_VACIA": (400, False, "El archivo está vacío."),
    "IMAGEN_CORRUPTA": (400, False, "La imagen no se puede abrir: está dañada o incompleta."),
    "FALTA_IMAGEN": (400, False, "Falta el campo «imagen» en la petición."),
    "TAREA_INVALIDA": (400, False, "La tarea pedida no existe; consulta /api/v1/capacidades."),
    "IMAGEN_DEMASIADO_GRANDE": (413, False, "La imagen supera el tamaño máximo permitido."),
    "RESOLUCION_EXCESIVA": (413, False, "La imagen tiene demasiados píxeles."),
    "FORMATO_NO_SOPORTADO": (415, False, "Formato no admitido: usa JPEG, PNG o WEBP."),
    "OCUPADO": (429, True, "El servidor IA está ocupado con otra imagen; vuelve a intentarlo en unos segundos."),
    "RESPUESTA_INVALIDA": (502, True, "El modelo devolvió una respuesta fuera de contrato; no se guardó nada."),
    "NO_DISPONIBLE": (503, True, "Ollama no responde en este equipo."),
    "MODELO_NO_INSTALADO": (503, False, "El modelo configurado no está instalado en Ollama."),
    "SIN_MEMORIA": (503, True, "El modelo no cabe en la memoria de la GPU en este momento."),
    "TIEMPO_AGOTADO": (504, True, "El modelo tardó demasiado en responder."),
    "ERROR_INTERNO": (500, True, "Error interno del servidor IA."),
}


class ErrorIA(Exception):
    def __init__(self, codigo: str, detalle: str = ""):
        if codigo not in CATALOGO:
            codigo = "ERROR_INTERNO"
        super().__init__(detalle or CATALOGO[codigo][2])
        self.codigo = codigo
        self.detalle = detalle  # para el log; nunca contiene texto de la imagen

    @property
    def estado(self) -> int:
        return CATALOGO[self.codigo][0]

    @property
    def reintentable(self) -> bool:
        return CATALOGO[self.codigo][1]

    def cuerpo(self, id_correlacion: str) -> dict:
        return {"error": {"codigo": self.codigo, "mensaje": CATALOGO[self.codigo][2],
                          "reintentable": self.reintentable, "id_correlacion": id_correlacion}}
