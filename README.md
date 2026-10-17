# ApuntIA – Backend de procesamiento de imágenes

Backend desarrollado con Python y FastAPI para el procesamiento y análisis de imágenes del proyecto ApuntIA.

## Requisitos previos

Antes de ejecutar el proyecto, instala:

- Python 3.11 o una versión compatible con las dependencias.
- Git.
- pip, incluido normalmente con Python.

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/victorgaelpch/ApuntIA.git
cd ApuntIA/Proyecto-RC/back/motori_magenes
```

> La ruta anterior corresponde a la estructura esperada del repositorio. Si las carpetas cambian, ajusta el comando `cd`.

### 2. Crear un entorno virtual

En Windows:

```powershell
python -m venv .venv
```

### 3. Activar el entorno virtual

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar las dependencias

Con el entorno virtual activado, ejecuta:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Este comando instala las librerías necesarias para ejecutar el backend.

## Ejecución del servidor

Desde la carpeta `motori_magenes`, inicia el servidor con:

```bash
uvicorn main:app --reload
```

**Nota:** el comando supone que el archivo principal se llama `main.py` y que la instancia de FastAPI se llama `app`. Si tienen otros nombres, sustituye `main:app` por el módulo y la variable correspondientes.

## Acceso a la API

Cuando el servidor esté iniciado, puedes acceder a:

- **Servidor:** http://127.0.0.1:8000
- **Documentación Swagger:** http://127.0.0.1:8000/docs
- **Documentación alternativa:** http://127.0.0.1:8000/redoc

## Detener el servidor

Para detener Uvicorn, presiona `Ctrl + C` en la terminal donde se está ejecutando.

## Tecnologías utilizadas

- Python
- FastAPI
- Uvicorn
- OpenCV
- NumPy

## Estado del proyecto

En desarrollo.

## Autoría

Proyecto ApuntIA.
