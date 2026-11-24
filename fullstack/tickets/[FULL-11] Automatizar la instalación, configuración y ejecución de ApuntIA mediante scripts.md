# [FULL-11] Automatizar la instalación, configuración y ejecución de ApuntIA mediante scripts

- Numero de Issue: #41
- Enlace: https://github.com/victorgaelpch/ApuntIA/issues/41
- Estado: closed
- Autor: victorgaelpch
- Responsables: victorgaelpch
- Etiquetas: frontend, backend, fullStack
- Creacion GitHub: 2026-11-09 13:45:59 -0600 (CDMX)
- Cierre GitHub: 2026-11-10 11:05:01 -0600 (CDMX)
- Actualizacion GitHub: 2026-11-10 11:05:01 -0600 (CDMX)
- Creacion UTC: 2026-11-09T19:45:59Z
- Cierre UTC: 2026-11-10T17:05:01Z

- Fecha de captura: 2026-11-24 12:05:39 -0600 (CDMX)
- [Captura original](%5BFULL-11%5D%20Automatizar%20la%20instalaci%C3%B3n%2C%20configuraci%C3%B3n%20y%20ejecuci%C3%B3n%20de%20ApuntIA%20mediante%20scripts-original.png)
- [Captura con metadatos](%5BFULL-11%5D%20Automatizar%20la%20instalaci%C3%B3n%2C%20configuraci%C3%B3n%20y%20ejecuci%C3%B3n%20de%20ApuntIA%20mediante%20scripts.png)

## Descripcion original

## Objetivo

Desarrollar scripts de automatización que permitan instalar las dependencias, configurar el entorno e iniciar todos los componentes de ApuntIA mediante un único comando, sin utilizar Docker.

El objetivo es que el profesor pueda descargar el repositorio desde GitHub y ejecutar la aplicación web sin tener que configurar manualmente los servicios.

La automatización deberá contemplar:

- Frontend: HTML, CSS y JavaScript.
- Backend: Spring Boot.
- Motor de procesamiento: Python, FastAPI y OpenCV.
- Configuración de la comunicación entre los servicios.

## Actividades por realizar

### 1. Analizar la estructura del proyecto

- [ ] Revisar la organización actual del repositorio.
- [ ] Identificar las dependencias de cada componente.
- [ ] Identificar los puertos utilizados por los servicios.
- [ ] Verificar los requisitos de Python y Java.
- [ ] Identificar las variables de entorno necesarias.
- [ ] Determinar el orden correcto de inicio de los servicios.

### 2. Automatizar la configuración de Python

- [ ] Implementar la creación automática del entorno virtual.
- [ ] Automatizar la instalación de dependencias desde requirements.txt.
- [ ] Verificar la disponibilidad de FastAPI, Uvicorn y OpenCV.
- [ ] Automatizar el inicio del servidor FastAPI.
- [ ] Implementar validaciones y manejo de errores.

### 3. Automatizar Spring Boot

- [ ] Verificar que Java esté instalado.
- [ ] Configurar Maven Wrapper para evitar instalar Maven manualmente.
- [ ] Automatizar la descarga de dependencias del backend.
- [ ] Automatizar la compilación del proyecto.
- [ ] Implementar el inicio automático de Spring Boot.
- [ ] Verificar que el servidor esté disponible.

### 4. Automatizar el frontend

- [ ] Configurar el servidor necesario para ejecutar la interfaz.
- [ ] Automatizar el inicio del frontend.
- [ ] Verificar la comunicación con el backend.
- [ ] Configurar la apertura automática del navegador.
- [ ] Comprobar que la interfaz funcione correctamente.

### 5. Crear los scripts de inicio

- [ ] Crear iniciar.bat para Windows.
- [ ] Crear iniciar.sh para Linux.
- [ ] Implementar la verificación automática de requisitos.
- [ ] Automatizar la preparación de los entornos.
- [ ] Automatizar la instalación de dependencias.
- [ ] Iniciar automáticamente todos los servicios.
- [ ] Comprobar que los servidores estén disponibles.
- [ ] Mostrar mensajes informativos durante la ejecución.
- [ ] Implementar el manejo de errores.
- [ ] Evitar rutas absolutas dependientes de una computadora.

### 6. Crear los scripts de detención

