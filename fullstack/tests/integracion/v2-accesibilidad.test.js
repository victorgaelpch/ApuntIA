// FRONT-21: accesibilidad y responsive de todas las pantallas (Chromium, backend real).
// Comprobaciones automáticas: idioma, un h1, landmarks, etiquetas, nombres accesibles,
// alt, ids únicos y referencias ARIA válidas, contraste de texto (WCAG AA), foco visible
// con teclado, diálogos y sin desbordamiento horizontal a 320, 768 y 1280 px.
// Con CAPTURAS=carpeta se guardan capturas de cada pantalla y ancho para revisarlas.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte } = require("./v2-apuntes-ayuda");

const CAPTURAS = process.env.CAPTURAS ? path.resolve(process.env.CAPTURAS) : null;
const ANCHOS = [320, 768, 1280];

// Se ejecuta en la página: devuelve la lista de problemas encontrados.
function auditar() {
    const problemas = [];
    const visible = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
    const nombre = (e) => (e.getAttribute("aria-label") || (e.getAttribute("aria-labelledby") || "").split(/\s+/).map((id) => (document.getElementById(id) || {}).textContent || "").join(" ")
        || (e.labels && [...e.labels].map((l) => l.textContent).join(" ")) || e.textContent || e.getAttribute("title") || e.getAttribute("alt") || "").trim();
    const desc = (e) => `${e.tagName.toLowerCase()}${e.id ? "#" + e.id : ""}${e.className && typeof e.className === "string" ? "." + e.className.split(" ")[0] : ""}`;

    if (document.documentElement.lang !== "es") problemas.push("html sin lang=es");
    if (document.querySelectorAll("h1").length !== 1) problemas.push(`${document.querySelectorAll("h1").length} h1`);
    if (!document.querySelector("main")) problemas.push("sin <main>");
    for (const e of document.querySelectorAll("input:not([type=hidden]), select, textarea")) {
        if (e.getAttribute("aria-hidden") === "true" || e.tabIndex < 0) continue;
        if (!nombre(e) || nombre(e) === e.value) problemas.push(`control sin etiqueta: ${desc(e)}`);
    }
    for (const e of document.querySelectorAll("button, a[href], [role=tab]")) if (visible(e) && !nombre(e)) problemas.push(`sin nombre accesible: ${desc(e)}`);
    for (const e of document.querySelectorAll("img")) if (!e.hasAttribute("alt")) problemas.push(`img sin alt: ${desc(e)}`);
    const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
    for (const id of new Set(ids.filter((x, i) => ids.indexOf(x) !== i))) problemas.push(`id repetido: ${id}`);
    for (const e of document.querySelectorAll("[aria-labelledby], [aria-describedby], [aria-controls]")) {
        for (const atr of ["aria-labelledby", "aria-describedby", "aria-controls"]) {
            for (const id of (e.getAttribute(atr) || "").split(/\s+/).filter(Boolean)) if (!document.getElementById(id)) problemas.push(`${atr} roto en ${desc(e)}: ${id}`);
        }
    }
    // Contraste (WCAG AA): 4.5:1, o 3:1 para texto grande.
    // rgb()/rgba() en 0-255, o color(srgb …) en 0-1 (así devuelve Chromium los color-mix()).
    const rgb = (c) => {
        const n = (c.match(/[\d.]+/g) || []).map(Number);
        if (/^color\(srgb/.test(c)) return n.map((v, i) => (i < 3 ? v * 255 : v));
        return n;
    };
    const lum = ([r, g, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    function fondo(e) {
        for (let n = e; n; n = n.parentElement) {
            const s = getComputedStyle(n);
            if (s.backgroundImage !== "none" && !/^url/.test(s.backgroundImage)) return null;  // degradado: no se puede calcular
            const c = rgb(s.backgroundColor);
            if (c.length === 3 || (c.length === 4 && c[3] >= 0.9)) return c.slice(0, 3);
            if (c.length === 4 && c[3] > 0.05) return null;  // semitransparente: no se puede calcular con fiabilidad
        }
        return [255, 255, 255];
    }
    for (const e of document.querySelectorAll("p, span, label, a, button, h1, h2, h3, td, th, li, small, legend, summary, figcaption, option")) {
        if (!visible(e) || !e.childNodes.length || ![...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
        if (e.closest("[disabled], .region, .visor__marco, video, .pane__frame, .viewfinder")) continue;
        const s = getComputedStyle(e);
        if (parseFloat(s.opacity) < 1) continue;
        const f = fondo(e);
        if (!f) continue;
        const c = rgb(s.color).slice(0, 3);
        const [a, b] = [lum(c) + 0.05, lum(f) + 0.05];
        const ratio = Math.max(a, b) / Math.min(a, b);
        const grande = parseFloat(s.fontSize) >= 24 || (parseFloat(s.fontSize) >= 18.66 && Number(s.fontWeight) >= 700);
        if (ratio < (grande ? 3 : 4.5)) problemas.push(`contraste ${ratio.toFixed(2)} en ${desc(e)}: «${e.textContent.trim().slice(0, 40)}»`);
    }
    return problemas;
}

describe("FRONT-21 accesibilidad y responsive", () => {
    let navegador, backend, cuentaCtx, idApunte;
    before(async () => {
        navegador = await chromium.launch();
        backend = await iniciarBackendV2();
        cuentaCtx = await navegador.newContext();
        const pagina = await cuentaCtx.newPage();
        await registrar(cuentaCtx, backend.url, { email: "a11y@example.com" });
        idApunte = (await crearApunte(cuentaCtx, backend.url, pagina, { cuenta: await (await cuentaCtx.request.get(`${backend.url}/api/v2/auth/estado`)).json() })).id;
        await pagina.close();
    });
    after(async () => { await cuentaCtx.close(); await navegador.close(); await backend.detener(); });

    const PAGINAS = [
        { nombre: "inicio", ruta: "/inicio", privada: false, listo: "#navPrincipal[data-sesion]" },
        { nombre: "ayuda", ruta: "/front/ayuda.html", privada: false, listo: "#tablaFunciones tr:nth-child(3)" },
        { nombre: "cuenta", ruta: "/front/cuenta.html", privada: false, listo: "#formEntrar" },
        { nombre: "nuevo", ruta: "/front/nuevo.html", privada: true, listo: "#navPrincipal a" },
        { nombre: "apuntes", ruta: "/front/apuntes.html", privada: true, listo: ".apunte" },
        { nombre: "editor", ruta: () => `/front/editor.html?id=${idApunte}`, privada: true, listo: ".bloque" },
        { nombre: "editor-pdf", ruta: () => `/front/editor.html?id=${idApunte}#pdf`, privada: true, listo: "#listaPdf li" },
        { nombre: "editor-versiones", ruta: () => `/front/editor.html?id=${idApunte}#versiones`, privada: true, listo: ".version" },
        { nombre: "editor-complementos", ruta: () => `/front/editor.html?id=${idApunte}#complementos`, privada: true, listo: "#listaComplementos li" },
        { nombre: "perfil", ruta: "/front/perfil.html", privada: true, listo: "#textoSesiones:not(:empty)" },
    ];

    for (const p of PAGINAS) {
        test(`${p.nombre}: estructura, etiquetas, contraste y anchos`, async () => {
            const contexto = p.privada ? cuentaCtx : await navegador.newContext();
            const pagina = await contexto.newPage();
            const ruta = typeof p.ruta === "function" ? p.ruta() : p.ruta;
            try {
                for (const ancho of ANCHOS) {
                    await pagina.setViewportSize({ width: ancho, height: 900 });
                    await pagina.goto(backend.url + ruta);
                    await pagina.waitForSelector(p.listo, { state: "attached", timeout: 30000 });
                    await pagina.waitForTimeout(150);
                    assert.ok(await sinDesbordamiento(pagina), `${p.nombre} desborda a ${ancho}px`);
                    if (ancho === 1280 || ancho === 320) assert.deepEqual(await pagina.evaluate(auditar), [], `${p.nombre} a ${ancho}px`);
                    if (CAPTURAS) {
                        fs.mkdirSync(CAPTURAS, { recursive: true });
                        await pagina.screenshot({ path: path.join(CAPTURAS, `${p.nombre}-${ancho}.png`), fullPage: true });
                    }
                }
            } finally {
                await pagina.close();
                if (!p.privada) await contexto.close();
            }
        });
    }

    test("teclado: el foco siempre se ve y llega a las acciones principales", async () => {
        const pagina = await cuentaCtx.newPage();
        for (const [ruta, objetivo] of [["/front/apuntes.html", "inpBuscar"], ["/front/perfil.html", "perfilNombre"], [`/front/editor.html?id=${idApunte}`, "inpTituloApunte"]]) {
            await pagina.goto(backend.url + ruta);
            await pagina.waitForSelector("#navPrincipal a");
            await pagina.waitForTimeout(300);
            const vistos = [];
            for (let i = 0; i < 40; i++) {
                await pagina.keyboard.press("Tab");
                const info = await pagina.evaluate(() => {
                    const e = document.activeElement;
                    const s = getComputedStyle(e);
                    return { id: e.id, visible: s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0 || s.boxShadow !== "none" };
                });
                vistos.push(info);
                if (info.id === objetivo) break;
            }
            assert.ok(vistos.some((v) => v.id === objetivo), `${ruta}: no se llega a #${objetivo} con Tab`);
            const sinFoco = vistos.filter((v) => !v.visible).map((v) => v.id || "(sin id)");
            assert.deepEqual(sinFoco, [], `${ruta}: elementos sin foco visible`);
        }
        await pagina.close();
    });

    test("diálogos: foco dentro, Escape cancela y vuelve a la página", async () => {
        const pagina = await cuentaCtx.newPage();
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector(".apunte");
        await pagina.focus(".apunte [data-accion=eliminar]");
        await pagina.keyboard.press("Enter");
        await pagina.waitForSelector(".dlg-app[open]");
        assert.equal(await pagina.evaluate(() => Boolean(document.activeElement.closest(".dlg-app"))), true);
        assert.equal(await pagina.evaluate(() => document.querySelector(".dlg-app").getAttribute("aria-labelledby")), "confirmarTitulo");
        await pagina.keyboard.press("Escape");
        await pagina.waitForSelector(".dlg-app", { state: "detached" });
        assert.equal(await pagina.locator(".apunte").count(), 1, "no se borró");
        await pagina.close();
    });
});
