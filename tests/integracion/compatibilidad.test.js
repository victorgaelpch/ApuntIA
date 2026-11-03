// Compatibilidad de datos entre frontend y backend (FULL-06).
//
// Captura las peticiones reales que hace el navegador y las respuestas reales
// de FastAPI, y las compara con el contrato (docs/api.md), incluidos los casos límite.
//   npm run test:integracion
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const { chromium } = require("playwright");
const { iniciarBackend, iniciarEstatico } = require("./entorno");

const RAIZ = path.resolve(__dirname, "..", "..");

function partesMultipart(cuerpo, contentType) {
    const limite = contentType.match(/boundary=(.+)$/)[1];
    return cuerpo.toString("latin1").split(`--${limite}`).slice(1, -1).map((bloque) => {
        const [cabecera] = bloque.split("\r\n\r\n");
        return {
            nombre: (cabecera.match(/name="([^"]+)"/) || [])[1],
            archivo: (cabecera.match(/filename="([^"]*)"/) || [])[1],
            tipo: (cabecera.match(/Content-Type: (.+)/i) || [])[1],
        };
    });
}

describe("Compatibilidad frontend ↔ backend", () => {
    let backend, estatico, navegador, contexto, pagina;

    before(async () => {
        backend = await iniciarBackend();
        estatico = await iniciarEstatico();
        navegador = await chromium.launch();
        contexto = await navegador.newContext();
        pagina = await contexto.newPage();
        await pagina.goto(`${estatico.url}/index.html?api=${backend.url}`);
        await pagina.evaluate(() => window.ApuntIA.app.limitesListos);
    });
    after(async () => {
        await navegador.close();
        await estatico.cerrar();
        await backend.detener();
    });

    // Envía bytes con el cliente real (api.js), sin la validación de la interfaz.
    // Los bytes viajan en base64; `relleno` añade ceros en el navegador (archivos grandes).
    const crearEnPagina = `(b64, relleno, nombre, tipo) => {
        const bin = atob(b64); const datos = new Uint8Array(bin.length + relleno);
        for (let i = 0; i < bin.length; i++) datos[i] = bin.charCodeAt(i);
        return new File([datos], nombre, { type: tipo });
    }`;
    const enviarBytes = (bytes, nombre, tipo, opciones = {}, relleno = 0) => pagina.evaluate(async ({ b64, relleno, nombre, tipo, opciones, crear }) => {
        const archivo = eval(crear)(b64, relleno, nombre, tipo);
        try {
            const r = await window.ApuntIA.api.procesarImagen(archivo, opciones);
            const bmp = await createImageBitmap(r.blob);
            return { ok: true, tipo: r.blob.type, perspectiva: r.perspectiva, dimensiones: r.dimensiones, tiempoMs: r.tiempoMs, archivoRecibido: r.archivoRecibido, nombreDescarga: r.nombreDescarga, real: `${bmp.width}x${bmp.height}` };
        } catch (e) {
            return { ok: false, codigo: e.codigo, status: e.status, tipo: e.tipo, mensaje: e.mensaje };
        }
    }, { b64: Buffer.from(bytes).toString("base64"), relleno, nombre, tipo, opciones, crear: crearEnPagina });

    const validarEnCliente = (bytes, nombre, relleno = 0) => pagina.evaluate(async ({ b64, relleno, nombre, crear }) =>
        window.ApuntIA.validacion.validarArchivo(eval(crear)(b64, relleno, nombre, "")), { b64: Buffer.from(bytes).toString("base64"), relleno, nombre, crear: crearEnPagina });

    const png = fs.readFileSync(path.join(RAIZ, "back", "bd", "img", "image.png"));

    test("la petición del navegador cumple el contrato (método, ruta, multipart, campo «file»)", async () => {
        // Un servidor de eco guarda la petición tal como la envía el navegador (bytes reales).
        let capturada = null;
        const eco = http.createServer((req, res) => {
            const trozos = [];
            req.on("data", (t) => trozos.push(t));
            req.on("end", () => {
                if (req.method === "POST") capturada = { metodo: req.method, url: req.url, cabeceras: req.headers, cuerpo: Buffer.concat(trozos) };
                res.writeHead(req.url === "/salud" ? 200 : 200, { "Access-Control-Allow-Origin": "*", "Content-Type": req.url === "/salud" ? "application/json" : "image/png" });
                res.end(req.url === "/salud" ? "{}" : png);
            });
        });
        await new Promise((r) => eco.listen(0, "127.0.0.1", r));
        const p = await contexto.newPage();
        await p.goto(`${estatico.url}/index.html?api=http://localhost:${eco.address().port}`);
        await p.evaluate(async (b64) => {
            const datos = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
            await window.ApuntIA.api.procesarImagen(new File([datos], "pizarrón día 1.png", { type: "image/png" }), { ruido: "mediana" });
        }, png.toString("base64"));
        await p.close();
        eco.close();

        const url = new URL(capturada.url, "http://x");
        assert.equal(capturada.metodo, "POST");
        assert.equal(url.pathname, "/analisis");
        assert.equal(url.searchParams.get("ruido"), "mediana");
        const contentType = capturada.cabeceras["content-type"];
        assert.match(contentType, /^multipart\/form-data; boundary=/);
        const partes = partesMultipart(capturada.cuerpo, contentType);
        assert.equal(partes.length, 1, "un solo campo");
        assert.equal(partes[0].nombre, "file");
        assert.equal(partes[0].tipo.trim(), "image/png");
        assert.equal(Buffer.from(partes[0].archivo, "latin1").toString("utf8"), "pizarrón día 1.png", "nombre en UTF-8");
        assert.ok(capturada.cuerpo.includes(png), "el archivo viaja íntegro");
        assert.equal(capturada.cabeceras.cookie, undefined, "sin credenciales");
    });

    test("la respuesta cumple el contrato y sus cabeceras son legibles desde el navegador (CORS)", async () => {
        const r = await enviarBytes(png, "pizarrón día 1.png", "image/png");
        assert.equal(r.tipo, "image/png");
        assert.ok(["corregida", "no_detectada", "desactivada"].includes(r.perspectiva));
        assert.deepEqual(r.dimensiones && `${r.dimensiones.ancho}x${r.dimensiones.alto}`, r.real, "X-ApuntIA-Dimensiones = imagen real");
        assert.ok(Number.isFinite(r.tiempoMs));
        assert.equal(r.archivoRecibido, "pizarrón día 1.png", "nombre UTF-8 ida y vuelta");
        assert.equal(r.nombreDescarga, "pizarrón día 1_apuntia.png");
    });

    test("los límites del cliente se sincronizan con GET /salud", async () => {
        const [cfg, salud] = await pagina.evaluate(async () => [window.ApuntIA.config, await window.ApuntIA.api.obtenerSalud()]);
        assert.equal(cfg.maxMb, salud.max_mb);
        assert.deepEqual(cfg.formatos, salud.formatos);
    });

    test("límite de tamaño idéntico en las dos capas (10 MB exactos se aceptan, +1 byte se rechaza)", async () => {
        // PNG válido con relleno de ceros tras IEND hasta 10 MB exactos.
        const relleno = 10 * 1024 * 1024 - png.length;
        assert.equal((await validarEnCliente(png, "x.png", relleno)).ok, true);
        assert.equal((await enviarBytes(png, "x.png", "image/png", {}, relleno)).ok, true);
        assert.equal((await validarEnCliente(png, "x.png", relleno + 1)).codigo, "ARCHIVO_DEMASIADO_GRANDE");
        const r = await enviarBytes(png, "x.png", "image/png", {}, relleno + 1);
        assert.deepEqual([r.status, r.codigo], [413, "ARCHIVO_DEMASIADO_GRANDE"]);
    });

    test("mismo criterio de formato: lo que el cliente rechaza, el servidor también", async () => {
        for (const [bytes, nombre] of [[Buffer.from("%PDF-1.4 x"), "doc.png"], [Buffer.from("GIF89a" + "0".repeat(20)), "a.gif"], [Buffer.alloc(0), "vacio.png"]]) {
            const cliente = await validarEnCliente(bytes, nombre);
            const servidor = await enviarBytes(bytes, nombre, "image/png");
            assert.equal(cliente.ok, false);
            assert.equal(servidor.ok, false);
            assert.equal(cliente.codigo, servidor.codigo, `${nombre}: cliente ${cliente.codigo} / servidor ${servidor.codigo}`);
        }
    });

    test("formatos y codificaciones que produce el navegador son aceptados", async () => {
        const r = await pagina.evaluate(async () => {
            const lienzo = document.createElement("canvas");
            lienzo.width = 320; lienzo.height = 240;
            const ctx = lienzo.getContext("2d");
            ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, 320, 240);
            const salida = {};
            for (const tipo of ["image/jpeg", "image/png", "image/webp"]) {
                const blob = await new Promise((res) => lienzo.toBlob(res, tipo, 0.9)); // como la cámara en vivo
                try { salida[tipo] = (await window.ApuntIA.api.procesarImagen(new File([blob], "foto", { type: tipo }))).dimensiones; }
                catch (e) { salida[tipo] = e.codigo; }
            }
            return salida;
        });
        for (const tipo of ["image/jpeg", "image/png", "image/webp"]) assert.deepEqual(r[tipo], { ancho: 320, alto: 240 }, tipo);
    });

    test("PNG con transparencia y orientación EXIF de celular", async () => {
        const { PNG_ALFA, JPEG_EXIF6 } = require("./muestras");
        const alfa = await enviarBytes(PNG_ALFA, "alfa.png", "image/png");
        assert.equal(alfa.ok, true);
        // EXIF Orientation=6: guardada a 400x200, se muestra a 200x400.
        const vistaPrevia = await pagina.evaluate(async (b64) => {
            const bin = atob(b64); const datos = Uint8Array.from(bin, (c) => c.charCodeAt(0));
            const bmp = await createImageBitmap(new Blob([datos], { type: "image/jpeg" }));
            return `${bmp.width}x${bmp.height}`;
        }, JPEG_EXIF6.toString("base64"));
        const exif = await enviarBytes(JPEG_EXIF6, "celular.jpg", "image/jpeg", { perspectiva: false });
        assert.equal(vistaPrevia, "200x400", "el navegador aplica EXIF");
        assert.equal(exif.real, "200x400", "el backend devuelve la misma orientación que ve el usuario");
    });

    test("todos los códigos de error del backend tienen mensaje en el frontend", async () => {
        const contrato = fs.readFileSync(path.join(RAIZ, "docs", "api.md"), "utf8");
        const codigosContrato = [...contrato.matchAll(/^\| \d{3} \| `([A-Z_]+)` \|/gm)].map((m) => m[1]);
        const codigosBackend = new Set();
        for (const archivo of ["app/core/errores.py", "app/services/validacion.py"]) {
            const fuente = fs.readFileSync(path.join(RAIZ, "back", "motori_magenes", archivo), "utf8");
            for (const m of fuente.matchAll(/"([A-Z]+(?:_[A-Z]+)+)"/g)) codigosBackend.add(m[1]);
        }
        const catalogo = await pagina.evaluate(() => Object.keys(window.ApuntIA.mensajes.CATALOGO));
        for (const codigo of [...codigosContrato, ...codigosBackend].filter((c) => c !== "ERROR_CLIENTE")) {
            assert.ok(catalogo.includes(codigo), `falta mensaje para ${codigo}`);
        }
        assert.ok(codigosContrato.length >= 11);
    });

    test("la página abierta con doble clic (file://, origen «null») funciona contra la API", async () => {
        const p = await contexto.newPage();
        await p.goto(`file://${path.join(RAIZ, "index.html")}?api=${backend.url}`);
        const r = await p.evaluate(async () => (await window.ApuntIA.api.obtenerSalud()).estado);
        assert.equal(r, "ok");
        await p.close();
    });
});

describe("Límites configurados en el servidor", () => {
    test("con MAX_UPLOAD_MB=1 en el backend, la interfaz valida y avisa con 1 MB", async () => {
        const backend = await iniciarBackend({ MAX_UPLOAD_MB: "1" });
        const estatico = await iniciarEstatico();
        const navegador = await chromium.launch();
        try {
            const pagina = await navegador.newPage();
            await pagina.goto(`${estatico.url}/index.html?api=${backend.url}`);
            await pagina.evaluate(() => window.ApuntIA.app.limitesListos);
            const r = await pagina.evaluate(async () => {
                const archivo = new File([new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), new Uint8Array(1.5 * 1024 * 1024)], "grande.png");
                await window.ApuntIA.app.seleccionarArchivo(archivo, "archivo");
                return { maxMb: window.ApuntIA.config.maxMb, texto: document.getElementById("estado").textContent, ayuda: document.getElementById("formatos").textContent };
            });
            assert.equal(r.maxMb, 1);
            assert.match(r.texto, /pesa más de 1 MB/);
            assert.match(r.ayuda, /hasta 1 MB/);
        } finally {
            await navegador.close();
            await estatico.cerrar();
            await backend.detener();
        }
    });
});
