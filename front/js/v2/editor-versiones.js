// Versiones, guardado automático y comparación de cambios (FRONT-22).
//
// - Guardado automático opcional (activado por defecto) con espera de 4 s tras el
//   último cambio. Usa el mismo PUT con If-Match que el botón «Guardar»: solo se
//   muestra «Guardado» cuando responde el servidor. Se pausa sin conexión, con la
//   sesión caducada o tras un conflicto (409), que siempre decide la persona.
// - El historial lista las versiones del servidor; cualquiera se puede ver,
//   comparar con la actual (o con los cambios sin guardar) y restaurar. Restaurar
//   crea una versión nueva: no se borra nada.
// - La comparación distingue el texto reconocido en la foto, las correcciones y lo
//   añadido a mano, y muestra aparte los complementos externos.
// - No hay base de datos en el navegador: lo no guardado solo vive en la pestaña.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, $, vaciar, pedir, avisar, avisarError, confirmar, fecha } = NS.v2;
    const ed = NS.editor;
    const E = ed.E;
    const ESPERA_MS = 4000;
    const MOTIVOS = { creacion: "Creación", analisis: "Análisis de las fotos", edicion: "Edición", restauracion: "Restauración",
                      investigacion: "Complementos encontrados", ampliacion: "Revisión de complementos" };

    let reloj = null;
    const auto = { activo: true };

    // ---------------------------------------------------------------- guardado automático
    function programar() {
        clearTimeout(reloj);
        if (!auto.activo || E.conflicto || E.sesionCaducada || !ed.editable() || !ed.hayCambios()) return;
        if (navigator.onLine === false) return;  // se reintenta al volver la conexión
        reloj = setTimeout(async () => {
            if (!ed.hayCambios()) return;
            await ed.guardar();
        }, ESPERA_MS);
    }

    ed.alGuardar((evento) => {
        if (evento.tipo === "cambio") programar();
        if (evento.tipo === "guardado") pintarHistorial();
    });
    global.addEventListener("online", programar);
    global.addEventListener("pagehide", () => clearTimeout(reloj));

    ed.alCargar(() => {
        const cabecera = document.querySelector(".editor-cabecera");
        if ($("#chkAutoguardado")) return;
        const casilla = h("input", { type: "checkbox", id: "chkAutoguardado", checked: auto.activo,
                                     onchange: (e) => { auto.activo = e.target.checked; programar(); } });
        cabecera.insertBefore(h("span", { class: "casilla autoguardado" }, casilla,
                                h("label", { for: "chkAutoguardado", text: "Guardar automáticamente" })), $("#btGuardar"));
    });

    // ---------------------------------------------------------------- diferencias
    // Diferencia por palabras (LCS): [{tipo: "igual"|"quitado"|"anadido", texto}]
    function diferenciaPalabras(a, b) {
        // Cada palabra con su espacio final; se comparan sin espacios para que estos no
        // cuenten como coincidencias y mezclen las dos versiones.
        const trozos = (t) => (t || "").match(/\S+\s*|\s+/g) || [];
        const x = trozos(a), y = trozos(b);
        const igual = (p, q) => p.trim() === q.trim();
        if (x.length * y.length > 400000) return [{ tipo: "quitado", texto: a }, { tipo: "anadido", texto: b }];
        const m = x.length, n = y.length;
        const tabla = Array.from({ length: m + 1 }, () => new Uint32Array(n + 1));
        for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--) {
            tabla[i][j] = igual(x[i], y[j]) ? tabla[i + 1][j + 1] + 1 : Math.max(tabla[i + 1][j], tabla[i][j + 1]);
        }
        const partes = [];
        const empujar = (tipo, texto) => {
            const ultima = partes[partes.length - 1];
            if (ultima && ultima.tipo === tipo) ultima.texto += texto; else partes.push({ tipo, texto });
        };
        let i = 0, j = 0;
        while (i < m && j < n) {
            if (igual(x[i], y[j])) { empujar("igual", y[j]); i++; j++; }
            else if (tabla[i + 1][j] >= tabla[i][j + 1]) empujar("quitado", x[i++]);
            else empujar("anadido", y[j++]);
        }
        while (i < m) empujar("quitado", x[i++]);
        while (j < n) empujar("anadido", y[j++]);
        return partes;
    }

    function contenido(b) {
        if (!b) return "";
        if (b.tabla) return [b.tabla.encabezados.join(" | "), ...b.tabla.filas.map((f) => f.join(" | "))].join("\n");
        if (b.tipo === "formula") return b.latex ? `$${b.latex}$` : (b.texto || "");
        return b.texto || "";
    }

    function procedencia(b) {
        if (b.origen === "usuario") return "Añadido por ti";
        return contenido(b) !== (b.texto_original || "") && b.tipo !== "formula" && !b.tabla ? "Reconocido en la foto y corregido" : "Reconocido en la foto";
    }

    // Compara dos documentos bloque a bloque (por id) y devuelve un resumen pintable.
    function comparar(antes, despues) {
        const previos = new Map(antes.bloques.map((b) => [b.id, b]));
        const actuales = new Set(despues.bloques.map((b) => b.id));
        const filas = [];
        for (const b of despues.bloques) {
            const a = previos.get(b.id);
            if (!a) filas.push({ tipo: "anadido", bloque: b });
            else if (contenido(a) !== contenido(b) || a.tipo !== b.tipo) filas.push({ tipo: "cambiado", bloque: b, antes: a });
        }
        for (const a of antes.bloques) if (!actuales.has(a.id)) filas.push({ tipo: "quitado", bloque: a });
        const amp = new Map(antes.ampliaciones.map((x) => [x.id, x]));
        const ampliaciones = despues.ampliaciones
            .filter((x) => !amp.has(x.id) || amp.get(x.id).estado !== x.estado)
            .map((x) => ({ ampliacion: x, antes: amp.get(x.id) }));
        return { titulo: antes.titulo !== despues.titulo ? [antes.titulo, despues.titulo] : null, filas, ampliaciones };
    }

    function pintarComparacion(contenedor, cmp, { etiquetaAntes, etiquetaDespues }) {
        vaciar(contenedor);
        contenedor.append(h("p", { class: "ayuda", text: `Comparando «${etiquetaAntes}» con «${etiquetaDespues}». ` +
            "Tachado y en rojo: lo que se quita; subrayado y en verde: lo que se añade." }));
        if (!cmp.titulo && !cmp.filas.length && !cmp.ampliaciones.length) {
            contenedor.append(h("p", { class: "vacio", text: "No hay diferencias." }));
            return;
        }
        if (cmp.titulo) contenedor.append(h("p", {}, h("b", { text: "Título: " }), h("del", { text: cmp.titulo[0] }), " → ", h("ins", { text: cmp.titulo[1] })));
        const lista = h("ol", { class: "diferencias" });
        for (const f of cmp.filas) {
            const etiqueta = { anadido: "Bloque añadido", quitado: "Bloque quitado", cambiado: "Bloque cambiado" }[f.tipo];
            const cuerpo = h("div", { class: "diferencia__texto" });
            if (f.tipo === "cambiado") {
                diferenciaPalabras(contenido(f.antes), contenido(f.bloque)).forEach((p) =>
                    cuerpo.append(p.tipo === "igual" ? document.createTextNode(p.texto) : h(p.tipo === "anadido" ? "ins" : "del", { text: p.texto })));
            } else {
                cuerpo.append(h(f.tipo === "anadido" ? "ins" : "del", { text: contenido(f.bloque) || "(sin texto: imagen)" }));
            }
            lista.append(h("li", { class: `diferencia diferencia--${f.tipo}`, "data-bloque": f.bloque.id },
                h("p", { class: "diferencia__cabecera" }, h("b", { text: etiqueta }), " · ",
                  h("span", { text: `${ed.TIPOS[f.bloque.tipo] || f.bloque.tipo} · ${procedencia(f.bloque)}` })),
                cuerpo));
        }
        contenedor.append(lista);
        if (cmp.ampliaciones.length) {
            contenedor.append(h("h3", { text: "Complementos externos (no forman parte de tu apunte)" }),
                h("ul", {}, cmp.ampliaciones.map(({ ampliacion: a, antes }) => h("li", {
                    text: `${a.concepto} (${a.fuente.titulo}): ${antes ? `${antes.estado} → ${a.estado}` : `nuevo, ${a.estado}`}` }))));
        }
    }

    // ---------------------------------------------------------------- historial
    let versiones = [];
    function crear(panel) {
        panel.append(
            h("div", { class: "tarjeta" },
                h("h2", { text: "Historial de versiones" }),
                h("p", { class: "ayuda", text: "Cada vez que se guarda se crea una versión. Restaurar una antigua crea otra nueva: no se pierde nada." }),
                h("div", { class: "aviso", id: "avisoVersiones", hidden: true }),
                h("ol", { class: "versiones", id: "listaVersiones", "aria-label": "Versiones, de la más reciente a la más antigua" })),
            h("div", { class: "tarjeta", id: "cajaComparacion", hidden: true, tabindex: "-1", "aria-labelledby": "tituloComparacion" },
                h("h2", { id: "tituloComparacion", text: "Comparación" }),
                h("div", { id: "comparacion", "aria-live": "polite" })));
    }

    async function pintarHistorial() {
        const lista = $("#listaVersiones");
        if (!lista) return;
        try {
            versiones = (await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/versiones`)).versiones;
        } catch (err) {
            avisarError($("#avisoVersiones"), err, [{ texto: "Reintentar", alHacer: pintarHistorial }]);
            return;
        }
        vaciar(lista);
        for (const v of versiones) {
            const actual = v.numero === E.version;
            lista.append(h("li", { class: "version", "data-version": String(v.numero), "aria-current": actual ? "true" : null },
                h("span", { class: "version__datos" },
                    h("b", { text: `Versión ${v.numero}` }), actual ? h("span", { class: "estado-chip estado-listo", text: "Actual" }) : null,
                    h("span", { text: ` · ${MOTIVOS[v.motivo] || v.motivo} · ${fecha(v.creado)}` })),
                h("span", { class: "botones" },
                    h("button", { type: "button", class: "btn sm", dataset: { accion: "comparar" }, onclick: () => compararVersion(v.numero),
                                  text: actual ? (ed.hayCambios() ? "Ver mis cambios sin guardar" : "Ver") : "Comparar con la actual" }),
                    actual ? null : h("button", { type: "button", class: "btn sm", dataset: { accion: "restaurar" }, disabled: !ed.editable(),
                                                  onclick: () => restaurar(v.numero), text: "Restaurar" }),
                    E.extrasVersion ? E.extrasVersion(v) : null)));
        }
    }

    async function documentoVersion(numero) {
        return (await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/versiones/${numero}`)).documento;
    }

    async function compararVersion(numero) {
        const caja = $("#cajaComparacion");
        try {
            const antiguo = await documentoVersion(numero);
            const actualGuardado = numero === E.version ? antiguo : await documentoVersion(E.version);
            const despues = ed.hayCambios() ? E.doc : actualGuardado;
            pintarComparacion($("#comparacion"), comparar(antiguo, despues), {
                etiquetaAntes: `versión ${numero}`,
                etiquetaDespues: ed.hayCambios() ? "lo que tienes ahora (sin guardar)" : `versión ${E.version} (actual)` });
            caja.hidden = false;
            caja.focus();
        } catch (err) {
            avisarError($("#avisoVersiones"), err);
        }
    }

    async function restaurar(numero) {
        const texto = ed.hayCambios()
            ? `Tienes cambios sin guardar que se perderán. Se creará una versión nueva igual a la ${numero}.`
            : `Se creará una versión nueva igual a la ${numero}. La actual seguirá en el historial.`;
        if (!await confirmar({ titulo: `¿Restaurar la versión ${numero}?`, texto, aceptar: "Restaurar" })) return;
        try {
            const r = await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}/versiones/${numero}/restaurar`, { method: "POST" });
            await ed.recargar();
            avisar($("#avisoVersiones"), "exito", `Restaurada: ahora la versión ${r.version} es igual a la ${numero}.`);
            pintarHistorial();
        } catch (err) {
            avisarError($("#avisoVersiones"), err);
        }
    }

    // En un conflicto (409): comparar lo guardado por otra pestaña con lo que hay aquí.
    E.compararConflicto = async () => {
        try {
            const servidor = (await pedir(`/api/v2/apuntes/${encodeURIComponent(E.id)}`)).apunte;
            ed.mostrarPestana("versiones");
            pintarComparacion($("#comparacion"), comparar(servidor.documento, E.doc), {
                etiquetaAntes: `versión ${servidor.version} guardada en otra pestaña`, etiquetaDespues: "tus cambios sin guardar" });
            $("#cajaComparacion").hidden = false;
            $("#cajaComparacion").focus();
        } catch (err) {
            avisarError($("#avisoEditor"), err);
        }
    };

    ed.registrarPestana({ id: "versiones", titulo: "Versiones", orden: 40, crear, pintar: pintarHistorial, alMostrar: pintarHistorial });
    NS.editorVersiones = { diferenciaPalabras, comparar, auto };
})(window);
