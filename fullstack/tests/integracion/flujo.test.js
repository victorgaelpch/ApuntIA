// Pruebas de integración de extremo a extremo (FULL-07): interfaz real en el
// navegador + FastAPI real (uvicorn), manejadas como lo haría el usuario.
//   npm run test:integracion        (CAPTURAS=fullstack/docs/evidencias para guardar evidencias)
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackend, iniciarEstatico } = require("./entorno");

const RAIZ = path.resolve(__dirname, "..", "..", "..");
const FOTO_REAL = path.join(RAIZ, "back", "bd", "img", "image.png");
const CAPTURAS = process.env.CAPTURAS ? path.resolve(process.env.CAPTURAS) : null;
const resultados = [];

async function prepararPagina(navegador, estatico, api) {
    const contexto = await navegador.newContext({ viewport: { width: 1280, height: 900 } });
    const pagina = await contexto.newPage();
    const consola = [];
    pagina.on("console", (m) => consola.push(`${m.type()}: ${m.text()}`));
    pagina.on("pageerror", (e) => consola.push(`pageerror: ${e.message}`));
    await pagina.goto(`${estatico.url}/index.html?api=${api}`);
    await pagina.evaluate(() => window.ApuntIA.app.limitesListos);
    return { contexto, pagina, consola };
}

const leerEstado = (pagina) => pagina.evaluate(() => {
    const e = document.getElementById("estado");
    return {
        tipo: e.dataset.estado,
        texto: e.querySelector(".status__texto").textContent,
        acciones: [...e.querySelectorAll(".status__acciones button")].map((b) => b.textContent),
        detalle: (e.querySelector(".status__detalle p") || {}).textContent || null,
        info: document.getElementById("infoResultado").textContent,
        resultadoVisible: !document.getElementById("imagenResultado").hidden,
        controlesLibres: !document.getElementById("btEnviar").disabled && !document.getElementById("btCambiar").disabled,
    };
});

async function procesar(pagina, archivo) {
    if (archivo) await pagina.setInputFiles("#inpImagen", archivo);
    await pagina.waitForFunction(() => window.ApuntIA.app.estado.archivo);
    const inicio = Date.now();
    await pagina.click("#btEnviar");
    await pagina.waitForFunction(() => ["hecho", "error"].includes(document.getElementById("estado").dataset.estado), null, { timeout: 30000 });
    return Date.now() - inicio;
}

async function capturar(pagina, nombre) {
    if (!CAPTURAS) return;
    fs.mkdirSync(CAPTURAS, { recursive: true });
    await pagina.locator("#resultados").screenshot({ path: path.join(CAPTURAS, nombre), type: "jpeg", quality: 78 });
}

