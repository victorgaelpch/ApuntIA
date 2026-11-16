"""Arranque del servidor IA:  python -m ia_servidor   (desde la raíz del repositorio).

Lee la configuración del entorno (ver ia_servidor/.env.example), se niega a arrancar si es
insegura y sirve con uvicorn en 127.0.0.1:IA_PUERTO (8100 por defecto).
"""

import logging
import sys

from ia_servidor.config import Configuracion, ConfiguracionInvalida


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        config = Configuracion.desde_entorno()
    except ConfiguracionInvalida as e:
        print(f"ERROR de configuración: {e}", file=sys.stderr)
        return 2
    import uvicorn

    from ia_servidor.app import crear_app
    uvicorn.run(crear_app(config), host=config.host, port=config.puerto, log_level="warning",
                access_log=False, server_header=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
