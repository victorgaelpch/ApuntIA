"""Comprueba que la suite detecta regresiones introducidas a propósito (BACK-25).

Copia el backend a una carpeta temporal, aplica UNA mutación (un fallo típico:
quitar un filtro de propietario, no escapar texto, saltarse el CSRF…), ejecuta
la suite rápida y espera que falle. Si alguna mutación «sobrevive», falta una
prueba. El código original no se toca.

    python herramientas/mutaciones.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REPO = RAIZ.parents[1]

# (descripción, archivo, texto original, texto mutado)
MUTACIONES = [
    ("IDOR: el apunte no se filtra por propietario", "app/datos/apuntes.py",
     '"SELECT * FROM apuntes WHERE id = ? AND usuario_id = ?", (apunte_id, usuario_id)',
     '"SELECT * FROM apuntes WHERE id = ? AND ? IS NOT NULL", (apunte_id, usuario_id)'),
    ("CSRF: no se comprueba el token", "app/core/seguridad.py",
     "if not hmac.compare_digest(enviado, sesion.csrf):", "if False:"),
    ("Procedencia: el cliente puede reescribir lo que dijo la foto", "app/services/documento.py",
     "datos[campo] = getattr(previo, campo)", "pass"),
    ("PDF: el texto del usuario no se escapa", "app/services/pdf.py",
     'return escape(limpio).replace("\\n", "<br/>")', 'return limpio.replace("\\n", "<br/>")'),
    ("OCR: una palabra dudosa ya no vuelve incierto el bloque", "app/services/ocr.py",
     "self.minima < UMBRAL_RECONOCIDO:", "self.minima < 0:"),
    ("Abuso: sin límite de trabajos por usuario", "app/services/trabajos.py",
     "if activos >= MAX_ACTIVOS_POR_USUARIO:", "if False:"),
    ("Investigación: se aceptan páginas con instrucciones incrustadas", "app/services/investigacion.py",
     "elif INYECCION.search(h.fragmento) or INYECCION.search(h.titulo):", "elif False:"),
    ("Cabeceras: sin nosniff", "app/core/endurecimiento.py", 'b"nosniff"', 'b"sniff"'),
    ("Contrato v1: /analisis deja de devolver PNG", "app/routers/imagenes.py",
     'media_type="image/png",', 'media_type="image/jpeg",'),
    ("Archivos: se sirven archivos de otro apunte del mismo usuario", "app/routers/v2_apuntes.py",
     'if archivo.apunte_id != apunte_id or archivo.tipo == "pdf":', 'if archivo.tipo == "pdf":'),
]


def copiar(destino: Path) -> Path:
    """Copia el backend (y fullstack/docs/, que leen algunas pruebas) con la misma estructura del repositorio."""
    ignorar = shutil.ignore_patterns("__pycache__", "*.sqlite3", ".pytest_cache", "venv*", ".venv")
    backend = destino / RAIZ.relative_to(REPO)
    backend.mkdir(parents=True)
    for nombre in ("app", "tests", "herramientas", "pytest.ini"):
        origen = RAIZ / nombre
        if origen.is_dir():
            shutil.copytree(origen, backend / nombre, ignore=ignorar)
        else:
            shutil.copy2(origen, backend / nombre)
    shutil.copytree(REPO / "fullstack" / "docs", destino / "fullstack" / "docs", ignore=ignorar)
    return backend


def ejecutar(carpeta: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-rf", "-p", "no:cacheprovider"],
                       cwd=carpeta, capture_output=True, text=True, timeout=900)
    fallo = next((linea.split(" ")[1] for linea in r.stdout.splitlines() if linea.startswith("FAILED")), "")
    return r.returncode, fallo


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="apuntia-mut-") as tmp:
        codigo, _ = ejecutar(copiar(Path(tmp)))
        if codigo != 0:
            print("La suite falla SIN mutaciones: arréglala antes de evaluar las mutaciones.")
            return 2
    sobrevivientes = 0
    print("| Mutación | Detectada | Primera prueba que falla |")
    print("|----------|-----------|--------------------------|")
    for descripcion, archivo, original, mutado in MUTACIONES:
        with tempfile.TemporaryDirectory(prefix="apuntia-mut-") as tmp:
            carpeta = copiar(Path(tmp))
            ruta = carpeta / archivo
            codigo = ruta.read_text(encoding="utf-8")
            if codigo.count(original) != 1:
                print(f"| {descripcion} | ERROR: el texto a mutar no aparece una vez en {archivo} | |")
                sobrevivientes += 1
                continue
            ruta.write_text(codigo.replace(original, mutado), encoding="utf-8")
            codigo_salida, fallo = ejecutar(carpeta)
            detectada = codigo_salida == 1 and bool(fallo)  # 1 = pruebas fallidas (no errores de recolección)
            sobrevivientes += not detectada
            print(f"| {descripcion} | {'sí' if detectada else '**NO**'} | `{fallo}` |")
    print(f"\nMutaciones detectadas: {len(MUTACIONES) - sobrevivientes}/{len(MUTACIONES)}")
    return 1 if sobrevivientes else 0


if __name__ == "__main__":
    sys.exit(main())
