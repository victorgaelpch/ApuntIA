// FULL-13: prueba de humo del arranque con Docker Compose (opt-in: necesita Docker).
//   npm run test:docker                      (construye las imágenes)
//   APUNTIA_DOCKER_SIN_BUILD=1 npm run test:docker   (usa imágenes ya construidas)
// Usa el proyecto «apuntia-prueba» y su propio volumen, que se borra al final: no toca los
// datos de un arranque normal. Comprueba salud, cabeceras, interfaz, OCR y PDF dentro de los
// contenedores, y que los datos sobreviven a «down» + «up».
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");
const net = require("node:net");
const { chromium } = require("playwright");
const { claveDePrueba } = require("../claves");

const RAIZ = path.resolve(__dirname, "..", "..", "..");
const COMPOSE = ["compose", "-f", path.join(RAIZ, "fullstack", "compose.yaml"), "-p", "apuntia-prueba"];
const hayDocker = spawnSync("docker", ["info"], { stdio: "ignore" }).status === 0;

function docker(args, env = {}) {
    const r = spawnSync("docker", [...COMPOSE, ...args], { cwd: RAIZ, encoding: "utf8", env: { ...process.env, ...env }, timeout: 1800000 });
    if (r.status !== 0) throw new Error(`docker ${args.join(" ")}: ${r.stderr.slice(-2000)}`);
    return r.stdout;
}
const puertoLibre = () => new Promise((r) => { const s = net.createServer().listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => r(port)); }); });

async function esperarSalud(url, ms = 180000) {
    const fin = Date.now() + ms;
    while (Date.now() < fin) {
        try { const r = await fetch(`${url}/salud`); if (r.ok && (await r.json()).estado === "ok") return; } catch (_) { /* aún no */ }
        await new Promise((r) => setTimeout(r, 1000));
    }
    throw new Error("Docker no respondió a tiempo");
}

describe("FULL-13 Docker Compose", { skip: !hayDocker && "Docker no está disponible" }, () => {
    let url, env, navegador;
    before(async () => {
        const puerto = await puertoLibre();
        env = { APUNTIA_PUERTO: String(puerto) };
        url = `http://localhost:${puerto}`;
        docker(["up", "-d", ...(process.env.APUNTIA_DOCKER_SIN_BUILD ? ["--no-build"] : ["--build"]), "--wait"], env);
        await esperarSalud(url);
        navegador = await chromium.launch();
    });
    after(async () => {
        if (navegador) await navegador.close();
        try { docker(["down", "-v"], env); } catch (_) { /* ya parado */ }
    });

    test("salud, OCR dentro del contenedor, cabeceras e interfaz por el mismo origen", async () => {
        const salud = await (await fetch(`${url}/salud`)).json();
        assert.equal(salud.ocr.disponible, true);
        assert.ok(salud.ocr.idiomas.includes("spa"));
        assert.deepEqual(await (await fetch(`${url}/`)).json(), { message: "Hola Mundo" }, "v1 intacta");
        const inicio = await fetch(`${url}/inicio`);
        assert.equal(inicio.status, 200);
        assert.match(inicio.headers.get("content-security-policy"), /script-src 'self'/);
        assert.equal(inicio.headers.get("x-frame-options"), "DENY");
        assert.equal((await fetch(`${url}/front/apuntes.html`)).status, 200);
        assert.equal((await fetch(`${url}/front/tests/servidor.js`)).status, 404);
        assert.equal((await fetch(`${url}/front/maqueta.html`)).status, 404);
        const estado = docker(["ps", "--format", "{{.Service}} {{.Health}}"], env);
        assert.match(estado, /backend healthy/);
        assert.match(estado, /web healthy/);
        // Usuarios sin privilegios
        assert.equal(docker(["exec", "-T", "backend", "id", "-u"], env).trim(), "10001");
    });

    test("cuenta, apunte con OCR y PDF desde el navegador; los datos sobreviven a down + up", async () => {
        const contexto = await navegador.newContext({ acceptDownloads: true });
        const pagina = await contexto.newPage();
        await pagina.goto(`${url}/front/cuenta.html?modo=registro`);
        await pagina.fill("#regNombre", "Docker");
        await pagina.fill("#regEmail", "docker@example.com");
        await pagina.fill("#regPassword", claveDePrueba("c9"));
        await pagina.fill("#regConfirmar", claveDePrueba("c9"));
        await Promise.all([pagina.waitForURL(/nuevo\.html/), pagina.click("#formRegistro button[type=submit]")]);
        const png = await pagina.evaluate(() => {
            const c = document.createElement("canvas"); c.width = 1400; c.height = 800;
            const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, 1400, 800);
            g.fillStyle = "#111"; g.font = "bold 80px sans-serif"; g.fillText("Contenedores", 80, 180);
            g.font = "54px sans-serif"; g.fillText("Docker empaqueta la aplicacion.", 80, 360);
            return c.toDataURL("image/png").split(",")[1];
        });
        await pagina.setInputFiles("#inpFotos", { name: "foto.png", mimeType: "image/png", buffer: Buffer.from(png, "base64") });
        await pagina.waitForSelector("#listaPaginas li");
        await Promise.all([pagina.waitForURL(/editor\.html/), pagina.click("#btCrear")]);
        await pagina.waitForSelector(".bloque", { timeout: 180000 });
        assert.match((await pagina.$$eval(".bloque textarea", (t) => t.map((x) => x.value))).join(" "), /Docker empaqueta/);
        await pagina.click("#tab-pdf");
        await pagina.click("#btGenerarPdf");
        await pagina.waitForSelector("#cajaVistaPdf:not([hidden])", { timeout: 120000 });
        const cookies = await contexto.cookies();
        await contexto.close();

        docker(["down"], env);   // sin -v: el volumen de datos se conserva
        docker(["up", "-d", "--no-build", "--wait"], env);
        await esperarSalud(url);
        const otra = await navegador.newContext();
        await otra.addCookies(cookies);   // la sesión está en la base de datos persistente
        const p2 = await otra.newPage();
        await p2.goto(`${url}/front/apuntes.html`);
        await p2.waitForSelector(".apunte");
        assert.match(await p2.textContent(".apunte"), /1 PDF/);
        await otra.close();
    });
});
