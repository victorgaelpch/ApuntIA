// FULL-22: la MISMA prueba de humo principal con los dos métodos de arranque (scripts y Docker),
// y persistencia después de reiniciar. Usa la foto real de pizarrón del repositorio.
//   npm run test:entrega        (Docker: solo si está disponible; APUNTIA_DOCKER_SIN_BUILD=1 reutiliza imágenes)
const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");
const { humoPrincipal, comprobarPersistencia } = require("./humo");
const { claveDePrueba } = require("../claves");

const RAIZ = path.resolve(__dirname, "..", "..", "..");
const FOTO = fs.readFileSync(path.join(RAIZ, "back", "bd", "img", "image.png"));
const hayDocker = spawnSync("docker", ["info"], { stdio: "ignore" }).status === 0;
const puertoLibre = () => new Promise((r) => { const s = net.createServer().listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => r(port)); }); });

describe("FULL-22 humo principal en los dos modos", () => {
    test("scripts: arrancar, humo, detener, volver a arrancar y los datos siguen", async () => {
        const datos = fs.mkdtempSync(path.join(os.tmpdir(), "apuntia-entrega-"));
        const env = { ...process.env, DATA_DIR: path.join(datos, "datos") };
        const puerto = await puertoLibre();
        const url = `http://localhost:${puerto}`;
        const iniciar = () => spawnSync(path.join(RAIZ, "iniciar.sh"), ["--puerto", String(puerto), "--sin-navegador", "--sin-venv"], { env, encoding: "utf8", timeout: 600000 });
        const detener = () => spawnSync(path.join(RAIZ, "detener.sh"), [], { env, encoding: "utf8" });
        try {
            assert.equal(iniciar().status, 0);
            const h = await humoPrincipal(url, FOTO);
            assert.equal(detener().status, 0);
            assert.equal(iniciar().status, 0);
            await comprobarPersistencia(url, h);
        } finally {
            detener();
            fs.rmSync(datos, { recursive: true, force: true });
        }
    });

    test("demostración: datos sintéticos APARTE de los reales y restauración segura", async () => {
        const base = fs.mkdtempSync(path.join(os.tmpdir(), "apuntia-demo-"));
        const reales = path.join(base, "reales"), demo = path.join(base, "demo");
        fs.mkdirSync(reales); fs.writeFileSync(path.join(reales, "testigo"), "datos reales");
        const env = { ...process.env, DATA_DIR: reales, APUNTIA_DEMO_DIR: demo };
        const puerto = await puertoLibre();
        const url = `http://localhost:${puerto}`;
        const iniciar = (...extra) => spawnSync(path.join(RAIZ, "iniciar.sh"), ["--puerto", String(puerto), "--sin-navegador", "--sin-venv", ...extra], { env, encoding: "utf8", timeout: 600000 });
        const detener = () => spawnSync(path.join(RAIZ, "detener.sh"), [], { env, encoding: "utf8" });
        const apuntesDemo = async () => {
            const r = await fetch(`${url}/api/v2/auth/sesion`, { method: "POST", headers: { "Content-Type": "application/json", Origin: url, Connection: "close" },
                                                                body: JSON.stringify({ email: "demo@example.com", password: claveDePrueba("demo") }) });
            assert.equal(r.status, 200);
            const lista = await (await fetch(`${url}/api/v2/apuntes`, { headers: { Cookie: r.headers.get("set-cookie").split(";")[0] } })).json();
            return lista.elementos.map((a) => [a.titulo, a.estado]).sort();
        };
        const esperado = [["Demostración: cuaderno", "listo"], ["Demostración: pizarrón", "listo"]];
        try {
            let r = iniciar("--demo");
            assert.equal(r.status, 0, r.stderr);
            assert.match(r.stdout, /Demostración lista/);
            assert.deepEqual(await apuntesDemo(), esperado);
            assert.equal(detener().status, 0);
            assert.deepEqual(fs.readdirSync(reales), ["testigo"], "la demostración no toca los datos reales");
            assert.ok(fs.existsSync(path.join(demo, "datos", "apuntia.sqlite3")));

            // Una carpeta sin la marca de demostración no se borra nunca.
            const ajena = path.join(base, "ajena");
            fs.mkdirSync(ajena); fs.writeFileSync(path.join(ajena, "importante"), "x");
            r = spawnSync(path.join(RAIZ, "iniciar.sh"), ["--puerto", String(puerto), "--sin-navegador", "--sin-venv", "--demo-nueva"],
                          { env: { ...env, APUNTIA_DEMO_DIR: ajena }, encoding: "utf8" });
            assert.equal(r.status, 1);
            assert.match(r.stderr, /no es una carpeta de demostración/);
            assert.ok(fs.existsSync(path.join(ajena, "importante")));

            // --demo-nueva: vuelve al estado inicial (los cambios hechos en la demo se pierden a propósito).
            fs.writeFileSync(path.join(demo, "datos", "cambio-del-presentador"), "x");
            r = iniciar("--demo-nueva");
            assert.equal(r.status, 0, r.stderr);
            assert.ok(!fs.existsSync(path.join(demo, "datos", "cambio-del-presentador")));
            assert.deepEqual(await apuntesDemo(), esperado);
        } finally {
            detener();
            fs.rmSync(base, { recursive: true, force: true });
        }
    });

    test("Docker: el mismo humo, down + up y los datos siguen", { skip: !hayDocker && "Docker no está disponible" }, async () => {
        const puerto = await puertoLibre();
        const url = `http://localhost:${puerto}`;
        const env = { ...process.env, APUNTIA_PUERTO: String(puerto), COMPOSE_PROJECT_NAME: "apuntia-entrega" };
        const compose = (...args) => {
            const r = spawnSync("docker", ["compose", "-f", path.join(RAIZ, "fullstack", "compose.yaml"), ...args], { env, encoding: "utf8", timeout: 1800000 });
            assert.equal(r.status, 0, r.stderr.slice(-1500));
        };
        try {
            compose("up", "-d", "--wait", ...(process.env.APUNTIA_DOCKER_SIN_BUILD ? ["--no-build"] : ["--build"]));
            const h = await humoPrincipal(url, FOTO);
            compose("down");
            compose("up", "-d", "--wait", "--no-build");
            await comprobarPersistencia(url, h);
        } finally {
            spawnSync("docker", ["compose", "-f", path.join(RAIZ, "fullstack", "compose.yaml"), "down", "-v"], { env });
        }
    });
});
