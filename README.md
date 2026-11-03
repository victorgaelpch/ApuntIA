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
cd ApuntIA/back/motori_magenes
```

> Consulta `back/motori_magenes/README.md` para ver la estructura del backend, las rutas y las variables de entorno.

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

El punto de entrada es `main.py`, que expone la instancia `app` creada en `app/main.py`. Por compatibilidad, `uvicorn index:app --reload` también funciona.

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
