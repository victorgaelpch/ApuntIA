// FRONT-22: guardado automático, historial, comparación, restauración y conflictos.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola } = require("./v2-entorno");
const { crearApunte } = require("./v2-apuntes-ayuda");

describe("FRONT-22 versiones y guardado", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function abrir() {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        const creado = await crearApunte(contexto, backend.url, pagina);
        const puts = [];
        pagina.on("request", (r) => { if (r.method() === "PUT") puts.push(r.headers()["if-match"]); });
        await pagina.goto(`${backend.url}/front/editor.html?id=${creado.id}`);
        await pagina.waitForSelector(".bloque");
        return { contexto, pagina, errores, puts, ...creado };
    }
    const estado = (p) => p.textContent("#estadoGuardado");
    const esperarGuardado = (p, version) => p.waitForFunction((v) => document.getElementById("estadoGuardado").textContent.includes(`Guardado · versión ${v}`), version, { timeout: 15000 });

    test("guardado automático: una sola petición tras dejar de escribir y solo con respuesta del servidor", async () => {
        const { contexto, pagina, puts, errores } = await abrir();
        const area = pagina.locator(".bloque >> nth=1 >> textarea");
        await area.click();
        await pagina.keyboard.press("End");
        await pagina.keyboard.type(" Añadido poco a poco.", { delay: 60 });
        assert.equal(await estado(pagina), "Cambios sin guardar");
        assert.equal(puts.length, 0, "no guarda mientras se escribe");
        await esperarGuardado(pagina, 3);
        assert.deepEqual(puts, ["2"], "un único PUT con If-Match de la versión editada");
        assert.equal(await pagina.isDisabled("#btGuardar"), true);
        // Desactivarlo: ya no guarda solo
        await pagina.uncheck("#chkAutoguardado");
        await area.fill("Otro cambio");
        await pagina.waitForTimeout(5000);
        assert.equal(await estado(pagina), "Cambios sin guardar");
        assert.equal(puts.length, 1);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("sin conexión: no afirma haber guardado y guarda al volver la conexión", async () => {
        const { contexto, pagina, puts } = await abrir();
        await contexto.setOffline(true);
        await pagina.fill(".bloque >> nth=0 >> textarea", "Escrito sin conexión");
        assert.match(await estado(pagina), /Sin conexión: los cambios solo están en esta pestaña/);
        await pagina.waitForTimeout(4500);
        assert.equal(puts.length, 0);
        await contexto.setOffline(false);
        await esperarGuardado(pagina, 3);
        await contexto.close();
    });

    test("historial: comparar una versión anterior y restaurarla sin perder la actual", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.uncheck("#chkAutoguardado");
        const original = await pagina.inputValue(".bloque >> nth=1 >> textarea");
        await pagina.fill(".bloque >> nth=1 >> textarea", "Texto nuevo de la versión tres");
        await pagina.click("#btGuardar");
        await esperarGuardado(pagina, 3);
        await pagina.click("#tab-versiones");
        await pagina.waitForSelector(".version[data-version='3'][aria-current=true]");
        const motivos = await pagina.$$eval(".version .version__datos", (v) => v.map((x) => x.textContent));
        assert.equal(motivos.length, 3);
        assert.match(motivos[0], /Versión 3.*Edición/);
        assert.match(motivos[1], /Versión 2.*Análisis/);
        await pagina.click(".version[data-version='2'] [data-accion=comparar]");
        await pagina.waitForSelector("#cajaComparacion:not([hidden]) .diferencia--cambiado");
        assert.match(await pagina.textContent(".diferencia--cambiado del"), new RegExp(original.split(" ")[0]));
        assert.match((await pagina.$$eval(".diferencia--cambiado ins", (e) => e.map((x) => x.textContent))).join(""), /Texto nuevo de .*versión tres/);
        assert.match(await pagina.textContent(".diferencia--cambiado .diferencia__cabecera"), /corregido/);
        // Restaurar la 2 (con confirmación)
        await pagina.click(".version[data-version='2'] [data-accion=restaurar]");
        await pagina.click(".dlg-app button[type=submit]");
        await pagina.waitForSelector(".version[data-version='4'][aria-current=true]");
        assert.match(await pagina.textContent("#avisoVersiones"), /versión 4 es igual a la 2/);
        await pagina.click("#tab-transcripcion");
        assert.equal(await pagina.inputValue(".bloque >> nth=1 >> textarea"), original);
        assert.equal(await pagina.locator(".version").count(), 4, "la versión 3 sigue en el historial");
        await contexto.close();
    });

    test("conflicto entre dos pestañas: se pausa el guardado automático y se pueden comparar los cambios", async () => {
        const { contexto, pagina, id } = await abrir();
        await pagina.uncheck("#chkAutoguardado");
        const otra = await contexto.newPage();
        await otra.goto(`${backend.url}/front/editor.html?id=${id}`);
        await otra.waitForSelector(".bloque");
        await otra.fill(".bloque >> nth=0 >> textarea", "Guardado desde la otra pestaña");
        await otra.click("#btGuardar");
        await esperarGuardado(otra, 3);
        await pagina.check("#chkAutoguardado");
        await pagina.fill(".bloque >> nth=0 >> textarea", "Mi versión en esta pestaña");
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]", { timeout: 15000 });
        await pagina.click("#avisoEditor >> text=Comparar");
        await pagina.waitForSelector("#cajaComparacion:not([hidden]) .diferencia");
        const comparacion = await pagina.textContent("#comparacion");
        assert.match(comparacion, /guardada en otra pestaña/);
        assert.match(comparacion, /otra pestaña/);
        assert.match(comparacion, /Mi versión en esta pestaña/);
        // Pausado: no reintenta solo
        await pagina.click("#tab-transcripcion");
        await pagina.fill(".bloque >> nth=0 >> textarea", "Mi versión en esta pestaña, editada");
        await pagina.waitForTimeout(5000);
        assert.equal(await estado(pagina), "Cambios sin guardar");
        await pagina.click("#avisoEditor >> text=Guardar encima");
        await esperarGuardado(pagina, 4);
        await contexto.close();
    });

    test("diferencia por palabras", async () => {
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/front/editor.html`);
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        const partes = await pagina.evaluate(() => window.ApuntIA.editorVersiones.diferenciaPalabras("la derivada mide el cambio", "la derivada mide la razón de cambio"));
        assert.deepEqual(partes.filter((p) => p.tipo !== "igual").map((p) => [p.tipo, p.texto.trim()]),
                         [["quitado", "el"], ["anadido", "la razón de"]]);
        await contexto.close();
    });
});
