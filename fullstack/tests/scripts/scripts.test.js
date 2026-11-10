// FULL-11: pruebas de los scripts de arranque y detención (Linux/macOS).
// Se ejecutan los scripts reales con --sin-venv (usan el Python del sistema, como en CI).
// Los .ps1/.bat de Windows no se pueden ejecutar en este entorno: ver docs/arranque.md.
const { test, describe, after } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync, spawn } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");

const RAIZ = path.resolve(__dirname, "..", "..", "..");
const ESTADO = path.join(RAIZ, "fullstack", ".estado");
const ejecutar = (script, args = [], env = {}, cwd = os.tmpdir()) =>
    spawnSync(path.join(RAIZ, script), args, { cwd, encoding: "utf8", env: { ...process.env, ...env }, timeout: 300000 });
const limpio = (t) => t.replace(/\x1b\[[0-9;]*m/g, "");

function puertoLibre() {
    return new Promise((r) => { const s = net.createServer().listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => r(port)); }); });
}

describe("FULL-11 scripts de arranque", () => {
    after(() => { ejecutar("detener.sh"); });

    test("--help y --comprobar no arrancan nada", () => {
        const ayuda = ejecutar("iniciar.sh", ["--help"]);
        assert.equal(ayuda.status, 0);
        assert.match(ayuda.stdout, /--puerto N/);
        const r = ejecutar("iniciar.sh", ["--comprobar", "--puerto", "8799"]);
        assert.equal(r.status, 0, r.stderr);
        assert.match(limpio(r.stdout), /Python 3\.\d+/);
        assert.match(limpio(r.stdout), /Sin backend Spring Boot/);
        assert.match(limpio(r.stdout), /Comprobación terminada/);
    });

    test("opciones y puertos no válidos: mensaje claro y código de salida", async () => {
        assert.equal(ejecutar("iniciar.sh", ["--inventada"]).status, 1);
        const bajo = ejecutar("iniciar.sh", ["--comprobar", "--puerto", "80"]);
        assert.equal(bajo.status, 1);
        assert.match(limpio(bajo.stderr), /Puerto no válido/);
        // Puerto ocupado por otro programa
        const puerto = await puertoLibre();
        const ocupante = net.createServer().listen(puerto, "127.0.0.1");
        await new Promise((r) => ocupante.once("listening", r));
        const r = ejecutar("iniciar.sh", ["--comprobar", "--puerto", String(puerto)]);
        ocupante.close();
        assert.equal(r.status, 3);
        assert.match(limpio(r.stderr), /ocupado por otro programa/);
    });

    test("arranca desde cualquier carpeta, sirve la interfaz y la API, no duplica y se detiene", async () => {
        const puerto = await puertoLibre();
        const r = ejecutar("iniciar.sh", ["--puerto", String(puerto), "--sin-navegador", "--sin-venv"], {}, os.homedir());
        assert.equal(r.status, 0, limpio(r.stdout + r.stderr));
        assert.match(limpio(r.stdout), new RegExp(`http://localhost:${puerto}/inicio`));
        const salud = await (await fetch(`http://localhost:${puerto}/salud`)).json();
        assert.equal(salud.estado, "ok");
        assert.equal((await fetch(`http://localhost:${puerto}/inicio`)).status, 200);
        assert.equal((await fetch(`http://localhost:${puerto}/front/apuntes.html`)).status, 200);
        // Segunda vez: detecta que ya está en marcha
        const otra = ejecutar("iniciar.sh", ["--puerto", String(puerto), "--sin-navegador", "--sin-venv"]);
        assert.equal(otra.status, 0);
        assert.match(limpio(otra.stdout), /ya está en marcha/);
        const pid = Number(fs.readFileSync(path.join(ESTADO, "backend.pid"), "utf8"));
        assert.ok(fs.readFileSync(`/proc/${pid}/cmdline`, "utf8").includes("uvicorn"), "el PID guardado es el del servidor");
        const d = ejecutar("detener.sh");
        assert.equal(d.status, 0);
        assert.match(limpio(d.stdout), /backend detenido/);
        await assert.rejects(fetch(`http://localhost:${puerto}/salud`, { signal: AbortSignal.timeout(2000) }));
        assert.ok(!fs.existsSync(path.join(ESTADO, "backend.pid")));
        assert.match(limpio(ejecutar("detener.sh").stdout), /no estaba en marcha/);
    });

    test("detener no mata un proceso ajeno que reutilizó el PID", () => {
        const ajeno = spawn("sleep", ["30"]);
        fs.mkdirSync(ESTADO, { recursive: true });
        fs.writeFileSync(path.join(ESTADO, "backend.pid"), String(ajeno.pid));
        const d = ejecutar("detener.sh");
        assert.match(limpio(d.stdout), /ya no es de ApuntIA: no se toca/);
        assert.doesNotThrow(() => process.kill(ajeno.pid, 0), "sigue vivo");
        ajeno.kill();
    });

    test("detecta un backend Spring Boot si se añade (sin inventarlo si no existe)", () => {
        const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "apuntia-spring-"));
        try {
            for (const rel of ["fullstack/scripts/iniciar.sh", "fullstack/config/.env.example"]) {
                fs.mkdirSync(path.dirname(path.join(tmp, rel)), { recursive: true });
                fs.copyFileSync(path.join(RAIZ, rel), path.join(tmp, rel));
            }
            fs.chmodSync(path.join(tmp, "fullstack/scripts/iniciar.sh"), 0o755);
            fs.mkdirSync(path.join(tmp, "back/motori_magenes"), { recursive: true });
            fs.mkdirSync(path.join(tmp, "back/servicio-java"), { recursive: true });
            fs.writeFileSync(path.join(tmp, "back/servicio-java/pom.xml"), "<project/>");
            const r = spawnSync(path.join(tmp, "fullstack/scripts/iniciar.sh"), ["--comprobar", "--puerto", "8798"], { encoding: "utf8" });
            const salida = limpio(r.stdout + r.stderr);
            if (spawnSync("java", ["-version"]).status === 0) {
                assert.equal(r.status, 0, salida);
                assert.match(salida, /Spring Boot detectado en back\/servicio-java/);
            } else {
                assert.equal(r.status, 1);
                assert.match(salida, /falta Java/);
            }
        } finally {
            fs.rmSync(tmp, { recursive: true, force: true });
        }
    });
});
