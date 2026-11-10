// FRONT-11: concepto visual, navegación con y sin sesión, ayuda con el estado
// real de las funciones y la página de inicio servida por el backend.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");

const FOTO = path.resolve(__dirname, "..", "..", "..", "back", "bd", "img", "image.png");

describe("FRONT-11 navegación y concepto", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    test("sin sesión: solo enlaces públicos y «Entrar»; la ayuda muestra el estado real", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/inicio`);
        await pagina.waitForSelector("#navPrincipal[data-sesion=sin-sesion]");
        const enlaces = await pagina.$$eval("#navPrincipal a", (as) => as.map((a) => a.textContent));
        assert.deepEqual(enlaces, ["Inicio", "Cómo funciona", "Ayuda", "Entrar"]);
        assert.match(await pagina.textContent(".tagline"), /pizarrón o de un cuaderno/);
        await pagina.click("text=Ayuda");
        await pagina.waitForSelector("#tablaFunciones tr:nth-child(6)");
        const filas = await pagina.$$eval("#tablaFunciones tr", (tr) => tr.map((f) => f.textContent));
        assert.ok(filas.some((f) => /Información complementaria.*No disponible/.test(f)), "investigación desactivada");
        assert.ok(filas.some((f) => /Reconocer texto \(OCR\).*Disponible/.test(f)), "OCR real disponible");
        const privados = await pagina.$$eval("#navPrincipal a", (as) => as.map((a) => a.textContent));
        assert.ok(!privados.includes("Mis apuntes") && privados.includes("Entrar"));
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("con sesión: Crear apuntes, Mis apuntes, Perfil y Salir", async () => {
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/inicio`);
        await pagina.waitForSelector("#navPrincipal[data-sesion=activa]");
        const enlaces = await pagina.$$eval("#navPrincipal a", (as) => as.map((a) => a.textContent));
        assert.deepEqual(enlaces.slice(-3), ["Crear apuntes", "Mis apuntes", "Perfil"]);
        await pagina.goto(`${backend.url}/front/ayuda.html`);
        await pagina.waitForSelector("#btSalir");
        await contexto.close();
    });

    test("la mejora de una foto (PNG) sigue funcionando desde /inicio, en el mismo origen", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/inicio`);
        await pagina.evaluate(() => window.ApuntIA.app.limitesListos);
        assert.equal(await pagina.evaluate(() => window.ApuntIA.api.urlBase()), backend.url);
        await pagina.setInputFiles("#inpImagen", FOTO);
        await pagina.click("#btEnviar");
        await pagina.waitForFunction(() => document.getElementById("estado").dataset.estado === "hecho", null, { timeout: 30000 });
        assert.equal(await pagina.isVisible("#imagenResultado"), true);
        assert.deepEqual(errores, [], "sin errores ni violaciones de la CSP");
        await contexto.close();
    });

    test("cabeceras: CSP sin scripts en línea y sin servir las pruebas", async () => {
        const r = await fetch(`${backend.url}/front/ayuda.html`);
        assert.match(r.headers.get("content-security-policy"), /script-src 'self'/);
        assert.equal(r.headers.get("x-frame-options"), "DENY");
        assert.equal((await fetch(`${backend.url}/front/tests/servidor.js`)).status, 404);
        assert.equal((await fetch(`${backend.url}/front/README.md`)).status, 404);
        assert.deepEqual(await (await fetch(`${backend.url}/`)).json(), { message: "Hola Mundo" }, "GET / sigue igual (v1)");
    });

    test("teclado y pantallas estrechas", async () => {
        for (const ancho of [320, 768, 1280]) {
            const contexto = await navegador.newContext({ viewport: { width: ancho, height: 800 } });
            const pagina = await contexto.newPage();
            for (const ruta of ["/inicio", "/front/ayuda.html"]) {
                await pagina.goto(backend.url + ruta);
                await pagina.waitForSelector("#navPrincipal a");
                assert.ok(await sinDesbordamiento(pagina), `${ruta} a ${ancho}px`);
            }
            await pagina.keyboard.press("Tab");
            assert.equal(await pagina.evaluate(() => document.activeElement.className), "skip");
            await contexto.close();
        }
    });
});
