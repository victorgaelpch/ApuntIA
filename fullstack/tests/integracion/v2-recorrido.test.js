// FRONT-21: recorrido completo como lo haría una persona nueva, solo con la interfaz:
// registro → fotos → análisis real (Tesseract) → corrección → fórmula y tabla →
// complemento citado (Wikipedia simulada) → PDF descargado y leído → Mis apuntes → salir.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");
const { iniciarBackendV2, vigilarConsola } = require("./v2-entorno");
const { fotoApunte } = require("./v2-apuntes-ayuda");
const { claveDePrueba } = require("../claves");

const CAPTURAS = process.env.CAPTURAS ? path.resolve(process.env.CAPTURAS) : null;

async function capturar(pagina, nombre) {
    if (!CAPTURAS) return;
    fs.mkdirSync(CAPTURAS, { recursive: true });
    await pagina.screenshot({ path: path.join(CAPTURAS, `recorrido-${nombre}.png`), fullPage: false });
}

describe("FRONT-21 recorrido completo desde la foto hasta el PDF", () => {
    let navegador, backend;
    before(async () => {
        navegador = await chromium.launch();
        backend = await iniciarBackendV2({ INVESTIGACION_PROVEEDOR: "wikipedia" }, { modulo: "app_wikipedia_simulada" });
    });
    after(async () => { await navegador.close(); await backend.detener(); });

    test("una alumna nueva crea, corrige, amplía y descarga su apunte", async () => {
        const contexto = await navegador.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        try {
            // 1. Inicio → Entrar → crear cuenta
            await pagina.goto(`${backend.url}/inicio`);
            await pagina.click("#navPrincipal >> text=Entrar");
            await pagina.click("#tabRegistro");
            await pagina.fill("#regNombre", "Lucía");
            await pagina.fill("#regEmail", "lucia@example.com");
            await pagina.fill("#regPassword", claveDePrueba("c22"));
            await pagina.fill("#regConfirmar", claveDePrueba("c22"));
            await Promise.all([pagina.waitForURL(/nuevo\.html/), pagina.click("#formRegistro button[type=submit]")]);
            await capturar(pagina, "1-nuevo");

            // 2. Dos fotos, en orden, y crear
            const fotos = [
                await fotoApunte(pagina, { lineas: ["Derivadas", "La derivada mide la razon de cambio.", "Ejemplo: la funcion crece."] }),
                await fotoApunte(pagina, { lineas: ["Repaso", "La integral acumula el area."] }),
            ];
            await pagina.setInputFiles("#inpFotos", fotos.map((buffer, i) => ({ name: `pagina${i + 1}.png`, mimeType: "image/png", buffer })));
            await pagina.waitForFunction(() => document.querySelectorAll("#listaPaginas li").length === 2);
            await pagina.fill("#inpTitulo", "Cálculo — semana 3");
            await Promise.all([pagina.waitForURL(/editor\.html/), pagina.click("#btCrear")]);

            // 3. Análisis y corrección del texto (tildes que el OCR no puede adivinar)
            await pagina.waitForSelector(".bloque", { timeout: 180000 });
            await pagina.uncheck("#chkAutoguardado");
            await capturar(pagina, "2-editor");
            const area = pagina.locator(".bloque", { hasText: "" }).locator("textarea").first();
            const texto = await area.inputValue();
            assert.match(texto, /Derivadas/);
            await area.fill(texto.replace("razon", "razón").replace("funcion", "función"));
            // 4. Fórmula y tabla a mano
            await pagina.click("#btAnadirFormula");
            await pagina.locator("textarea.latex").last().fill("f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}");
            await pagina.waitForSelector(".formula-estado[data-tipo=exito]");
            await pagina.click("#btAnadirTabla");
            await pagina.locator(".tabla-editable [data-celda=c0]").last().fill("Función");
            await pagina.locator(".tabla-editable [data-celda=c1]").last().fill("Derivada");
            await pagina.locator(".tabla-editable [data-celda=f0c0]").last().fill("x²");
            await pagina.locator(".tabla-editable [data-celda=f0c1]").last().fill("2x");
            await pagina.click("#btGuardar");
            await pagina.waitForFunction(() => /Guardado · versión 3/.test(document.getElementById("estadoGuardado").textContent));

            // 5. Complemento citado (con permiso y consentimiento)
            await pagina.click("#tab-complementos");
            await pagina.click("#avisoInvestigacion >> text=Permitir en mi perfil");
            await pagina.click(".dlg-app button[type=submit]");
            await pagina.check("#chkInvestigar");
            for (const c of await pagina.$$("#listaConceptos input:checked")) await c.uncheck();
            await pagina.fill("#inpConcepto", "Derivada");
            await pagina.click("#btAnadirConcepto");
            await pagina.check("#chkConsentimiento");
            await pagina.click("#btInvestigar");
            await pagina.waitForSelector(".complemento", { timeout: 60000 });
            await pagina.click(".complemento [data-accion=aceptar]");
            await pagina.waitForSelector("#avisoComplementos[data-tipo=exito]");
            await capturar(pagina, "3-complementos");

            // 6. PDF: generar, ver y descargar
            await pagina.click("#tab-pdf");
            await pagina.click("#btGenerarPdf");
            await pagina.waitForSelector("#cajaVistaPdf:not([hidden])", { timeout: 120000 });
            await capturar(pagina, "4-pdf");
            const [descarga] = await Promise.all([pagina.waitForEvent("download"), pagina.click("#enlaceDescargaPdf")]);
            assert.equal(descarga.suggestedFilename(), "calculo-semana-3-v5.pdf");  // v3 edición, v4 complementos, v5 aceptado
            const textoPdf = execFileSync("pdftotext", ["-enc", "UTF-8", "-layout", await descarga.path(), "-"], { encoding: "utf8" });
            for (const esperado of ["Cálculo — semana 3", "razón de cambio", "Repaso", "Derivada", "2x",
                                    "Información complementaria", "Fuentes", "es.wikipedia.org/wiki/Derivada"]) {
                assert.ok(textoPdf.includes(esperado), `«${esperado}» en el PDF`);
            }
            // Orden de las páginas: con frases que solo están en el cuerpo (no en el índice)
            assert.ok(textoPdf.indexOf("razón de cambio") < textoPdf.indexOf("integral acumula"), "las páginas en el orden elegido");

            // 7. Mis apuntes y salir
            await pagina.click("#navPrincipal >> text=Mis apuntes");
            await pagina.waitForSelector(".apunte");
            assert.match(await pagina.textContent(".apunte"), /Cálculo — semana 3[\s\S]*Listo[\s\S]*2 páginas[\s\S]*1 PDF/);
            await capturar(pagina, "5-mis-apuntes");
            await Promise.all([pagina.waitForURL(/motivo=salida/), pagina.click("#btSalir")]);
            assert.deepEqual(errores, []);
        } catch (e) {
            await capturar(pagina, "fallo");
            throw e;
        } finally {
            await contexto.close();
        }
    });
});
