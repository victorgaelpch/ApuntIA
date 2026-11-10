// FRONT-15: información complementaria con consentimiento y fuentes, con el backend real
// y una Wikipedia simulada (app_wikipedia_simulada.py): ok, lenta, caída y sin resultados.
const { test, describe, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, vigilarConsola } = require("./v2-entorno");
const { crearApunte, fotoApunte } = require("./v2-apuntes-ayuda");

const LINEAS = ["Historia y cálculo", "La Revolución francesa empezó en 1790.", "La derivada mide la razón de cambio."];
let navegador;
const backends = {};
async function backend(modo) {
    if (!backends[modo]) {
        backends[modo] = modo === "ninguno" ? await iniciarBackendV2()
            : await iniciarBackendV2({ INVESTIGACION_PROVEEDOR: "wikipedia", APUNTIA_WIKI: modo }, { modulo: "app_wikipedia_simulada" });
    }
    return backends[modo];
}

async function abrir(modo) {
    navegador = navegador || await chromium.launch();
    const be = await backend(modo);
    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();
    const errores = vigilarConsola(pagina);
    await pagina.goto(`${be.url}/front/ayuda.html`);
    const creado = await crearApunte(contexto, be.url, pagina, { fotos: [await fotoApunte(pagina, { lineas: LINEAS })] });
    const posts = [];
    pagina.on("request", (r) => { if (r.method() === "POST" && r.url().includes("/investigacion")) posts.push(r.postDataJSON()); });
    await pagina.goto(`${be.url}/front/editor.html?id=${creado.id}`);
    await pagina.waitForSelector(".bloque");
    await pagina.uncheck("#chkAutoguardado");
    await pagina.click("#tab-complementos");
    return { contexto, pagina, errores, posts, be, ...creado };
}

async function prepararBusqueda(pagina, conceptos) {
    await pagina.waitForFunction(() => document.getElementById("textoProveedor").textContent !== "");
    if (await pagina.isVisible("#avisoInvestigacion >> text=Permitir en mi perfil")) {
        await pagina.click("#avisoInvestigacion >> text=Permitir en mi perfil");
        await pagina.click(".dlg-app button[type=submit]");
    }
    await pagina.waitForSelector("#chkInvestigar:not([disabled])");
    await pagina.check("#chkInvestigar");
    for (const c of await pagina.$$("#listaConceptos input:checked")) await c.uncheck();
    for (const c of conceptos) {
        await pagina.fill("#inpConcepto", c);
        await pagina.click("#btAnadirConcepto");
    }
}

