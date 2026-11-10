// Información complementaria con fuentes citadas (FRONT-15).
//
// - Desactivada por defecto: hay que activarla en el apunte, tener permitido el uso en
//   el perfil y dar el consentimiento expreso cada vez. Se explica qué se envía (solo
//   las palabras clave elegidas, nunca la foto ni el texto) y a quién.
// - Los complementos se muestran en su propia pestaña, separados del apunte, con su
//   fuente (título, enlace, autor, licencia y fecha de consulta). Solo los aceptados
//   entran en el PDF; el texto del apunte nunca se cambia.
// - Si la fuente parece contradecir al apunte, se avisa y se pide revisar.
// - Sin proveedor o sin conexión, el resto funciona y el PDF se puede crear igual.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, $, vaciar, pedir, avisar, avisarError, confirmar, textoTrabajo, esperarTrabajo, sesion } = NS.v2;
    const ed = NS.editor;
    const E = ed.E;
    const MAX_CONCEPTOS = 8;
    const ESTADOS = { propuesta: "Pendiente de revisar", aceptada: "Aceptado (irá al PDF)", rechazada: "Descartado" };
    let info = { disponible: false, proveedor: "ninguno", conceptos: [] };
    let control = null;

    function crear(panel) {
        panel.append(
            h("div", { class: "tarjeta" },
                h("h2", { text: "Información complementaria" }),
                h("p", { class: "ayuda", text: "Opcional. Busca explicaciones de los conceptos de tu apunte en una fuente externa citada. Lo que encuentre se muestra aquí, separado de tu apunte, y solo entra en el PDF si lo aceptas. Puedes crear el PDF sin esto." }),
                h("div", { class: "aviso", id: "avisoInvestigacion", hidden: true }),
                h("div", { class: "casilla" },
                    h("input", { type: "checkbox", id: "chkInvestigar", onchange: (e) => { $("#formInvestigar").hidden = !e.target.checked; } }),
                    h("label", { for: "chkInvestigar", text: "Buscar información complementaria" })),
                h("form", { id: "formInvestigar", hidden: true, novalidate: true, onsubmit: (e) => { e.preventDefault(); investigar(); } },
                    h("p", { id: "textoProveedor" }),
                    h("fieldset", { class: "conceptos" },
                        h("legend", { text: `Conceptos que se buscarán (máximo ${MAX_CONCEPTOS})` }),
                        h("div", { id: "listaConceptos", class: "conceptos__lista" }),
                        h("div", { class: "con-boton" },
                            h("label", { for: "inpConcepto", class: "sr-only", text: "Añadir otro concepto" }),
                            h("input", { type: "text", id: "inpConcepto", maxlength: "80", placeholder: "Añadir otro concepto (palabras clave)" }),
                            h("button", { type: "button", class: "btn sm", id: "btAnadirConcepto", text: "Añadir", onclick: anadirConcepto }))),
                    h("div", { class: "campo" },
                        h("label", { for: "selIdioma", text: "Idioma de la fuente" }),
                        h("select", { id: "selIdioma" }, h("option", { value: "es", text: "Español" }), h("option", { value: "en", text: "Inglés" }))),
                    h("div", { class: "casilla" },
                        h("input", { type: "checkbox", id: "chkConsentimiento", required: true }),
                        h("label", { for: "chkConsentimiento", id: "textoConsentimiento" })),
                    h("div", { class: "botones" }, h("button", { type: "submit", class: "btn primary", id: "btInvestigar", text: "Buscar ahora" }))),
                h("div", { id: "progresoInvestigacion", hidden: true },
                    h("p", { id: "textoInvestigacion", "aria-live": "polite" }),
                    h("div", { class: "progreso", role: "progressbar", "aria-labelledby": "textoInvestigacion", "aria-valuemin": "0",
                               "aria-valuemax": "100", "aria-valuenow": "0", id: "barraInvestigacion" }, h("span")),
                    h("div", { class: "botones" }, h("button", { type: "button", class: "btn", id: "btCancelarInvestigacion", text: "Cancelar búsqueda", onclick: cancelar })))),
            h("div", { class: "tarjeta" },
                h("h2", { text: "Complementos encontrados" }),
                h("p", { class: "ayuda", text: "Lee cada uno y su fuente antes de aceptarlo. No forman parte de lo que escribiste: en el PDF aparecen en una sección aparte y citados." }),
                h("div", { class: "aviso", id: "avisoComplementos", hidden: true }),
                h("ol", { class: "complementos", id: "listaComplementos" })));
    }

    // ---------------------------------------------------------------- formulario
    function pintarFormulario() {
        const prov = info.proveedor === "wikipedia" ? "Wikipedia (es.wikipedia.org o en.wikipedia.org)" : info.proveedor;
        const permitida = sesion.usuario && sesion.usuario.preferencias && sesion.usuario.preferencias.investigacion_permitida;
        const avisoEl = $("#avisoInvestigacion");
        $("#chkInvestigar").disabled = !info.disponible || !ed.editable();
        if (!info.disponible) {
            avisar(avisoEl, "aviso", "La búsqueda externa no está disponible en este servidor (sin conexión o desactivada). Tu apunte y su PDF funcionan igual sin ella.",
                   [{ texto: "Ir al PDF", alHacer: () => ed.mostrarPestana("pdf") }]);
        } else if (!permitida) {
            avisar(avisoEl, "info", "Para usar la búsqueda externa primero tienes que permitirla en tu perfil.",
                   [{ texto: "Permitir en mi perfil", alHacer: permitir }]);
            $("#chkInvestigar").disabled = true;
        } else {
            avisar(avisoEl, "info", "");
        }
        $("#textoProveedor").textContent = `Fuente: ${prov}. Solo se envían las palabras clave marcadas abajo; nunca tus fotos ni el texto de tu apunte. Licencia del contenido: CC BY-SA 4.0.`;
        $("#textoConsentimiento").textContent = `Acepto enviar estas palabras clave a ${info.proveedor === "wikipedia" ? "Wikipedia" : prov} para buscar información.`;
        const lista = vaciar($("#listaConceptos"));
        if (!info.conceptos.length) lista.append(h("p", { class: "ayuda", text: "No se encontraron conceptos claros en el apunte: añade los que quieras." }));
        info.conceptos.forEach((c, i) => {
            const id = `concepto-${i}`;
            lista.append(h("span", { class: "casilla concepto" },
                h("input", { type: "checkbox", id, value: c, checked: i < 3, name: "concepto" }),
                h("label", { for: id, text: c })));
        });
    }

    async function permitir() {
        if (!await confirmar({ titulo: "¿Permitir la búsqueda externa?", aceptar: "Permitir",
            texto: "Podrás buscar información complementaria de tus apuntes. Cada búsqueda te pedirá confirmación y solo enviará las palabras clave que elijas. Puedes desactivarlo en tu perfil." })) return;
        try {
            const r = await pedir("/api/v2/perfil", { method: "PATCH", json: { preferencias: { investigacion_permitida: true } } });
            sesion.usuario = r.usuario;
            pintarFormulario();
        } catch (err) { avisarError($("#avisoInvestigacion"), err); }
    }

    function anadirConcepto() {
        const input = $("#inpConcepto");
        const valor = input.value.replace(/\s+/g, " ").trim();
        if (!valor) return;
        if (/[@/\\<>{}]|https?:|www\./i.test(valor) || valor.split(" ").length > 6) {
            avisar($("#avisoInvestigacion"), "error", "Escribe solo palabras clave (hasta 6 palabras, sin direcciones ni emails).");
            return;
        }
        if (!info.conceptos.includes(valor)) info.conceptos.push(valor);
        input.value = "";
        pintarFormulario();
        const ultimo = [...document.querySelectorAll("#listaConceptos input")].find((i) => i.value === valor);
        if (ultimo) { ultimo.checked = true; ultimo.focus(); }
    }

    // ---------------------------------------------------------------- búsqueda
    async function investigar() {
        const elegidos = [...document.querySelectorAll("#listaConceptos input:checked")].map((i) => i.value);
        const avisoEl = $("#avisoInvestigacion");
        if (!elegidos.length) { avisar(avisoEl, "error", "Marca al menos un concepto."); return; }
        if (elegidos.length > MAX_CONCEPTOS) { avisar(avisoEl, "error", `Marca como máximo ${MAX_CONCEPTOS} conceptos.`); return; }
        if (!$("#chkConsentimiento").checked) {
            avisar(avisoEl, "error", "Marca la casilla de consentimiento para continuar.");
            $("#chkConsentimiento").focus();
            return;
        }
        // Los complementos crean una versión: primero se guardan los cambios pendientes.
        if (ed.hayCambios() && !await ed.guardar()) return;
        try {
            const { trabajo } = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/investigacion`, {
                method: "POST", json: { consentimiento: true, conceptos: elegidos, idioma: $("#selIdioma").value } });
            $("#chkConsentimiento").checked = false;  // el consentimiento vale para esta búsqueda
            avisar(avisoEl, "info", "");
            await seguir(trabajo);
        } catch (err) {
            avisarError(avisoEl, err);
        }
    }

    async function seguir(trabajo) {
        const caja = $("#progresoInvestigacion");
        const barra = $("#barraInvestigacion");
        caja.hidden = false;
        $("#btInvestigar").disabled = true;
        $("#btCancelarInvestigacion").disabled = false;
        E.trabajoInvestigacion = trabajo.id;
        control = new AbortController();
        try {
            const final = await esperarTrabajo(trabajo.id, { signal: control.signal, alAvanzar: (t) => {
                $("#textoInvestigacion").textContent = t.estado === "pendiente" ? "En cola…" : textoTrabajo(t);
                barra.setAttribute("aria-valuenow", String(t.progreso || 0));
                barra.firstElementChild.style.width = `${t.progreso || 0}%`;
            } });
            await terminar(final);
        } catch (err) {
            if (err.codigo !== "CANCELADO") avisarError($("#avisoInvestigacion"), err);
        } finally {
            caja.hidden = true;
            $("#btInvestigar").disabled = false;
            E.trabajoInvestigacion = null;
        }
    }

    async function terminar(t) {
        const avisoEl = $("#avisoInvestigacion");
        const r = t.resultado || {};
        if (t.estado === "cancelado") { avisar(avisoEl, "info", "Búsqueda cancelada. Tu apunte no cambió."); return; }
        if (t.estado === "fallido") {
            avisar(avisoEl, "error", `${(t.error && t.error.mensaje) || "La búsqueda falló."} Puedes seguir sin información complementaria.`,
                   [{ texto: "Ir al PDF", alHacer: () => ed.mostrarPestana("pdf") }]);
            return;
        }
        const partes = [];
        if (r.propuestas) partes.push(`${r.propuestas} complemento(s) nuevo(s) para revisar.`);
        if (r.sin_resultado) partes.push(`${r.sin_resultado} concepto(s) sin fuentes fiables: no se añadió nada para ellos.`);
        if (r.descartados) partes.push(`${r.descartados} resultado(s) descartados por contener instrucciones sospechosas.`);
        if (r.discrepancias) partes.push(`${r.discrepancias} parecen contradecir tu apunte: revísalos.`);
        if (t.estado === "parcial") partes.push("Algunos conceptos no se pudieron consultar.");
        if (r.aviso && !r.propuestas) partes.push(r.aviso);
        avisar(avisoEl, r.propuestas ? "exito" : "aviso", partes.join(" ") || "Búsqueda terminada.");
        await actualizarComplementos();
    }

    async function cancelar() {
        if (!E.trabajoInvestigacion) return;
        $("#btCancelarInvestigacion").disabled = true;
        try { await pedir(`/api/v2/trabajos/${E.trabajoInvestigacion}`, { method: "DELETE" }); }
        catch (err) { avisarError($("#avisoInvestigacion"), err); }
    }

    // Trae la versión nueva con los complementos sin perder cambios locales.
    async function actualizarComplementos() {
        if (ed.hayCambios()) {
            avisar($("#avisoComplementos"), "aviso", "Hay complementos nuevos en el servidor. Guarda tus cambios para verlos aquí.",
                   [{ texto: "Guardar y ver", alHacer: async () => { if (await ed.guardar({ sobrescribir: true })) await ed.recargar(); } }]);
            return;
        }
        await ed.recargar();
        ed.mostrarPestana("complementos");
    }

    // ---------------------------------------------------------------- complementos
    function pintarComplementos() {
        const lista = vaciar($("#listaComplementos"));
        const amp = (E.doc && E.doc.ampliaciones) || [];
        if (!amp.length) { lista.append(h("li", { class: "vacio", text: "Todavía no hay complementos." })); return; }
        const soloLectura = !ed.editable();
        for (const a of amp) {
            const f = a.fuente;
            const enlace = /^https:\/\//.test(f.url)
                ? h("a", { href: f.url, target: "_blank", rel: "noopener noreferrer", text: f.titulo })
                : h("span", { text: `${f.titulo} (enlace no verificable)` });
            lista.append(h("li", { class: `complemento estado-borde-${a.estado}`, "data-ampliacion": a.id },
                h("div", { class: "complemento__cabecera" },
                    h("h3", { text: a.concepto }),
                    h("span", { class: `estado-chip estado-${a.estado}`, text: ESTADOS[a.estado] || a.estado })),
                a.discrepancia ? h("p", { class: "aviso", "data-tipo": "aviso", role: "note", text: `Atención: ${a.discrepancia}` }) : null,
                h("blockquote", { class: "complemento__texto", text: a.texto }),
                h("p", { class: "complemento__fuente" }, "Fuente: ", enlace,
                  `. ${f.autor ? `${f.autor}. ` : ""}${f.proveedor}. Consultado el ${f.consultado}.${f.licencia ? ` Licencia ${f.licencia}.` : ""}`),
                soloLectura ? null : h("div", { class: "botones" },
                    h("button", { type: "button", class: "btn sm primary", dataset: { accion: "aceptar" }, disabled: a.estado === "aceptada",
                                  onclick: () => revisar(a, "aceptada"), text: "Aceptar" }),
                    h("button", { type: "button", class: "btn sm", dataset: { accion: "rechazar" }, disabled: a.estado === "rechazada",
                                  onclick: () => revisar(a, "rechazada"), text: "Descartar" }))));
        }
    }

    async function revisar(a, estado) {
        const avisoEl = $("#avisoComplementos");
        if (ed.hayCambios() && !await ed.guardar()) return;
        try {
            const r = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/ampliaciones/${encodeURIComponent(a.id)}`, {
                method: "PATCH", json: { estado }, headers: { "If-Match": String(E.version) } });
            E.version = r.version;
            E.apunte = r.apunte;
            E.doc.ampliaciones = r.apunte.documento.ampliaciones;
            E.guardado = ed.serializar(E.doc);
            ed.actualizarEstadoGuardado();
            E.alGuardar.forEach((fn) => fn({ tipo: "guardado", version: r.version }));
            avisar(avisoEl, "exito", estado === "aceptada" ? `«${a.concepto}» irá al PDF, citado.` : `«${a.concepto}» no irá al PDF.`);
            pintarComplementos();
            const boton = document.querySelector(`[data-ampliacion="${CSS.escape(a.id)}"] [data-accion=${estado === "aceptada" ? "rechazar" : "aceptar"}]`);
            if (boton) boton.focus();
        } catch (err) {
            avisarError(avisoEl, err, err.codigo === "CONFLICTO_VERSION" ? [{ texto: "Recargar", alHacer: () => ed.recargar() }] : []);
        }
    }

    async function cargarInfo() {
        try {
            const r = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/conceptos`);
            info = { disponible: r.disponible, proveedor: r.proveedor, conceptos: r.conceptos.slice(0, 12) };
        } catch (_) {
            info = { disponible: false, proveedor: "ninguno", conceptos: [] };
        }
        pintarFormulario();
    }

    ed.registrarPestana({ id: "complementos", titulo: "Complementos", orden: 20, crear,
                          pintar: () => { pintarComplementos(); },
                          alMostrar: () => { if (!info.cargado) { info.cargado = true; cargarInfo(); } pintarComplementos(); } });
    ed.alCargar((apunte) => {
        const t = apunte.ultimo_trabajo;
        cargarInfo().then(() => { info.cargado = true; });
        if (t && t.tipo === "investigacion" && ["pendiente", "procesando"].includes(t.estado)) {
            $("#chkInvestigar").checked = true;
            seguir(t);
        }
    });
})(window);
