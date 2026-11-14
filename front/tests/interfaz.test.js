// Pruebas de funcionamiento de la interfaz (FRONT-10).
//
//   npm install && npx playwright install chromium
//   npm run test:front
//
// Usan la API simulada (?mock=...), así que no necesitan el backend. Variables:
//   NAVEGADORES=chromium,firefox,webkit   (por defecto chromium)
//   CAPTURAS=fullstack/docs/evidencias              (guarda capturas de evidencia)
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const playwright = require("playwright");
const { iniciar } = require("./servidor");

const NAVEGADORES = (process.env.NAVEGADORES || "chromium").split(",").map((n) => n.trim());
const CAPTURAS = process.env.CAPTURAS ? path.resolve(process.env.CAPTURAS) : null;

// Imágenes de prueba generadas en el navegador, sin archivos externos.
async function crearArchivo(pagina, { nombre = "pizarron.png", ancho = 80, alto = 60, tipo = "image/png", bytes = null } = {}) {
    return pagina.evaluateHandle(async ({ nombre, ancho, alto, tipo, bytes }) => {
        if (bytes) return new File([new Uint8Array(bytes)], nombre, { type: tipo });
        const c = document.createElement("canvas");
        c.width = ancho; c.height = alto;
        const ctx = c.getContext("2d");
        ctx.fillStyle = "#eee"; ctx.fillRect(0, 0, ancho, alto);
        ctx.fillStyle = "#123"; ctx.fillRect(ancho * 0.1, alto * 0.4, ancho * 0.6, alto * 0.15);
        const blob = await new Promise((r) => c.toBlob(r, tipo));
        return new File([blob], nombre, { type: tipo });
    }, { nombre, ancho, alto, tipo, bytes });
}

async function elegir(pagina, opciones) {
    const archivo = await crearArchivo(pagina, opciones);
    await pagina.evaluate((f) => window.ApuntIA.app.seleccionarArchivo(f, "archivo"), archivo);
}

const estadoUI = (pagina) => pagina.evaluate(() => {
    const e = document.getElementById("estado");
    return {
        tipo: e.dataset.estado,
        texto: (e.querySelector(".status__texto") || e).textContent,
        acciones: [...e.querySelectorAll(".status__acciones button")].map((b) => b.textContent),
        archivo: window.ApuntIA.app.estado.archivo && window.ApuntIA.app.estado.archivo.name,
        enviar: document.getElementById("btEnviar").disabled,
    };
});

