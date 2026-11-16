# Investigación verificada (BACK-18, ampliada en BACK-38)

La información complementaria es **opcional**, **citada** y **aparte** de lo fotografiado. Código:
`back/motori_magenes/app/services/investigacion.py`; interfaz: pestaña «Información complementaria»
del editor ([front/docs](../../front/docs/)). Contrato HTTP: [api-v2.md §7](api-v2.md).

## 1. Reglas (auditadas el 14/11/2026)

| Regla | Cómo se cumple |
|-------|----------------|
| Opt-in explícito | preferencia `investigacion_permitida` del perfil **y** `consentimiento: true` en cada petición |
| Privacidad | solo se envían las palabras clave que la persona marca (≤ 8, ≤ 6 palabras, sin URLs, rutas ni números largos); nunca la foto ni el texto del apunte |
| Sin SSRF | el servidor solo consulta hosts fijos (`es`/`en` de cada proyecto); nunca una URL del usuario, del modelo ni de la respuesta; **las redirecciones a otro host o a `http` se rechazan** (BACK-38, `_SoloHosts`) |
| Respuesta acotada | `https` obligatorio, 512 KB máximo, timeout `INVESTIGACION_TIMEOUT_S` (6 s), 404 = «sin resultado», 429/5xx/red = «no disponible» |
| Contenido no confiable | se quita el HTML, se recorta a una cita breve (≤ 600 caracteres, hasta la última frase) y se descarta si contiene instrucciones dirigidas a un asistente |
| Sin citas inventadas | la URL citada se construye con la clave de la página, no se copia de la respuesta; sin fuente no hay ampliación |
| Discrepancias | si el apunte y la fuente dan cifras distintas, o el apunte define en negativo, se marca `discrepancia` y se pide revisar |
| Aceptación | cada ampliación nace `propuesta`; solo las `aceptadas` van al PDF, en «Información complementaria» y «Fuentes» |
| Sin Internet | `INVESTIGACION_PROVEEDOR=ninguno` o red caída: el apunte, el editor y el PDF funcionan igual (`INVESTIGACION_NO_DISPONIBLE`) |

## 2. Fuentes disponibles

`INVESTIGACION_PROVEEDOR` (en `back/motori_magenes/.env`):

| Valor | Qué consulta | Licencia y atribución |
|-------|--------------|-----------------------|
| `wikipedia` (por defecto) | `es`/`en.wikipedia.org`: búsqueda REST + resumen de la página | CC BY-SA 4.0 · «Colaboradores de Wikipedia» |
| `wikilibros` | `es`/`en.wikibooks.org`, libros de texto abiertos: búsqueda REST + extracto en texto plano (TextExtracts, sin títulos de sección) | CC BY-SA 4.0 · «Colaboradores de Wikilibros» |
| `wikipedia,wikilibros` | en ese orden: si la primera no tiene resultado o no responde, se prueba la siguiente; solo es «no disponible» si fallan todas | la de la fuente que respondió |
| `ninguno` | nada | — |

Comprobación real (14/11/2026, término genérico «Derivada», sin datos del usuario): Wikipedia respondió
en 437 ms y Wikilibros en 360 ms; ambas citas (`https://es.wikipedia.org/wiki/Derivada`,
`https://es.wikibooks.org/wiki/Matemáticas/Bachillerato_LOGSE/Derivadas`) resolvieron con HTTP 200. El
«summary» REST de Wikilibros llega vacío para páginas de libro (empiezan por secciones), por eso allí
se usa TextExtracts.

### Fuentes que NO se añadieron (y por qué)

El ticket menciona universidades, documentación oficial y artículos con DOI. No se integraron:
no hay una API pública única con licencia que permita citar fragmentos, sus términos de uso varían por
sitio y un buscador general devolvería URLs arbitrarias (riesgo de SSRF y de citas no verificables).
Para añadir una, implementar `Proveedor` con **hosts fijos**, licencia conocida y pruebas offline como
las de `tests/test_investigacion.py`; nunca aceptar URLs que proponga el modelo.

## 3. De dónde salen los conceptos

`GET /api/v2/apuntes/{id}/conceptos` sugiere conceptos sacados del propio apunte (glosario, títulos,
términos frecuentes) **solo de bloques confirmados**: una propuesta del servidor IA sin revisar no
decide qué se busca fuera (BACK-38). La persona elige y puede escribir los suyos.

## 4. Errores y recuperación

| Situación | Resultado | Qué ve la persona |
|-----------|-----------|-------------------|
| 404 / sin páginas | concepto «sin resultado», no se inventa nada | «No se encontraron fuentes fiables…» |
| 429, 5xx, timeout, sin red | `ProveedorNoDisponible`; si fallan todos: `INVESTIGACION_NO_DISPONIBLE` | «No se pudo consultar la fuente externa. Tu apunte sigue intacto» |
| Algunos conceptos fallan | trabajo `parcial` con los que sí | «Algunos conceptos no se pudieron consultar» |
| Página con instrucciones | descartada | «descartados por contener instrucciones» |
| Redirección a otro host | rechazada, cuenta como no disponible | igual que un fallo de red |
| El apunte cambió durante la búsqueda | se añade sobre la versión más reciente (3 intentos) | sin pérdida de ediciones |

## 5. Pruebas

`tests/test_investigacion.py` (offline, fuente simulada): cita real y breve, privacidad, consentimiento,
conceptos inválidos, sin proveedor, caída, sin resultados, desambiguación e inyección, contradicción,
parcial, aceptar/rechazar sin duplicar, el cliente no reescribe lo investigado, ediciones concurrentes,
URL fija, **Wikilibros con su host y atribución, cadena de fuentes, configuración, redirecciones
rechazadas y conceptos solo de lo confirmado**. Interfaz: `fullstack/tests/integracion/v2-investigacion.test.js`.
