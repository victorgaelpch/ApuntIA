// Entorno de integración: levanta el backend FastAPI real (uvicorn) y el
// servidor estático del frontend en puertos libres. Variables:
//   PYTHON=python3 (o la ruta al python del .venv)
const { spawn } = require("node:child_process");
const net = require("node:net");
const path = require("node:path");
const { iniciar: iniciarEstatico } = require("../../front/tests/servidor");

const BACKEND = path.resolve(__dirname, "..", "..", "back", "motori_magenes");

function puertoLibre() {
    return new Promise((resolve) => {
        const s = net.createServer().listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => resolve(port)); });
    });
}

async function esperar(url, ms = 20000) {
    const fin = Date.now() + ms;
    while (Date.now() < fin) {
        try { if ((await fetch(url)).ok) return; } catch (_) { /* aún no arranca */ }
        await new Promise((r) => setTimeout(r, 200));
    }
    throw new Error(`No respondió: ${url}`);
}

// fallo: "" | "procesamiento" | "inesperado" | "lento" (ver app_con_fallos.py)
async function iniciarBackend(env = {}, { fallo = "" } = {}) {
    const puerto = await puertoLibre();
    const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
    const args = fallo
        ? ["-m", "uvicorn", "app_con_fallos:app", "--app-dir", __dirname, "--port", String(puerto)]
        : ["-m", "uvicorn", "main:app", "--port", String(puerto)];
    const proceso = spawn(python, args, {
        cwd: BACKEND, env: { ...process.env, ...env, APUNTIA_FALLO: fallo }, stdio: ["ignore", "pipe", "pipe"],
    });
    const log = [];
    proceso.stdout.on("data", (d) => log.push(String(d)));
    proceso.stderr.on("data", (d) => log.push(String(d)));
    const url = `http://localhost:${puerto}`;
    await esperar(`${url}/salud`);
    return {
        url, log,
        detener: () => new Promise((r) => { proceso.once("exit", r); proceso.kill("SIGKILL"); }),
    };
}

module.exports = { iniciarBackend, iniciarEstatico, BACKEND };
