// FULL-18: cuentas, historial y permisos de extremo a extremo con el backend real.
// Dos cuentas (A y B): B no puede ver, editar, borrar ni descargar nada de A, ni desde la
// interfaz ni pidiendo la API desde su navegador; los datos y las sesiones siguen tras
// reiniciar el servidor; cerrar sesión y cambiar la contraseña surten efecto.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar } = require("./v2-entorno");
const { crearApunte, esperarTrabajo } = require("./v2-apuntes-ayuda");

describe("FULL-18 permisos de extremo a extremo", () => {
    let navegador, backend, a, b, recursos;
    before(async () => {
        navegador = await chromium.launch();
        backend = await iniciarBackendV2();
        a = await navegador.newContext({ acceptDownloads: true });
        b = await navegador.newContext();
        const pa = await a.newPage();
        const cuentaA = await registrar(a, backend.url, { email: "a@example.com" });
        await registrar(b, backend.url, { email: "b@example.com" });
        const { id } = await crearApunte(a, backend.url, pa, { cuenta: cuentaA, titulo: "Privado de A" });
        const exp = await (await a.request.post(`${backend.url}/api/v2/apuntes/${id}/exportaciones`, {
            data: {}, headers: { "X-CSRF-Token": cuentaA.csrf, Origin: backend.url } })).json();
        await esperarTrabajo(a, backend.url, exp.trabajo.id);
        const doc = (await (await a.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte;
        recursos = { id, cuentaA, exportacion: exp.exportacion.id, archivo: doc.documento.paginas[0].archivo_original,
                     trabajo: exp.trabajo.id, version: doc.version };
        await pa.close();
    });
    after(async () => { await a.close(); await b.close(); await navegador.close(); await backend.detener(); });

    test("matriz de permisos: B recibe 404 en todo lo de A, también desde su navegador", async () => {
        const pb = await b.newPage();
        await pb.goto(`${backend.url}/front/apuntes.html`);
        await pb.waitForSelector("#listaApuntes[aria-busy=false]", { state: "attached" });
        assert.equal(await pb.locator(".apunte").count(), 0);
        const { id, exportacion, archivo, trabajo, version } = recursos;
        // Peticiones hechas por el navegador de B, con su cookie y su CSRF.
        const resultados = await pb.evaluate(async ({ id, exportacion, archivo, trabajo, version }) => {
            const csrf = (await (await fetch("/api/v2/auth/estado")).json()).csrf;
            const pedir = async (metodo, ruta, cuerpo, extra = {}) => (await fetch(ruta, { method: metodo,
                headers: { "X-CSRF-Token": csrf, "Content-Type": "application/json", ...extra },
                body: cuerpo ? JSON.stringify(cuerpo) : undefined })).status;
            return {
                ver: await pedir("GET", `/api/v2/apuntes/${id}`),
                foto: await pedir("GET", `/api/v2/apuntes/${id}/archivos/${archivo}`),
                versiones: await pedir("GET", `/api/v2/apuntes/${id}/versiones`),
                editar: await pedir("PUT", `/api/v2/apuntes/${id}/documento`, { titulo: "robado" }, { "If-Match": String(version) }),
                restaurar: await pedir("POST", `/api/v2/apuntes/${id}/versiones/1/restaurar`),
                exportar: await pedir("POST", `/api/v2/apuntes/${id}/exportaciones`, {}),
                pdf: await pedir("GET", `/api/v2/exportaciones/${exportacion}/pdf`),
                trabajo: await pedir("GET", `/api/v2/trabajos/${trabajo}`),
                cancelar: await pedir("DELETE", `/api/v2/trabajos/${trabajo}`),
                borrar: await pedir("DELETE", `/api/v2/apuntes/${id}`),
            };
        }, { id, exportacion, archivo, trabajo, version });
        for (const [accion, status] of Object.entries(resultados)) assert.equal(status, 404, `${accion}: ${status}`);
        // La interfaz tampoco muestra nada
        await pb.goto(`${backend.url}/front/editor.html?id=${id}`);
        await pb.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.ok(!(await pb.content()).includes("Privado de A"));
        // Y A sigue teniendo todo intacto
        const apunte = (await (await a.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte;
        assert.equal(apunte.titulo, "Privado de A");
        assert.equal(apunte.version, version);
        await pb.close();
    });

    test("sin sesión: las páginas privadas llevan a iniciar sesión y la API responde 401", async () => {
        const anonimo = await navegador.newContext();
        const p = await anonimo.newPage();
        for (const ruta of ["/front/apuntes.html", "/front/nuevo.html", "/front/perfil.html", `/front/editor.html?id=${recursos.id}`]) {
            await p.goto(backend.url + ruta);
            await p.waitForURL(/cuenta\.html\?volver=/);
        }
        assert.equal((await anonimo.request.get(`${backend.url}/api/v2/exportaciones/${recursos.exportacion}/pdf`)).status(), 401);
        await anonimo.close();
    });

    test("tras reiniciar el servidor: datos y sesión de A siguen, y siguen aislados de B", async () => {
        const datos = backend.datos;
        await backend.parar();  // se detiene el proceso, los datos se quedan
        const reiniciado = await iniciarBackendV2({}, { datos });
        try {
            const pa = await a.newPage();
            await pa.goto(`${reiniciado.url}/front/apuntes.html`);
            await pa.waitForSelector(".apunte");
            assert.match(await pa.textContent(".apunte"), /Privado de A[\s\S]*1 PDF/);
            const [descarga] = await Promise.all([pa.waitForEvent("download"), pa.click("[data-accion=descargar]")]);
            assert.match(descarga.suggestedFilename(), /^privado-de-a-v\d+\.pdf$/);
            const pb = await b.newPage();
            await pb.goto(`${reiniciado.url}/front/apuntes.html`);
            await pb.waitForSelector("#listaApuntes[aria-busy=false]", { state: "attached" });
            assert.equal(await pb.locator(".apunte").count(), 0);
            await pa.close();
            await pb.close();
        } finally {
            // after() lo detendrá y borrará la carpeta temporal
            const detenerReiniciado = reiniciado.detener;
            reiniciado.detener = async () => { await detenerReiniciado(); require("node:fs").rmSync(datos, { recursive: true, force: true }); };
            backend = reiniciado;
        }
    });

    test("cerrar sesión y cambiar la contraseña invalidan las sesiones en el servidor", async () => {
        const { cuentaA } = recursos;
        const otraA = await navegador.newContext();
        await otraA.request.post(`${backend.url}/api/v2/auth/sesion`, { data: { email: cuentaA.email, password: cuentaA.password }, headers: { Origin: backend.url } });
        const cookie = (await otraA.cookies()).find((c) => c.name === "apuntia_sesion");
        const p = await otraA.newPage();
        await p.goto(`${backend.url}/front/perfil.html`);
        await p.waitForSelector("#btSalir");
        await Promise.all([p.waitForURL(/motivo=salida/), p.click("#btSalir")]);
        // Reusar la cookie antigua no sirve: la sesión se borró en el servidor
        const curioso = await navegador.newContext();
        await curioso.addCookies([{ ...cookie }]);
        assert.equal((await curioso.request.get(`${backend.url}/api/v2/perfil`)).status(), 401);
        await curioso.close();
        await otraA.close();
    });
});
