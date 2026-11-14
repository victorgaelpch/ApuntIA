# Datos, migraciones, copias de seguridad y recuperación (FULL-23)

## 1. Dónde viven los datos

Una sola fuente de verdad: `DATA_DIR` (por defecto `back/motori_magenes/datos/`; en Docker, el
volumen `apuntia_datos` montado en `/datos`).

| Ruta | Qué es | ¿En la copia? |
|------|--------|---------------|
| `apuntia.sqlite3` | Base de datos: cuentas, sesiones, apuntes, versiones, trabajos, exportaciones | Sí (instantánea consistente) |
| `archivos/<usuario>/<id>` | Fotos, imágenes procesadas, recortes y PDF | Sí |
| `tmp/` | Escrituras a medio hacer; se limpian al arrancar | No |
| `buzon/` | Enlaces de recuperación de desarrollo (un solo uso, 30 min) | No |
| `respaldos/` | Copias automáticas antes de migrar | No |

Los archivos son **privados**: solo salen por rutas autenticadas que comprueban el propietario.
`DATA_DIR` nunca se sirve como estático (ni por el backend ni por Nginx) y está en `.gitignore`;
en Docker los datos van en un volumen, nunca en la imagen.

**Política:** cada guardado crea una versión (no se sobrescribe ninguna); los PDF son regenerables
desde su versión; borrar un apunte borra en cascada sus versiones, trabajos, archivos y PDF; borrar
la cuenta borra todo lo suyo.

## 2. Migraciones

- Archivos `back/motori_magenes/app/datos/migraciones/NNNN_*.sql`, aplicados en orden al arrancar,
  cada uno en una transacción. Se registra su SHA-256: si alguien modifica una migración ya aplicada,
  el arranque se detiene con un error claro («crea una nueva»).
- Una migración que falla hace ROLLBACK y el error queda **visible** (el servidor no arranca a medias).
- **Copia automática:** si al arrancar hay migraciones pendientes sobre una base con datos, antes de
  aplicarlas se guarda `DATA_DIR/respaldos/antes-de-migrar-desde-vN-<fecha>.sqlite3` y se avisa en el log.
- `GET /api/v2/listo` responde 503 si el esquema no está al día.

**Plan de recuperación ante una migración fallida:** 1) detener; 2) volver a la versión anterior del
código; 3) si la base quedó dañada, sustituir `apuntia.sqlite3` por la copia automática de
`respaldos/` (o restaurar la última copia completa); 4) avisar del fallo con el log.

**Cambio de ubicación por la carpeta `fullstack/`:** no afectó a los datos (siguen en `DATA_DIR`).
Si se cambia `DATA_DIR`, basta con mover la carpeta entera o restaurar una copia en la nueva ruta.

## 3. Copias de seguridad

```bash
fullstack/scripts/respaldar.sh
```

```bash
fullstack/scripts/respaldar.sh --docker
```

Crea `respaldos/apuntia-AAAAMMDD-HHMMSS.tar.gz` (permisos 0600; `respaldos/` está en `.gitignore`)
con la base de datos (copia en línea de SQLite: **se puede hacer con la aplicación en marcha**), los
archivos y un `manifiesto.json` (versión del esquema, recuentos y SHA-256 de cada archivo, sin datos
personales). Después la verifica. La copia **contiene datos personales**: guárdala en un lugar con
acceso restringido y, si sale del equipo, cífrala (p. ej. `gpg -c copia.tar.gz`).

## 4. Restauración

```bash
./detener.sh
```

```bash
fullstack/scripts/restaurar.sh respaldos/apuntia-AAAAMMDD-HHMMSS.tar.gz --forzar
```

En Docker: `fullstack/scripts/restaurar.sh copia.tar.gz --docker --forzar` (para los servicios,
restaura en el volumen y los vuelve a arrancar).

1. Verifica la copia (SHA-256 de cada archivo, integridad de SQLite, sin rutas `../` ni enlaces).
2. Si `DATA_DIR` tiene datos, exige `--forzar` y **los aparta** (no los borra): `DATA_DIR.antes-<fecha>`,
   o `DATA_DIR/.antes-<fecha>` en un volumen de Docker.
3. Extrae la base de datos y los archivos y aplica las migraciones que falten si la copia es de una
   versión anterior.
4. Si algo falla, deja todo como estaba.

Con la aplicación en marcha, `restaurar.sh` (modo local) se niega y pide detenerla.

## 5. Evidencia

| Prueba | Qué comprueba |
|--------|---------------|
| `tests/test_respaldo.py` (9) | Copia → entorno borrado → restauración en limpio: la cuenta entra con su contraseña, el apunte con sus versiones, la foto y el PDF (idéntico byte a byte) vuelven y otra cuenta sigue sin verlo; copia con escrituras simultáneas; copias dañadas y con `../`; no pisar sin `--forzar`; restaurar en un punto de montaje; restauración fallida que no toca nada; copia de una versión anterior que se migra; copia automática antes de migrar |
| `tests/test_regresion.py` | Migración 0004 sobre datos de la versión anterior |
| `fullstack/tests/scripts` | `respaldar.sh` con la app en marcha, `restaurar.sh` que se niega si está en marcha, pérdida de datos y restauración |
| `fullstack/tests/docker` | Copia en Docker, `down -v` (se pierde el volumen), restauración y la cuenta vuelve |
| `test_seguridad_api.py` | Ningún archivo privado es accesible sin ser su propietario; traversal |