for (const nombre of NAVEGADORES) {
    describe(`Interfaz en ${nombre}`, () => {
        let navegador, servidor;
        const abrir = async (query = "?mock=ok", opciones = {}) => {
            const contexto = await navegador.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true, ...opciones });
            const pagina = await contexto.newPage();
            const errores = [];
            pagina.on("pageerror", (e) => errores.push(e.message));
            await pagina.goto(servidor.url + "/index.html" + query);
            return { contexto, pagina, errores };
        };
        const captura = async (pagina, archivo) => {
            if (!CAPTURAS || nombre !== "chromium") return;
            fs.mkdirSync(CAPTURAS, { recursive: true });
            await pagina.screenshot({ path: path.join(CAPTURAS, archivo), fullPage: true, type: "jpeg", quality: 78 });
        };

        before(async () => {
            servidor = await iniciar();
            const opciones = nombre === "chromium" ? { args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"] } : {};
            navegador = await playwright[nombre].launch(opciones);
        });
        after(async () => {
            await navegador.close();
            await servidor.cerrar();
        });

        test("C01 estado inicial: acciones visibles y «Procesar» deshabilitado", async () => {
            const { contexto, pagina, errores } = await abrir();
            assert.ok(await pagina.isVisible("text=Cargar imagen"));
            assert.ok(await pagina.isVisible("#btCamara"));
            const s = await estadoUI(pagina);
            assert.equal(s.tipo, "vacio");
            assert.equal(s.enviar, true);
            assert.deepEqual(errores, []);
            await captura(pagina, "front-10-inicio.jpg");
            await contexto.close();
        });

        test("C02 seleccionar con el input de archivo muestra la vista previa y sus datos", async () => {
            const { contexto, pagina } = await abrir();
            const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAYAAAD0In+KAAAAEUlEQVR4nGP4z8DwHwyZGBgAH/AD/a6kn4EAAAAASUVORK5CYII=", "base64");
            await pagina.setInputFiles("#inpImagen", { name: "pizarron.png", mimeType: "image/png", buffer: png });
            await pagina.waitForSelector("#imagenEnviada:not([hidden])");
            await pagina.waitForFunction(() => !document.getElementById("infoPreview").hidden);
            const info = await pagina.textContent("#infoPreview");
            assert.match(info, /pizarron\.png · \d+ B · 2×1 px \(horizontal\)/);
            assert.equal((await estadoUI(pagina)).enviar, false);
            await contexto.close();
        });

        test("C03 reemplazar con «Cambiar» y quitar la imagen", async () => {
            const { contexto, pagina } = await abrir();
            await elegir(pagina, { nombre: "a.png" });
            await elegir(pagina, { nombre: "b.png", ancho: 40, alto: 90 });
            assert.equal((await estadoUI(pagina)).archivo, "b.png");
            await pagina.waitForFunction(() => document.getElementById("infoPreview").textContent.includes("vertical"));
            const [selector] = await Promise.all([pagina.waitForEvent("filechooser"), pagina.click("#btCambiar")]);
            assert.equal(await selector.element().evaluate((e) => e.id), "inpImagen");
            await pagina.click("#btQuitar");
            const s = await estadoUI(pagina);
            assert.equal(s.archivo, null);
            assert.equal(s.enviar, true);
            assert.equal(await pagina.isHidden("#imagenEnviada"), true);
            await contexto.close();
        });

        test("C04 archivos no válidos se rechazan conservando la imagen anterior", async () => {
            const { contexto, pagina } = await abrir();
            await elegir(pagina, { nombre: "buena.png" });
            const casos = [
                [{ nombre: "falso.png", bytes: [...Buffer.from("%PDF-1.4 documento")] }, /no es una imagen admitida/],
                [{ nombre: "vacio.png", bytes: [] }, /vacío/],
            ];
            for (const [opciones, esperado] of casos) {
                await elegir(pagina, opciones);
                const s = await estadoUI(pagina);
                assert.equal(s.tipo, "error");
                assert.match(s.texto, esperado);
                assert.match(s.texto, /Se mantiene «buena\.png»/);
                assert.equal(s.archivo, "buena.png");
            }
            await pagina.evaluate(async () => { await window.ApuntIA.app.limitesListos; window.ApuntIA.config.maxMb = 0.0001; });
            await elegir(pagina, { nombre: "grande.png", ancho: 200, alto: 200 });
            assert.match((await estadoUI(pagina)).texto, /pesa más de/);
            await contexto.close();
        });

        test("C05 cancelar el selector conserva la selección", async () => {
            const { contexto, pagina } = await abrir();
            await pagina.dispatchEvent("#inpImagen", "cancel");
            assert.match((await estadoUI(pagina)).texto, /No elegiste ninguna imagen/);
            await elegir(pagina, { nombre: "x.png" });
            await pagina.dispatchEvent("#inpImagen", "cancel");
            assert.match((await estadoUI(pagina)).texto, /Se mantiene «x\.png»/);
            await contexto.close();
        });

        test("C06 procesar: indicador de carga, controles bloqueados y resultado", async () => {
            const { contexto, pagina } = await abrir("?mock=lento");
            await elegir(pagina);
            await pagina.click("#btEnviar");
            await pagina.waitForSelector("[data-estado=cargando] .spinner");
            const bloqueados = await pagina.evaluate(() => ["btEnviar", "btCambiar", "btQuitar", "btCamara", "inpImagen"].every((id) => document.getElementById(id).disabled));
            assert.equal(bloqueados, true);
            assert.equal(await pagina.getAttribute("#resultados", "aria-busy"), "true");
            await captura(pagina, "front-10-cargando.jpg");
            await pagina.waitForSelector("[data-estado=hecho]", { timeout: 8000 });
            assert.equal(await pagina.isVisible("#imagenResultado"), true);
            assert.match(await pagina.textContent("#infoResultado"), /enderezado/);
            assert.equal((await estadoUI(pagina)).enviar, false);
            await captura(pagina, "front-10-resultado.jpg");
            await contexto.close();
        });

        test("C07 doble clic en «Procesar» envía una sola petición", async () => {
            const { contexto, pagina } = await abrir("?mock=lento");
            await elegir(pagina);
            await pagina.evaluate(() => {
                const original = window.ApuntIA.api.procesarImagen;
                window.__llamadas = 0;
                window.ApuntIA.api.procesarImagen = (...a) => { window.__llamadas++; return original(...a); };
                const b = document.getElementById("btEnviar"); b.click(); b.click(); b.click();
            });
            await pagina.waitForSelector("[data-estado=hecho]", { timeout: 8000 });
            assert.equal(await pagina.evaluate(() => window.__llamadas), 1);
            await contexto.close();
        });

        test("C08 comparar con la original y descargar el resultado", async () => {
            const { contexto, pagina } = await abrir();
            await elegir(pagina, { nombre: "clase.png" });
            await pagina.click("#btEnviar");
            await pagina.waitForSelector("[data-estado=hecho]");
            const srcResultado = await pagina.getAttribute("#imagenResultado", "src");
            await pagina.hover("#btComparar");
            await pagina.mouse.down();
            assert.equal(await pagina.getAttribute("#imagenResultado", "src"), await pagina.evaluate(() => window.ApuntIA.app.estado.urlPreview));
            await pagina.mouse.up();
            assert.equal(await pagina.getAttribute("#imagenResultado", "src"), srcResultado);
            const [descarga] = await Promise.all([pagina.waitForEvent("download"), pagina.click("#btDescargar")]);
            assert.equal(descarga.suggestedFilename(), "clase_apuntia.png");
            await contexto.close();
        });

        const ERRORES = [
            ["tipo", /no es una imagen admitida/, ["Elegir otra imagen"]],
            ["grande", /pesa más de 10 MB/, ["Elegir otra imagen"]],
            ["corrupta", /dañada/, ["Elegir otra imagen"]],
            ["servidor", /problema en el servidor/, ["Reintentar"]],
            ["red", /No se pudo conectar/, ["Reintentar"]],
            ["vacia", /no se puede mostrar/, ["Reintentar"]],
        ];
        for (const [escenario, texto, acciones] of ERRORES) {
            test(`C09 error «${escenario}»: mensaje útil, acciones y controles restaurados`, async () => {
                const { contexto, pagina } = await abrir(`?mock=${escenario}`);
                await elegir(pagina);
                await pagina.click("#btEnviar");
                await pagina.waitForSelector("[data-estado=error]");
                const s = await estadoUI(pagina);
                assert.match(s.texto, texto);
                assert.deepEqual(s.acciones, acciones);
                assert.equal(s.enviar, false);
                assert.doesNotMatch(await pagina.textContent("#estado"), /Traceback|Error:|at \w+ \(/);
                if (escenario === "servidor") await captura(pagina, "front-10-error.jpg");
                await contexto.close();
            });
        }

        test("C10 «Reintentar» vuelve a enviar la misma imagen", async () => {
            const { contexto, pagina } = await abrir("?mock=servidor");
            await elegir(pagina, { nombre: "r.png" });
            await pagina.click("#btEnviar");
            await pagina.waitForSelector("[data-estado=error]");
            await pagina.evaluate(() => {
                const original = window.ApuntIA.api.procesarImagen;
                window.__archivos = [];
                window.ApuntIA.api.procesarImagen = (f, ...a) => { window.__archivos.push(f.name); return original(f, ...a); };
            });
            await pagina.click("text=Reintentar");
            await pagina.waitForSelector("[data-estado=error]");
            assert.deepEqual(await pagina.evaluate(() => window.__archivos), ["r.png"]);
            await contexto.close();
        });

        test("C11 cancelar un procesamiento en curso", async () => {
            const { contexto, pagina } = await abrir("?mock=colgado");
            await elegir(pagina);
            await pagina.click("#btEnviar");
            await pagina.click(".status__acciones >> text=Cancelar");
            await pagina.waitForSelector("[data-estado=listo]");
            assert.match((await estadoUI(pagina)).texto, /cancelado/);
            assert.equal((await estadoUI(pagina)).enviar, false);
            await contexto.close();
        });

        test("C12 cámara denegada ofrece alternativas", async () => {
            const { contexto, pagina } = await abrir("?mock=ok");
            await pagina.evaluate(() => { navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException("x", "NotAllowedError")); });
            await pagina.click("#btCamara");
            await pagina.waitForSelector("[data-estado=error]");
            assert.deepEqual((await estadoUI(pagina)).acciones, ["Usar la app de cámara", "Cargar imagen"]);
            await contexto.close();
        });

        test("C13 cámara en vivo: capturar una foto la deja lista", { skip: nombre !== "chromium" && "solo Chromium tiene cámara simulada" }, async () => {
            const { contexto, pagina } = await abrir("?mock=ok");
            await pagina.click("#btCamara");
            await pagina.waitForSelector("#btCapturar:not([disabled])", { timeout: 5000 });
            await pagina.click("#btCapturar");
            await pagina.waitForSelector("[data-estado=listo]");
            const s = await estadoUI(pagina);
            assert.match(s.archivo, /^foto-\d{8}-\d{6}\.jpg$/);
            assert.equal(await pagina.evaluate(() => document.getElementById("camVideo").srcObject), null);
            await contexto.close();
        });

        test("C14 sin desbordamiento horizontal en móvil y escritorio", async () => {
            for (const viewport of [{ width: 320, height: 640 }, { width: 390, height: 844 }, { width: 844, height: 390 }, { width: 1920, height: 1080 }]) {
                const { contexto, pagina } = await abrir("?mock=ok", { viewport });
                await elegir(pagina, { ancho: 3000, alto: 1000 });
                await pagina.click("#btEnviar");
                await pagina.waitForSelector("[data-estado=hecho]");
                const ancho = await pagina.evaluate(() => document.documentElement.scrollWidth);
                assert.ok(ancho <= viewport.width, `${viewport.width}px: scrollWidth ${ancho}`);
                if (viewport.width === 390) await captura(pagina, "front-10-movil.jpg");
                await contexto.close();
            }
        });

        test("C15 orden de tabulación coherente con el visual", async () => {
            const { contexto, pagina } = await abrir();
            const orden = [];
            for (let i = 0; i < 8; i++) {
                await pagina.keyboard.press("Tab");
                orden.push(await pagina.evaluate(() => document.activeElement.id || document.activeElement.textContent.trim().slice(0, 12)));
            }
            const iCargar = orden.indexOf("inpImagen");
            const iCamara = orden.indexOf("btCamara");
            assert.ok(iCargar >= 0 && iCamara === iCargar + 1, orden.join(" → "));
            await contexto.close();
        });
    });
}