- [ ] Crear detener.bat para Windows.
- [ ] Crear detener.sh para Linux.
- [ ] Implementar la detención controlada de los servicios.
- [ ] Evitar finalizar procesos ajenos a ApuntIA.
- [ ] Verificar que los servicios puedan reiniciarse correctamente.

### 7. Actualizar README.md

- [ ] Agregar una sección de instalación automatizada.
- [ ] Documentar los requisitos mínimos del sistema.
- [ ] Explicar cómo descargar el repositorio.
- [ ] Documentar la ejecución mediante iniciar.bat.
- [ ] Documentar la ejecución mediante iniciar.sh.
- [ ] Explicar cómo acceder a la aplicación desde el navegador.
- [ ] Documentar cómo detener los servicios.
- [ ] Agregar soluciones para errores comunes.
- [ ] Verificar que las instrucciones coincidan con los scripts implementados.

### 8. Realizar pruebas de funcionamiento

- [ ] Descargar el repositorio en un entorno limpio.
- [ ] Ejecutar el sistema utilizando únicamente el script correspondiente.
- [ ] Verificar la creación automática del entorno virtual.
- [ ] Comprobar la instalación de dependencias.
- [ ] Verificar el inicio de Spring Boot.
- [ ] Verificar el inicio de FastAPI.
- [ ] Comprobar el funcionamiento del frontend.
- [ ] Realizar una prueba de carga y procesamiento de imágenes.
- [ ] Verificar la comunicación entre todos los componentes.
- [ ] Comprobar la detención y el reinicio del sistema.
- [ ] Realizar pruebas en Windows y Linux.
- [ ] Documentar los resultados obtenidos.

## Criterios de aceptación

El Issue se considerará completado cuando:

- [ ] ApuntIA pueda iniciarse mediante un único script.
- [ ] No sea necesario instalar manualmente las dependencias del proyecto.
- [ ] Se verifique automáticamente la disponibilidad de Python y Java.
- [ ] El entorno virtual se configure automáticamente.
- [ ] Spring Boot y FastAPI se inicien correctamente.
- [ ] El frontend esté disponible desde el navegador.
- [ ] Los servicios puedan comunicarse correctamente.
- [ ] Los scripts detecten y notifiquen errores.
- [ ] El sistema pueda detenerse y reiniciarse correctamente.
- [ ] Los scripts funcionen en Windows y Linux.
- [ ] El README.md contenga instrucciones completas y verificadas.
- [ ] No se utilice Docker.
- [ ] No existan rutas absolutas específicas de los desarrolladores.

## Entregables

1. iniciar.bat: script de instalación y ejecución para Windows.
2. iniciar.sh: script de instalación y ejecución para Linux.
3. detener.bat: script de detención para Windows.
4. detener.sh: script de detención para Linux.
5. Configuraciones necesarias para la automatización.
6. README.md actualizado.
7. Evidencias de funcionamiento en Windows y Linux.
8. Commits y Pull Request correspondientes.

## Evidencias requeridas

- Capturas o registros de la ejecución automatizada.
- Evidencia de la instalación automática de dependencias.
- Evidencia de los servidores funcionando.
- Captura de ApuntIA ejecutándose en el navegador.
- Prueba de carga y procesamiento de una imagen.
- Resultados de las pruebas en Windows y Linux.
- Enlaces a los commits realizados.

## Bitácora de desarrollo

Registrar durante la implementación:

- Fecha de trabajo.
- Tiempo dedicado.
- Actividades realizadas.
- Archivos creados o modificados.
- Problemas encontrados.
- Soluciones implementadas.
- Pruebas realizadas.
- Resultados obtenidos.
- Evidencias y commits correspondientes.

## Resultado esperado

Al finalizar esta actividad, ApuntIA contará con un mecanismo automatizado de instalación y ejecución que permitirá descargar el repositorio, ejecutar un único script y utilizar la aplicación web sin configurar manualmente las dependencias ni iniciar individualmente sus componentes.

La solución deberá funcionar sin Docker y estar documentada en el README.md para facilitar su ejecución y evaluación.

## Evidencia visual

![Captura del Issue #41](%5BFULL-11%5D%20Automatizar%20la%20instalaci%C3%B3n%2C%20configuraci%C3%B3n%20y%20ejecuci%C3%B3n%20de%20ApuntIA%20mediante%20scripts.png)
