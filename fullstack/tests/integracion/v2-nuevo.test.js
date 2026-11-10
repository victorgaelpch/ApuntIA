// FRONT-12: subir, ordenar y quitar varias fotos y crear el apunte con el backend real.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");

// PNG generados en el navegador: oscuros (pizarrón) o claros (cuaderno), con un texto distinto.
async function crearFotos(pagina, especificaciones) {
    const datos = await pagina.evaluate((specs) => specs.map(({ texto, oscura, ancho = 1200, alto = 900 }) => {
        const c = document.createElement("canvas");
        c.width = ancho; c.height = alto;
        const g = c.getContext("2d");
        g.fillStyle = oscura ? "#123b30" : "#f7f5ee"; g.fillRect(0, 0, ancho, alto);
        g.fillStyle = oscura ? "#ffffff" : "#1a1a1a"; g.font = "bold 90px sans-serif"; g.fillText(texto, 80, 300);
        return c.toDataURL("image/png").split(",")[1];
    }), especificaciones);
    return datos.map((b64, i) => ({ name: `${especificaciones[i].texto}.png`, mimeType: "image/png", buffer: Buffer.from(b64, "base64") }));
}

const sha = (b) => crypto.createHash("sha256").update(b).digest("hex");

describe("FRONT-12 varias fotos", () => {
    let navegador, backend;
    before(async () => {
        navegador = await chromium.launch({ args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"] });
        backend = await iniciarBackendV2({ MAX_UPLOAD_MB: "1" });
    });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function nueva(viewport) {
        const contexto = await navegador.newContext(viewport ? { viewport } : {});
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await pagina.goto(`${backend.url}/front/nuevo.html`);
        await pagina.waitForSelector("#navPrincipal a");
        return { contexto, pagina, errores };
    }
    const nombres = (pagina) => pagina.$$eval("#listaPaginas .pagina__nombre", (e) => e.map((x) => x.textContent.split(" · ")[0]));

    test("sin sesión lleva a iniciar sesión y vuelve", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/front/nuevo.html`);
        await pagina.waitForURL(/cuenta\.html\?volver=%2Ffront%2Fnuevo\.html/);
        await contexto.close();
    });

    test("una foto elegida mientras la página aún se prepara no se pierde", async () => {
        // Antes, el evento se escuchaba tras esperar a la sesión y a /salud: con un servidor lento (la CI)
        // la foto elegida en ese intervalo se perdía sin aviso.
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await pagina.route("**/salud", async (ruta) => { await new Promise((r) => setTimeout(r, 1500)); await ruta.continue(); });
        await pagina.goto(`${backend.url}/front/nuevo.html`, { waitUntil: "domcontentloaded" });
        const [foto] = await crearFotos(pagina, [{ texto: "rapida" }]);
        await pagina.setInputFiles("#inpFotos", foto);
        await pagina.waitForSelector("#listaPaginas li", { timeout: 15000 });
        await contexto.close();
    });

    test("añadir, sugerir tipo, reordenar, quitar, evitar duplicados y enviar en el orden elegido", async () => {
        const { contexto, pagina, errores } = await nueva();
        const fotos = await crearFotos(pagina, [{ texto: "uno", oscura: true }, { texto: "dos" }, { texto: "tres" }]);
        await pagina.setInputFiles("#inpFotos", fotos);
        await pagina.waitForFunction(() => document.querySelectorAll("#listaPaginas li").length === 3);
        assert.deepEqual(await nombres(pagina), ["uno.png", "dos.png", "tres.png"]);
        assert.match(await pagina.textContent("#tipo-pag1 option[value=auto]"), /pizarrón/);
        assert.match(await pagina.textContent("#tipo-pag2 option[value=auto]"), /cuaderno/);
        // Duplicado
        await pagina.setInputFiles("#inpFotos", [fotos[1]]);
        await pagina.waitForSelector("#avisoNuevo[data-tipo=aviso]");
        assert.match(await pagina.textContent("#avisoNuevo"), /ya estaba/);
        assert.equal(await pagina.locator("#listaPaginas li").count(), 3);
        // Reordenar con teclado/botones: «tres» sube dos veces, y se quita «dos»
        await pagina.click('[aria-label="Subir la página 3"]');
        await pagina.click('[aria-label="Subir la página 2"]');
        assert.deepEqual(await nombres(pagina), ["tres.png", "uno.png", "dos.png"]);
        await pagina.click('[aria-label="Quitar la página 3"]');
        assert.deepEqual(await nombres(pagina), ["tres.png", "uno.png"]);
        await pagina.selectOption("#tipo-pag3", "pizarron");
        await pagina.fill("#inpTitulo", "Clase del lunes");
        await Promise.all([pagina.waitForURL(/editor\.html\?id=/), pagina.click("#btCrear")]);
        const id = new URL(pagina.url()).searchParams.get("id");
        const apunte = (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte;
        assert.equal(apunte.titulo, "Clase del lunes");
        const paginas = apunte.documento.paginas;
        assert.deepEqual(paginas.map((p) => p.tipo_fuente), ["pizarron", "pizarron"]);
        // El backend conserva el orden: compara los bytes originales
        for (const [i, foto] of [fotos[2], fotos[0]].entries()) {
            const r = await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}/archivos/${paginas[i].archivo_original}`);
            assert.equal(sha(await r.body()), sha(foto.buffer), `página ${i + 1}`);
        }
        assert.deepEqual(errores.filter((e) => !e.includes("404")), []);
        await contexto.close();
    });

    test("archivos inválidos y demasiado grandes se marcan y bloquean el envío", async () => {
        const { contexto, pagina } = await nueva();
        const [buena] = await crearFotos(pagina, [{ texto: "buena" }]);
        const grande = { name: "grande.png", mimeType: "image/png", buffer: Buffer.concat([buena.buffer, Buffer.alloc(1100 * 1024)]) };
        const falsa = { name: "falsa.png", mimeType: "image/png", buffer: Buffer.from("<html>no soy una imagen</html>") };
        await pagina.setInputFiles("#inpFotos", [buena, falsa, grande]);
        await pagina.waitForFunction(() => document.querySelectorAll("#listaPaginas li").length === 3);
        const errores = await pagina.$$eval(".pagina__error", (e) => e.map((x) => x.textContent));
        assert.equal(errores.length, 2);
        assert.match(errores.join(" "), /no es una imagen admitida/);
        assert.match(errores.join(" "), /más de 1 MB/);
        assert.equal(await pagina.isDisabled("#btCrear"), true);
        await pagina.click('[aria-label="Quitar la página 3"]');
        await pagina.click('[aria-label="Quitar la página 2"]');
        assert.equal(await pagina.isDisabled("#btCrear"), false);
        await contexto.close();
    });

    test("fallo de red: reintento sin duplicar el apunte (Idempotency-Key)", async () => {
        const { contexto, pagina } = await nueva();
        await pagina.setInputFiles("#inpFotos", await crearFotos(pagina, [{ texto: "red" }]));
        await pagina.waitForSelector("#listaPaginas li");
        let primera = true;
        const claves = [];
        await pagina.route("**/api/v2/apuntes", async (ruta) => {
            claves.push(ruta.request().headers()["idempotency-key"]);
            // La primera petición llega al servidor, pero la respuesta «se pierde».
            if (primera) { primera = false; await ruta.fetch(); return ruta.abort("connectionreset"); }
            return ruta.continue();
        });
        await pagina.click("#btCrear");
        await pagina.waitForSelector("#avisoNuevo[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoNuevo"), /conectar/i);
        await Promise.all([pagina.waitForURL(/editor\.html/), pagina.click("#avisoNuevo >> text=Reintentar")]);
        assert.equal(claves.length, 2);
        assert.equal(claves[0], claves[1], "misma clave en el reintento");
        const lista = await (await contexto.request.get(`${backend.url}/api/v2/apuntes`)).json();
        assert.equal(lista.total, 1, "no se duplicó el apunte");
        await contexto.close();
    });

    test("cancelar el envío conserva las fotos", async () => {
        const { contexto, pagina } = await nueva();
        await pagina.setInputFiles("#inpFotos", await crearFotos(pagina, [{ texto: "lenta" }]));
        await pagina.waitForSelector("#listaPaginas li");
        await pagina.route("**/api/v2/apuntes", () => { /* nunca responde */ });
        await pagina.click("#btCrear");
        await pagina.waitForSelector("#btCancelarSubida:not([hidden])");
        await pagina.click("#btCancelarSubida");
        await pagina.waitForSelector("#avisoNuevo[data-tipo=info]");
        assert.match(await pagina.textContent("#avisoNuevo"), /cancelado/);
        assert.equal(await pagina.locator("#listaPaginas li").count(), 1);
        assert.equal(await pagina.isDisabled("#btCrear"), false);
        await contexto.close();
    });

    test("cámara simulada añade la foto a la misma colección; móvil sin desbordamiento", async () => {
        const { contexto, pagina } = await nueva({ width: 360, height: 780 });
        await pagina.setInputFiles("#inpFotos", await crearFotos(pagina, [{ texto: "antes" }]));
        await pagina.waitForSelector("#listaPaginas li");
        await pagina.click("#btCamaraNuevo");
        await pagina.waitForSelector("#btCapturar:not([disabled])");
        await pagina.click("#btCapturar");
        await pagina.waitForFunction(() => document.querySelectorAll("#listaPaginas li").length === 2);
        assert.match((await nombres(pagina))[1], /^foto-/);
        assert.ok(await sinDesbordamiento(pagina));
        await contexto.close();
    });
});
