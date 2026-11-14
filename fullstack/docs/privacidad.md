# Privacidad (FULL-20)

Política de datos de ApuntIA, escrita para quien la usa y para quien la instala.

## 1. Qué datos se guardan y para qué

| Dato | Para qué | Dónde |
|------|----------|-------|
| Email y nombre | Iniciar sesión y saludarte | Base de datos del servidor |
| Contraseña | Solo su huella (scrypt); nadie puede leerla | Base de datos |
| Fotos que subes, sus recortes y sus PDF | Crear y mostrar tus apuntes | Carpeta privada del servidor |
| Texto de tus apuntes y sus versiones | Editar y recuperar versiones anteriores | Base de datos |
| Preferencias | Tipo de fuente, idioma del OCR, opciones del PDF, permiso de investigación | Base de datos |
| Sesiones | Mantenerte conectado (máx. 12 h sin uso, 7 días en total) | Cookie + huella en la base de datos |

«Mejorar una foto» (sin cuenta) **no guarda nada**: la foto se procesa en memoria y se devuelve.

No hay publicidad, analítica ni seguimiento de terceros. Las fuentes tipográficas de la interfaz se
cargan de Google Fonts (el navegador hace esa petición); el resto del código es propio.

## 2. Quién puede ver tus datos

Solo tú. Cada consulta comprueba que el apunte, la foto o el PDF son tuyos; cualquier otra cuenta
recibe «no existe». No hay enlaces públicos. Quien administra el servidor tiene acceso técnico a la
carpeta de datos: instálalo en un equipo de confianza.

## 3. Información complementaria (servicio externo)

Está **desactivada por defecto**. Para usarla tienes que permitirla en tu perfil y confirmar cada
búsqueda. Solo se envían a Wikipedia las **palabras clave que marques** (nunca tus fotos ni el texto
de tu apunte). Lo encontrado se guarda con su fuente y solo entra en tu PDF si lo aceptas. Sin
Internet o con la opción desactivada, todo lo demás funciona.

El reconocimiento de texto (Tesseract) y la generación del PDF se hacen **en el propio servidor**:
no se envía nada a servicios de OCR en la nube.

## 4. Conservación y borrado

| Qué | Cuánto tiempo |
|-----|---------------|
| Apuntes, versiones, fotos y PDF | Hasta que los borres (o borres la cuenta) |
| Borrar un apunte | Se borran al momento sus versiones, fotos, recortes y PDF |
| Borrar la cuenta | Se borra todo lo tuyo y se cierran tus sesiones |
| Temporales de escrituras interrumpidas | Se limpian al arrancar el servidor |
| Imágenes intermedias de un análisis cancelado | Se borran al cancelar |
| Enlaces de recuperación | 30 minutos, un solo uso |
| Registros del servidor | Sin contraseñas, tokens, emails ni texto de apuntes; en modo local se sobrescriben en cada arranque |
| Copias de seguridad | Las que haga quien administra el servidor (contienen datos personales: deben guardarse con acceso restringido y borrarse cuando ya no hagan falta) |
| Lo enviado a Wikipedia | Solo palabras clave; su conservación depende de Wikipedia |

## 5. Datos de terceros en las fotos

Las fotos de un pizarrón o de un cuaderno pueden contener nombres u otros datos de compañeros o
docentes. Súbelas solo si tienes derecho a hacerlo. Las fotos reales **nunca** se incluyen en el
repositorio ni en las pruebas: el corpus de evaluación es sintético.

## 6. Tus opciones

- Ver, corregir y borrar tus apuntes en «Mis apuntes» y en el editor.
- Cambiar tus datos, preferencias, permiso de investigación y contraseña en «Perfil».
- Cerrar la sesión en los demás navegadores.
- Borrar la cuenta entera desde «Perfil».
