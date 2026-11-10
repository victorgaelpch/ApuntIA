// Crear un apunte con varias fotos (FRONT-12).
//
// - Las fotos solo viven en memoria (objetos File y URLs blob: de las miniaturas,
//   que se liberan al quitarlas): no se guardan en el almacenamiento del navegador.
// - Se validan con las mismas reglas que el backend (validacion.js + límites de
//   GET /salud) y el backend vuelve a validar. Una foto inválida no se envía
//   en silencio: se marca y no deja crear el apunte hasta quitarla.
// - Envío con el contrato v2: campos «paginas» (en orden), «tipos» y «titulo»,
//   con Idempotency-Key para que un reintento no cree dos apuntes.
(function () {
    "use strict";
    const NS = window.ApuntIA;
    const { h, $, vaciar, requerirSesion, cabecera, avisar, avisarError, textoDeError, sesion } = NS.v2;
    const { validarArchivo, formatearTamano } = NS.validacion;
    const aviso = $("#avisoNuevo");
    const lista = $("#listaPaginas");

    const estado = { paginas: [], maxPaginas: 20, enviando: null, clave: null, siguienteId: 1 };
    const NOMBRES = { pizarron: "Pizarrón", cuaderno: "Cuaderno" };

    // ---------------------------------------------------------------- análisis local
    // Sugerencia de tipo: un pizarrón suele ser oscuro (verde o negro) y una hoja, clara.
    function analizarImagen(url) {
        return new Promise((resolver) => {
            const img = new Image();
            img.onload = () => {
                const lienzo = document.createElement("canvas");
                const escala = 64 / Math.max(img.naturalWidth, img.naturalHeight);
                lienzo.width = Math.max(1, Math.round(img.naturalWidth * escala));
                lienzo.height = Math.max(1, Math.round(img.naturalHeight * escala));
                const ctx = lienzo.getContext("2d");
                ctx.drawImage(img, 0, 0, lienzo.width, lienzo.height);
                const d = ctx.getImageData(0, 0, lienzo.width, lienzo.height).data;
                let suma = 0;
                for (let i = 0; i < d.length; i += 4) suma += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
                const brillo = suma / (d.length / 4);
                resolver({ ancho: img.naturalWidth, alto: img.naturalHeight, brillo });
            };
            img.onerror = () => resolver(null);
            img.src = url;
        });
    }

    async function huella(archivo) {
        if (!(window.crypto && crypto.subtle)) return `${archivo.name}|${archivo.size}|${archivo.lastModified}`;
        const digest = await crypto.subtle.digest("SHA-256", await archivo.arrayBuffer());
        return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
    }

    // ---------------------------------------------------------------- añadir
    async function anadir(archivos) {
        if (estado.enviando) return;
        const preferido = $("#selFuente").value;
        let rechazadas = 0, repetidas = 0;
        for (const archivo of archivos) {
            if (estado.paginas.length >= estado.maxPaginas) {
                avisar(aviso, "aviso", `Un apunte admite hasta ${estado.maxPaginas} fotos. Las demás no se añadieron.`);
                break;
            }
            const id = `pag${estado.siguienteId++}`;
            const validacion = await validarArchivo(archivo);
            const marca = await huella(archivo);
            if (estado.paginas.some((p) => p.huella === marca)) { repetidas++; continue; }
            const pagina = { id, archivo, huella: marca, url: URL.createObjectURL(archivo), tipo: preferido,
                             sugerido: null, error: null, avisos: [] };
            if (!validacion.ok) {
                pagina.error = textoDeError({ codigo: validacion.codigo });
                rechazadas++;
            } else {
                const info = await analizarImagen(pagina.url);
                if (!info) {
                    pagina.error = textoDeError({ codigo: "IMAGEN_CORRUPTA" });
                    rechazadas++;
                } else {
                    pagina.sugerido = info.brillo < 110 ? "pizarron" : "cuaderno";
                    if (Math.min(info.ancho, info.alto) < 700) pagina.avisos.push("Resolución baja: puede que el texto no se lea bien.");
                    if (info.brillo < 45) pagina.avisos.push("Foto muy oscura: si puedes, repítela con más luz.");
                    const mp = (info.ancho * info.alto) / 1e6;
                    if (mp > (NS.config.maxMegapixeles || 50)) { pagina.error = textoDeError({ codigo: "IMAGEN_DEMASIADO_GRANDE" }); rechazadas++; }
                }
            }
            estado.paginas.push(pagina);
        }
        if (repetidas) avisar(aviso, "aviso", repetidas === 1 ? "Esa foto ya estaba en la lista: no se añadió dos veces."
                                                            : `${repetidas} fotos ya estaban en la lista y no se repitieron.`);
        else if (rechazadas) avisar(aviso, "error", "Alguna foto no se puede usar. Quítala o cámbiala para continuar.");
        cambio();
    }

    // ---------------------------------------------------------------- lista
    function tipoFinal(p) { return p.tipo === "auto" ? (p.sugerido || "cuaderno") : p.tipo; }

    function mover(indice, destino) {
        if (destino < 0 || destino >= estado.paginas.length) return;
        const [p] = estado.paginas.splice(indice, 1);
        estado.paginas.splice(destino, 0, p);
        cambio(p.id);
    }

    function quitar(indice) {
        const [p] = estado.paginas.splice(indice, 1);
        URL.revokeObjectURL(p.url);
        cambio(estado.paginas[Math.min(indice, estado.paginas.length - 1)]?.id);
        if (!estado.paginas.some((x) => x.error)) avisar(aviso, "info", "");
    }

    let arrastrada = null;
    function pintar(enfocar) {
        vaciar(lista);
        const n = estado.paginas.length;
        estado.paginas.forEach((p, i) => {
            const etiqueta = `Página ${i + 1}`;
            const selector = h("select", { id: `tipo-${p.id}`, "aria-label": `Tipo de fuente de la ${etiqueta.toLowerCase()}`,
                                           onchange: (e) => { p.tipo = e.target.value; cambio(); },
                                           disabled: Boolean(estado.enviando) },
                h("option", { value: "auto", selected: p.tipo === "auto",
                              text: `Automático${p.sugerido ? `: ${NOMBRES[p.sugerido].toLowerCase()}` : ""}` }),
                h("option", { value: "pizarron", selected: p.tipo === "pizarron", text: "Pizarrón" }),
                h("option", { value: "cuaderno", selected: p.tipo === "cuaderno", text: "Cuaderno" }));
            const ocupado = Boolean(estado.enviando);
            const li = h("li", { class: "pagina", draggable: ocupado ? "false" : "true", dataset: { id: p.id },
                                 "data-error": p.error ? "" : null, "aria-label": etiqueta },
                h("span", { class: "pagina__num", "aria-hidden": "true", text: String(i + 1) }),
                h("img", { src: p.url, alt: `Vista previa de la ${etiqueta.toLowerCase()} (${p.archivo.name})` }),
                h("span", { class: "pagina__nombre", text: `${p.archivo.name} · ${formatearTamano(p.archivo.size)}` }),
                p.error ? h("span", { class: "pagina__error", id: `error-${p.id}`, text: p.error }) : null,
                p.avisos.map((a) => h("span", { class: "pagina__aviso", text: a })),
                selector,
                h("span", { class: "pagina__acciones" },
                    h("button", { type: "button", class: "btn sm", disabled: i === 0 || ocupado, "aria-label": `Subir la ${etiqueta.toLowerCase()}`,
                                  dataset: { accion: "subir" }, onclick: () => mover(i, i - 1), text: "↑" }),
                    h("button", { type: "button", class: "btn sm", disabled: i === n - 1 || ocupado, "aria-label": `Bajar la ${etiqueta.toLowerCase()}`,
                                  dataset: { accion: "bajar" }, onclick: () => mover(i, i + 1), text: "↓" }),
                    h("button", { type: "button", class: "btn sm", disabled: ocupado, "aria-label": `Quitar la ${etiqueta.toLowerCase()}`,
                                  dataset: { accion: "quitar" }, onclick: () => quitar(i), text: "Quitar" })));
            li.addEventListener("dragstart", () => { arrastrada = i; li.classList.add("arrastrando"); });
            li.addEventListener("dragend", () => { arrastrada = null; li.classList.remove("arrastrando"); });
            li.addEventListener("dragover", (e) => { if (arrastrada !== null) { e.preventDefault(); li.classList.add("destino"); } });
            li.addEventListener("dragleave", () => li.classList.remove("destino"));
            li.addEventListener("drop", (e) => { e.preventDefault(); e.stopPropagation(); if (arrastrada !== null) mover(arrastrada, i); });
            lista.append(li);
        });
        const errores = estado.paginas.filter((p) => p.error).length;
        $("#contadorPaginas").textContent = n === 0 ? "Aún no hay fotos."
            : `${n} ${n === 1 ? "foto" : "fotos"} de ${estado.maxPaginas} como máximo${errores ? ` · ${errores} con problemas` : ""}.`;
        $("#btCrear").disabled = n === 0 || errores > 0 || Boolean(estado.enviando);
        if (enfocar) {
            const destino = lista.querySelector(`[data-id="${enfocar}"] .pagina__acciones button:not([disabled])`);
            if (destino) destino.focus();
        }
    }

    // La selección cambió: un envío nuevo es otro apunte (otra Idempotency-Key).
    function cambio(enfocar) { estado.clave = null; pintar(enfocar); }

    // ---------------------------------------------------------------- envío
    function progreso(texto, porcentaje) {
        $("#cajaSubida").hidden = false;
        $("#textoSubida").textContent = texto;
        const barra = $("#barraSubida");
        barra.setAttribute("aria-valuenow", String(porcentaje));
        barra.firstElementChild.style.width = `${porcentaje}%`;
    }

    function enviar() {
        if (!estado.paginas.length || estado.paginas.some((p) => p.error) || estado.enviando) return;
        estado.clave = estado.clave || (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
        const datos = new FormData();
        for (const p of estado.paginas) datos.append("paginas", p.archivo, p.archivo.name);
        for (const p of estado.paginas) datos.append("tipos", tipoFinal(p));
        datos.append("titulo", $("#inpTitulo").value.trim());

        const clave = estado.clave;
        const xhr = new XMLHttpRequest();
        estado.enviando = xhr;
        pintar();
        $("#btCancelarSubida").hidden = false;
        avisar(aviso, "info", "");
        progreso("Enviando fotos… 0 %", 0);
        xhr.open("POST", "/api/v2/apuntes");
        xhr.setRequestHeader("X-CSRF-Token", sesion.csrf);
        xhr.setRequestHeader("Idempotency-Key", clave);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.timeout = 180000;
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                progreso(`Enviando fotos… ${pct} %`, pct);
            }
        };
        const terminar = () => { estado.enviando = null; $("#btCancelarSubida").hidden = true; pintar(); };
        xhr.onload = () => {
            let cuerpo = {};
            try { cuerpo = JSON.parse(xhr.responseText || "{}"); } catch (_) { /* respuesta no JSON */ }
            if (xhr.status === 202 || xhr.status === 200) {
                progreso("Fotos recibidas. Abriendo el apunte…", 100);
                estado.paginas.forEach((p) => URL.revokeObjectURL(p.url));
                estado.paginas = [];
                window.removeEventListener("beforeunload", alSalir);
                location.assign(`/front/editor.html?id=${encodeURIComponent(cuerpo.apunte.id)}`);
                return;
            }
            terminar();
            $("#cajaSubida").hidden = true;
            const error = { ...(cuerpo.error || {}), status: xhr.status };
            error.codigo = error.codigo || (xhr.status >= 500 ? "ERROR_INTERNO" : "ERROR_CLIENTE");
            if (xhr.status === 401) { NS.v2.irACuenta("expirada"); return; }
            if (Array.isArray(error.detalles)) {
                for (const d of error.detalles) {
                    const p = estado.paginas[d.pagina - 1];
                    if (p) p.error = d.mensaje.charAt(0).toUpperCase() + d.mensaje.slice(1);
                }
                pintar();
                avisar(aviso, "error", "El servidor rechazó alguna foto. Quítala o cámbiala y vuelve a intentarlo.");
            } else {
                avisarError(aviso, error, error.status >= 500 || error.codigo === "DEMASIADOS_TRABAJOS" ? [{ texto: "Reintentar", alHacer: enviar }] : []);
            }
        };
        xhr.onerror = () => { terminar(); $("#cajaSubida").hidden = true; avisarError(aviso, { codigo: "SIN_CONEXION" }, [{ texto: "Reintentar", alHacer: enviar }]); };
        xhr.ontimeout = () => { terminar(); $("#cajaSubida").hidden = true; avisarError(aviso, { codigo: "TIEMPO_AGOTADO" }, [{ texto: "Reintentar", alHacer: enviar }]); };
        xhr.onabort = () => { terminar(); $("#cajaSubida").hidden = true; avisar(aviso, "info", "Envío cancelado. Tus fotos siguen aquí."); };
        xhr.send(datos);
    }

    function alSalir(e) {
        if (estado.paginas.length) { e.preventDefault(); e.returnValue = ""; }
    }

    // ---------------------------------------------------------------- inicio
    // Las fotos elegidas MIENTRAS la página aún se prepara (sesión, límites de /salud) no se pierden:
    // el evento se escucha desde el principio y se procesan cuando todo está listo.
    let marcarListo;
    const listo = new Promise((r) => { marcarListo = r; });
    const alElegir = (e) => { const archivos = [...e.target.files]; e.target.value = ""; listo.then(() => anadir(archivos)); };

    async function iniciar() {
        $("#inpFotos").addEventListener("change", alElegir);
        $("#inpCamaraNuevo").addEventListener("change", alElegir);
        const usuario = await requerirSesion();
        cabecera("nuevo");
        const preferido = (usuario.preferencias || {}).tipo_fuente;
        if (["auto", "pizarron", "cuaderno"].includes(preferido)) $("#selFuente").value = preferido;
        try {
            const s = await (await fetch("/salud", { cache: "no-store" })).json();
            NS.config.maxMb = s.max_mb;
            NS.config.formatos = s.formatos;
            NS.config.maxMegapixeles = s.max_megapixeles;
            estado.maxPaginas = s.max_paginas || 20;
            $("#limitesFotos").textContent = `JPEG, PNG o WEBP · hasta ${s.max_mb} MB y ${s.max_megapixeles} megapíxeles por foto · hasta ${estado.maxPaginas} fotos. También puedes arrastrarlas aquí.`;
            if (s.ocr && !s.ocr.disponible) {
                avisar(aviso, "error", "El reconocimiento de texto no está disponible en este servidor: el apunte no se podrá analizar. Puedes usar «Mejorar una foto» mientras tanto.");
            }
        } catch (_) { /* se usan los límites por defecto; el backend valida igualmente */ }

        const visor = NS.camara.crearVisor({ dialogo: $("#dlgCamara"), video: $("#camVideo"), mensaje: $("#camMensaje"),
                                            btCapturar: $("#btCapturar"), btCerrar: $("#btCerrarCamara"), flash: $("#camFlash") });
        $("#btCamaraNuevo").addEventListener("click", () => {
            if (!NS.camara.disponible()) { $("#inpCamaraNuevo").click(); return; }
            visor.abrir({ onFoto: (archivo) => anadir([archivo]),
                          onError: (codigo) => avisarError(aviso, { codigo }, [{ texto: "Usar la app de cámara", alHacer: () => $("#inpCamaraNuevo").click() }]) });
        });
        $("#btCrear").addEventListener("click", enviar);
        $("#btCancelarSubida").addEventListener("click", () => estado.enviando && estado.enviando.abort());
        const zona = $("#main");
        zona.addEventListener("dragover", (e) => { if (e.dataTransfer && [...e.dataTransfer.types].includes("Files")) { e.preventDefault(); zona.classList.add("zona-soltar"); } });
        zona.addEventListener("dragleave", (e) => { if (e.target === zona) zona.classList.remove("zona-soltar"); });
        zona.addEventListener("drop", (e) => {
            zona.classList.remove("zona-soltar");
            if (e.dataTransfer && e.dataTransfer.files.length) { e.preventDefault(); anadir([...e.dataTransfer.files]); }
        });
        window.addEventListener("beforeunload", alSalir);
        window.addEventListener("pagehide", () => estado.paginas.forEach((p) => URL.revokeObjectURL(p.url)));
        pintar();
        marcarListo();
    }
    iniciar();
})();
