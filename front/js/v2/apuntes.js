// Panel «Mis apuntes» (FRONT-18).
//
// - Lista paginada del servidor (solo los apuntes de la sesión: el backend filtra por
//   propietario), con búsqueda, estado, fuente, fechas y orden.
// - Los filtros viven en la URL (?q=…&pagina=…) para volver al mismo punto desde el
//   editor; la posición de desplazamiento se recuerda solo en esta pestaña.
// - No se cargan imágenes privadas en la lista: el detalle se abre en el editor.
// - Acciones según el estado: abrir, ver el progreso, reintentar, PDF y eliminar con
//   confirmación.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { h, $, vaciar, pedir, requerirSesion, cabecera, avisar, avisarError, confirmar, chipEstado, fecha } = NS.v2;
    const POR_PAGINA = 12;
    const FUENTES = { pizarron: "Pizarrón", cuaderno: "Cuaderno", mixto: "Pizarrón y cuaderno" };
    const CAMPOS = { q: "#inpBuscar", estado: "#selEstado", tipo_fuente: "#selFuente", desde: "#inpDesde", hasta: "#inpHasta", orden: "#selOrden" };
    const aviso = () => $("#avisoLista");
    let filtros = {};
    let total = 0;

    function leerUrl() {
        const p = new URLSearchParams(location.search);
        filtros = { pagina: Math.max(1, Number(p.get("pagina")) || 1) };
        for (const [clave, sel] of Object.entries(CAMPOS)) {
            filtros[clave] = p.get(clave) || "";
            $(sel).value = filtros[clave] || (clave === "orden" ? "reciente" : "");
        }
    }

    function escribirUrl() {
        const p = new URLSearchParams();
        for (const [clave, valor] of Object.entries(filtros)) if (valor && !(clave === "pagina" && valor === 1) && !(clave === "orden" && valor === "reciente")) p.set(clave, valor);
        history.replaceState(null, "", `${location.pathname}${p.toString() ? `?${p}` : ""}`);
    }

    function hayFiltros() { return Boolean(filtros.q || filtros.estado || filtros.tipo_fuente || filtros.desde || filtros.hasta); }

    // ---------------------------------------------------------------- cargar
    async function cargar({ restaurarScroll = false } = {}) {
        const lista = $("#listaApuntes");
        lista.setAttribute("aria-busy", "true");
        vaciar(lista);
        for (let i = 0; i < 3; i++) lista.append(h("li", { class: "esqueleto", "aria-hidden": "true" }));
        const p = new URLSearchParams({ pagina: String(filtros.pagina), por_pagina: String(POR_PAGINA), orden: filtros.orden || "reciente" });
        for (const clave of ["q", "estado", "tipo_fuente", "desde", "hasta"]) if (filtros[clave]) p.set(clave, filtros[clave]);
        try {
            const r = await pedir(`/api/v2/apuntes?${p}`);
            total = r.total;
            const paginas = Math.max(1, Math.ceil(total / POR_PAGINA));
            if (filtros.pagina > paginas && total) { filtros.pagina = paginas; escribirUrl(); return cargar(); }
            avisar(aviso(), "info", "");
            pintar(r.elementos);
            pintarPaginacion(paginas);
            $("#resumenLista").textContent = total === 0 ? (hayFiltros() ? "Ningún apunte coincide." : "Todavía no tienes apuntes.")
                : `${total} ${total === 1 ? "apunte" : "apuntes"}${hayFiltros() ? " con estos filtros" : ""}.`;
            if (restaurarScroll) {
                let y = 0;
                try { y = Number(sessionStorage.getItem("apuntia:scroll-apuntes") || 0); } catch (_) { /* sin almacenamiento */ }
                if (y) global.scrollTo(0, y);
            }
        } catch (err) {
            vaciar(lista);
            $("#paginacion").hidden = true;
            avisarError(aviso(), err, [{ texto: "Reintentar", alHacer: () => cargar() }]);
        } finally {
            lista.setAttribute("aria-busy", "false");
        }
    }

    function pintarPaginacion(paginas) {
        $("#paginacion").hidden = paginas <= 1;
        $("#textoPaginacion").textContent = `Página ${filtros.pagina} de ${paginas}`;
        $("#btAnterior").disabled = filtros.pagina <= 1;
        $("#btSiguiente").disabled = filtros.pagina >= paginas;
    }

    // ---------------------------------------------------------------- tarjetas
    function pintar(elementos) {
        const lista = vaciar($("#listaApuntes"));
        if (!elementos.length) {
            lista.append(h("li", { class: "vacio" }, hayFiltros()
                ? [h("p", { text: "No hay apuntes que coincidan con la búsqueda." }),
                   h("button", { type: "button", class: "btn", onclick: limpiar, text: "Limpiar filtros" })]
                : [h("p", { text: "Aún no has creado ningún apunte. Sube las fotos de un pizarrón o de tu cuaderno para empezar." }),
                   h("a", { class: "btn primary", href: "/front/nuevo.html", text: "Crear mi primer apunte" })]));
            return;
        }
        for (const a of elementos) lista.append(tarjeta(a));
    }

    function tarjeta(a) {
        const editor = `/front/editor.html?id=${encodeURIComponent(a.id)}`;
        const enCurso = ["pendiente", "procesando"].includes(a.estado);
        const acciones = [
            h("a", { class: "btn sm primary", href: editor, dataset: { accion: "abrir" },
                     text: enCurso ? "Ver progreso" : a.estado === "fallido" || a.estado === "cancelado" ? "Revisar y reintentar" : "Abrir y editar" }),
        ];
        if (!enCurso && a.estado !== "fallido" && a.estado !== "cancelado") {
            acciones.push(h("a", { class: "btn sm", href: `${editor}#pdf`, dataset: { accion: "exportar" }, text: "Exportar PDF" }));
        }
        if (a.pdfs > 0) {
            acciones.push(h("button", { type: "button", class: "btn sm", dataset: { accion: "descargar" }, text: "Descargar último PDF",
                                        onclick: (e) => descargarUltimo(a, e.currentTarget) }));
        }
        acciones.push(h("button", { type: "button", class: "btn sm danger", dataset: { accion: "eliminar" }, text: "Eliminar",
                                    "aria-label": `Eliminar «${a.titulo}»`, onclick: () => eliminar(a) }));
        return h("li", { class: "apunte", "data-apunte": a.id },
            h("h2", {}, h("a", { href: editor, text: a.titulo })),
            h("p", { class: "apunte__datos" }, chipEstado(a.estado),
              h("span", { text: FUENTES[a.tipo_fuente] || a.tipo_fuente }),
              h("span", { text: `${a.paginas} ${a.paginas === 1 ? "página" : "páginas"}` }),
              h("span", { text: `${a.pdfs} PDF` })),
            h("p", { class: "apunte__datos" }, h("span", { text: `Creado: ${fecha(a.creado)}` }), h("span", { text: `Modificado: ${fecha(a.actualizado)}` })),
            h("div", { class: "botones" }, acciones));
    }

    async function descargarUltimo(a, boton) {
        boton.disabled = true;
        try {
            const { exportaciones } = await pedir(`/api/v2/apuntes/${encodeURIComponent(a.id)}/exportaciones`);
            const ultima = exportaciones.find((x) => x.estado === "completado");
            if (!ultima) throw new NS.v2.ErrorV2({ codigo: "NO_ENCONTRADO", mensaje: "Este apunte ya no tiene PDF. Ábrelo para generar uno.", status: 404 });
            const r = await pedir(ultima.descarga, { crudo: true, timeoutMs: 60000, headers: { Accept: "application/pdf" } });
            const nombre = (/filename="([^"]+)"/.exec(r.headers.get("Content-Disposition") || "") || [])[1] || "apunte.pdf";
            const url = URL.createObjectURL(await r.blob());
            const enlace = h("a", { href: url, download: nombre, hidden: true });
            document.body.append(enlace);
            enlace.click();
            enlace.remove();
            setTimeout(() => URL.revokeObjectURL(url), 30000);
            avisar(aviso(), "exito", `Descargando «${nombre}» (versión ${ultima.version}${ultima.version !== a.version ? ", anterior a la actual" : ""}).`);
        } catch (err) {
            avisarError(aviso(), err);
        } finally {
            boton.disabled = false;
        }
    }

    async function eliminar(a) {
        const ok = await confirmar({ titulo: `¿Eliminar «${a.titulo}»?`, peligro: true, aceptar: "Eliminar",
            texto: "Se borrarán sus fotos, todas sus versiones y sus PDF. No se puede deshacer." });
        if (!ok) return;
        try {
            await pedir(`/api/v2/apuntes/${encodeURIComponent(a.id)}`, { method: "DELETE" });
            await cargar();
            avisar(aviso(), "exito", `«${a.titulo}» se eliminó.`);
            $("#inpBuscar").focus();
        } catch (err) {
            if (err.status === 404) { await cargar(); avisar(aviso(), "info", "Ese apunte ya no existía."); }
            else avisarError(aviso(), err);
        }
    }

    // ---------------------------------------------------------------- filtros
    function aplicar(e) {
        if (e) e.preventDefault();
        for (const [clave, sel] of Object.entries(CAMPOS)) filtros[clave] = $(sel).value.trim();
        if (filtros.desde && filtros.hasta && filtros.desde > filtros.hasta) {
            avisar(aviso(), "error", "La fecha «Desde» es posterior a «Hasta».");
            $("#inpDesde").focus();
            return;
        }
        filtros.pagina = 1;
        escribirUrl();
        cargar();
    }

    function limpiar() {
        for (const sel of Object.values(CAMPOS)) $(sel).value = sel === "#selOrden" ? "reciente" : "";
        aplicar();
    }

    function irA(delta) {
        filtros.pagina += delta;
        escribirUrl();
        cargar();
        $("#listaApuntes").scrollIntoView({ block: "start" });
    }

    async function iniciar() {
        await requerirSesion();
        cabecera("apuntes");
        leerUrl();
        $("#formFiltros").addEventListener("submit", aplicar);
        ["#selEstado", "#selFuente", "#selOrden", "#inpDesde", "#inpHasta"].forEach((s) => $(s).addEventListener("change", aplicar));
        $("#btLimpiar").addEventListener("click", limpiar);
        $("#btAnterior").addEventListener("click", () => irA(-1));
        $("#btSiguiente").addEventListener("click", () => irA(1));
        global.addEventListener("pagehide", () => {
            try { sessionStorage.setItem("apuntia:scroll-apuntes", String(Math.round(global.scrollY))); } catch (_) { /* sin almacenamiento */ }
        });
        await cargar({ restaurarScroll: true });
    }
    iniciar();
})(window);
