// FRONT-26: el editor muestra las propuestas del servidor IA como lo que son (sin confirmar), con
// su recorte, las dudas del modelo y la marca «revisado» que se guarda. Backend REAL + servidor IA
// FALSO con el mismo contrato (ia-falsa.js), sin GPU.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { iniciarIAFalsa } = require("./ia-falsa");

const FOTO = path.resolve(__dirname, "..", "..", "..", "back", "bd", "img", "image.png");

describe("FRONT-26 editor con propuestas del servidor IA", () => {
    let navegador, backend, ia, contexto, apunteId;
    before(async () => {
        ia = await iniciarIAFalsa();
        backend = await iniciarBackendV2({ APUNTIA_IA_URL: ia.url });
        navegador = await chromium.launch();
        contexto = await navegador.newContext();
        const cuenta = await registrar(contexto, backend.url);
        const cab = { Origin: backend.url, "X-CSRF-Token": cuenta.csrf };
        let r = await contexto.request.post(`${backend.url}/api/v2/ia/vinculacion`, { headers: cab });
        assert.equal(r.status(), 201, await r.text());
        r = await contexto.request.get(`${backend.url}/api/v2/ia/vinculacion`, { headers: cab });
        assert.equal((await r.json()).estado, "vinculado");
        r = await contexto.request.post(`${backend.url}/api/v2/apuntes`, { headers: cab, multipart: {
            paginas: { name: "hoja.png", mimeType: "image/png", buffer: fs.readFileSync(FOTO) },
            tipos: "cuaderno", titulo: "Con IA", motor: "ia_remota" } });
        assert.equal(r.status(), 202, await r.text());
        const creado = await r.json();
        apunteId = creado.apunte.id;
        for (let i = 0; i < 100; i++) {
            const t = (await (await contexto.request.get(`${backend.url}/api/v2/trabajos/${creado.trabajo.id}`)).json()).trabajo;
            if (!["pendiente", "procesando"].includes(t.estado)) { assert.equal(t.estado, "completado", JSON.stringify(t)); break; }
            await new Promise((x) => setTimeout(x, 200));
        }
    });
    after(async () => { await navegador.close(); await backend.detener(); await ia.cerrar(); });

    test("las propuestas de IA se distinguen, con recorte, dudas y aviso de revisión", async () => {
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/front/editor.html?id=${apunteId}`);
        await pagina.waitForSelector("article.bloque.propuesta-ia");
        const chips = await pagina.$$eval("article.propuesta-ia .estado-chip", (c) => c.map((x) => x.textContent));
        assert.deepEqual(chips, ["Propuesta de IA · sin revisar", "Propuesta de IA · sin revisar", "IA: sin leer"]);
        assert.ok(!chips.some((c) => /%/.test(c)), "un VLM no tiene confianza calibrada: sin porcentajes");
        // El texto también se muestra junto a su recorte (no solo fórmulas o dudosos)
        assert.equal(await pagina.locator("article[data-origen=ia] img.bloque__recorte").count(), 3);
        assert.match(await pagina.textContent("article[data-bloque=p1b1]"), /Dudas del modelo/);
        assert.match(await pagina.textContent("article[data-bloque=p1b1]"), /6\/8, \+\/−, i\/j\/k/);
        assert.match(await pagina.textContent("article[data-bloque=p1b2]"), /compárala con el recorte/);
        assert.deepEqual(errores, []);
        await pagina.close();
    });

    test("marcar como revisado se guarda y sobrevive a recargar; la procedencia no cambia", async () => {
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/front/editor.html?id=${apunteId}`);
        await pagina.waitForSelector("article[data-bloque=p1b2]");
        await pagina.click("article[data-bloque=p1b2] [data-accion=revisado]");
        assert.equal(await pagina.getAttribute("article[data-bloque=p1b2]", "data-revisado"), "true");
        assert.match(await pagina.textContent("article[data-bloque=p1b2] .estado-chip"), /revisada/);
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado/.test(document.querySelector("#estadoGuardado").textContent));
        await pagina.reload();
        await pagina.waitForSelector("article[data-bloque=p1b2][data-revisado=true]");
        const doc = (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${apunteId}`)).json()).apunte.documento;
        const b = doc.bloques.find((x) => x.id === "p1b2");
        assert.equal(b.revisado, true);
        assert.equal(b.procedencia.motor, "ia_remota");           // la procedencia no la cambia el usuario
        assert.equal(b.revision, "sin_confirmar");
        await pagina.close();
    });

    test("móvil: el editor con propuestas de IA no desborda", async () => {
        const movil = await navegador.newContext({ viewport: { width: 360, height: 780 }, storageState: await contexto.storageState() });
        const pagina = await movil.newPage();
        await pagina.goto(`${backend.url}/front/editor.html?id=${apunteId}`);
        await pagina.waitForSelector("article.propuesta-ia");
        assert.equal(await sinDesbordamiento(pagina), true);
        await movil.close();
    });
});
