// FRONT-20: mensajes de error uniformes y contenido no confiable inerte en todas las
// pantallas con cuenta. El backend es real; algunos errores se fuerzan interceptando la
// respuesta en el navegador (page.route) para no depender de provocarlos de verdad.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola } = require("./v2-entorno");
const { crearApunte } = require("./v2-apuntes-ayuda");
const { claveDePrueba } = require("../claves");

const error = (status, codigo, mensaje) => ({ status, contentType: "application/json", body: JSON.stringify({ error: { codigo, mensaje } }) });

describe("FRONT-20 errores y seguridad de interfaz", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function lista(rutaFalsa) {
        const contexto = await navegador.newContext();
        const cuenta = await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        if (rutaFalsa) await pagina.route(/\/api\/v2\/apuntes\?/, rutaFalsa);
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector("#listaApuntes[aria-busy=false]", { state: "attached" });
        return { contexto, pagina, errores, cuenta };
    }
    const aviso = async (p) => ({ tipo: await p.getAttribute("#avisoLista", "data-tipo"), rol: await p.getAttribute("#avisoLista", "role"),
                                  texto: await p.textContent("#avisoLista") });

    test("red cortada: mensaje claro, sin bucles, y «Reintentar» recupera", async () => {
        let peticiones = 0;
        const { contexto, pagina } = await lista((r) => { peticiones++; return r.abort("internetdisconnected"); });
        const a = await aviso(pagina);
        assert.equal(a.tipo, "error");
        assert.equal(a.rol, "alert");
        assert.match(a.texto, /No se pudo conectar|No hay conexión/);
        await pagina.waitForTimeout(1500);
        assert.equal(peticiones, 1, "no reintenta solo en bucle");
        await pagina.unroute(/\/api\/v2\/apuntes\?/);
        await pagina.click("#avisoLista >> text=Reintentar");
        await pagina.waitForFunction(() => /Todavía no tienes apuntes/.test(document.getElementById("resumenLista").textContent));
        assert.equal(await pagina.isHidden("#avisoLista"), true);
        await contexto.close();
    });

    test("500: mensaje del catálogo, nunca el detalle interno", async () => {
        const { contexto, pagina, errores } = await lista((r) => r.fulfill(error(500, "ERROR_INTERNO", "Traceback /home/servidor/app.py token=abc")));
        const a = await aviso(pagina);
        assert.match(a.texto, /Ocurrió un problema en el servidor/);
        assert.ok(!/Traceback|\/home|abc/.test(a.texto));
        assert.ok(errores.some((e) => /ERROR_INTERNO/.test(e)), "se registra en la consola el código, sin datos");
        assert.ok(!errores.some((e) => /Traceback|token=/.test(e)));
        await contexto.close();
    });

    test("500 con referencia: se muestra para correlacionar con el registro del servidor", async () => {
        const { contexto, pagina } = await lista((r) => r.fulfill({ ...error(500, "ERROR_INTERNO", "x"), headers: { "X-ApuntIA-Error-Id": "ab12cd34ef56" } }));
        assert.match((await aviso(pagina)).texto, /Referencia: ab12cd34ef56/);
        await contexto.close();
    });

    test("429 es un aviso (se puede continuar) con el mensaje del servidor", async () => {
        const { contexto, pagina } = await lista((r) => r.fulfill(error(429, "DEMASIADAS_PETICIONES", "Has hecho demasiadas peticiones seguidas. Espera un poco.")));
        const a = await aviso(pagina);
        assert.equal(a.tipo, "aviso");
        assert.equal(a.rol, "status");
        assert.match(a.texto, /Espera un poco/);
        await contexto.close();
    });

    test("código desconocido: texto genérico útil", async () => {
        const { contexto, pagina } = await lista((r) => r.fulfill({ status: 502, contentType: "text/html", body: "<h1>Bad gateway</h1>" }));
        const a = await aviso(pagina);
        assert.match(a.texto, /Ocurrió un problema en el servidor|Algo salió mal/);
        assert.ok(!/Bad gateway|<h1>/.test(a.texto));
        await contexto.close();
    });

    test("401 en una página privada: a iniciar sesión, y luego de vuelta", async () => {
        const { contexto, pagina, cuenta } = await lista();
        await contexto.clearCookies();
        await pagina.click("#formFiltros button[type=submit]");
        await pagina.waitForURL(/cuenta\.html\?volver=%2Ffront%2Fapuntes\.html&motivo=expirada/);
        await pagina.fill("#entrarEmail", cuenta.email);
        await pagina.fill("#entrarPassword", cuenta.password);
        await Promise.all([pagina.waitForURL(/apuntes\.html$/), pagina.click("#formEntrar button[type=submit]")]);
        await contexto.close();
    });

    test("413 al subir fotos: mensaje junto al envío", async () => {
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await pagina.route("**/api/v2/apuntes", (r) => r.fulfill(error(413, "CARGA_DEMASIADO_GRANDE", "La petición supera el máximo de 200 MB.")));
        await pagina.goto(`${backend.url}/front/nuevo.html`);
        await pagina.waitForSelector("#navPrincipal a");
        const png = await pagina.evaluate(() => { const c = document.createElement("canvas"); c.width = 900; c.height = 700; return c.toDataURL("image/png").split(",")[1]; });
        await pagina.setInputFiles("#inpFotos", { name: "a.png", mimeType: "image/png", buffer: Buffer.from(png, "base64") });
        await pagina.waitForSelector("#listaPaginas li");
        await pagina.click("#btCrear");
        await pagina.waitForSelector("#avisoNuevo[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoNuevo"), /supera el máximo/);
        assert.equal(await pagina.locator("#listaPaginas li").count(), 1, "las fotos siguen");
        await contexto.close();
    });

    test("títulos y nombres maliciosos se muestran como texto en todas las pantallas", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const titulo = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>';
        const { id } = await crearApunte(contexto, backend.url, pagina, { titulo });
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector(".apunte h2");
        assert.equal(await pagina.textContent(".apunte h2"), titulo);
        await pagina.click("[data-accion=eliminar]");
        assert.match(await pagina.textContent(".dlg-app h2"), /<img src=x/);
        await pagina.click(".dlg-app >> text=Cancelar");
        await pagina.goto(`${backend.url}/front/editor.html?id=${id}`);
        await pagina.waitForSelector(".bloque");
        assert.equal(await pagina.inputValue("#inpTituloApunte"), titulo);
        assert.equal(await pagina.evaluate(() => window.__xss), undefined);
        assert.equal(await pagina.locator("img[src=x], script:not([src])").count(), 0);
        await contexto.close();
    });

    test("cerrar sesión no deja datos de la cuenta anterior al entrar con otra", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        await crearApunte(contexto, backend.url, pagina, { titulo: "Privado de A" });
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector(".apunte");
        await Promise.all([pagina.waitForURL(/motivo=salida/), pagina.click("#btSalir")]);
        await pagina.click("#tabRegistro");
        await pagina.fill("#regNombre", "B");
        await pagina.fill("#regEmail", "b-errores@example.com");
        await pagina.fill("#regPassword", claveDePrueba("c21"));
        await pagina.fill("#regConfirmar", claveDePrueba("c21"));
        await Promise.all([pagina.waitForURL(/nuevo\.html/), pagina.click("#formRegistro button[type=submit]")]);
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector("#listaApuntes[aria-busy=false]");
        assert.equal(await pagina.locator(".apunte").count(), 0);
        assert.ok(!(await pagina.content()).includes("Privado de A"));
        await contexto.close();
    });
});
