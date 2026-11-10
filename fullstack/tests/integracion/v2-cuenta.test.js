// FRONT-17: registro, inicio de sesión, cierre y recuperación de contraseña con el
// backend real. El «correo» de recuperación se lee del buzón de desarrollo.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { claveDePrueba } = require("../claves");

describe("FRONT-17 cuentas", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function nueva(viewport) {
        const contexto = await navegador.newContext(viewport ? { viewport } : {});
        const pagina = await contexto.newPage();
        const peticiones = [];
        pagina.on("request", (r) => { if (r.url().includes("/api/v2/")) peticiones.push(`${r.method()} ${new URL(r.url()).pathname}`); });
        return { contexto, pagina, peticiones, errores: vigilarConsola(pagina) };
    }
    const aviso = (pagina) => pagina.textContent("#avisoCuenta");

    test("validación en el cliente: no se envía nada inválido", async () => {
        const { contexto, pagina, peticiones } = await nueva();
        await pagina.goto(`${backend.url}/front/cuenta.html?modo=registro`);
        await pagina.fill("#regNombre", "Ana");
        await pagina.fill("#regEmail", "no-es-un-email");
        await pagina.fill("#regPassword", claveDePrueba("corta").slice(-5));
        await pagina.fill("#regConfirmar", claveDePrueba("otra").slice(-4));
        await pagina.click("#formRegistro button[type=submit]");
        assert.match(await pagina.textContent("#regEmailError"), /email válido/);
        assert.match(await pagina.textContent("#regPasswordError"), /al menos 10/);
        assert.match(await pagina.textContent("#regConfirmarError"), /no coinciden/);
        assert.equal(await pagina.getAttribute("#regEmail", "aria-invalid"), "true");
        assert.equal(await pagina.evaluate(() => document.activeElement.id), "regEmail");
        assert.ok(!peticiones.some((p) => p.startsWith("POST")), "no hubo POST");
        await contexto.close();
    });

    test("registro → sesión activa, cookie HttpOnly y nada secreto en el almacenamiento", async () => {
        const { contexto, pagina, errores } = await nueva();
        await pagina.goto(`${backend.url}/front/cuenta.html`);
        await pagina.click("#tabRegistro");
        await pagina.fill("#regNombre", "Ana Pérez");
        await pagina.fill("#regEmail", "ana@example.com");
        await pagina.fill("#regPassword", claveDePrueba("c14"));
        await pagina.fill("#regConfirmar", claveDePrueba("c14"));
        await Promise.all([pagina.waitForURL(/\/front\/nuevo\.html$/), pagina.click("#formRegistro button[type=submit]")]);
        const cookie = (await contexto.cookies()).find((c) => c.name === "apuntia_sesion");
        assert.ok(cookie && cookie.httpOnly && cookie.sameSite === "Lax");
        const almacenado = await pagina.evaluate(() => JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }));
        assert.ok(!almacenado.includes(claveDePrueba("c14")) && !almacenado.includes(cookie.value), "sin contraseñas ni tokens");
        assert.ok(!pagina.url().includes(claveDePrueba("c14")));
        assert.deepEqual(errores.filter((e) => !e.includes("404")), []);
        await contexto.close();
    });

    test("email ya usado: mensaje que no confirma la cuenta y caminos alternativos", async () => {
        const { contexto, pagina } = await nueva();
        await pagina.goto(`${backend.url}/front/cuenta.html?modo=registro`);
        await pagina.fill("#regNombre", "Otra");
        await pagina.fill("#regEmail", "ana@example.com");
        await pagina.fill("#regPassword", claveDePrueba("c15"));
        await pagina.fill("#regConfirmar", claveDePrueba("c15"));
        await pagina.click("#formRegistro button[type=submit]");
        await pagina.waitForSelector("#avisoCuenta[data-tipo=error]");
        assert.match(await aviso(pagina), /No se pudo crear la cuenta/);
        assert.equal(await pagina.inputValue("#regPassword"), "", "la contraseña se borra");
        await pagina.click("#avisoCuenta >> text=Recuperar contraseña");
        assert.equal(await pagina.inputValue("#olvidoEmail"), "ana@example.com");
        await contexto.close();
    });

    test("inicio de sesión: error genérico, mostrar contraseña, volver a la página pedida y sin redirección abierta", async () => {
        const { contexto, pagina } = await nueva();
        await pagina.goto(`${backend.url}/front/cuenta.html?volver=${encodeURIComponent("/front/ayuda.html")}`);
        assert.match(await aviso(pagina), /Inicia sesión para continuar/);
        await pagina.fill("#entrarEmail", "ana@example.com");
        await pagina.fill("#entrarPassword", claveDePrueba("c16"));
        await pagina.click("#panelEntrar .ver-password");
        assert.equal(await pagina.getAttribute("#entrarPassword", "type"), "text");
        assert.equal(await pagina.getAttribute("#panelEntrar .ver-password", "aria-pressed"), "true");
        await pagina.click("#formEntrar button[type=submit]");
        await pagina.waitForSelector("#avisoCuenta[data-tipo=error]");
        assert.match(await aviso(pagina), /Email o contraseña incorrectos/);
        assert.equal(await pagina.inputValue("#entrarPassword"), "");
        await pagina.fill("#entrarPassword", claveDePrueba("c14"));
        await Promise.all([pagina.waitForURL(/\/front\/ayuda\.html$/), pagina.click("#formEntrar button[type=submit]")]);
        await contexto.close();

        const otro = await nueva();
        await otro.pagina.goto(`${backend.url}/front/cuenta.html?volver=${encodeURIComponent("https://malicioso.example/")}`);
        await otro.pagina.fill("#entrarEmail", "ana@example.com");
        await otro.pagina.fill("#entrarPassword", claveDePrueba("c14"));
        await Promise.all([otro.pagina.waitForURL(/\/front\/apuntes\.html$/), otro.pagina.click("#formEntrar button[type=submit]")]);
        await otro.contexto.close();
    });

    test("recuperación: enlace de un solo uso, token fuera de la barra y nueva contraseña", async () => {
        const { contexto, pagina } = await nueva();
        await pagina.goto(`${backend.url}/front/cuenta.html`);
        await pagina.click("#tabOlvido");
        await pagina.fill("#olvidoEmail", "ana@example.com");
        await pagina.click("#formOlvido button[type=submit]");
        await pagina.waitForSelector("#avisoCuenta[data-tipo=exito]");
        assert.match(await aviso(pagina), /Si existe una cuenta/);
        const buzon = path.join(backend.datos, "buzon");
        const mensaje = fs.readFileSync(path.join(buzon, fs.readdirSync(buzon)[0]), "utf8");
        const enlace = mensaje.match(/(http\S+#recuperar=\S+)/)[1];
        assert.ok(enlace.includes("/front/cuenta.html#recuperar="));
        await pagina.goto(enlace);
        await pagina.waitForSelector("#panelRestablecer:not([hidden])");
        assert.ok(!pagina.url().includes("recuperar"), "el token se quita de la URL");
        await pagina.fill("#restPassword", claveDePrueba("c17"));
        await pagina.fill("#restConfirmar", claveDePrueba("c17"));
        await pagina.click("#formRestablecer button[type=submit]");
        await pagina.waitForSelector("#avisoCuenta[data-tipo=exito]");
        assert.match(await aviso(pagina), /Contraseña cambiada/);
        // El mismo enlace ya no sirve
        await pagina.goto("about:blank");
        await pagina.goto(enlace);
        await pagina.fill("#restPassword", claveDePrueba("c18"));
        await pagina.fill("#restConfirmar", claveDePrueba("c18"));
        await pagina.click("#formRestablecer button[type=submit]");
        await pagina.waitForSelector("#avisoCuenta[data-tipo=error]");
        assert.match(await aviso(pagina), /no es válido o ya caducó/);
        await pagina.click("#avisoCuenta >> text=Pedir otro enlace");
        assert.equal(await pagina.isVisible("#panelOlvido"), true);
        // Entra con la nueva
        await pagina.click("#tabEntrar");
        await pagina.fill("#entrarEmail", "ana@example.com");
        await pagina.fill("#entrarPassword", claveDePrueba("c17"));
        await Promise.all([pagina.waitForURL(/apuntes\.html$/), pagina.click("#formEntrar button[type=submit]")]);
        await contexto.close();
    });

    test("cerrar sesión y sesión caducada", async () => {
        const { contexto, pagina } = await nueva();
        await registrar(contexto, backend.url);
        await pagina.goto(`${backend.url}/front/cuenta.html`);
        await pagina.waitForSelector("#yaConectado:not([hidden])");
        await Promise.all([pagina.waitForURL(/motivo=salida/), pagina.click("#btSalirCuenta")]);
        assert.match(await aviso(pagina), /Cerraste la sesión/);
        const estado = await (await contexto.request.get(`${backend.url}/api/v2/auth/estado`)).json();
        assert.equal(estado.autenticado, false);
        await pagina.goto(`${backend.url}/front/cuenta.html?motivo=expirada&volver=%2Ffront%2Fayuda.html`);
        assert.match(await aviso(pagina), /sesión caducó/);
        await contexto.close();
    });

    test("móvil y teclado", async () => {
        const { contexto, pagina } = await nueva({ width: 320, height: 700 });
        await pagina.goto(`${backend.url}/front/cuenta.html`);
        assert.ok(await sinDesbordamiento(pagina));
        await pagina.focus("#tabEntrar");
        await pagina.keyboard.press("ArrowRight");
        assert.equal(await pagina.evaluate(() => document.activeElement.id), "tabRegistro");
        assert.equal(await pagina.isVisible("#panelRegistro"), true);
        await contexto.close();
    });
});
