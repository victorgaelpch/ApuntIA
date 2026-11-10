// Catálogo de mensajes para el usuario (FRONT-08).
//
// Cada código, ya sea del contrato de la API (docs/api.md y docs/api-v2.md), de
// validación en el navegador, de la cámara o de red, se traduce a:
//   texto:    mensaje público, en lenguaje sencillo y orientado a la solución
//   acciones: lo que se ofrece para resolverlo (ids que app.js convierte en botones;
//             las páginas con cuenta añaden sus propios botones)
//   tipo:     "error" (por defecto), "aviso" (se puede continuar) o "info"
//
// Es el catálogo ÚNICO de la interfaz (FRONT-20): las páginas con cuenta lo usan a
// través de nucleo.js. Los mensajes 4xx de la API v2 ya son textos para el usuario y
// tienen prioridad; el catálogo cubre los 5xx, los errores del cliente y los códigos
// sin mensaje.
//
// El detalle técnico (status, codigo, errorId, causa) nunca se muestra como
// texto principal: va a la consola y a un desplegable «Detalles técnicos»
// que solo contiene el código y la referencia, sin trazas.
(function (global) {
    "use strict";

    const NS = (global.ApuntIA = global.ApuntIA || {});
    const maxMb = () => (NS.config && NS.config.maxMb) || 10;
    const formatos = () => {
        const lista = ((NS.config && NS.config.formatos) || ["image/jpeg", "image/png", "image/webp"]).map((f) => f.replace("image/", "").toUpperCase());
        return lista.length > 1 ? `${lista.slice(0, -1).join(", ")} o ${lista[lista.length - 1]}` : lista[0];
    };

    const CATALOGO = {
        // --- selección y validación (navegador y API)
        ARCHIVO_AUSENTE: { texto: "Primero elige una foto del pizarrón o del cuaderno.", acciones: ["cargar", "camara"] },
        ARCHIVO_VACIO: { texto: "El archivo está vacío. Elige otra imagen.", acciones: ["elegirOtra"] },
        TIPO_NO_PERMITIDO: {
            texto: () => `Ese archivo no es una imagen admitida. Usa una foto ${formatos()}. (Las fotos HEIC del iPhone se pueden exportar como JPEG.)`,
            acciones: ["elegirOtra"],
        },
        ARCHIVO_DEMASIADO_GRANDE: { texto: () => `La imagen pesa más de ${maxMb()} MB. Elige una más ligera o reduce su tamaño.`, acciones: ["elegirOtra"] },
        IMAGEN_DEMASIADO_GRANDE: { texto: "La imagen tiene demasiada resolución. Usa una foto de menor resolución.", acciones: ["elegirOtra"] },
        IMAGEN_CORRUPTA: { texto: "No se pudo leer la imagen; puede estar dañada o incompleta. Elige otra.", acciones: ["elegirOtra"] },

        // --- cámara
        CAMARA_PERMISO_DENEGADO: {
            texto: "No se dio permiso para usar la cámara. Puedes permitirlo desde el icono junto a la dirección del navegador, o usar otra opción:",
            acciones: ["camaraApp", "cargar"],
        },
        CAMARA_NO_DISPONIBLE: { texto: "No se encontró ninguna cámara en este dispositivo. Usa otra opción:", acciones: ["camaraApp", "cargar"] },
        CAMARA_OCUPADA: { texto: "La cámara está siendo usada por otra aplicación. Ciérrala y vuelve a intentarlo, o usa otra opción:", acciones: ["camara", "cargar"] },
        CAMARA_ERROR: { texto: "No se pudo iniciar la cámara. Usa otra opción:", acciones: ["camaraApp", "cargar"] },

        // --- red y tiempos
        SIN_CONEXION: {
            texto: () => (global.navigator.onLine === false
                ? "No hay conexión a la red. Revisa tu conexión y vuelve a intentarlo."
                : "No se pudo conectar con el servidor de ApuntIA. Comprueba que esté encendido y vuelve a intentarlo."),
            acciones: ["reintentar"],
        },
        TIEMPO_AGOTADO: { texto: "El servidor tardó demasiado en responder. Vuelve a intentarlo; si se repite, prueba con una foto más ligera.", acciones: ["reintentar", "elegirOtra"] },
        CANCELADO: { texto: "Procesamiento cancelado. Puedes volver a intentarlo o elegir otra imagen.", acciones: ["reintentar"], tipo: "listo" },

        // --- servidor
        ERROR_PROCESAMIENTO: { texto: "No se pudo procesar esta imagen. Vuelve a intentarlo o prueba con otra foto.", acciones: ["reintentar", "elegirOtra"] },
        ERROR_INTERNO: { texto: "Ocurrió un problema en el servidor. Vuelve a intentarlo en unos momentos.", acciones: ["reintentar"] },
        RESPUESTA_INVALIDA: { texto: "El servidor devolvió un resultado que no se puede mostrar. Vuelve a intentarlo.", acciones: ["reintentar"] },

        // --- errores de configuración o de la aplicación (no causados por el usuario)
        PARAMETRO_INVALIDO: { texto: "La aplicación envió una petición incorrecta. Recarga la página y vuelve a intentarlo.", acciones: ["recargar"] },
        DATOS_INVALIDOS: { texto: "Algunos datos no son válidos. Revísalos y vuelve a intentarlo.", acciones: ["reintentar"] },
        CARGA_DEMASIADO_GRANDE: { texto: "Lo que intentas enviar es demasiado grande. Prueba con menos fotos o fotos más ligeras.", acciones: ["elegirOtra"] },
        RUTA_NO_ENCONTRADA: { texto: "La dirección del servidor no es la correcta. Revisa la configuración de la API.", acciones: ["reintentar"] },
        SERVIDOR_REQUERIDO: { texto: "Abre ApuntIA desde el servidor (por ejemplo http://localhost:8000/inicio) para usar tu cuenta.", acciones: [] },

        // ===== API v2 (docs/api-v2.md §6), agrupados por etapa =====
        // --- cuenta y sesión
        NO_AUTENTICADO: { texto: "Tu sesión no es válida o caducó. Inicia sesión de nuevo.", acciones: [] },
        CREDENCIALES_INVALIDAS: { texto: "Email o contraseña incorrectos.", acciones: [] },
        EMAIL_EN_USO: { texto: "No se pudo crear la cuenta con ese email. Si ya tienes cuenta, inicia sesión o recupera tu contraseña.", acciones: [] },
        TOKEN_INVALIDO: { texto: "El enlace no es válido o ya caducó. Solicita uno nuevo.", acciones: [] },
        CSRF_INVALIDO: { texto: "La página caducó. Recárgala e inténtalo de nuevo.", acciones: ["recargar"] },
        ORIGEN_NO_PERMITIDO: { texto: "La petición se rechazó porque no venía de ApuntIA. Recarga la página.", acciones: ["recargar"] },
        DEMASIADOS_INTENTOS: { texto: "Demasiados intentos fallidos. Espera 15 minutos o recupera tu contraseña.", acciones: [] },
        DEMASIADAS_PETICIONES: { texto: "Has hecho demasiadas peticiones seguidas. Espera un poco e inténtalo de nuevo.", acciones: [], tipo: "aviso" },
        // --- apuntes y fotos
        PAGINAS_INVALIDAS: { texto: "Alguna foto no es válida. Revisa las marcadas y vuelve a intentarlo.", acciones: [] },
        DEMASIADAS_PAGINAS: { texto: "Has añadido más fotos de las permitidas en un apunte.", acciones: [] },
        NO_ENCONTRADO: { texto: "No encontramos lo que buscas: no existe o no es tuyo.", acciones: [] },
        APUNTE_EN_PROCESO: { texto: "El apunte se está analizando. Espera a que termine.", acciones: [], tipo: "aviso" },
        CONFLICTO_VERSION: { texto: "El apunte cambió en otra pestaña o dispositivo mientras editabas.", acciones: [] },
        VERSION_REQUERIDA: { texto: "Falta la versión del apunte. Recarga la página.", acciones: ["recargar"] },
        DOCUMENTO_INVALIDO: { texto: "El apunte no se pudo guardar porque algún bloque no es válido. La versión anterior sigue intacta.", acciones: [] },
        CUOTA_EXCEDIDA: { texto: "Tu espacio está lleno. Borra apuntes antiguos para subir más.", acciones: [] },
        ALMACENAMIENTO_LLENO: { texto: "El servidor no tiene espacio para guardar más archivos. Avisa al administrador.", acciones: [] },
        // --- trabajos: análisis, investigación y PDF
        DEMASIADOS_TRABAJOS: { texto: "Ya tienes varios procesos en curso. Espera a que terminen.", acciones: [], tipo: "aviso" },
        TRABAJO_NO_REINTENTABLE: { texto: "Ese proceso no se puede reintentar porque no falló.", acciones: [], tipo: "info" },
        PARCIAL: { texto: "Una parte no se pudo completar; el resto está listo.", acciones: [], tipo: "aviso" },
        OCR_NO_DISPONIBLE: { texto: "El reconocimiento de texto no está disponible en el servidor. Mientras tanto puedes usar «Mejorar una foto».", acciones: [] },
        OCR_IDIOMA_NO_DISPONIBLE: { texto: "Falta en el servidor el idioma elegido para leer el texto. Cambia el idioma en tu perfil.", acciones: [] },
        OCR_TIEMPO_AGOTADO: { texto: "Leer el texto de una página tardó demasiado. Prueba con una foto más nítida o más pequeña.", acciones: [] },
        OCR_FALLO: { texto: "No se pudo leer el texto de una página.", acciones: [] },
        ANALISIS_FALLIDO: { texto: "No se pudo analizar ninguna página. Prueba con fotos más nítidas.", acciones: [] },
        // --- fórmulas
        LATEX_INVALIDO: { texto: "La fórmula no se puede dibujar: revisa su sintaxis.", acciones: [] },
        LATEX_NO_PERMITIDO: { texto: "La fórmula usa un comando que no está permitido.", acciones: [] },
        // --- investigación (opcional)
        CONSENTIMIENTO_REQUERIDO: { texto: "Para buscar información externa necesitas permitirlo en tu perfil y confirmar la búsqueda.", acciones: [], tipo: "aviso" },
        INVESTIGACION_NO_DISPONIBLE: { texto: "La búsqueda externa no está disponible ahora. Puedes continuar sin información complementaria.", acciones: [], tipo: "aviso" },
        // --- PDF
        APUNTE_VACIO: { texto: "El apunte no tiene contenido para exportar. Revisa el análisis o edítalo.", acciones: [] },
        PDF_MAQUETACION: { texto: "Un elemento del apunte no cabe en la página del PDF; revisa tablas o imágenes muy grandes.", acciones: [] },
        PDF_FALLO: { texto: "No se pudo generar el PDF. Vuelve a intentarlo.", acciones: [] },
        PDF_NO_LISTO: { texto: "El PDF todavía no está listo.", acciones: [], tipo: "info" },
        METODO_NO_PERMITIDO: { texto: "La dirección del servidor no es la correcta. Revisa la configuración de la API.", acciones: ["reintentar"] },
    };

    const GENERICO = { texto: "Algo salió mal. Vuelve a intentarlo.", acciones: ["reintentar"] };

    // Tipo del aviso para un código (error si no se indica otro).
    const tipoDe = (codigo) => (CATALOGO[codigo] && CATALOGO[codigo].tipo) || "error";

    /**
     * @param {string} codigo
     * @param {{status?: number, errorId?: string}} [error]
     * @returns {{tipo: string, texto: string, acciones: string[], detalle: string|null}}
     */
    function paraUsuario(codigo, error = {}) {
        const entrada = CATALOGO[codigo] || (error.status >= 500 ? CATALOGO.ERROR_INTERNO : GENERICO);
        const texto = typeof entrada.texto === "function" ? entrada.texto() : entrada.texto;
        const partes = [codigo && `Código: ${codigo}`, error.status && `HTTP ${error.status}`, error.errorId && `Referencia: ${error.errorId}`].filter(Boolean);
        return { tipo: entrada.tipo || "error", texto, acciones: entrada.acciones, detalle: partes.length ? partes.join(" · ") : null };
    }

    NS.mensajes = { paraUsuario, tipoDe, CATALOGO, GENERICO };
})(window);