describe("FRONT-15 información complementaria", () => {
    after(async () => {
        if (navegador) await navegador.close();
        for (const b of Object.values(backends)) await b.detener();
    });

    test("desactivada por defecto, consentimiento expreso, fuentes citables, aceptar y descartar", async () => {
        const { contexto, pagina, posts, id, be, errores } = await abrir("ok");
        assert.equal(await pagina.isChecked("#chkInvestigar"), false);
        assert.equal(await pagina.isHidden("#formInvestigar"), true);
        await pagina.waitForFunction(() => /permitirla en tu perfil/.test(document.getElementById("avisoInvestigacion").textContent));
        await prepararBusqueda(pagina, ["Derivada", "Revolución francesa", "Trampa"]);
        assert.match(await pagina.textContent("#textoProveedor"), /Solo se envían las palabras clave/);
        // Sin consentimiento no sale nada
        await pagina.click("#btInvestigar");
        assert.match(await pagina.textContent("#avisoInvestigacion"), /consentimiento/);
        assert.equal(posts.length, 0);
        await pagina.check("#chkConsentimiento");
        await pagina.click("#btInvestigar");
        await pagina.waitForSelector(".complemento", { timeout: 30000 });
        assert.deepEqual(posts, [{ consentimiento: true, conceptos: ["Derivada", "Revolución francesa", "Trampa"], idioma: "es" }],
                         "solo palabras clave, nunca el texto del apunte");
        assert.equal(await pagina.isChecked("#chkConsentimiento"), false, "el consentimiento vale para una búsqueda");
        const aviso = await pagina.textContent("#avisoInvestigacion");
        assert.match(aviso, /2 complemento\(s\) nuevo/);
        assert.match(aviso, /descartados por contener instrucciones/);
        assert.equal(await pagina.locator(".complemento").count(), 2);
        // Fuente inspeccionable
        const enlace = pagina.locator(".complemento >> nth=0 >> a");
        assert.match(await enlace.getAttribute("href"), /^https:\/\/es\.wikipedia\.org\/wiki\//);
        assert.equal(await enlace.getAttribute("rel"), "noopener noreferrer");
        assert.match(await pagina.textContent(".complemento >> nth=0 >> .complemento__fuente"),
                     /Colaboradores de Wikipedia.*Consultado el \d{4}-\d\d-\d\d.*CC BY-SA 4\.0/);
        // Contradicción: se avisa, el apunte no cambia
        const revolucion = pagina.locator(".complemento", { hasText: "Revolución francesa" });
        assert.match(await revolucion.locator("[role=note]").textContent(), /1790.*1789/);
        await pagina.locator(".complemento", { hasText: "Derivada" }).locator("[data-accion=aceptar]").click();
        await pagina.waitForSelector("#avisoComplementos[data-tipo=exito]");
        await revolucion.locator("[data-accion=rechazar]").click();
        await pagina.waitForFunction(() => /no irá al PDF/.test(document.getElementById("avisoComplementos").textContent));
        await pagina.click("#tab-transcripcion");
        assert.match((await pagina.$$eval(".bloque textarea", (t) => t.map((x) => x.value))).join(" "), /1790/);
        const estructura = (await (await contexto.request.get(`${be.url}/api/v2/apuntes/${id}/estructura`)).json()).estructura;
        assert.deepEqual(estructura.complementos.map((c) => c.concepto), ["Derivada"]);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("fuente caída: error claro y se puede seguir sin complementos", async () => {
        const { contexto, pagina } = await abrir("caido");
        await prepararBusqueda(pagina, ["Derivada"]);
        await pagina.check("#chkConsentimiento");
        await pagina.click("#btInvestigar");
        await pagina.waitForSelector("#avisoInvestigacion[data-tipo=error]", { timeout: 30000 });
        assert.match(await pagina.textContent("#avisoInvestigacion"), /No se pudo consultar la fuente externa.*seguir sin información complementaria/);
        assert.equal(await pagina.locator(".complemento").count(), 0);
        await contexto.close();
    });

    test("respuesta lenta: progreso visible y cancelar", async () => {
        const { contexto, pagina } = await abrir("lento");
        await prepararBusqueda(pagina, ["Derivada", "Función"]);
        await pagina.check("#chkConsentimiento");
        await pagina.click("#btInvestigar");
        await pagina.waitForSelector("#progresoInvestigacion:not([hidden])");
        await pagina.click("#btCancelarInvestigacion");
        await pagina.waitForFunction(() => /cancelada/.test(document.getElementById("avisoInvestigacion").textContent), null, { timeout: 30000 });
        assert.equal(await pagina.locator(".complemento").count(), 0);
        await contexto.close();
    });

    test("sin resultados: no se inventa nada", async () => {
        const { contexto, pagina } = await abrir("sin_resultados");
        await prepararBusqueda(pagina, ["Derivada"]);
        await pagina.check("#chkConsentimiento");
        await pagina.click("#btInvestigar");
        await pagina.waitForSelector("#avisoInvestigacion[data-tipo=aviso]", { timeout: 30000 });
        assert.match(await pagina.textContent("#avisoInvestigacion"), /sin fuentes fiables/);
        assert.match(await pagina.textContent("#listaComplementos"), /Todavía no hay complementos/);
        await contexto.close();
    });

    test("servidor sin proveedor (sin Internet): no se ofrece y el resto funciona", async () => {
        const { contexto, pagina } = await abrir("ninguno");
        await pagina.waitForFunction(() => /no está disponible en este servidor/.test(document.getElementById("avisoInvestigacion").textContent));
        assert.equal(await pagina.isDisabled("#chkInvestigar"), true);
        await contexto.close();
    });
});
