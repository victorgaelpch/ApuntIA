// FULL-16: flujo completo foto → apunte editable → PDF, con casos reales y fallos:
// foto real de pizarrón + página de cuaderno con fórmula, corrección que llega al PDF,
// investigación caída sin bloquear el PDF, OCR no disponible con causa y reintento sin
// duplicados, y dos sesiones a la vez sin mezclar contenido.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola } = require("./v2-entorno");
const { crearApunte, fotoApunte, esperarTrabajo } = require("./v2-apuntes-ayuda");

const FOTO_REAL = fs.readFileSync(path.resolve(__dirname, "..", "..", "..", "back", "bd", "img", "image.png"));

function textoPdf(buffer) {
    const archivo = path.join(fs.mkdtempSync(path.join(require("node:os").tmpdir(), "apuntia-flujo-")), "a.pdf");
    fs.writeFileSync(archivo, buffer);
    try { return execFileSync("pdftotext", ["-enc", "UTF-8", "-layout", archivo, "-"], { encoding: "utf8" }); }
    finally { fs.rmSync(path.dirname(archivo), { recursive: true, force: true }); }
}

async function pdfDesdeLaInterfaz(pagina) {
    await pagina.click("#tab-pdf");
    await pagina.click("#btGenerarPdf");
    await pagina.waitForSelector("#cajaVistaPdf:not([hidden])", { timeout: 120000 });
    const [descarga] = await Promise.all([pagina.waitForEvent("download"), pagina.click("#enlaceDescargaPdf")]);
    return textoPdf(fs.readFileSync(await descarga.path()));
}

