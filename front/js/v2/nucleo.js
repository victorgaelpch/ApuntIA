// Núcleo común de las páginas con cuenta (FRONT-11, FRONT-17, FRONT-20).
//
// - pedir(): cliente de la API v2 (mismo origen, cookie de sesión HttpOnly y
//   cabecera X-CSRF-Token en lo que modifica datos). Lanza ErrorV2 con
//   {codigo, mensaje, status, detalles} del contrato {error:{codigo,mensaje}}.
// - h(): crea elementos con textContent. Nada que venga del servidor o del
//   usuario (OCR, citas, nombres de archivo…) se inserta como HTML.
// - El token CSRF vive solo en memoria: no se guarda en localStorage, en la URL
//   ni en cookies legibles por JS.
(function (global) {
    "use strict";
    const NS = (global.ApuntIA = global.ApuntIA || {});
    const doc = global.document;
    const sesion = { usuario: null, csrf: "" };

    // ------------------------------------------------------------------ DOM seguro
    function h(etiqueta, atributos = {}, ...hijos) {
        const el = doc.createElement(etiqueta);
        for (const [clave, valor] of Object.entries(atributos || {})) {
            if (valor === null || valor === undefined || valor === false) continue;
            if (clave === "class") el.className = valor;
            else if (clave === "text") el.textContent = valor;
            else if (clave === "dataset") Object.assign(el.dataset, valor);
            else if (clave.startsWith("on") && typeof valor === "function") el.addEventListener(clave.slice(2), valor);
            else if (clave === "hidden" || clave === "disabled" || clave === "checked" || clave === "selected" ||
                     clave === "required" || clave === "multiple") el[clave] = Boolean(valor);
            else if (clave === "value") el.value = valor;
            else el.setAttribute(clave, valor === true ? "" : String(valor));
        }
        for (const hijo of hijos.flat()) {
            if (hijo === null || hijo === undefined || hijo === false) continue;
            el.append(hijo instanceof global.Node ? hijo : doc.createTextNode(String(hijo)));
        }
        return el;
    }
    const $ = (sel, raiz = doc) => raiz.querySelector(sel);
    const vaciar = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };

    // ------------------------------------------------------------------ API
    class ErrorV2 extends Error {
        constructor({ codigo, mensaje = "", status = 0, detalles = null, tipo = "http" }) {
            super(`${codigo}${mensaje ? ": " + mensaje : ""}`);
            Object.assign(this, { name: "ErrorV2", codigo, mensaje, status, detalles, tipo });
        }
    }

    function base() {
        // Las páginas con cuenta deben servirse desde el backend (misma origen).
        return /^https?:$/.test(global.location.protocol) ? "" : null;
    }

    async function pedir(ruta, { method = "GET", json, form, headers = {}, signal, timeoutMs = 30000,
                                 crudo = false, sinAvisoSesion = false } = {}) {
        if (base() === null) {
            throw new ErrorV2({ codigo: "SERVIDOR_REQUERIDO", tipo: "red",
                mensaje: "Abre ApuntIA desde el servidor (por ejemplo http://localhost:8000/inicio) para usar tu cuenta." });
        }
        const cab = { Accept: "application/json", ...headers };
        let cuerpo;
        if (json !== undefined) { cab["Content-Type"] = "application/json"; cuerpo = JSON.stringify(json); }
        else if (form) cuerpo = form;
        if (!["GET", "HEAD"].includes(method) && sesion.csrf) cab["X-CSRF-Token"] = sesion.csrf;
        const control = new AbortController();
        let porTiempo = false;
        const reloj = setTimeout(() => { porTiempo = true; control.abort(); }, timeoutMs);
        if (signal) {
            if (signal.aborted) control.abort();
            else signal.addEventListener("abort", () => control.abort(), { once: true });
        }
        let r;
        try {
            r = await fetch(ruta, { method, headers: cab, body: cuerpo, credentials: "same-origin",
                                    signal: control.signal, cache: "no-store" });
        } catch (e) {
            if (porTiempo) throw new ErrorV2({ codigo: "TIEMPO_AGOTADO", tipo: "tiempo" });
            if (signal && signal.aborted) throw new ErrorV2({ codigo: "CANCELADO", tipo: "cancelado" });
            throw new ErrorV2({ codigo: "SIN_CONEXION", tipo: "red" });
        } finally {
            clearTimeout(reloj);
        }
        if (r.ok) {
            if (crudo) return r;
            if (r.status === 204) return null;
            try { return await r.json(); } catch (_) { throw new ErrorV2({ codigo: "RESPUESTA_INVALIDA", status: r.status }); }
        }
        let error = {};
        try { error = (await r.json()).error || {}; } catch (_) { /* cuerpo no JSON */ }
        const err = new ErrorV2({ codigo: error.codigo || (r.status >= 500 ? "ERROR_INTERNO" : "ERROR_CLIENTE"),
                                  mensaje: error.mensaje || "", status: r.status, detalles: error.detalles || null });
        if (r.status === 401 && !sinAvisoSesion) {
            olvidarSesion();
            const evento = new CustomEvent("apuntia:sesion-expirada", { cancelable: true, detail: err });
            if (global.dispatchEvent(evento)) irACuenta("expirada");
        }
        throw err;
    }

    // ------------------------------------------------------------------ sesión
    function olvidarSesion() { sesion.usuario = null; sesion.csrf = ""; }

    async function cargarSesion() {
        const r = await pedir("/api/v2/auth/estado", { sinAvisoSesion: true, timeoutMs: 8000 });
        if (r.autenticado) { sesion.usuario = r.usuario; sesion.csrf = r.csrf; } else olvidarSesion();
        return sesion.usuario;
    }

    function fijarSesion({ usuario, csrf }) { sesion.usuario = usuario; sesion.csrf = csrf; }

    function irACuenta(motivo) {
        const volver = global.location.pathname + global.location.search;
        const p = new URLSearchParams({ volver });
        if (motivo) p.set("motivo", motivo);
        global.location.assign(`/front/cuenta.html?${p}`);
    }

    // Para páginas privadas: si no hay sesión, a iniciar sesión (y volver luego).
    async function requerirSesion() {
        const usuario = await cargarSesion();
        if (!usuario) { irACuenta(); return new Promise(() => {}); }
        return usuario;
    }

    async function cerrarSesion() {
        try { await pedir("/api/v2/auth/sesion", { method: "DELETE", sinAvisoSesion: true }); } catch (_) { /* ya cerrada */ }
        olvidarSesion();
        global.location.assign("/front/cuenta.html?motivo=salida");
    }

    // ------------------------------------------------------------------ navegación
    const ENLACES = [
        { id: "nuevo", texto: "Crear apuntes", href: "/front/nuevo.html", privado: true },
        { id: "apuntes", texto: "Mis apuntes", href: "/front/apuntes.html", privado: true },
        { id: "perfil", texto: "Perfil", href: "/front/perfil.html", privado: true },
        { id: "mejorar", texto: "Mejorar una foto", href: "/inicio", privado: false },
        { id: "ayuda", texto: "Ayuda", href: "/front/ayuda.html", privado: false },
    ];

    function cabecera(activa) {
        const nav = $("#navPrincipal");
        if (!nav) return;
        vaciar(nav);
        for (const e of ENLACES) {
            if (e.privado && !sesion.usuario) continue;
            nav.append(h("a", { href: e.href, "aria-current": e.id === activa ? "page" : null, text: e.texto }));
        }
        if (sesion.usuario) {
            nav.append(h("button", { type: "button", class: "btn sm", id: "btSalir", onclick: cerrarSesion,
                                     title: `Sesión de ${sesion.usuario.nombre}`, text: "Salir" }));
        } else {
            nav.append(h("a", { href: "/front/cuenta.html", class: "btn sm primary", text: "Entrar" }));
        }
    }

    // ------------------------------------------------------------------ mensajes
    function textoDeError(error) {
        const m = NS.mensajes && NS.mensajes.CATALOGO && NS.mensajes.CATALOGO[error.codigo];
        if (m) return typeof m.texto === "function" ? m.texto(error) : m.texto;
        if (error.mensaje) return error.mensaje;   // mensajes del servidor: en español y para el usuario
        return "Algo salió mal. Vuelve a intentarlo.";
    }

    // tipo: info | exito | aviso | error. Las acciones son {texto, alHacer}.
    function avisar(region, tipo, texto, acciones = []) {
        if (!region) return;
        vaciar(region);
        region.dataset.tipo = tipo;
        region.setAttribute("role", tipo === "error" ? "alert" : "status");
        region.hidden = !texto;
        if (!texto) return;
        region.append(h("span", { class: "aviso__texto", text: texto }));
        if (acciones.length) {
            region.append(h("span", { class: "aviso__acciones" },
                acciones.map((a) => h("button", { type: "button", class: "btn sm", onclick: a.alHacer, text: a.texto }))));
        }
    }
    const avisarError = (region, error, acciones = []) => avisar(region, "error", textoDeError(error), acciones);

    function confirmar({ titulo, texto, aceptar = "Aceptar", peligro = false, escribir = null }) {
        return new Promise((resolver) => {
            const entrada = escribir ? h("input", { type: "text", id: "confirmarTexto", autocomplete: "off",
                                                    "aria-describedby": "confirmarAyuda" }) : null;
            const btOk = h("button", { type: "submit", class: `btn ${peligro ? "danger" : "primary"}`, text: aceptar,
                                       disabled: Boolean(escribir) });
            const dlg = h("dialog", { class: "dlg-app", "aria-labelledby": "confirmarTitulo" },
                h("form", { method: "dialog" },
                    h("h2", { id: "confirmarTitulo", text: titulo }),
                    h("p", { text: texto }),
                    escribir ? h("label", { for: "confirmarTexto", id: "confirmarAyuda",
                                            text: `Escribe «${escribir}» para confirmar` }) : null,
                    entrada,
                    h("div", { class: "dlg-app__botones" },
                        h("button", { type: "button", class: "btn", value: "no", text: "Cancelar",
                                      onclick: () => dlg.close("no") }),
                        btOk)));
            if (entrada) entrada.addEventListener("input", () => { btOk.disabled = entrada.value.trim() !== escribir; });
            btOk.value = "si";
            dlg.addEventListener("close", () => { resolver(dlg.returnValue === "si"); dlg.remove(); });
            doc.body.append(dlg);
            dlg.showModal();
            (entrada || btOk).focus();
        });
    }

    // ------------------------------------------------------------------ trabajos
    const TERMINALES = ["completado", "parcial", "fallido", "cancelado"];

    async function esperarTrabajo(id, { alAvanzar = () => {}, signal, intervaloMs = 700 } = {}) {
        for (;;) {
            const { trabajo } = await pedir(`/api/v2/trabajos/${encodeURIComponent(id)}`, { signal });
            alAvanzar(trabajo);
            if (TERMINALES.includes(trabajo.estado)) return trabajo;
            await new Promise((r, rechazar) => {
                const t = setTimeout(r, intervaloMs);
                if (signal) signal.addEventListener("abort", () => { clearTimeout(t); rechazar(new ErrorV2({ codigo: "CANCELADO", tipo: "cancelado" })); }, { once: true });
            });
        }
    }

    const ETAPAS = { validando: "Validando", preprocesando: "Preparando las fotos", ocr: "Leyendo el texto",
                     formulas: "Detectando fórmulas", estructurando: "Organizando el apunte",
                     investigando: "Consultando fuentes", maquetando: "Maquetando el PDF" };
    const ESTADOS = { pendiente: "En cola", procesando: "Procesando", listo: "Listo", parcial: "Parcial",
                      fallido: "Falló", cancelado: "Cancelado", completado: "Completado" };

    function chipEstado(estado) {
        return h("span", { class: `estado-chip estado-${estado}`, text: ESTADOS[estado] || estado });
    }

    function textoTrabajo(t) {
        if (t.estado === "procesando") return `${ETAPAS[t.etapa] || "Procesando"}… ${t.progreso || 0} %`;
        return ESTADOS[t.estado] || t.estado;
    }

    function fecha(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("es", { dateStyle: "medium", timeStyle: "short" });
    }

    NS.v2 = { h, $, vaciar, pedir, ErrorV2, sesion, cargarSesion, fijarSesion, requerirSesion, cerrarSesion,
              irACuenta, cabecera, avisar, avisarError, textoDeError, confirmar, esperarTrabajo, chipEstado,
              textoTrabajo, fecha, ESTADOS, ETAPAS, TERMINALES };
})(window);
