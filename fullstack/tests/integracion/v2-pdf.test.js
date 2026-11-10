// FRONT-16: progreso, vista previa y descarga real del PDF con el backend real.
const { test, describe, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");
const { iniciarBackendV2, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte } = require("./v2-apuntes-ayuda");

let navegador;
const backends = {};
async function backend(lento) {
    const clave = lento ? "lento" : "normal";
    if (!backends[clave]) backends[clave] = await iniciarBackendV2({}, lento ? { modulo: "app_pdf_lento" } : {});
    return backends[clave];
}

async function abrir({ lento = false, viewport } = {}) {
    navegador = navegador || await chromium.launch();
    const be = await backend(lento);
    const contexto = await navegador.newContext({ acceptDownloads: true, ...(viewport ? { viewport } : {}) });
    const pagina = await contexto.newPage();
    const errores = vigilarConsola(pagina);
    const creado = await crearApunte(contexto, be.url, pagina, { titulo: "Física: Óptica" });
    await pagina.goto(`${be.url}/front/editor.html?id=${creado.id}`);
    await pagina.waitForSelector(".bloque");
    await pagina.uncheck("#chkAutoguardado");
    await pagina.click("#tab-pdf");
    return { contexto, pagina, errores, be, ...creado };
}
const listo = (pagina) => pagina.waitForSelector("#cajaVistaPdf:not([hidden])", { timeout: 60000 });

describe("FRONT-16 PDF", () => {
    after(async () => {
        if (navegador) await navegador.close();
        for (const b of Object.values(backends)) await b.detener();
    });

    test("generar: progreso, vista previa y descarga de un PDF válido con nombre seguro", async () => {
        const { contexto, pagina, errores } = await abrir();
        const posts = [];
        pagina.on("request", (r) => { if (r.method() === "POST" && r.url().endsWith("/exportaciones")) posts.push(r.postDataJSON()); });
        await pagina.selectOption("#selEstiloPdf", "basico");
        await pagina.check("#chkOriginalesPdf");
        await pagina.click("#btGenerarPdf");
        await listo(pagina);
        assert.deepEqual(posts, [{ estilo: "basico", incluir_complementos: true, incluir_originales: true }]);
        assert.match(await pagina.textContent("#avisoPdf"), /PDF listo: \d+ página/);
        assert.match(await pagina.getAttribute("#marcoPdf", "src"), /^blob:/);
        assert.equal(await pagina.getAttribute("#enlaceDescargaPdf", "download"), "fisica-optica-v2.pdf");
        const [descarga] = await Promise.all([pagina.waitForEvent("download"), pagina.click("#enlaceDescargaPdf")]);
        assert.equal(descarga.suggestedFilename(), "fisica-optica-v2.pdf");
        const ruta = await descarga.path();
        const bytes = fs.readFileSync(ruta);
        assert.ok(bytes.length > 1000 && bytes.subarray(0, 5).toString() === "%PDF-");
        const texto = execFileSync("pdftotext", ["-layout", ruta, "-"], { encoding: "utf8" });
        assert.match(texto, /Física: Óptica/);
        assert.match(texto, /Anexo: fotos originales/);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("pedir el mismo PDF lo reutiliza; tras editar queda desactualizado y se regenera con la versión nueva", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.click("#btGenerarPdf");
        await listo(pagina);
        await pagina.click("#btGenerarPdf");
        await pagina.waitForFunction(() => /se reutiliza/.test(document.getElementById("avisoPdf").textContent));
        assert.equal(await pagina.locator("#listaPdf .version").count(), 1);
        // Editar sin guardar: la vista previa ya no es la actual
        await pagina.click("#tab-transcripcion");
        await pagina.fill(".bloque >> nth=0 >> textarea", "Texto corregido para el PDF nuevo");
        await pagina.click("#tab-pdf");
        assert.equal(await pagina.isVisible("#avisoObsoleto"), true);
        assert.match(await pagina.textContent("#avisosPrevios"), /cambios sin guardar/);
        // Regenerar guarda primero y usa la versión 3
        await pagina.click("#btRegenerarPdf");
        await pagina.waitForFunction(() => /fisica-optica-v3\.pdf/.test(document.getElementById("datosPdf").textContent), null, { timeout: 60000 });
        assert.match(await pagina.textContent("#estadoGuardado"), /versión 3/);
        assert.equal(await pagina.isHidden("#avisoObsoleto"), true);
        const etiquetas = await pagina.$$eval("#listaPdf .version", (l) => l.map((x) => x.textContent));
        assert.ok(etiquetas.some((t) => /Versión 2.*Versión anterior/.test(t)), "el PDF viejo se marca como de una versión anterior");
        await contexto.close();
    });

    test("una versión sin contenido falla de forma controlada", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.waitForSelector("#selVersionPdf option[value='1']", { state: "attached" });
        await pagina.selectOption("#selVersionPdf", "1");
        await pagina.click("#btGenerarPdf");
        await pagina.waitForSelector("#avisoPdf[data-tipo=error]", { timeout: 60000 });
        assert.match(await pagina.textContent("#avisoPdf"), /no tiene contenido para exportar/);
        assert.equal(await pagina.isHidden("#cajaVistaPdf"), true, "no se presenta un PDF vacío");
        assert.equal(await pagina.isVisible("#avisoPdf >> text=Reintentar"), true);
        await contexto.close();
    });

    test("la versión elegida no se pierde si la lista de versiones llega tarde", async () => {
        // Antes, una respuesta tardía de /versiones devolvía la selección a «la actual» y se generaba
        // el PDF de otra versión (lo destapó la CI, más lenta).
        const { contexto, pagina } = await abrir();
        await pagina.waitForSelector("#selVersionPdf option[value='1']", { state: "attached" });
        await pagina.route("**/versiones", async (ruta) => { await new Promise((r) => setTimeout(r, 2000)); await ruta.continue(); });
        const tardia = pagina.waitForResponse((r) => r.url().endsWith("/versiones"));
        await pagina.click("#tab-transcripcion");
        await pagina.click("#tab-pdf");                        // vuelve a pedir la lista, que tardará
        await pagina.selectOption("#selVersionPdf", "1");      // el usuario elige mientras tanto
        await tardia;
        await pagina.waitForTimeout(200);
        assert.equal(await pagina.$eval("#selVersionPdf", (s) => s.value), "1");
        await contexto.close();
    });

    test("cancelar, y recuperar la exportación en curso al recargar", async () => {
        const { contexto, pagina } = await abrir({ lento: true });
        await pagina.click("#btGenerarPdf");
        await pagina.waitForSelector("#progresoPdf:not([hidden])");
        await pagina.click("#btCancelarPdf");
        await pagina.waitForFunction(() => /cancelada/.test(document.getElementById("avisoPdf").textContent), null, { timeout: 30000 });
        assert.equal(await pagina.isHidden("#cajaVistaPdf"), true);
        // Otra vez, y se recarga la página a mitad
        await pagina.click("#btGenerarPdf");
        await pagina.waitForSelector("#progresoPdf:not([hidden])");
        await pagina.reload();
        await pagina.waitForSelector("#panel-pdf:not([hidden]) #progresoPdf:not([hidden])");
        await listo(pagina);
        await contexto.close();
    });

    test("sesión caducada al descargar: no se muestra nada privado", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.click("#btGenerarPdf");
        await listo(pagina);
        await contexto.clearCookies();
        await pagina.click("#listaPdf [data-accion=ver]");
        await pagina.waitForURL(/cuenta\.html\?.*motivo=expirada/);
        await contexto.close();
    });

    test("móvil", async () => {
        const { contexto, pagina } = await abrir({ viewport: { width: 360, height: 780 } });
        assert.ok(await sinDesbordamiento(pagina));
        await contexto.close();
    });
});
