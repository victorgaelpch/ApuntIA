// Editor de un apunte (FRONT-13). Núcleo que amplían:
//   editor-contenido.js (FRONT-14: fórmulas, tablas y esquemas),
//   editor-versiones.js (FRONT-22), editor-investigacion.js (FRONT-15) y
//   editor-pdf.js (FRONT-16), registrando pestañas y tipos de bloque.
//
// Reglas:
// - El documento se edita en memoria y solo se da por guardado cuando el servidor
//   responde (PUT con If-Match = versión editada). Si otra pestaña guardó antes, el
//   409 se muestra y se ofrece qué hacer: nunca se pisa en silencio.
// - Todo el texto (OCR, correcciones, nombres) se pinta con textContent/value.
// - Las reglas de procedencia las aplica el backend: aquí solo se cambian texto,
//   tipo, orden y bloques nuevos (origen «usuario»).
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, $, vaciar, pedir, avisar, avisarError, chipEstado, textoTrabajo, esperarTrabajo } = NS.v2;

    const E = {
        id: null, apunte: null, doc: null, version: 0, guardado: "", guardando: null, pendienteGuardar: false,
        pagina: null, seleccionado: null, verOriginal: false, sesionCaducada: false,
        pestanas: [], renderizadores: {}, alCargar: [], alGuardar: [], acciones: [],
    };
    const aviso = () => $("#avisoEditor");

    // ---------------------------------------------------------------- extensiones
    function registrarPestana(p) { E.pestanas.push(p); E.pestanas.sort((a, b) => a.orden - b.orden); }
    function registrarTipo(tipo, fn) { E.renderizadores[tipo] = fn; }
    function registrarAccionBloque(fn) { E.acciones.push(fn); }
    function alCargar(fn) { E.alCargar.push(fn); }
    function alGuardar(fn) { E.alGuardar.push(fn); }

    // ---------------------------------------------------------------- documento
    function nuevoId(prefijo = "u") {
        return `${prefijo}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
    }

    // Lo que se compara para saber si hay cambios (el orden se recalcula al guardar).
    function serializar(doc) {
        const copia = JSON.parse(JSON.stringify(doc));
        copia.bloques.forEach((b, i) => { b.orden = i; delete b.editado; });
        return JSON.stringify(copia);
    }

    function hayCambios() { return E.doc && serializar(E.doc) !== E.guardado; }

    function bloque(id) { return E.doc.bloques.find((b) => b.id === id); }
    function indice(id) { return E.doc.bloques.findIndex((b) => b.id === id); }
    function paginaDe(id) { return E.doc.paginas.find((p) => p.id === id); }

    function marcarCambio() {
        actualizarEstadoGuardado();
        E.alGuardar.forEach((fn) => fn({ tipo: "cambio" }));
    }

    function editado(b) {
        return b.editado || b.origen === "usuario" || (b.texto_original !== null && b.texto_original !== undefined && b.texto !== b.texto_original);
    }

    // ---------------------------------------------------------------- estado de guardado
    function actualizarEstadoGuardado(forzado) {
        const el = $("#estadoGuardado");
        const cambios = hayCambios();
        let tipo = "limpio", texto;
        if (forzado) ({ tipo, texto } = forzado);
        else if (E.guardando) { tipo = "guardando"; texto = "Guardando…"; }
        else if (E.sesionCaducada) { tipo = "error"; texto = "Sin guardar: la sesión caducó"; }
        else if (cambios) { tipo = "sucio"; texto = navigator.onLine === false ? "Sin conexión: los cambios solo están en esta pestaña" : "Cambios sin guardar"; }
        else texto = E.guardadoEn ? `Guardado · versión ${E.version} · ${E.guardadoEn}` : `Versión ${E.version}`;
        el.dataset.tipo = tipo;
        el.textContent = texto;
        $("#btGuardar").disabled = !cambios || Boolean(E.guardando) || !editable();
        document.title = `${cambios ? "• " : ""}${E.doc ? E.doc.titulo : "Editor"} — ApuntIA`;
    }

    function editable() { return E.apunte && !["pendiente", "procesando"].includes(E.apunte.estado); }

    async function guardar({ sobrescribir = false } = {}) {
        if (!E.doc || !editable()) return false;
        if (E.guardando) { E.pendienteGuardar = true; return E.guardando; }
        if (!hayCambios()) return true;
        const enviado = serializar(E.doc);
        let version = E.version;
        E.guardando = (async () => {
            actualizarEstadoGuardado();
            try {
                if (sobrescribir) version = (await pedir(`/api/v2/apuntes/${E.id}`)).apunte.version;
                const r = await pedir(`/api/v2/apuntes/${E.id}/documento`, {
                    method: "PUT", json: JSON.parse(enviado), headers: { "If-Match": String(version) } });
                E.version = r.version;
                E.apunte = r.apunte;
                E.guardado = enviado;
                E.guardadoEn = new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
                E.sesionCaducada = false;
                // El servidor marca «editado» según la procedencia: se copian sus marcas.
                const marcas = new Map(r.apunte.documento.bloques.map((b) => [b.id, b.editado]));
                E.doc.bloques.forEach((b) => { if (marcas.has(b.id)) b.editado = marcas.get(b.id); });
                avisar(aviso(), "info", "");
                E.alGuardar.forEach((fn) => fn({ tipo: "guardado", version: r.version }));
                return true;
            } catch (err) {
                tratarErrorGuardado(err);
                return false;
            } finally {
                E.guardando = null;
                actualizarEstadoGuardado();
                pintarMarcas();
                if (E.pendienteGuardar) { E.pendienteGuardar = false; if (hayCambios() && !E.sesionCaducada) guardar(); }
            }
        })();
        return E.guardando;
    }

    function textoPlano(doc) {
        return [doc.titulo, ...doc.bloques.map((b) => b.tabla ? [b.tabla.encabezados.join(" | "), ...b.tabla.filas.map((f) => f.join(" | "))].join("\n")
                                                                  : (b.latex ? `$${b.latex}$` : b.texto))].filter(Boolean).join("\n\n");
    }

    async function copiarCambios() {
        const texto = textoPlano(E.doc);
        try {
            await navigator.clipboard.writeText(texto);
            avisar(aviso(), "exito", "Tus cambios se copiaron al portapapeles como texto.");
        } catch (_) {
            // Sin permiso de portapapeles: se ofrece como archivo.
            const url = URL.createObjectURL(new Blob([texto], { type: "text/plain;charset=utf-8" }));
            const a = h("a", { href: url, download: "mis-cambios.txt" });
            document.body.append(a); a.click(); a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
    }

    function tratarErrorGuardado(err) {
        if (err.codigo === "CONFLICTO_VERSION") {
            const acciones = [
                { texto: "Ver la versión guardada (descarta mis cambios)", alHacer: () => recargar() },
                { texto: "Copiar mis cambios", alHacer: copiarCambios },
                { texto: "Guardar encima", alHacer: () => guardar({ sobrescribir: true }) },
            ];
            if (E.compararConflicto) acciones.unshift({ texto: "Comparar", alHacer: E.compararConflicto });
            avisar(aviso(), "error", "Este apunte se guardó desde otra pestaña o dispositivo mientras editabas. Tus cambios siguen aquí: elige qué hacer.", acciones);
        } else if (err.status === 401) {
            E.sesionCaducada = true;
            avisar(aviso(), "error", "Tu sesión caducó y los cambios no se guardaron. Siguen en esta pestaña: inicia sesión en otra pestaña y vuelve a pulsar «Guardar».",
                   [{ texto: "Iniciar sesión en otra pestaña", alHacer: () => global.open("/front/cuenta.html", "_blank", "noopener") }]);
        } else {
            avisarError(aviso(), err, [{ texto: "Reintentar", alHacer: () => guardar() }]);
        }
    }

    // ---------------------------------------------------------------- carga
    async function cargar() {
        const r = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}`);
        E.apunte = r.apunte;
        E.doc = r.apunte.documento;
        E.version = r.apunte.version;
        E.guardado = serializar(E.doc);
        if (!E.pagina || !paginaDe(E.pagina)) E.pagina = (E.doc.paginas[0] || {}).id || null;
        return r.apunte;
    }

    async function recargar() {
        avisar(aviso(), "info", "");
        await cargar();
        pintarTodo();
    }

    // ---------------------------------------------------------------- análisis en curso
    async function seguirAnalisis(trabajo) {
        const panel = $("#panelAnalisis");
        panel.hidden = false;
        const barra = $("#barraAnalisis");
        const control = new AbortController();
        $("#btCancelarAnalisis").onclick = async () => {
            $("#btCancelarAnalisis").disabled = true;
            try { await pedir(`/api/v2/trabajos/${trabajo.id}`, { method: "DELETE" }); } catch (err) { avisarError(aviso(), err); }
        };
        try {
            const final = await esperarTrabajo(trabajo.id, { signal: control.signal, alAvanzar: (t) => {
                $("#textoAnalisis").textContent = textoTrabajo(t);
                barra.setAttribute("aria-valuenow", String(t.progreso || 0));
                barra.firstElementChild.style.width = `${t.progreso || 0}%`;
            } });
            panel.hidden = true;
            await cargar();
            pintarTodo();
            informarAnalisis(final);
        } catch (err) {
            panel.hidden = true;
            avisarError(aviso(), err, [{ texto: "Recargar", alHacer: () => location.reload() }]);
        }
    }

    function informarAnalisis(t) {
        if (!t || t.tipo !== "analisis") return;
        if (t.estado === "fallido" || t.estado === "cancelado") {
            const texto = t.estado === "cancelado" ? "Cancelaste el análisis. Puedes reanudarlo cuando quieras."
                : NS.v2.textoDeError({ codigo: t.error && t.error.codigo, mensaje: t.error && t.error.mensaje, status: 400 });
            avisar(aviso(), "error", texto, [{ texto: "Reintentar el análisis", alHacer: async () => {
                try {
                    const r = await pedir(`/api/v2/trabajos/${t.id}/reintentar`, { method: "POST" });
                    avisar(aviso(), "info", "");
                    E.apunte.estado = "pendiente";
                    pintarTodo();
                    seguirAnalisis(r.trabajo);
                } catch (err) { avisarError(aviso(), err); }
            } }]);
        } else if (t.estado === "parcial") {
            avisar(aviso(), "aviso", (t.error && t.error.mensaje) || "Alguna página no se pudo analizar.");
        } else if (t.estado === "completado" && t.resultado) {
            const r = t.resultado;
            const partes = [`Análisis terminado: ${r.bloques} bloque(s).`];
            if (r.inciertos) partes.push(`${r.inciertos} con reconocimiento incierto (márgenes naranjas): revísalos.`);
            if (r.no_reconocidos) partes.push(`${r.no_reconocidos} sin leer: escríbelos tú o consérvalos como imagen.`);
            avisar(aviso(), r.inciertos || r.no_reconocidos ? "aviso" : "exito", partes.join(" "));
        }
    }

    // ---------------------------------------------------------------- pintar
    function pintarTodo() {
        const titulo = $("#inpTituloApunte");
        titulo.value = E.doc.titulo;
        titulo.disabled = !editable();
        vaciar($("#chipEstadoApunte")).append(chipEstado(E.apunte.estado));
        const tabs = $("#pestanasEditor"), paneles = $("#panelesEditor");
        if (!tabs.childElementCount) {
            E.pestanas.forEach((p, i) => {
                const tab = h("button", { type: "button", role: "tab", id: `tab-${p.id}`, "aria-controls": `panel-${p.id}`,
                                          "aria-selected": String(i === 0), tabindex: i === 0 ? null : "-1", text: p.titulo });
                tab.addEventListener("click", () => mostrarPestana(p.id));
                tab.addEventListener("keydown", (e) => {
                    const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
                    if (!d) return;
                    const sig = E.pestanas[(i + d + E.pestanas.length) % E.pestanas.length];
                    mostrarPestana(sig.id);
                    $(`#tab-${sig.id}`).focus();
                });
                tabs.append(tab);
                const panel = h("section", { role: "tabpanel", id: `panel-${p.id}`, "aria-labelledby": `tab-${p.id}`, hidden: i !== 0 });
                paneles.append(panel);
                p.crear(panel);
            });
        }
        E.pestanas.forEach((p) => p.pintar && p.pintar($(`#panel-${p.id}`)));
        actualizarEstadoGuardado();
    }

    function mostrarPestana(id) {
        E.pestanas.forEach((p) => {
            const activa = p.id === id;
            const tab = $(`#tab-${p.id}`);
            tab.setAttribute("aria-selected", String(activa));
            tab.tabIndex = activa ? 0 : -1;
            $(`#panel-${p.id}`).hidden = !activa;
            if (activa && p.alMostrar) p.alMostrar($(`#panel-${p.id}`));
        });
    }

    // ---------------------------------------------------------------- transcripción
    const TIPOS = { titulo: "Título", texto: "Texto", manuscrito: "Manuscrito", formula: "Fórmula", tabla: "Tabla", imagen: "Imagen o esquema" };
    const ESTADO_BLOQUE = { reconocido: "Reconocido", incierto: "Incierto: revisa", no_reconocido: "Sin leer" };

    function urlArchivo(archivo) { return `/api/v2/apuntes/${encodeURIComponent(E.id)}/archivos/${encodeURIComponent(archivo)}`; }

    function crearTranscripcion(panel) {
        panel.append(h("div", { class: "transcripcion" },
            h("div", { class: "visor", id: "visor" },
                h("div", { class: "visor__paginas", id: "visorPaginas", role: "group", "aria-label": "Páginas" }),
                h("p", { class: "visor__info", id: "visorAvisos" }),
                h("div", { class: "visor__marco", id: "visorMarco" }),
                h("div", { class: "botones" },
                    h("button", { type: "button", class: "btn sm", id: "btVerOriginal", "aria-pressed": "false",
                                  onclick: () => { E.verOriginal = !E.verOriginal; pintarVisor(); }, text: "Ver la foto original" })),
                h("p", { class: "visor__info", text: "Pulsa una región de la foto para ir a su bloque. Bordes: amarillo = reconocido, naranja discontinuo = incierto, rojo punteado = sin leer." })),
            h("div", {},
                h("div", { class: "bloques", id: "listaBloques", "aria-label": "Bloques de texto de la página" }),
                h("div", { class: "botones" },
                    h("button", { type: "button", class: "btn", id: "btAnadirBloque", onclick: () => anadirBloque("texto"), text: "+ Añadir texto" }),
                    h("button", { type: "button", class: "btn", id: "btAnadirTitulo", onclick: () => anadirBloque("titulo"), text: "+ Añadir título" }),
                    h("span", { id: "botonesAnadirExtra" })))));
        $("#inpTituloApunte").addEventListener("input", (e) => { E.doc.titulo = e.target.value; marcarCambio(); });
    }

    function pintarTranscripcion() {
        const paginas = vaciar($("#visorPaginas"));
        E.doc.paginas.forEach((p) => paginas.append(h("button", { type: "button", class: "btn sm", "aria-pressed": String(p.id === E.pagina),
            "data-error": p.error ? "" : null, onclick: () => { E.pagina = p.id; E.seleccionado = null; pintarTranscripcion(); },
            text: `Página ${p.orden}${p.error ? " ⚠" : ""}` })));
        pintarVisor();
        pintarBloques();
        $("#btAnadirBloque").disabled = $("#btAnadirTitulo").disabled = !editable();
        document.querySelectorAll("#botonesAnadirExtra button").forEach((bt) => { bt.disabled = !editable(); });
    }

    function pintarVisor() {
        const marco = vaciar($("#visorMarco"));
        const p = paginaDe(E.pagina);
        const avisos = $("#visorAvisos");
        $("#btVerOriginal").setAttribute("aria-pressed", String(E.verOriginal));
        $("#btVerOriginal").textContent = E.verOriginal ? "Ver la foto procesada" : "Ver la foto original";
        $("#btVerOriginal").hidden = !p || !p.archivo_procesado;
        if (!p) { avisos.textContent = ""; return; }
        const advert = { BAJA_RESOLUCION: "resolución baja", IMAGEN_BORROSA: "imagen borrosa" };
        avisos.textContent = [p.error ? `Esta página no se pudo analizar: ${p.error}` : "",
                              (p.advertencias || []).length ? `Avisos de la foto: ${p.advertencias.map((a) => advert[a] || a).join(", ")}.` : ""]
            .filter(Boolean).join(" ");
        const procesada = p.archivo_procesado && !E.verOriginal;
        marco.append(h("img", { src: urlArchivo(procesada ? p.archivo_procesado : p.archivo_original),
                                alt: `Página ${p.orden}${procesada ? " procesada" : " original"}` }));
        if (!procesada || !p.ancho || !p.alto) return;  // las regiones están en coordenadas de la imagen procesada
        E.doc.bloques.filter((b) => b.pagina === p.id && b.bbox).forEach((b, n) => {
            const [x0, y0, x1, y1] = b.bbox;
            const region = h("button", { type: "button", class: "region", "data-estado": b.estado, "data-bloque": b.id,
                "aria-label": `Región del bloque ${n + 1} (${TIPOS[b.tipo] || b.tipo})`, "aria-current": String(b.id === E.seleccionado),
                onclick: () => seleccionar(b.id, true) });
            Object.assign(region.style, { left: `${(x0 / p.ancho) * 100}%`, top: `${(y0 / p.alto) * 100}%`,
                                          width: `${((x1 - x0) / p.ancho) * 100}%`, height: `${((y1 - y0) / p.alto) * 100}%` });
            marco.append(region);
        });
    }

    function seleccionar(id, enfocar) {
        E.seleccionado = id;
        document.querySelectorAll(".region").forEach((r) => r.setAttribute("aria-current", String(r.dataset.bloque === id)));
        document.querySelectorAll(".bloque").forEach((b) => b.setAttribute("aria-current", String(b.dataset.bloque === id)));
        if (enfocar) {
            const tarjeta = document.querySelector(`.bloque[data-bloque="${CSS.escape(id)}"]`);
            if (tarjeta) {
                tarjeta.scrollIntoView({ block: "center", behavior: "smooth" });
                (tarjeta.querySelector(".bloque__cuerpo textarea, .bloque__cuerpo input") || tarjeta.querySelector("select") || tarjeta).focus({ preventScroll: true });
            }
        }
    }

    function bloquesVisibles() {
        return E.doc.bloques.filter((b) => b.pagina === E.pagina || (!b.pagina && E.doc.paginas[E.doc.paginas.length - 1]?.id === E.pagina)
                                           || (!E.doc.paginas.length));
    }

    function pintarBloques() {
        const lista = vaciar($("#listaBloques"));
        const visibles = bloquesVisibles();
        if (!visibles.length) {
            lista.append(h("p", { class: "vacio", text: editable() ? "Esta página no tiene bloques. Puedes añadir texto a mano." : "El análisis todavía no ha terminado." }));
            return;
        }
        visibles.forEach((b, n) => lista.append(tarjetaBloque(b, n + 1)));
    }

    function pintarMarcas() {
        document.querySelectorAll(".bloque").forEach((t) => {
            const b = bloque(t.dataset.bloque);
            const marca = t.querySelector(".etiqueta-editado");
            if (b && marca) marca.hidden = !editado(b);
        });
    }

    function tarjetaBloque(b, n) {
        const soloLectura = !editable();
        const tipos = ["titulo", "texto", "manuscrito", "formula"].concat(b.tabla ? ["tabla"] : [], b.recorte ? ["imagen"] : []);
        const confianza = typeof b.confianza === "number" ? ` ${Math.round(b.confianza * 100)} %` : "";
        const tarjeta = h("article", { class: "bloque", "data-bloque": b.id, "data-estado": b.origen === "ocr" ? b.estado : "usuario",
                                       "aria-current": String(b.id === E.seleccionado), "aria-labelledby": `titulo-${b.id}`, tabindex: "-1",
                                       onfocusin: () => seleccionar(b.id, false) },
            h("div", { class: "bloque__cabecera" },
                h("span", { class: "bloque__titulo", id: `titulo-${b.id}`, text: `Bloque ${n}` }),
                b.origen === "ocr" ? h("span", { class: `estado-chip estado-${b.estado}`, title: "Confianza del reconocimiento",
                                                text: `${ESTADO_BLOQUE[b.estado] || b.estado}${confianza}` })
                                   : h("span", { class: "estado-chip", text: "Añadido por ti" }),
                h("span", { class: "etiqueta-editado", hidden: !editado(b), text: "corregido" }),
                h("label", { class: "sr-only", for: `tipo-${b.id}`, text: `Tipo del bloque ${n}` }),
                h("select", { id: `tipo-${b.id}`, disabled: soloLectura, onchange: (e) => cambiarTipo(b, e.target.value) },
                    tipos.map((t) => h("option", { value: t, selected: t === b.tipo, text: TIPOS[t] })))));
        const cuerpo = h("div", { class: "bloque__cuerpo" });
        (E.renderizadores[b.tipo] || renderTexto)(b, cuerpo, { soloLectura, n, urlArchivo, marcarCambio, tarjeta });
        tarjeta.append(cuerpo);
        if (b.palabras_dudosas && b.palabras_dudosas.length && b.estado !== "reconocido") {
            tarjeta.append(h("p", { class: "bloque__dudosas", text: `Palabras dudosas: ${b.palabras_dudosas.slice(0, 12).join(", ")}` }));
        }
        if (!soloLectura) {
            const acciones = h("div", { class: "bloque__acciones", role: "group", "aria-label": `Acciones del bloque ${n}` },
                h("button", { type: "button", class: "btn sm", dataset: { accion: "dividir" }, onclick: () => dividir(b.id),
                              text: "Dividir", title: "Divide el bloque donde está el cursor" }),
                h("button", { type: "button", class: "btn sm", dataset: { accion: "unir" }, onclick: () => unir(b.id),
                              text: "Unir con el siguiente", disabled: !siguienteDeMismaPagina(b) }),
                h("button", { type: "button", class: "btn sm", dataset: { accion: "subir" }, onclick: () => moverBloque(b.id, -1), text: "↑",
                              "aria-label": `Subir el bloque ${n}` }),
                h("button", { type: "button", class: "btn sm", dataset: { accion: "bajar" }, onclick: () => moverBloque(b.id, 1), text: "↓",
                              "aria-label": `Bajar el bloque ${n}` }),
                b.texto_original && b.texto !== b.texto_original
                    ? h("button", { type: "button", class: "btn sm", dataset: { accion: "restaurar" }, text: "Volver al texto reconocido",
                                    onclick: () => { b.texto = b.texto_original; marcarCambio(); pintarBloques(); } }) : null,
                h("button", { type: "button", class: "btn sm danger", dataset: { accion: "borrar" }, onclick: () => borrar(b.id),
                              text: "Borrar", "aria-label": `Borrar el bloque ${n}` }));
            E.acciones.forEach((fn) => { const extra = fn(b); if (extra) acciones.append(extra); });
            tarjeta.append(acciones);
        }
        return tarjeta;
    }

    // Texto, título y manuscrito: el texto en un textarea, junto al recorte si es dudoso.
    function renderTexto(b, cuerpo, { soloLectura, n }) {
        if (b.recorte && (b.estado !== "reconocido" || ["manuscrito", "imagen"].includes(b.tipo))) {
            cuerpo.append(h("img", { class: "bloque__recorte", src: urlArchivo(b.recorte), alt: `Recorte de la foto del bloque ${n}`, loading: "lazy" }));
        }
        const area = h("textarea", { id: `texto-${b.id}`, rows: String(Math.min(12, Math.max(2, (b.texto || "").split("\n").length + 1))),
                                     "aria-label": `Texto del bloque ${n}`, readonly: soloLectura ? "" : null, spellcheck: "true",
                                     placeholder: b.estado === "no_reconocido" ? "No se pudo leer este fragmento. Escríbelo tú o consérvalo como imagen." : "" });
        area.value = b.texto || "";
        area.addEventListener("input", () => { b.texto = area.value; marcarCambio(); });
        // Al pulsar «Dividir» el foco pasa al botón: se recuerda dónde estaba el cursor.
        area.addEventListener("blur", () => { E.cursor = { id: b.id, pos: area.selectionStart }; });
        cuerpo.append(area);
        if (b.recorte && !soloLectura) {
            const id = `conservar-${b.id}`;
            const casilla = h("input", { type: "checkbox", id, checked: b.conservar_imagen,
                                         onchange: (e) => { b.conservar_imagen = e.target.checked; marcarCambio(); } });
            cuerpo.append(h("div", { class: "casilla" }, casilla,
                h("label", { for: id, text: "Conservar la imagen original de este fragmento en el PDF" })));
        }
    }

    // ---------------------------------------------------------------- operaciones
    function siguienteDeMismaPagina(b) {
        const i = indice(b.id);
        const sig = E.doc.bloques[i + 1];
        return sig && sig.pagina === b.pagina && !sig.tabla && !b.tabla ? sig : null;
    }

    function anadirBloque(tipo, extra = {}) {
        const nuevo = { id: nuevoId(), pagina: E.pagina, orden: 0, tipo, origen: "usuario", estado: "reconocido",
                        texto: "", bbox: null, ...extra };
        const ref = E.seleccionado ? indice(E.seleccionado) : -1;
        const visibles = bloquesVisibles();
        const despues = ref >= 0 ? ref : (visibles.length ? indice(visibles[visibles.length - 1].id) : E.doc.bloques.length - 1);
        E.doc.bloques.splice(despues + 1, 0, nuevo);
        E.seleccionado = nuevo.id;
        marcarCambio();
        pintarTranscripcion();
        seleccionar(nuevo.id, true);
        return nuevo;
    }

    function cambiarTipo(b, tipo) { b.tipo = tipo; marcarCambio(); pintarBloques(); seleccionar(b.id, true); }

    function borrar(id) {
        const i = indice(id);
        if (i < 0) return;
        const [quitado] = E.doc.bloques.splice(i, 1);
        marcarCambio();
        pintarTranscripcion();
        avisar(aviso(), "info", "Bloque borrado.", [{ texto: "Deshacer", alHacer: () => {
            E.doc.bloques.splice(i, 0, quitado); marcarCambio(); avisar(aviso(), "info", ""); pintarTranscripcion(); seleccionar(quitado.id, true);
        } }]);
    }

    function dividir(id) {
        const b = bloque(id);
        const area = document.getElementById(`texto-${id}`);
        const texto = b.texto || "";
        let corte = area && document.activeElement === area ? area.selectionStart
            : (E.cursor && E.cursor.id === id ? E.cursor.pos : -1);
        if (corte <= 0 || corte >= texto.length) {  // sin cursor: por la mitad, en un salto de línea si lo hay
            const mitad = Math.floor(texto.length / 2);
            const salto = texto.indexOf("\n", mitad);
            corte = salto > 0 ? salto : texto.lastIndexOf(" ", mitad);
        }
        if (corte <= 0 || corte >= texto.length) { avisar(aviso(), "aviso", "Coloca el cursor donde quieres dividir el bloque."); return; }
        b.texto = texto.slice(0, corte).replace(/\s+$/, "");
        const nuevo = { id: nuevoId(), pagina: b.pagina, orden: 0, tipo: b.tipo === "titulo" ? "texto" : b.tipo, origen: "usuario",
                        estado: "reconocido", texto: texto.slice(corte).replace(/^\s+/, ""), bbox: null };
        E.doc.bloques.splice(indice(id) + 1, 0, nuevo);
        marcarCambio();
        pintarTranscripcion();
        seleccionar(nuevo.id, true);
    }

    function unir(id) {
        const b = bloque(id);
        const sig = siguienteDeMismaPagina(b);
        if (!sig) return;
        b.texto = [b.texto, sig.texto].filter(Boolean).join("\n");
        E.doc.bloques.splice(indice(sig.id), 1);
        marcarCambio();
        pintarTranscripcion();
        seleccionar(b.id, true);
    }

    function moverBloque(id, delta) {
        const i = indice(id);
        const visibles = bloquesVisibles().map((b) => b.id);
        const pos = visibles.indexOf(id);
        const destinoId = visibles[pos + delta];
        if (!destinoId) return;
        const j = indice(destinoId);
        [E.doc.bloques[i], E.doc.bloques[j]] = [E.doc.bloques[j], E.doc.bloques[i]];
        marcarCambio();
        pintarBloques();
        seleccionar(id, false);
        const boton = document.querySelector(`.bloque[data-bloque="${CSS.escape(id)}"] [data-accion=${delta < 0 ? "subir" : "bajar"}]`);
        if (boton) boton.focus();
    }

    registrarPestana({ id: "transcripcion", titulo: "Transcripción", orden: 10, crear: crearTranscripcion, pintar: pintarTranscripcion });

    NS.editor = { E, registrarPestana, registrarTipo, registrarAccionBloque, alCargar, alGuardar, guardar, recargar, cargar,
                  marcarCambio, hayCambios, editable, serializar, bloque, indice, anadirBloque, pintarBloques, pintarTranscripcion,
                  pintarTodo, seguirAnalisis, informarAnalisis, urlArchivo, mostrarPestana, textoPlano, copiarCambios,
                  actualizarEstadoGuardado, nuevoId, TIPOS, renderTexto };
})(window);
