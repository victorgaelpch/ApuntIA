// Generar, previsualizar y descargar el PDF del apunte (FRONT-16).
//
// - El PDF se genera en el servidor a partir de una versión GUARDADA. Con cambios sin
//   guardar se pide guardarlos antes, para que el PDF no use una transcripción anterior.
// - El estado (en cola, maquetando, listo, falló, cancelado) es el del trabajo real; no
//   se dice «listo» hasta que el servidor entrega un archivo que empieza por %PDF.
// - La descarga pasa por la API autenticada y se ofrece como URL blob: temporal, que se
//   libera al cambiarla o al salir. No hay URL públicas de archivos privados.
// - Si el apunte cambia, la vista previa se marca como desactualizada.
// - La exportación en curso se recupera al recargar la página.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, $, vaciar, pedir, avisar, avisarError, textoTrabajo, esperarTrabajo, fecha, ErrorV2 } = NS.v2;
    const ed = NS.editor;
    const E = ed.E;
    const ESTILOS = { extendido: "Completo (con resumen, conceptos y glosario)", basico: "Básico (solo la transcripción)" };
    const ESTADOS = { pendiente: "Generándose", completado: "Listo", fallido: "Falló", cancelado: "Cancelado" };
    let vista = { url: null, exportacion: null };
    let control = null;

    function crear(panel) {
        panel.append(
            h("div", { class: "tarjeta" },
                h("h2", { text: "PDF del apunte" }),
                h("p", { class: "ayuda", text: "Un documento con portada, índice, la transcripción corregida, fórmulas, tablas y esquemas, y —si los aceptaste— los complementos citados. Para descargar solo la foto mejorada usa «Mejorar una foto»." }),
                h("div", { class: "aviso", id: "avisoPdf", hidden: true }),
                h("ul", { class: "avisos-previos", id: "avisosPrevios" }),
                h("form", { id: "formPdf", novalidate: true, onsubmit: (e) => { e.preventDefault(); generar(); } },
                    h("div", { class: "columnas" },
                        h("div", { class: "campo" },
                            h("label", { for: "selVersionPdf", text: "Versión" }),
                            h("select", { id: "selVersionPdf" })),
                        h("div", { class: "campo" },
                            h("label", { for: "selEstiloPdf", text: "Nivel de detalle" }),
                            h("select", { id: "selEstiloPdf" }, Object.entries(ESTILOS).map(([v, t]) => h("option", { value: v, text: t }))))),
                    h("div", { class: "casilla" },
                        h("input", { type: "checkbox", id: "chkComplementosPdf", checked: true }),
                        h("label", { for: "chkComplementosPdf", id: "etiquetaComplementosPdf", text: "Incluir los complementos aceptados, con sus fuentes" })),
                    h("div", { class: "casilla" },
                        h("input", { type: "checkbox", id: "chkOriginalesPdf" }),
                        h("label", { for: "chkOriginalesPdf", text: "Añadir al final las fotos originales" })),
                    h("p", { class: "ayuda", text: "El título y la portada usan el título del apunte; cámbialo arriba si quieres." }),
                    h("div", { class: "botones" }, h("button", { type: "submit", class: "btn primary", id: "btGenerarPdf", text: "Generar PDF" }))),
                h("div", { id: "progresoPdf", hidden: true },
                    h("p", { id: "textoPdf", "aria-live": "polite" }),
                    h("div", { class: "progreso", role: "progressbar", "aria-labelledby": "textoPdf", "aria-valuemin": "0",
                               "aria-valuemax": "100", "aria-valuenow": "0", id: "barraPdf" }, h("span")),
                    h("div", { class: "botones" }, h("button", { type: "button", class: "btn", id: "btCancelarPdf", text: "Cancelar", onclick: cancelar })))),
            h("div", { class: "tarjeta", id: "cajaVistaPdf", hidden: true },
                h("h2", { id: "tituloVistaPdf", text: "Vista previa" }),
                h("p", { class: "aviso", id: "avisoObsoleto", "data-tipo": "aviso", hidden: true }),
                h("div", { class: "botones" },
                    h("a", { class: "btn primary", id: "enlaceDescargaPdf", text: "Descargar PDF" }),
                    h("a", { class: "btn", id: "enlaceAbrirPdf", target: "_blank", rel: "noopener", text: "Abrir en otra pestaña" })),
                h("p", { class: "ayuda", id: "datosPdf" }),
                h("iframe", { id: "marcoPdf", class: "marco-pdf", title: "Vista previa del PDF del apunte" })),
            h("div", { class: "tarjeta" },
                h("h2", { text: "PDF generados" }),
                h("ol", { class: "versiones", id: "listaPdf" })));
    }

    // ---------------------------------------------------------------- antes de generar
    function avisosPrevios() {
        const lista = vaciar($("#avisosPrevios"));
        const b = E.doc.bloques;
        const inciertos = b.filter((x) => x.origen === "ocr" && x.estado === "incierto" && !x.editado).length;
        const sinLeer = b.filter((x) => x.estado === "no_reconocido" && !(x.texto || "").trim()).length;
        const formulas = b.filter((x) => x.tipo === "formula" && x.latex_valido === false).length;
        const propuestas = (E.doc.ampliaciones || []).filter((a) => a.estado === "propuesta").length;
        const aceptadas = (E.doc.ampliaciones || []).filter((a) => a.estado === "aceptada").length;
        const items = [];
        if (ed.hayCambios()) items.push("Tienes cambios sin guardar: se guardarán antes de generar el PDF.");
        if (inciertos) items.push(`${inciertos} bloque(s) con reconocimiento incierto sin revisar.`);
        if (sinLeer) items.push(`${sinLeer} fragmento(s) sin leer: irán como imagen original.`);
        if (formulas) items.push(`${formulas} fórmula(s) que no se pueden dibujar: irán como imagen original.`);
        if (propuestas) items.push(`${propuestas} complemento(s) sin revisar: no se incluirán.`);
        items.forEach((t) => lista.append(h("li", { text: t })));
        lista.hidden = !items.length;
        $("#etiquetaComplementosPdf").textContent = `Incluir los complementos aceptados, con sus fuentes (${aceptadas})`;
    }

    async function opcionesVersion() {
        const sel = $("#selVersionPdf");
        const previa = sel.value;
        let versiones = [];
        try { versiones = (await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/versiones`)).versiones; } catch (_) { /* solo la actual */ }
        vaciar(sel).append(h("option", { value: "", text: `La actual (versión ${E.version})` }));
        versiones.filter((v) => v.numero !== E.version).forEach((v) => sel.append(h("option", { value: String(v.numero), text: `Versión ${v.numero} · ${fecha(v.creado)}` })));
        if ([...sel.options].some((o) => o.value === previa)) sel.value = previa;
    }

    // ---------------------------------------------------------------- generar
    async function generar() {
        const avisoEl = $("#avisoPdf");
        avisar(avisoEl, "info", "");
        if (!$("#selVersionPdf").value && ed.hayCambios()) {
            if (!await ed.guardar()) { avisar(avisoEl, "error", "No se pudo guardar el apunte: el PDF no se generó. Revisa el aviso de arriba."); return; }
        }
        const version = $("#selVersionPdf").value ? Number($("#selVersionPdf").value) : null;
        const cuerpo = { estilo: $("#selEstiloPdf").value, incluir_complementos: $("#chkComplementosPdf").checked,
                         incluir_originales: $("#chkOriginalesPdf").checked, ...(version ? { version } : {}) };
        try {
            const r = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/exportaciones`, { method: "POST", json: cuerpo });
            if (r.exportacion.estado === "completado") {
                avisar(avisoEl, "info", "Ya tenías un PDF de esta versión con estas opciones: se reutiliza.");
                await mostrar(r.exportacion);
            } else {
                await seguir(r.exportacion, r.trabajo || { id: r.exportacion.trabajo_id });
            }
        } catch (err) {
            avisarError(avisoEl, err, err.status >= 500 || err.codigo === "DEMASIADOS_TRABAJOS" ? [{ texto: "Reintentar", alHacer: generar }] : []);
        }
        pintarLista();
    }

    async function seguir(exportacion, trabajo) {
        const caja = $("#progresoPdf"), barra = $("#barraPdf"), avisoEl = $("#avisoPdf");
        caja.hidden = false;
        $("#btGenerarPdf").disabled = true;
        $("#btCancelarPdf").disabled = false;
        E.trabajoPdf = trabajo.id;
        control = new AbortController();
        try {
            const t = await esperarTrabajo(trabajo.id, { signal: control.signal, alAvanzar: (x) => {
                $("#textoPdf").textContent = x.estado === "pendiente" ? "En cola…" : textoTrabajo(x);
                barra.setAttribute("aria-valuenow", String(x.progreso || 0));
                barra.firstElementChild.style.width = `${x.progreso || 0}%`;
            } });
            if (t.estado === "completado") {
                const exp = (await pedir(`/api/v2/exportaciones/${encodeURIComponent(exportacion.id)}`)).exportacion;
                await mostrar(exp);
                avisar(avisoEl, "exito", `PDF listo: ${exp.paginas} página(s).`);
            } else if (t.estado === "cancelado") {
                avisar(avisoEl, "info", "Generación cancelada.", [{ texto: "Generar de nuevo", alHacer: generar }]);
            } else {
                const mensaje = NS.v2.textoErrorTrabajo(t.error, "No se pudo generar el PDF.");
                avisar(avisoEl, "error", mensaje, [{ texto: "Reintentar", alHacer: generar }]);
            }
        } catch (err) {
            if (err.codigo !== "CANCELADO") avisarError(avisoEl, err, [{ texto: "Reintentar", alHacer: generar }]);
        } finally {
            caja.hidden = true;
            $("#btGenerarPdf").disabled = false;
            E.trabajoPdf = null;
            pintarLista();
        }
    }

    async function cancelar() {
        if (!E.trabajoPdf) return;
        $("#btCancelarPdf").disabled = true;
        try { await pedir(`/api/v2/trabajos/${E.trabajoPdf}`, { method: "DELETE" }); }
        catch (err) { avisarError($("#avisoPdf"), err); }
    }

    // ---------------------------------------------------------------- mostrar y descargar
    function nombreArchivo(cabecera, exp) {
        const m = /filename="([^"]+)"/.exec(cabecera || "");
        return m ? m[1] : `apunte-v${exp.version}.pdf`;
    }

    async function descargarBlob(exp) {
        const r = await pedir(exp.descarga, { crudo: true, timeoutMs: 60000, headers: { Accept: "application/pdf" } });
        const blob = await r.blob();
        const firma = new Uint8Array(await blob.slice(0, 5).arrayBuffer());
        if (blob.type !== "application/pdf" || String.fromCharCode(...firma) !== "%PDF-") {
            throw new ErrorV2({ codigo: "RESPUESTA_INVALIDA", mensaje: "El servidor no devolvió un PDF válido.", status: 500 });
        }
        return { blob, nombre: nombreArchivo(r.headers.get("Content-Disposition"), exp) };
    }

    function liberar() {
        if (vista.url) URL.revokeObjectURL(vista.url);
        vista = { url: null, exportacion: null };
    }

    async function mostrar(exp) {
        try {
            const { blob, nombre } = await descargarBlob(exp);
            liberar();
            vista = { url: URL.createObjectURL(blob), exportacion: exp };
            const descarga = $("#enlaceDescargaPdf");
            descarga.href = vista.url;
            descarga.setAttribute("download", nombre);
            $("#enlaceAbrirPdf").href = vista.url;
            $("#marcoPdf").src = vista.url;
            $("#datosPdf").textContent = `${nombre} · versión ${exp.version} · ${exp.paginas} página(s) · ${(exp.tamano / 1024).toFixed(0)} KB · ${ESTILOS[exp.opciones.estilo] || exp.opciones.estilo}`;
            $("#cajaVistaPdf").hidden = false;
            marcarObsoleto();
        } catch (err) {
            avisarError($("#avisoPdf"), err, [{ texto: "Reintentar", alHacer: () => mostrar(exp) }]);
        }
    }

    // Una vista previa de una versión anterior (o con cambios sin guardar) no es «la actual».
    function marcarObsoleto() {
        const el = $("#avisoObsoleto");
        if (!vista.exportacion) return;
        const v = vista.exportacion.version;
        const obsoleto = v !== E.version || ed.hayCambios();
        el.hidden = !obsoleto;
        vaciar(el);
        if (obsoleto) {
            el.append(h("span", { text: ed.hayCambios() ? "Has hecho cambios después de este PDF. " : `Este PDF corresponde a la versión ${v}; el apunte va por la ${E.version}. ` }),
                      h("button", { type: "button", class: "btn sm", id: "btRegenerarPdf", text: "Generar con la versión actual",
                                    onclick: () => { $("#selVersionPdf").value = ""; generar(); } }));
        }
    }

    async function pintarLista() {
        const lista = $("#listaPdf");
        if (!lista) return;
        let exportaciones = [];
        try { exportaciones = (await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/exportaciones`)).exportaciones; }
        catch (err) { avisarError($("#avisoPdf"), err); return; }
        vaciar(lista);
        if (!exportaciones.length) { lista.append(h("li", { class: "vacio", text: "Todavía no has generado ningún PDF." })); return exportaciones; }
        for (const x of exportaciones) {
            const anterior = x.version !== E.version;
            lista.append(h("li", { class: "version", "data-exportacion": x.id },
                h("span", { class: "version__datos" },
                    h("b", { text: `Versión ${x.version}` }),
                    h("span", { class: `estado-chip estado-${x.estado}`, text: ESTADOS[x.estado] || x.estado }),
                    anterior ? h("span", { class: "estado-chip estado-parcial", text: "Versión anterior" }) : null,
                    h("span", { text: ` · ${x.opciones.estilo === "basico" ? "Básico" : "Completo"}${x.opciones.incluir_originales ? " + fotos" : ""} · ${fecha(x.actualizado)}` })),
                x.estado === "completado" ? h("button", { type: "button", class: "btn sm", dataset: { accion: "ver" }, text: "Ver y descargar",
                                                          onclick: () => mostrar(x) }) : null));
        }
        return exportaciones;
    }

    // ---------------------------------------------------------------- integración
    ed.registrarPestana({ id: "pdf", titulo: "PDF", orden: 30, crear,
                          pintar: () => { avisosPrevios(); marcarObsoleto(); },
                          alMostrar: () => { avisosPrevios(); opcionesVersion(); pintarLista(); } });
    ed.alGuardar(() => { if ($("#avisosPrevios")) { avisosPrevios(); marcarObsoleto(); } });
    ed.alCargar(async () => {
        // Opciones propuestas según las preferencias del perfil (FRONT-19).
        const p = (NS.v2.sesion.usuario && NS.v2.sesion.usuario.preferencias) || {};
        if (p.estilo_pdf) $("#selEstiloPdf").value = p.estilo_pdf;
        if (typeof p.incluir_complementos_pdf === "boolean") $("#chkComplementosPdf").checked = p.incluir_complementos_pdf;
        if (typeof p.incluir_originales_pdf === "boolean") $("#chkOriginalesPdf").checked = p.incluir_originales_pdf;
        await opcionesVersion();
        const exportaciones = await pintarLista() || [];
        const enCurso = exportaciones.find((x) => x.estado === "pendiente" && x.trabajo_id);
        if (enCurso) { ed.mostrarPestana("pdf"); seguir(enCurso, { id: enCurso.trabajo_id }); }
    });
    // «PDF de esta versión» en el historial.
    E.extrasVersion = (v) => h("button", { type: "button", class: "btn sm", dataset: { accion: "pdf" }, text: "PDF de esta versión",
        onclick: async () => { ed.mostrarPestana("pdf"); await opcionesVersion(); $("#selVersionPdf").value = v.numero === E.version ? "" : String(v.numero); } });
    global.addEventListener("pagehide", liberar);
})(window);
