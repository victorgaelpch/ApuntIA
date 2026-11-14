// FRONT-25: página «Servidor IA» y selector de reconocimiento contra el backend REAL
// (sin servidor IA: estados local / sin vincular, validación de la URL, diagnóstico con DNS
// caído, modo local, accesibilidad básica y que ningún secreto llega al navegador).
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");

describe("FRONT-25 servidor IA en la interfaz", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2({ APUNTIA_IA_URL: "" }); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function abrir(ruta, opciones = {}) {
        const contexto = await navegador.newContext(opciones);
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}${ruta}`);
        return { contexto, pagina, errores };
    }

    test("sin servidor configurado: modo local con texto (no solo color)", async () => {
        const { contexto, pagina, errores } = await abrir("/front/ia.html");
        await pagina.waitForSelector("#estadoIA[data-estado=local]");
        assert.match(await pagina.textContent("#estadoIATexto"), /modo local/);
        assert.equal(await pagina.getAttribute("#estadoIA", "role"), "status");
        assert.equal(await pagina.isVisible("#btVincularIA"), false);
        assert.equal(await pagina.isChecked("input[name=modoIA][value=auto]"), true);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("URL manual: rechaza la insegura con un mensaje en el campo y acepta https", async () => {
        const { contexto, pagina } = await abrir("/front/ia.html");
        await pagina.waitForSelector("#estadoIA[data-estado=local]");
        await pagina.check("input[name=modoIA][value=manual]");
        await pagina.fill("#inpUrlIA", "http://ia.ejemplo.org/?token=robado");
        await pagina.click("#formUrlIA button[type=submit]");
        await pagina.waitForSelector("#inpUrlIA[aria-invalid=true]");
        assert.match(await pagina.textContent("#inpUrlIAError"), /parámetros|https/);
        await pagina.fill("#inpUrlIA", "https://ia.ejemplo.invalid");
        await pagina.click("#formUrlIA button[type=submit]");
        await pagina.waitForSelector("#estadoIA[data-estado=sin_vincular]");
        assert.equal(await pagina.textContent("#urlIAActual"), "https://ia.ejemplo.invalid");
        assert.equal(await pagina.isVisible("#btVincularIA"), true);
        // Diagnóstico: el nombre no existe → paso DNS con su solución, en lenguaje claro
        await pagina.click("#btDiagnosticoIA");
        await pagina.waitForSelector("#listaDiagnosticoIA li.diag-error");
        const fallo = await pagina.textContent("#listaDiagnosticoIA li.diag-error");
        assert.match(fallo, /✗ Falla: Nombre del servidor \(DNS\)/);
        assert.match(fallo, /Qué hacer:/);
        assert.equal(await pagina.getAttribute("#estadoIA", "data-estado"), "sin_conexion");
        // Ningún secreto en el navegador
        const almacenado = await pagina.evaluate(() => JSON.stringify(localStorage) + JSON.stringify(sessionStorage));
        assert.ok(!/ia\.ejemplo|token/i.test(almacenado), almacenado);
        await contexto.close();
    });

    test("continuar sin IA y vuelta a automático", async () => {
        const { contexto, pagina } = await abrir("/front/ia.html");
        await pagina.waitForSelector("#estadoIA[data-estado]");
        await pagina.check("input[name=modoIA][value=local]");
        await pagina.waitForSelector("#avisoIA:not([hidden])");
        assert.match(await pagina.textContent("#avisoIA"), /Modo local/);
        assert.equal(await pagina.getAttribute("#estadoIA", "data-estado"), "local");
        await pagina.check("input[name=modoIA][value=auto]");
        await pagina.waitForFunction(() => /instalar/.test(document.querySelector("#avisoIA").textContent));
        await contexto.close();
    });

    test("crear apunte: sin vinculación, el servidor IA queda deshabilitado y se explica por qué", async () => {
        const { contexto, pagina, errores } = await abrir("/front/nuevo.html");
        await pagina.waitForFunction(() => !/Comprobando/.test(document.querySelector("#estadoMotorIA").textContent));
        assert.equal(await pagina.isDisabled("#motorRemoto"), true);
        assert.match(await pagina.textContent("#estadoMotorIA"), /reconocimiento local|no está vinculado/);
        assert.equal(await pagina.isChecked("input[name=motor][value=auto]"), true);
        assert.equal(await pagina.getAttribute("#estadoMotorIA a", "href"), "/front/ia.html");
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("móvil 320 px y teclado: sin desbordamiento y controles alcanzables", async () => {
        const { contexto, pagina, errores } = await abrir("/front/ia.html", { viewport: { width: 320, height: 720 } });
        await pagina.waitForSelector("#estadoIA[data-estado=local]");
        assert.equal(await sinDesbordamiento(pagina), true);
        await pagina.focus("input[name=modoIA][value=auto]");
        await pagina.keyboard.press("ArrowDown");          // grupo de radio con teclado
        assert.equal(await pagina.isChecked("input[name=modoIA][value=manual]"), true);
        assert.equal(await pagina.isVisible("#inpUrlIA"), true);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("perfil enlaza la página del servidor IA", async () => {
        const { contexto, pagina } = await abrir("/front/perfil.html");
        await pagina.waitForSelector("a[href='/front/ia.html']");
        await contexto.close();
    });
});
