# Estructura documental de ApuntIA (FULL-29)

Una **fuente canónica por tema**: cada asunto se documenta en un solo archivo y los demás lo
enlazan. Este documento fija dónde va cada cosa y cómo se comprueba.

## 1. Árbol real

```
README.md                    # Entrada principal: qué es, inicio rápido, mapa de documentación
CHANGELOG.md · CONTRIBUTING.md
front/
├── README.md                # Uso y estructura del frontend
└── docs/                    # Documentación SOLO de la interfaz
    ├── README.md            # Índice de front/docs
    ├── interfaz-v2.md       # Páginas con cuenta, estados, accesibilidad (FRONT-11…22)
    ├── pruebas-frontend.md  # Pruebas de interfaz v1 (FRONT-10)
    └── pruebas-interfaz.md  # Suites de interfaz, a11y y responsive (FRONT-21)
ia_servidor/                 # Servidor de inferencia IA (BACK-35); su guía: fullstack/docs/servidor-ia.md
back/motori_magenes/
├── README.md                # Instalación y uso del backend (BACK-10)
└── PROCESAMIENTO.md         # Notas técnicas internas del pipeline OpenCV/OCR (junto al código)
fullstack/
├── README.md                # Herramientas transversales y reglas de ubicación del código
├── docs/                    # Documentación transversal (este directorio)
│   ├── README.md            # Índice
│   ├── ESTRUCTURA_DOCUMENTAL.md
│   ├── *.md                 # Arquitectura, API, seguridad, pruebas, despliegue, aceptación…
│   └── evidencias/          # Capturas y registros de evidencia (una sola copia para todo el repo)
└── tickets/                 # Fichas de Issues, cronograma planificado y bitácoras reales
    ├── README.md · INDICE.md · PLANTILLA_TICKET.md · cronograma-planeado.md
    ├── <ID>.md              # Una ficha por Issue (FULL-29.md, BACK-28.md, issue-91.md…)
    ├── bitacora/            # Bitácoras manuales: el sincronizador NUNCA las toca
    └── datos/issues.json    # Snapshot regenerable de la API de GitHub (uso offline)
```

## 2. Reglas de ubicación

| Tipo de documento | Ubicación | Ejemplos |
|-------------------|-----------|----------|
| Global: arquitectura, contratos de API, seguridad, privacidad, pruebas transversales, algoritmos, despliegue, investigación, aceptación | `fullstack/docs/` | `api-v2.md`, `seguridad.md`, `entrega.md` |
| Frontend: pantallas, estados, componentes de UI, accesibilidad, pruebas de interfaz, contratos *consumidos* (enlazando al contrato global) | `front/docs/` | `interfaz-v2.md`, `pruebas-interfaz.md` |
| Backend interno: notas de implementación que solo tienen sentido leyendo el código | Junto al código, en `back/motori_magenes/` y enlazado desde `fullstack/docs/` | `PROCESAMIENTO.md` |
| Capturas y registros de evidencia | `fullstack/docs/evidencias/` (la documentación de `front/docs/` las enlaza con `../../fullstack/docs/evidencias/`) | `front-10-inicio.jpg` |
| Issues: ficha, estado, fechas, plan y bitácora | `fullstack/tickets/` | `FULL-29.md`, `bitacora/FULL-29.md` |
| Historial de versiones | `CHANGELOG.md` (raíz) | — |

Criterios de decisión:

- Si un documento lo necesita leer quien trabaja en **más de un área**, es global.
- Si describe *qué* hace la API, es global aunque lo consuma la interfaz; `front/docs/` enlaza a
  él, no lo copia.
- Nada se duplica: si dos documentos hablan del mismo tema, uno es canónico y el otro enlaza.
- `front/docs/` **no se publica** en el servidor web: el `.dockerignore` de la imagen web y
  `app/routers/frontend.py` lo excluyen (prueba: `tests/test_frontend_estaticos.py`).

## 3. Migración realizada (FULL-29)

| Ruta antigua | Ruta nueva |
|--------------|------------|
| `docs/*.md` (salvo los tres de la interfaz) | `fullstack/docs/*.md` |
| `docs/evidencias/` | `fullstack/docs/evidencias/` |
| `docs/interfaz-v2.md` | `front/docs/interfaz-v2.md` |
| `docs/pruebas-frontend.md` | `front/docs/pruebas-frontend.md` |
| `docs/pruebas-interfaz.md` | `front/docs/pruebas-interfaz.md` |

- Se movió con `git mv` (`git log --follow` conserva el historial; `git diff --find-renames
  origin/main` muestra los archivos como renombrados, no como borrados + nuevos).
- Se actualizaron los enlaces relativos de todos los `.md`, las rutas en comentarios del código,
  las pruebas que leen contratos (`test_documento.py`, `compatibilidad.test.js`), la herramienta de
  mutaciones, el workflow de CI y la plantilla de PR.
- `CHANGELOG.md` conserva las rutas antiguas en las entradas de versiones ya publicadas (son
  historia); sus **enlaces** sí apuntan a la ruta nueva para no romperse.
- **Enlaces externos** a `https://github.com/victorgaelpch/ApuntIA/blob/main/docs/...` dejarán de
  funcionar. No se dejó una carpeta `docs/` con avisos para no mantener duplicados; la tabla de
  arriba es la correspondencia oficial. Si el profesor lo pide, basta un `docs/README.md` de una
  línea que enlace a `fullstack/docs/README.md`.

## 4. Cómo se comprueba

```bash
python fullstack/scripts/comprobar_enlaces.py
```

Falla (código 1) y lista cada ruta rota si:

- un enlace relativo `[texto](ruta)` o una imagen `![alt](ruta)` apunta a un archivo inexistente;
- un `#ancla` no corresponde a ningún título del documento destino;
- un `.md` de `fullstack/docs/`, `front/docs/` o `fullstack/tickets/` no es alcanzable siguiendo
  enlaces desde el `README.md` raíz (documento huérfano).

Se ejecuta en `fullstack/scripts/validar.sh` y, por tanto, en el trabajo «rápido» de la CI.
Sus pruebas están en `fullstack/tests/docs/`.
