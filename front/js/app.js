// Controlador de la pantalla principal de ApuntIA: selección de imagen, vista
// previa y presentación del resultado. La comunicación con FastAPI está en
// api.js (FRONT-05); este archivo no conoce URLs ni el formato de la petición.
(function () {
    "use strict";

    const { api, validacion, camara } = window.ApuntIA;
    const $ = (id) => document.getElementById(id);

    const el = {
        btEnviar: $("btEnviar"),
        inpImagen: $("inpImagen"),
        inpCamara: $("inpCamara"),
        btCamara: $("btCamara"),
        btCamaraArchivo: $("btCamaraArchivo"),
        hero: $("inicio"),
        imgPreview: $("imagenEnviada"),
        infoPreview: $("infoPreview"),
        accionesPreview: $("accionesPreview"),
        btCambiar: $("btCambiar"),
        btQuitar: $("btQuitar"),
        imgResult: $("imagenResultado"),
        infoResultado: $("infoResultado"),
        accionesResultado: $("accionesResultado"),
        btComparar: $("btComparar"),
        btDescargar: $("btDescargar"),
        btVerCompleta: $("btVerCompleta"),
        selloComparar: $("selloComparar"),
        estado: $("estado"),
        resultados: $("resultados"),
    };

    // Estado único de la pantalla.
    const estado = {
        archivo: null,      // File listo para enviar (FRONT-02)
        origen: null,       // "archivo" | "camara" | "arrastre"
        enviando: false,    // evita envíos duplicados
        urlPreview: null,   // URL temporal de la vista previa (FRONT-04)
        urlResultado: null, // URL temporal del resultado (FRONT-06)
    };

    const MENSAJES_VALIDACION = {
        ARCHIVO_AUSENTE: "No se recibió ningún archivo. Elige una imagen.",
        ARCHIVO_VACIO: "El archivo está vacío. Elige otra imagen.",
        ARCHIVO_DEMASIADO_GRANDE: `La imagen pesa más de ${window.ApuntIA.config.maxMb} MB. Elige una más ligera.`,
        TIPO_NO_PERMITIDO: "Formato no admitido. Usa una imagen JPEG, PNG o WEBP.",
    };

    // acciones: [{texto, alHacer}] botones opcionales bajo el mensaje.
    function mostrarEstado(tipo, mensaje, acciones = []) {
        el.estado.dataset.estado = tipo;
        el.estado.textContent = mensaje;
        if (acciones.length) {
            const caja = document.createElement("div");
            caja.className = "status__acciones";
            for (const { texto, alHacer } of acciones) {
                const b = document.createElement("button");
                b.type = "button";
                b.className = "btn sm";
                b.textContent = texto;
                b.addEventListener("click", alHacer);
                caja.appendChild(b);
            }
            el.estado.appendChild(caja);
        }
    }

    function actualizarControles() {
        el.btEnviar.disabled = !estado.archivo || estado.enviando;
        el.btCambiar.disabled = el.btQuitar.disabled = el.btCamara.disabled = estado.enviando;
    }

    // ---------------------------------------------------------------- vista previa (FRONT-04)

    function liberarPreview() {
        if (estado.urlPreview) URL.revokeObjectURL(estado.urlPreview);
        estado.urlPreview = null;
    }

    function mostrarPreview(archivo) {
        liberarPreview();
        estado.urlPreview = URL.createObjectURL(archivo);
        el.imgPreview.onload = () => {
            const { naturalWidth: w, naturalHeight: h } = el.imgPreview;
            const orientacion = w > h ? "horizontal" : w < h ? "vertical" : "cuadrada";
            el.infoPreview.textContent =
                `${archivo.name} · ${validacion.formatearTamano(archivo.size)} · ${w}×${h} px (${orientacion})`;
            el.infoPreview.hidden = false;
        };
        el.imgPreview.onerror = () => {
            el.infoPreview.textContent = `${archivo.name} · ${validacion.formatearTamano(archivo.size)} · el navegador no puede mostrar la vista previa`;
            el.infoPreview.hidden = false;
        };
        el.imgPreview.src = estado.urlPreview;
        el.imgPreview.hidden = false;
        el.accionesPreview.hidden = false;
    }

    function quitarImagen() {
        if (estado.enviando) return;
        liberarPreview();
        estado.archivo = null;
        estado.origen = null;
        el.imgPreview.hidden = true;
        el.imgPreview.removeAttribute("src");
        el.infoPreview.hidden = true;
        el.accionesPreview.hidden = true;
        limpiarResultado();
        actualizarControles();
        mostrarEstado("vacio", "Imagen quitada. Usa «Cargar imagen» o «Tomar foto» para elegir otra.");
        el.inpImagen.focus();
    }

    el.btQuitar.addEventListener("click", quitarImagen);
    el.btCambiar.addEventListener("click", () => el.inpImagen.click());

    // ---------------------------------------------------------------- resultado (FRONT-06)

    const TEXTO_PERSPECTIVA = {
        corregida: "✓ Pizarrón detectado y enderezado",
        no_detectada: "Pizarrón no detectado: se mejoró la imagen sin enderezarla",
        desactivada: "Corrección de perspectiva desactivada",
    };

    function limpiarResultado() {
        if (estado.urlResultado) URL.revokeObjectURL(estado.urlResultado);
        estado.urlResultado = null;
        dejarDeComparar();
        el.imgResult.hidden = true;
        el.imgResult.removeAttribute("src");
        el.infoResultado.hidden = true;
        el.accionesResultado.hidden = true;
    }

    // Carga el blob en el panel y resuelve cuando el navegador lo ha decodificado.
    function mostrarResultado(resultado) {
        return new Promise((resolve, reject) => {
            limpiarResultado();
            estado.urlResultado = URL.createObjectURL(resultado.blob);
            el.imgResult.onload = () => {
                el.imgResult.onload = el.imgResult.onerror = null; // comparar cambia el src después
                const partes = [];
                if (resultado.perspectiva && TEXTO_PERSPECTIVA[resultado.perspectiva]) {
                    const clase = resultado.perspectiva === "corregida" ? ' class="ok"' : "";
                    partes.push(`<span${clase}>${TEXTO_PERSPECTIVA[resultado.perspectiva]}</span>`);
                }
                partes.push(`${el.imgResult.naturalWidth}×${el.imgResult.naturalHeight} px`);
                partes.push(validacion.formatearTamano(resultado.blob.size));
                if (resultado.tiempoMs !== null) partes.push(`procesada en ${(resultado.tiempoMs / 1000).toFixed(1)} s`);
                el.infoResultado.innerHTML = partes.join(" · ");
                el.infoResultado.hidden = false;
                el.btDescargar.href = el.btVerCompleta.href = estado.urlResultado;
                el.btDescargar.download = resultado.nombreDescarga;
                el.accionesResultado.hidden = false;
                resolve();
            };
            el.imgResult.onerror = () => {
                el.imgResult.onload = el.imgResult.onerror = null;
                limpiarResultado();
                reject(new api.ApiError({ tipo: "respuesta", codigo: "RESPUESTA_INVALIDA" }));
            };
            el.imgResult.src = estado.urlResultado;
            el.imgResult.hidden = false;
        });
    }

    // Comparar: mientras se mantiene pulsado (o al activarlo con teclado) el
    // panel de resultado muestra la original, para alternar en el mismo sitio.
    function comparar() {
        if (!estado.urlResultado || !estado.urlPreview) return;
        el.imgResult.src = estado.urlPreview;
        el.selloComparar.hidden = false;
        el.btComparar.setAttribute("aria-pressed", "true");
    }
    function dejarDeComparar() {
        if (el.btComparar.getAttribute("aria-pressed") !== "true") return;
        el.btComparar.setAttribute("aria-pressed", "false");
        el.selloComparar.hidden = true;
        if (estado.urlResultado) el.imgResult.src = estado.urlResultado;
    }
    el.btComparar.addEventListener("pointerdown", (e) => { e.preventDefault(); comparar(); });
    ["pointerup", "pointerleave", "pointercancel", "blur"].forEach((ev) => el.btComparar.addEventListener(ev, dejarDeComparar));
    el.btComparar.addEventListener("keydown", (e) => { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); comparar(); } });
    el.btComparar.addEventListener("keyup", (e) => { if (e.key === " " || e.key === "Enter") dejarDeComparar(); });

    // ---------------------------------------------------------------- selección (FRONT-02)

    async function seleccionarArchivo(archivo, origen) {
        if (estado.enviando) return; // no se cambia la imagen mientras se procesa

        const resultado = await validacion.validarArchivo(archivo);
        if (!resultado.ok) {
            const mantiene = estado.archivo ? ` Se mantiene «${estado.archivo.name}».` : "";
            mostrarEstado("error", MENSAJES_VALIDACION[resultado.codigo] + mantiene);
            return;
        }

        estado.archivo = archivo;
        estado.origen = origen;

        mostrarPreview(archivo);
        limpiarResultado();
        actualizarControles();
        mostrarEstado("listo", `Imagen lista: ${archivo.name} (${validacion.formatearTamano(archivo.size)}). Pulsa «Procesar imagen».`);
        el.resultados.scrollIntoView({ block: "start" });
    }

    function alCancelarSelector() {
        if (estado.enviando) return;
        if (estado.archivo) {
            mostrarEstado("listo", `No elegiste otra imagen. Se mantiene «${estado.archivo.name}».`);
        } else {
            mostrarEstado("vacio", "No elegiste ninguna imagen. Usa «Cargar imagen» o «Tomar foto» para comenzar.");
        }
    }

    [[el.inpImagen, "archivo"], [el.inpCamara, "camara"]].forEach(([input, origen]) => {
        input.addEventListener("change", () => {
            const archivo = input.files && input.files[0];
            input.value = ""; // permite volver a elegir el mismo archivo
            if (archivo) seleccionarArchivo(archivo, origen);
            else alCancelarSelector(); // navegadores sin evento "cancel"
        });
        input.addEventListener("cancel", alCancelarSelector);
    });

    // Arrastrar y soltar sobre el pizarrón (escritorio).
    let profundidadArrastre = 0;
    el.hero.addEventListener("dragenter", (e) => {
        if (!e.dataTransfer || ![...e.dataTransfer.types].includes("Files")) return;
        e.preventDefault();
        profundidadArrastre++;
        el.hero.classList.add("dropping");
    });
    el.hero.addEventListener("dragover", (e) => {
        if (e.dataTransfer && [...e.dataTransfer.types].includes("Files")) e.preventDefault();
    });
    el.hero.addEventListener("dragleave", () => {
        if (--profundidadArrastre <= 0) { profundidadArrastre = 0; el.hero.classList.remove("dropping"); }
    });
    el.hero.addEventListener("drop", (e) => {
        e.preventDefault();
        profundidadArrastre = 0;
        el.hero.classList.remove("dropping");
        const archivos = e.dataTransfer ? [...e.dataTransfer.files] : [];
        if (archivos.length > 1) mostrarEstado("error", "Suelta una sola imagen.");
        else seleccionarArchivo(archivos[0], "arrastre");
    });

    // ---------------------------------------------------------------- cámara (FRONT-03)

    const MENSAJES_CAMARA = {
        CAMARA_PERMISO_DENEGADO: "No se dio permiso para usar la cámara. Puedes permitirlo en la configuración del navegador (icono junto a la dirección) o usar una alternativa:",
        CAMARA_NO_DISPONIBLE: "No se encontró ninguna cámara en este dispositivo. Usa una alternativa:",
        CAMARA_OCUPADA: "La cámara está siendo usada por otra aplicación. Ciérrala e inténtalo de nuevo, o usa una alternativa:",
        CAMARA_ERROR: "No se pudo iniciar la cámara. Usa una alternativa:",
    };

    const alternativasCamara = [
        { texto: "Usar la app de cámara", alHacer: () => el.inpCamara.click() },
        { texto: "Cargar imagen", alHacer: () => el.inpImagen.click() },
    ];

    const visor = camara.crearVisor({
        dialogo: $("dlgCamara"),
        video: $("camVideo"),
        mensaje: $("camMensaje"),
        btCapturar: $("btCapturar"),
        btCerrar: $("btCerrarCamara"),
        flash: $("camFlash"),
    });

    el.btCamara.addEventListener("click", () => {
        if (estado.enviando) return;
        if (!camara.disponible()) {
            // http en la red local o navegador sin getUserMedia: app de cámara nativa.
            el.inpCamara.click();
            return;
        }
        visor.abrir({
            onFoto: (archivo) => seleccionarArchivo(archivo, "camara"),
            onError: (codigo) => mostrarEstado("error", MENSAJES_CAMARA[codigo], alternativasCamara),
        });
    });

    el.btCamaraArchivo.addEventListener("click", () => {
        visor.cerrar();
        el.inpImagen.click();
    });

    // ---------------------------------------------------------------- envío

    async function enviarImagen() {
        if (!estado.archivo || estado.enviando) return;
        estado.enviando = true;
        actualizarControles();
        el.resultados.setAttribute("aria-busy", "true");
        mostrarEstado("cargando", "Procesando imagen...");

        try {
            const resultado = await api.procesarImagen(estado.archivo);
            await mostrarResultado(resultado);
            mostrarEstado("hecho", "Listo. Compara la imagen original con la procesada o descárgala.");
        } catch (error) {
            console.error(error);
            const texto = error.tipo === "red"
                ? `No se pudo conectar con el servidor (${api.urlBase()}). Verifica que esté activo e inténtalo de nuevo.`
                : error.mensaje || "No se pudo procesar la imagen. Inténtalo de nuevo.";
            mostrarEstado("error", texto);
        } finally {
            estado.enviando = false;
            el.resultados.removeAttribute("aria-busy");
            actualizarControles();
        }
    }

    el.btEnviar.addEventListener("click", enviarImagen);

    // ---------------------------------------------------------------- navegación

    const enlaces = [...document.querySelectorAll(".site-nav a")];
    const secciones = enlaces.map((a) => document.querySelector(a.getAttribute("href")));
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entradas) => {
            entradas.forEach((entrada) => {
                if (!entrada.isIntersecting) return;
                enlaces.forEach((a) => {
                    if (a.getAttribute("href") === `#${entrada.target.id}`) a.setAttribute("aria-current", "page");
                    else a.removeAttribute("aria-current");
                });
            });
        }, { rootMargin: "-40% 0px -55% 0px" });
        secciones.forEach((s) => s && observer.observe(s));
    }

    // Acceso para pruebas automáticas (FRONT-10).
    window.ApuntIA.app = { estado, seleccionarArchivo };
})();
