// Fórmulas, tablas y esquemas en el editor (FRONT-14).
//
// Vista previa de fórmulas: la dibuja el servidor (POST /api/v2/formulas/validar)
// con el MISMO motor que el PDF (mathtext de matplotlib, lista blanca de comandos).
// Se eligió frente a KaTeX/MathJax porque: lo que se ve es exactamente lo que saldrá
// en el PDF, no hace falta cargar scripts de un CDN (la CSP solo permite los
// propios) y el navegador nunca interpreta macros LaTeX ni HTML del usuario: recibe
// una imagen PNG.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, vaciar, pedir, textoDeError } = NS.v2;
    const ed = NS.editor;
    const MAX_COLUMNAS = 30, MAX_FILAS = 500;

    // ---------------------------------------------------------------- fórmulas
    function renderFormula(b, cuerpo, { soloLectura, n, urlArchivo, marcarCambio }) {
        if (b.recorte) {
            cuerpo.append(h("figure", { class: "formula-original" },
                h("img", { class: "bloque__recorte", src: urlArchivo(b.recorte), alt: `Fórmula original del bloque ${n}`, loading: "lazy" }),
                h("figcaption", { text: "En la foto" })));
        }
        const idLatex = `latex-${b.id}`;
        const area = h("textarea", { id: idLatex, class: "latex", rows: "2", spellcheck: "false", autocapitalize: "off",
                                     readonly: soloLectura ? "" : null, "aria-describedby": `estado-${b.id}` });
        area.value = b.latex || "";
        const vista = h("div", { class: "formula-vista", id: `vista-${b.id}`, "aria-live": "polite" });
        const estado = h("p", { class: "formula-estado", id: `estado-${b.id}`, role: "status" });
        const lineal = h("input", { type: "text", id: `lineal-${b.id}`, placeholder: "Por ejemplo: x^2 + 1/2 o sqrt(x+1)",
                                    disabled: soloLectura });
        cuerpo.append(
            h("label", { for: idLatex, text: `LaTeX de la fórmula ${n}` }), area,
            h("details", { class: "formula-ayuda" },
                h("summary", { text: "Escribirla en texto normal" }),
                h("div", { class: "con-boton" }, lineal,
                    h("button", { type: "button", class: "btn sm", disabled: soloLectura, text: "Convertir",
                                  onclick: () => convertir(lineal.value) })),
                h("p", { class: "ayuda", text: "Se admiten fracciones (\\frac), raíces (\\sqrt), potencias (^), subíndices (_), letras griegas y símbolos comunes. Sin comandos como \\input o \\def." })),
            h("div", { class: "formula-previa" }, h("span", { class: "ayuda", text: "Vista previa (igual que en el PDF):" }), vista),
            estado);
        let reloj = null, ultimo = null;

        async function validar(cuerpoPeticion, actualizarTexto) {
            const control = (validar.control && validar.control.abort(), (validar.control = new AbortController()));
            estado.textContent = "Comprobando…";
            estado.dataset.tipo = "info";
            try {
                const r = await pedir("/api/v2/formulas/validar", { method: "POST", json: cuerpoPeticion, signal: control.signal });
                if (actualizarTexto && r.latex) { area.value = r.latex; b.latex = r.latex; tocada = true; }
                pintarResultado(r.valida, r.vista_previa, r.errores);
            } catch (err) {
                if (err.codigo === "CANCELADO") return;
                pintarResultado(false, null, [textoDeError(err)]);
            }
        }

        let tocada = false;  // solo una edición del usuario cambia latex_valido (la carga no ensucia el documento)
        function pintarResultado(valida, imagen, errores) {
            if (tocada) { b.latex_valido = valida; marcarCambio(); }
            vaciar(vista);
            if (imagen) vista.append(h("img", { src: imagen, alt: `Vista previa de la fórmula ${n}: ${b.latex}` }));
            else vista.append(h("span", { class: "ayuda", text: "Sin vista previa." }));
            estado.dataset.tipo = valida ? "exito" : "error";
            estado.textContent = valida ? "Fórmula válida." : `No se puede dibujar: ${(errores || []).join(" ")} En el PDF se usará la imagen original.`;
            area.setAttribute("aria-invalid", String(!valida));
        }

        function convertir(texto) {
            if (texto.trim()) validar({ texto: texto.trim() }, true);
        }

        area.addEventListener("input", () => {
            b.latex = area.value;
            tocada = true;
            marcarCambio();
            clearTimeout(reloj);
            reloj = setTimeout(() => {
                if (area.value.trim() && area.value !== ultimo) { ultimo = area.value; validar({ latex: area.value }); }
            }, 450);
        });
        if (b.latex) validar({ latex: b.latex });
        else pintarResultado(false, null, ["No se reconoció la fórmula; escríbela o conserva la imagen."]);
        if (b.recorte && !soloLectura) {
            const id = `conservar-${b.id}`;
            cuerpo.append(h("div", { class: "casilla" },
                h("input", { type: "checkbox", id, checked: b.conservar_imagen, onchange: (e) => { b.conservar_imagen = e.target.checked; marcarCambio(); } }),
                h("label", { for: id, text: "Usar la imagen original en lugar de la fórmula escrita" })));
        }
    }

    // ---------------------------------------------------------------- tablas
    function renderTabla(b, cuerpo, { soloLectura, n, marcarCambio }) {
        if (!b.tabla) b.tabla = { encabezados: ["Columna 1"], filas: [[""]] };
        const t = b.tabla;
        const rejilla = h("div", { class: "tabla-editable", role: "group", "aria-label": `Tabla del bloque ${n}` });
        function pintar(enfocar) {
            vaciar(rejilla);
            const tabla = h("table", {},
                h("caption", { class: "sr-only", text: `Tabla del bloque ${n}: ${t.filas.length} filas y ${t.encabezados.length} columnas` }),
                h("thead", {}, h("tr", {}, h("th", { scope: "col", class: "sr-only", text: "Fila" }),
                    t.encabezados.map((e, c) => h("th", { scope: "col" },
                        celda(e, `Encabezado de la columna ${c + 1}`, (v) => { t.encabezados[c] = v; }, `c${c}`),
                        soloLectura ? null : h("button", { type: "button", class: "btn sm quitar", disabled: t.encabezados.length === 1,
                            "aria-label": `Quitar la columna ${c + 1}`, text: "×",
                            onclick: () => { t.encabezados.splice(c, 1); t.filas.forEach((f) => f.splice(c, 1)); marcarCambio(); pintar(); } }))))),
                h("tbody", {}, t.filas.map((fila, f) => h("tr", {},
                    h("th", { scope: "row" }, String(f + 1),
                        soloLectura ? null : h("button", { type: "button", class: "btn sm quitar", "aria-label": `Quitar la fila ${f + 1}`, text: "×",
                            onclick: () => { t.filas.splice(f, 1); marcarCambio(); pintar(); } })),
                    fila.map((v, c) => h("td", {}, celda(v, `Fila ${f + 1}, ${t.encabezados[c] || `columna ${c + 1}`}`, (nv) => { fila[c] = nv; }, `f${f}c${c}`)))))));
            rejilla.append(h("div", { class: "tabla-scroll" }, tabla));
            if (!soloLectura) {
                rejilla.append(h("div", { class: "botones" },
                    h("button", { type: "button", class: "btn sm", dataset: { accion: "fila" }, disabled: t.filas.length >= MAX_FILAS,
                                  onclick: () => { t.filas.push(t.encabezados.map(() => "")); marcarCambio(); pintar(`f${t.filas.length - 1}c0`); }, text: "+ Fila" }),
                    h("button", { type: "button", class: "btn sm", dataset: { accion: "columna" }, disabled: t.encabezados.length >= MAX_COLUMNAS,
                                  onclick: () => { t.encabezados.push(`Columna ${t.encabezados.length + 1}`); t.filas.forEach((fila) => fila.push("")); marcarCambio(); pintar(`c${t.encabezados.length - 1}`); },
                                  text: "+ Columna" })));
            }
            if (enfocar) { const el = rejilla.querySelector(`[data-celda="${enfocar}"]`); if (el) el.focus(); }
        }
        function celda(valor, etiqueta, guardar, clave) {
            const input = h("input", { type: "text", value: valor, "aria-label": etiqueta, readonly: soloLectura ? "" : null,
                                       maxlength: "2000", dataset: { celda: clave } });
            input.addEventListener("input", () => { guardar(input.value); marcarCambio(); });
            return input;
        }
        pintar();
        cuerpo.append(rejilla);
    }

    // Texto con columnas separadas por «|» o tabuladores → tabla.
    function textoATabla(texto) {
        const lineas = (texto || "").split("\n").map((l) => l.trim()).filter(Boolean);
        const separador = lineas.some((l) => l.includes("|")) ? "|" : "\t";
        const filas = lineas.map((l) => l.split(separador).map((c) => c.trim()).filter((c, i, a) => !(c === "" && (i === 0 || i === a.length - 1))));
        const columnas = Math.max(1, ...filas.map((f) => f.length));
        const normal = filas.map((f) => Array.from({ length: columnas }, (_, i) => f[i] || ""));
        const [encabezados, ...resto] = normal.length ? normal : [[""]];
        return { encabezados: encabezados.map((e, i) => e || `Columna ${i + 1}`), filas: resto };
    }

    // ---------------------------------------------------------------- esquemas e imágenes
    function renderImagen(b, cuerpo, { soloLectura, n, urlArchivo, marcarCambio }) {
        if (b.recorte) {
            cuerpo.append(h("img", { class: "bloque__recorte bloque__recorte--grande", src: urlArchivo(b.recorte),
                                     alt: `Esquema o dibujo del bloque ${n}`, loading: "lazy" }));
        }
        cuerpo.append(h("p", { class: "ayuda", text: "Los esquemas y dibujos se incluyen en el PDF como la imagen original: ApuntIA no los redibuja, para no inventar relaciones que no están en tu apunte." }));
        const id = `desc-${b.id}`;
        const area = h("textarea", { id, rows: "2", readonly: soloLectura ? "" : null, placeholder: "Descripción opcional (por ejemplo, qué representa el esquema)" });
        area.value = b.texto || "";
        area.addEventListener("input", () => { b.texto = area.value; marcarCambio(); });
        cuerpo.append(h("label", { for: id, text: `Descripción del esquema ${n}` }), area);
    }

    ed.registrarTipo("formula", renderFormula);
    ed.registrarTipo("tabla", renderTabla);
    ed.registrarTipo("imagen", renderImagen);

    // «Convertir en tabla» para textos con columnas.
    ed.registrarAccionBloque((b) => {
        if (!["texto", "manuscrito"].includes(b.tipo)) return null;
        return h("button", { type: "button", class: "btn sm", dataset: { accion: "a-tabla" }, text: "Convertir en tabla", title: "Cada línea es una fila; separa las columnas con | o con tabuladores",
                             onclick: () => { b.tabla = textoATabla(b.texto); b.tipo = "tabla"; ed.marcarCambio(); ed.pintarBloques(); } });
    });

    // Botones para añadir fórmulas y tablas a mano.
    ed.alCargar(() => {
        const extra = document.getElementById("botonesAnadirExtra");
        if (!extra || extra.childElementCount) return;
        extra.append(
            h("button", { type: "button", class: "btn", id: "btAnadirFormula", text: "+ Añadir fórmula",
                          onclick: () => ed.anadirBloque("formula", { latex: "", latex_valido: false }) }),
            h("button", { type: "button", class: "btn", id: "btAnadirTabla", text: "+ Añadir tabla",
                          onclick: () => ed.anadirBloque("tabla", { tabla: { encabezados: ["Columna 1", "Columna 2"], filas: [["", ""]] } }) }));
    });

    NS.editorContenido = { textoATabla };
})(window);