describe("FULL-16 flujo completo", () => {
    let navegador, backend, sinOcr;
    before(async () => {
        navegador = await chromium.launch();
        // Investigación «caída»: el apunte y su PDF deben funcionar igual.
        backend = await iniciarBackendV2({ INVESTIGACION_PROVEEDOR: "wikipedia", APUNTIA_WIKI: "caido" }, { modulo: "app_wikipedia_simulada" });
        sinOcr = await iniciarBackendV2({ OCR_MOTOR: "ninguno" });
    });
    after(async () => { await navegador.close(); await backend.detener(); await sinOcr.detener(); });

    test("foto real de pizarrón + cuaderno con fórmula: dos páginas, corrección y PDF con la corrección", async () => {
        const contexto = await navegador.newContext({ acceptDownloads: true });
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/front/ayuda.html`);
        const cuaderno = await fotoApunte(pagina, { lineas: ["Ecuaciones", "Resolver la ecuacion:", "x^2 + 2x + 1 = 0"] });
        const cuenta = await registrar(contexto, backend.url);
        // Tipos distintos por página, como en la interfaz
        const creado = await pagina.evaluate(async ({ csrf, fotos }) => {
            const datos = new FormData();
            fotos.forEach((b64, i) => datos.append("paginas", new Blob([Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))], { type: "image/png" }), `p${i + 1}.png`));
            datos.append("tipos", "pizarron"); datos.append("tipos", "cuaderno"); datos.append("titulo", "Clase real");
            return (await fetch("/api/v2/apuntes", { method: "POST", body: datos, headers: { "X-CSRF-Token": csrf } })).json();
        }, { csrf: cuenta.csrf, fotos: [FOTO_REAL.toString("base64"), cuaderno.toString("base64")] });
        const t = await esperarTrabajo(contexto, backend.url, creado.trabajo.id);
        assert.ok(["completado", "parcial"].includes(t.estado), `análisis ${t.estado}`);
        await pagina.goto(`${backend.url}/front/editor.html?id=${creado.apunte.id}`);
        await pagina.waitForSelector("#visorPaginas button:nth-child(2)");
        await pagina.uncheck("#chkAutoguardado");
        // Página 2 (cuaderno): corregir la tilde que el OCR no puede saber
        await pagina.click("#visorPaginas button:nth-child(2)");
        await pagina.waitForSelector(".bloque");
        const indice = await pagina.$$eval(".bloque textarea", (t) => t.findIndex((x) => /Resolver/.test(x.value)));
        assert.ok(indice >= 0, "el OCR leyó la línea «Resolver la ecuacion»");
        const area = pagina.locator(".bloque textarea").nth(indice);
        const original = await area.inputValue();
        await area.fill(original.replace("ecuacion", "ecuación"));
        // La fórmula: como LaTeX verificado si se reconoció, o escrita a mano
        if (!await pagina.locator("textarea.latex").count()) await pagina.click("#btAnadirFormula");
        await pagina.locator("textarea.latex").first().fill("x^{2} + 2x + 1 = 0");
        await pagina.waitForSelector(".formula-estado[data-tipo=exito]");
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
        // Investigación caída: se informa y el PDF sigue disponible
        await pagina.click("#tab-complementos");
        await pagina.click("#avisoInvestigacion >> text=Permitir en mi perfil");
        await pagina.click(".dlg-app button[type=submit]");
        await pagina.check("#chkInvestigar");
        await pagina.fill("#inpConcepto", "Ecuación");
        await pagina.click("#btAnadirConcepto");
        await pagina.check("#chkConsentimiento");
        await pagina.click("#btInvestigar");
        await pagina.waitForSelector("#avisoInvestigacion[data-tipo=error]", { timeout: 60000 });
        const texto = await pdfDesdeLaInterfaz(pagina);
        assert.match(texto, /Resolver la ecuación/, "la corrección llega al PDF");
        assert.ok(!/ecuacion:/.test(texto), "no queda el texto sin corregir");
        assert.match(texto, /Página 1/);
        assert.ok(!texto.includes("Información complementaria"), "sin complementos al fallar la búsqueda");
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("OCR no disponible: causa accionable y reintento del MISMO trabajo, sin duplicar el apunte", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const { id, trabajo } = await crearApunte(contexto, sinOcr.url, pagina, { titulo: "Sin OCR" });
        assert.equal(trabajo.estado, "fallido");
        await pagina.goto(`${sinOcr.url}/front/editor.html?id=${id}`);
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoEditor"), /reconocimiento de texto no está disponible|desactivado/);
        const reintentos = [];
        pagina.on("request", (r) => { if (r.url().includes("/reintentar")) reintentos.push(r.url()); });
        await pagina.click("#avisoEditor >> text=Reintentar el análisis");
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]", { timeout: 30000 });
        assert.equal(reintentos.length, 1);
        assert.ok(reintentos[0].includes(trabajo.id), "reintenta el mismo trabajo");
        const lista = await (await contexto.request.get(`${sinOcr.url}/api/v2/apuntes`)).json();
        assert.equal(lista.total, 1);
        await contexto.close();
    });

    test("dos personas a la vez: cada PDF solo contiene lo suyo", async () => {
        const [a, b] = await Promise.all([navegador.newContext({ acceptDownloads: true }), navegador.newContext({ acceptDownloads: true })]);
        const [pa, pb] = await Promise.all([a.newPage(), b.newPage()]);
        await Promise.all([pa.goto(`${backend.url}/front/ayuda.html`), pb.goto(`${backend.url}/front/ayuda.html`)]);
        const [fa, fb] = await Promise.all([fotoApunte(pa, { lineas: ["Biologia", "La celula es la unidad de la vida."] }),
                                            fotoApunte(pb, { lineas: ["Quimica", "El atomo tiene protones."] })]);
        const [ca, cb] = await Promise.all([crearApunte(a, backend.url, pa, { fotos: [fa], titulo: "De A" }),
                                            crearApunte(b, backend.url, pb, { fotos: [fb], titulo: "De B" })]);
        for (const [pagina, c] of [[pa, ca], [pb, cb]]) {
            await pagina.goto(`${backend.url}/front/editor.html?id=${c.id}`);
            await pagina.waitForSelector(".bloque");
        }
        const [ta, tb] = await Promise.all([pdfDesdeLaInterfaz(pa), pdfDesdeLaInterfaz(pb)]);
        assert.match(ta, /celula/);
        assert.ok(!/atomo|Quimica|De B/.test(ta));
        assert.match(tb, /atomo/);
        assert.ok(!/celula|Biologia|De A/.test(tb));
        // Y B no puede pedir el PDF de A
        const exportaciones = await (await a.request.get(`${backend.url}/api/v2/apuntes/${ca.id}/exportaciones`)).json();
        const r = await b.request.get(`${backend.url}${exportaciones.exportaciones[0].descarga}`);
        assert.equal(r.status(), 404);
        await a.close();
        await b.close();
    });
});
