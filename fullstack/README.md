# `fullstack/`: herramientas transversales de ApuntIA

Aquí vive lo que **une** el frontend y el backend: arranque y detención, contenedores, configuración compartida y pruebas de integración.
**No** contiene código de la aplicación: el frontend sigue en `index.html` y `front/`, y el backend en `back/motori_magenes/`.

## Estructura

```
fullstack/
├── README.md               # Este archivo
├── config/
│   └── .env.example        # Variables de toda la aplicación (puertos, datos, OCR, límites)
├── scripts/                # Arranque y detención sin Docker (FULL-11), copias de seguridad (FULL-23)
├── docker/                 # Dockerfile, nginx y compose.yaml (FULL-13)
├── tests/
│   └── integracion/        # Pruebas frontend + backend reales (antes en tests/integracion/)
└── evaluacion/             # Banco de muestras y métricas de OCR, fórmulas y PDF (FULL-19)
```

Las subcarpetas `scripts/`, `docker/` y `evaluacion/` se añaden en sus issues; esta estructura es la acordada para ellas.

## Reglas de ubicación

| Si el archivo… | Va en |
|----------------|-------|
| Es código de la interfaz (HTML, CSS, JS de la página) o sus pruebas con la API simulada | `index.html`, `front/`, `front/tests/` |
| Es código del backend o sus pruebas unitarias (pytest) | `back/motori_magenes/` |
| Arranca, detiene o empaqueta **varias** partes a la vez | `fullstack/scripts/` o `fullstack/docker/` |
| Prueba el frontend **y** el backend reales juntos | `fullstack/tests/integracion/` |
| Es documentación de producto, contratos o decisiones | `docs/` (una sola copia; aquí solo se enlaza) |
| Es un lanzador que el usuario ejecuta | Raíz del repositorio (`iniciar.*`, `detener.*`), que llama a `fullstack/scripts/` |

## Comandos públicos (no cambian)

| Comando | Qué hace |
|---------|----------|
| `npm run test:front` | Pruebas de interfaz (`front/tests/`) |
| `npm run test:integracion` | Pruebas de integración (`fullstack/tests/integracion/`) |
| `python -m pytest` (en `back/motori_magenes`) | Pruebas del backend |

## Dependencias entre módulos

```mermaid
flowchart LR
    FT["front/ + index.html"] -->|HTTP: docs/api.md, docs/api-v2.md| BK["back/motori_magenes"]
    FS["fullstack/"] -.arranca y prueba.-> FT & BK
    DOC["docs/"] -.describe.-> FT & BK & FS
```

| Carpeta | Responsable (área de los issues) |
|---------|----------------------------------|
| `front/`, `index.html` | Frontend (FRONT-*) |
| `back/motori_magenes/` | Backend (BACK-*) |
| `fullstack/`, `docs/` | Full stack (FULL-*) |

## Migración desde la estructura anterior

| Antes | Ahora | Compatibilidad |
|-------|-------|----------------|
| `tests/integracion/` | `fullstack/tests/integracion/` | `npm run test:integracion` se mantiene; documentación y CI actualizadas |