describe("Integración de extremo a extremo con FastAPI real", () => {
    let navegador, estatico, backend;
    before(async () => {
        navegador = await chromium.launch();
        estatico = await iniciarEstatico();
        backend = await iniciarBackend();
    });
    after(async () => {
        await navegador.close();
        await estatico.cerrar();
        await backend.detener();
        if (resultados.length) {
            console.log("\n| Escenario | HTTP | Mensaje mostrado | Tiempo |\n|---|---|---|---|");
            for (const r of resultados) console.log(`| ${r.escenario} | ${r.http} | ${r.texto} | ${r.ms} ms |`);
        }
    });

    test("I01 imagen válida (foto real) → resultado visible", async () => {
        const { contexto, pagina, consola } = await prepararPagina(navegador, estatico, backend.url);
        const ms = await procesar(pagina, FOTO_REAL);
        const s = await leerEstado(pagina);
        assert.equal(s.tipo, "hecho");
        assert.equal(s.resultadoVisible, true);
        assert.match(s.info, /516×387 px/);
        assert.ok(ms < 10000, `tardó ${ms} ms`);
        assert.deepEqual(consola.filter((c) => c.startsWith("error") || c.startsWith("pageerror")), []);
        resultados.push({ escenario: "Imagen válida (foto real 516×387)", http: 200, texto: s.texto, ms });
        await capturar(pagina, "full-07-valida.jpg");
        await contexto.close();
    });

    test("I02 pizarrón inclinado 12 MP → enderezado y redimensionado", async () => {
        const { contexto, pagina } = await prepararPagina(navegador, estatico, backend.url);
        const foto = await pagina.evaluate(async () => {
            const c = document.createElement("canvas"); c.width = 4032; c.height = 3024;
            const x = c.getContext("2d"); x.fillStyle = "#465a5f"; x.fillRect(0, 0, c.width, c.height);
            x.fillStyle = "#f5f5f5"; x.beginPath(); x.moveTo(560, 360); x.lineTo(3550, 600); x.lineTo(3390, 2600); x.lineTo(400, 2420); x.closePath(); x.fill();
            x.fillStyle = "#222"; x.font = "160px sans-serif"; x.fillText("f'(x) = 2x", 900, 1300);
            const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", 0.9));
            return Array.from(new Uint8Array(await blob.arrayBuffer()));
        });
        const ruta = path.join(require("node:os").tmpdir(), "apuntia-12mp.jpg");
        fs.writeFileSync(ruta, Buffer.from(foto));
        const ms = await procesar(pagina, ruta);
        const s = await leerEstado(pagina);
        assert.equal(s.tipo, "hecho");
        assert.match(s.info, /enderezado/);
        const [ancho, alto] = s.info.match(/(\d+)×(\d+) px/).slice(1).map(Number);
        assert.ok(Math.max(ancho, alto) <= 2000);
        resultados.push({ escenario: "Pizarrón inclinado 4032×3024", http: 200, texto: s.info.split(" · ")[0], ms });
        await contexto.close();
    });

    test("I03 archivo inválido saltando la validación del navegador → 415 del servidor", async () => {
        const { contexto, pagina } = await prepararPagina(navegador, estatico, backend.url);
        // Se desactiva la validación del cliente para comprobar que el servidor también protege.
        await pagina.evaluate(() => { window.ApuntIA.validacion.validarArchivo = async () => ({ ok: true }); });
        await pagina.setInputFiles("#inpImagen", { name: "documento.png", mimeType: "image/png", buffer: Buffer.from("%PDF-1.7 no soy una imagen") });
        const ms = await procesar(pagina);
        const s = await leerEstado(pagina);
        assert.equal(s.tipo, "error");
        assert.match(s.texto, /no es una imagen admitida/);
        assert.match(s.detalle, /TIPO_NO_PERMITIDO · HTTP 415/);
        assert.deepEqual(s.acciones, ["Elegir otra imagen"]);
        assert.equal(s.controlesLibres, true);
        resultados.push({ escenario: "Archivo inválido (PDF), validación del cliente desactivada", http: 415, texto: s.texto, ms });
        await contexto.close();
    });

    test("I04 archivo inválido con la validación normal → se detiene en el navegador", async () => {
        const { contexto, pagina } = await prepararPagina(navegador, estatico, backend.url);
        await pagina.setInputFiles("#inpImagen", { name: "documento.png", mimeType: "image/png", buffer: Buffer.from("%PDF-1.7 no soy una imagen") });
        await pagina.waitForSelector("[data-estado=error]");
        const s = await leerEstado(pagina);
        assert.match(s.texto, /no es una imagen admitida/);
        assert.equal(await pagina.isDisabled("#btEnviar"), true, "no se envía nada");
        resultados.push({ escenario: "Archivo inválido (PDF), validación normal", http: "— (no se envía)", texto: s.texto, ms: 0 });
        await contexto.close();
    });

    test("I05 archivo grande (11 MB) saltando la validación → 413 del servidor", async () => {
        const { contexto, pagina } = await prepararPagina(navegador, estatico, backend.url);
        await pagina.evaluate(() => { window.ApuntIA.validacion.validarArchivo = async () => ({ ok: true }); });
        const png = fs.readFileSync(FOTO_REAL);
        await pagina.setInputFiles("#inpImagen", { name: "enorme.png", mimeType: "image/png", buffer: Buffer.concat([png, Buffer.alloc(11 * 1024 * 1024)]) });
        const ms = await procesar(pagina);
        const s = await leerEstado(pagina);
        assert.match(s.texto, /pesa más de 10 MB/);
        assert.match(s.detalle, /ARCHIVO_DEMASIADO_GRANDE · HTTP 413/);
        resultados.push({ escenario: "Archivo de 11 MB", http: 413, texto: s.texto, ms });
        await contexto.close();
    });

    test("I06 fallo de red (backend apagado) y reintento cuando vuelve", async () => {
        const temporal = await iniciarBackend();
        const { contexto, pagina } = await prepararPagina(navegador, estatico, temporal.url);
        await pagina.setInputFiles("#inpImagen", FOTO_REAL);
        await temporal.detener();
        const ms = await procesar(pagina);
        const s = await leerEstado(pagina);
        assert.match(s.texto, /No se pudo conectar con el servidor/);
        assert.deepEqual(s.acciones, ["Reintentar"]);
        assert.equal(s.resultadoVisible, false);
        resultados.push({ escenario: "Backend apagado", http: "— (sin respuesta)", texto: s.texto, ms });
        await capturar(pagina, "full-07-red.jpg");
        // Reintento: se redirige la página a un backend que sí responde.
        await pagina.evaluate((url) => { history.replaceState(null, "", `?api=${url}`); }, backend.url);
        await pagina.click("text=Reintentar");
        await pagina.waitForSelector("[data-estado=hecho]", { timeout: 20000 });
        resultados.push({ escenario: "Reintentar con el backend activo", http: 200, texto: (await leerEstado(pagina)).texto, ms: "—" });
        await contexto.close();
    });

    test("I07 error de procesamiento (cv2.error) → 500 ERROR_PROCESAMIENTO legible", async () => {
        const conFallo = await iniciarBackend({}, { fallo: "procesamiento" });
        const { contexto, pagina } = await prepararPagina(navegador, estatico, conFallo.url);
        const ms = await procesar(pagina, FOTO_REAL);
        const s = await leerEstado(pagina);
        await conFallo.detener();
        assert.match(s.texto, /No se pudo procesar esta imagen/);
        assert.match(s.detalle, /ERROR_PROCESAMIENTO · HTTP 500 · Referencia: [0-9a-f]{12}/);
        assert.deepEqual(s.acciones, ["Reintentar", "Elegir otra imagen"]);
        assert.ok(conFallo.log.join("").includes("fallo simulado"), "la traza queda en el log del servidor");
        resultados.push({ escenario: "Error de procesamiento (cv2.error)", http: 500, texto: s.texto, ms });
        await capturar(pagina, "full-07-error-procesamiento.jpg");
        await contexto.close();
    });

    test("I08 error inesperado del servidor → 500 ERROR_INTERNO legible (no «sin conexión»)", async () => {
        const conFallo = await iniciarBackend({}, { fallo: "inesperado" });
        const { contexto, pagina } = await prepararPagina(navegador, estatico, conFallo.url);
        const ms = await procesar(pagina, FOTO_REAL);
        const s = await leerEstado(pagina);
        await conFallo.detener();
        resultados.push({ escenario: "Excepción no prevista (RuntimeError)", http: 500, texto: s.texto, ms });
        assert.match(s.texto, /problema en el servidor/, `se mostró: «${s.texto}»`);
        assert.match(s.detalle || "", /ERROR_INTERNO · HTTP 500/);
        assert.doesNotMatch(await pagina.textContent("#estado"), /ruta\/interna/);
        await contexto.close();
    });

    test("I09 servidor lento: indicador de espera y resultado", async () => {
        const lento = await iniciarBackend({}, { fallo: "lento" });
        const { contexto, pagina } = await prepararPagina(navegador, estatico, lento.url);
        await pagina.setInputFiles("#inpImagen", FOTO_REAL);
        await pagina.waitForFunction(() => window.ApuntIA.app.estado.archivo);
        const inicio = Date.now();
        await pagina.click("#btEnviar");
        await pagina.waitForSelector("[data-estado=cargando] .spinner");
        await pagina.waitForFunction(() => document.querySelector(".status__texto").textContent.startsWith("Procesando"), null, { timeout: 5000 });
        await pagina.waitForSelector("[data-estado=hecho]", { timeout: 20000 });
        const ms = Date.now() - inicio;
        await lento.detener();
        assert.ok(ms >= 3000);
        resultados.push({ escenario: "Servidor lento (+3 s)", http: 200, texto: "Spinner → «Procesando la imagen…» → resultado", ms });
        await contexto.close();
    });
});
