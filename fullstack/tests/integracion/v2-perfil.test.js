// FRONT-19: perfil, preferencias que aplica el backend, contraseña, sesiones y borrado.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte } = require("./v2-apuntes-ayuda");
const { claveDePrueba } = require("../claves");

describe("FRONT-19 perfil", () => {
    let navegador, backend;
    before(async () => {
        navegador = await chromium.launch();
        backend = await iniciarBackendV2({ INVESTIGACION_PROVEEDOR: "wikipedia" }, { modulo: "app_wikipedia_simulada" });
    });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function abrir(opciones = {}) {
        const contexto = await navegador.newContext(opciones.viewport ? { viewport: opciones.viewport } : {});
        const cuenta = await registrar(contexto, backend.url, opciones);
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/front/perfil.html`);
        await pagina.waitForFunction(() => document.getElementById("perfilEmail").value !== "");
        return { contexto, pagina, errores, cuenta };
    }
    const perfil = async (contexto) => (await (await contexto.request.get(`${backend.url}/api/v2/perfil`)).json()).usuario;

    test("datos y preferencias se guardan en el servidor y se recuperan en otra sesión", async () => {
        const { contexto, pagina, errores, cuenta } = await abrir();
        assert.equal(await pagina.inputValue("#perfilEmail"), cuenta.email);
        assert.match(await pagina.textContent("#altaCuenta"), /Cuenta creada el/);
        await pagina.fill("#perfilNombre", "Ana María");
        await pagina.click("#formDatos button[type=submit]");
        await pagina.waitForSelector("#estadoDatos[data-tipo=exito]");
        await pagina.selectOption("#prefFuente", "pizarron");
        await pagina.selectOption("#prefEstiloPdf", "basico");
        await pagina.check("#prefOriginalesPdf");
        await pagina.uncheck("#prefComplementosPdf");
        await pagina.click("#formPreferencias button[type=submit]");
        await pagina.waitForSelector("#estadoPreferencias[data-tipo=exito]");
        // Nueva sesión (otro navegador): los valores siguen
        const otro = await navegador.newContext();
        await otro.request.post(`${backend.url}/api/v2/auth/sesion`, { data: { email: cuenta.email, password: cuenta.password }, headers: { Origin: backend.url } });
        const u = await perfil(otro);
        assert.equal(u.nombre, "Ana María");
        assert.deepEqual([u.preferencias.tipo_fuente, u.preferencias.estilo_pdf, u.preferencias.incluir_originales_pdf, u.preferencias.incluir_complementos_pdf],
                         ["pizarron", "basico", true, false]);
        // Las preferencias del PDF son las opciones propuestas al exportar
        const p2 = await otro.newPage();
        const { id } = await crearApunte(otro, backend.url, p2, { cuenta: { csrf: (await (await otro.request.get(`${backend.url}/api/v2/auth/estado`)).json()).csrf } });
        await p2.goto(`${backend.url}/front/editor.html?id=${id}`);
        await p2.waitForSelector(".bloque");
        await p2.click("#tab-pdf");
        assert.equal(await p2.inputValue("#selEstiloPdf"), "basico");
        assert.equal(await p2.isChecked("#chkOriginalesPdf"), true);
        assert.equal(await p2.isChecked("#chkComplementosPdf"), false);
        await otro.close();
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("la privacidad se aplica en el servidor, no solo en la pantalla", async () => {
        const { contexto, pagina, cuenta } = await abrir();
        const { id } = await crearApunte(contexto, backend.url, await contexto.newPage(), { cuenta });
        const investigar = () => contexto.request.post(`${backend.url}/api/v2/apuntes/${id}/investigacion`, {
            data: { consentimiento: true, conceptos: ["Derivada"] }, headers: { "X-CSRF-Token": cuenta.csrf, Origin: backend.url } });
        assert.equal((await investigar()).status(), 400, "desactivada por defecto");
        await pagina.check("#prefInvestigacion");
        await pagina.click("#formPreferencias button[type=submit]");
        await pagina.click(".dlg-app button[type=submit]");
        await pagina.waitForSelector("#estadoPreferencias[data-tipo=exito]");
        assert.equal((await investigar()).status(), 202);
        await pagina.uncheck("#prefInvestigacion");
        await pagina.click("#formPreferencias button[type=submit]");
        await pagina.waitForFunction(() => document.getElementById("estadoPreferencias").dataset.tipo === "exito" && !document.getElementById("prefInvestigacion").checked);
        await new Promise((r) => setTimeout(r, 300));
        assert.equal((await investigar()).status(), 400, "al desactivarla el servidor la rechaza");
        await contexto.close();
    });

    test("cambiar contraseña: la actual incorrecta se señala, los campos se vacían y cierra las otras sesiones", async () => {
        const { contexto, pagina, cuenta } = await abrir();
        const otro = await navegador.newContext();
        await otro.request.post(`${backend.url}/api/v2/auth/sesion`, { data: { email: cuenta.email, password: cuenta.password }, headers: { Origin: backend.url } });
        await pagina.reload();
        await pagina.waitForFunction(() => /1 sesión abierta/.test(document.getElementById("textoSesiones").textContent));
        await pagina.fill("#passActual", claveDePrueba("c24"));
        await pagina.fill("#passNueva", claveDePrueba("c19"));
        await pagina.fill("#passConfirmar", claveDePrueba("c19"));
        await pagina.click("#formPassword button[type=submit]");
        await pagina.waitForFunction(() => document.getElementById("passActualError").textContent !== "");
        assert.match(await pagina.textContent("#passActualError"), /no es correcta/);
        assert.deepEqual(await pagina.$$eval("#formPassword input[type=password]", (i) => i.map((x) => x.value)), ["", "", ""]);
        await pagina.fill("#passActual", cuenta.password);
        await pagina.fill("#passNueva", claveDePrueba("c19"));
        await pagina.fill("#passConfirmar", claveDePrueba("c19"));
        await pagina.click("#formPassword button[type=submit]");
        await pagina.waitForSelector("#estadoClave[data-tipo=exito]");
        assert.equal((await otro.request.get(`${backend.url}/api/v2/perfil`)).status(), 401, "la otra sesión se cerró");
        assert.equal((await contexto.request.get(`${backend.url}/api/v2/perfil`)).status(), 200, "esta sigue");
        assert.match(await pagina.textContent("#textoSesiones"), /Solo tienes abierta/);
        await otro.close();
        await contexto.close();
    });

    test("cerrar las demás sesiones", async () => {
        const { contexto, pagina, cuenta } = await abrir();
        const otro = await navegador.newContext();
        await otro.request.post(`${backend.url}/api/v2/auth/sesion`, { data: { email: cuenta.email, password: cuenta.password }, headers: { Origin: backend.url } });
        await pagina.reload();
        await pagina.waitForSelector("#btCerrarOtras:not([disabled])");
        await pagina.click("#btCerrarOtras");
        await pagina.waitForSelector("#estadoSesiones[data-tipo=exito]");
        assert.equal((await otro.request.get(`${backend.url}/api/v2/perfil`)).status(), 401);
        await otro.close();
        await contexto.close();
    });

    test("sesión caducada: vuelve a iniciar sesión sin mostrar datos", async () => {
        const { contexto, pagina } = await abrir();
        await contexto.clearCookies();
        await pagina.fill("#perfilNombre", "Cambio");
        await pagina.click("#formDatos button[type=submit]");
        await pagina.waitForURL(/cuenta\.html\?.*motivo=expirada/);
        await contexto.close();
    });

    test("borrar la cuenta: contraseña + escribir BORRAR, y se borran sus archivos", async () => {
        const { contexto, pagina, cuenta } = await abrir();
        await crearApunte(contexto, backend.url, await contexto.newPage(), { cuenta });
        await pagina.fill("#borrarPassword", claveDePrueba("c20"));
        await pagina.click("#formBorrar button[type=submit]");
        await pagina.fill("#confirmarTexto", "BORRAR");
        await pagina.click(".dlg-app button[type=submit]");
        await pagina.waitForFunction(() => document.getElementById("borrarPasswordError").textContent !== "");
        assert.equal(await pagina.inputValue("#borrarPassword"), "");
        await pagina.fill("#borrarPassword", cuenta.password);
        await pagina.click("#formBorrar button[type=submit]");
        assert.equal(await pagina.isDisabled(".dlg-app button[type=submit]"), true, "sin escribir BORRAR no deja");
        await pagina.fill("#confirmarTexto", "BORRAR");
        await Promise.all([pagina.waitForURL(/motivo=cuenta-borrada/), pagina.click(".dlg-app button[type=submit]")]);
        assert.match(await pagina.textContent("#avisoCuenta"), /se borraron/);
        const carpeta = path.join(backend.datos, "archivos", cuenta.usuario.id);
        assert.ok(!fs.existsSync(carpeta) || fs.readdirSync(carpeta).length === 0, "sin archivos del usuario");
        await contexto.close();
    });

    test("móvil y accesibilidad básica", async () => {
        const { contexto, pagina } = await abrir({ viewport: { width: 360, height: 780 } });
        assert.ok(await sinDesbordamiento(pagina));
        const sinEtiqueta = await pagina.$$eval("main input:not([type=hidden]), main select", (els) =>
            els.filter((e) => !(e.labels && e.labels.length) && !e.getAttribute("aria-label")).map((e) => e.id));
        assert.deepEqual(sinEtiqueta, []);
        await contexto.close();
    });
});
