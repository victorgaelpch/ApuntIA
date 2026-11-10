// Utilidades para probar las páginas con cuenta (FRONT-11 en adelante) contra el
// backend real: la interfaz la sirve el propio FastAPI (/inicio y /front/...),
// en el mismo origen que la API, con una carpeta de datos temporal y limpia.
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { iniciarBackend } = require("./entorno");
const { claveDePrueba } = require("../claves");

async function iniciarBackendV2(env = {}, opciones = {}) {
    const datos = fs.mkdtempSync(path.join(os.tmpdir(), "apuntia-e2e-"));
    const backend = await iniciarBackend({ DATA_DIR: datos, INVESTIGACION_PROVEEDOR: "ninguno", MAX_REGISTROS_HORA: "1000", ...env }, opciones);
    const detener = backend.detener;
    backend.datos = datos;
    backend.detener = async () => { await detener(); fs.rmSync(datos, { recursive: true, force: true }); };
    return backend;
}

let contador = 0;
// Crea una cuenta desde el contexto del navegador (comparte la cookie de sesión).
async function registrar(contexto, url, { email, nombre = "Alumna de prueba", password = claveDePrueba("c1") } = {}) {
    email = email || `alumna${Date.now()}${contador++}@example.com`;
    const r = await contexto.request.post(`${url}/api/v2/auth/registro`, {
        data: { email, nombre, password }, headers: { Origin: url },
    });
    if (r.status() !== 201) throw new Error(`registro: ${r.status()} ${await r.text()}`);
    return { email, password, nombre, ...(await r.json()) };
}

// Recoge errores de consola y de página (incluidas violaciones de la CSP).
function vigilarConsola(pagina) {
    const errores = [];
    pagina.on("console", (m) => { if (m.type() === "error") errores.push(m.text()); });
    pagina.on("pageerror", (e) => errores.push(`pageerror: ${e.message}`));
    return errores;
}

async function sinDesbordamiento(pagina) {
    return pagina.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
}

module.exports = { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento };
