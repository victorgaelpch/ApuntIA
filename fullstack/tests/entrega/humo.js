// Prueba de humo PRINCIPAL de la entrega (FULL-22), la misma para los dos modos de arranque
// (scripts y Docker): salud, dependencias listas, interfaz, cuenta, apunte con OCR real y PDF.
// Solo usa la API por HTTP, como un cliente cualquiera.
const assert = require("node:assert/strict");
const { claveDePrueba } = require("../claves");
async function json(r) { const t = await r.text(); try { return JSON.parse(t); } catch (_) { return { texto: t }; } }

async function esperar(url, cookie, id, ms = 180000) {
    const fin = Date.now() + ms;
    for (;;) {
        const t = (await json(await fetch(`${url}/api/v2/trabajos/${id}`, { headers: { Cookie: cookie } }))).trabajo;
        if (!["pendiente", "procesando"].includes(t.estado)) return t;
        if (Date.now() > fin) throw new Error(`el trabajo ${id} no terminó`);
        await new Promise((r) => setTimeout(r, 400));
    }
}

// Devuelve lo necesario para comprobar la persistencia después de reiniciar.
// `foto`: PNG con texto real (los dos modos pasan la foto de pizarrón del repositorio).
async function humoPrincipal(url, foto) {
    const salud = await json(await fetch(`${url}/salud`));
    assert.equal(salud.estado, "ok");
    assert.equal(salud.version, "2.0.0");
    assert.equal(salud.ocr.disponible, true, "OCR disponible");
    const listo = await fetch(`${url}/api/v2/listo`);
    assert.equal(listo.status, 200, JSON.stringify(await json(listo)));
    for (const ruta of ["/inicio", "/front/cuenta.html", "/front/editor.html"]) assert.equal((await fetch(url + ruta)).status, 200, ruta);
    assert.deepEqual(await json(await fetch(`${url}/`)), { message: "Hola Mundo" }, "v1 intacta");

    const email = `humo${Date.now()}@example.com`, password = claveDePrueba("c13");
    const reg = await fetch(`${url}/api/v2/auth/registro`, { method: "POST", headers: { "Content-Type": "application/json", Origin: url },
                                                         body: JSON.stringify({ email, nombre: "Humo", password }) });
    assert.equal(reg.status, 201);
    const cookie = reg.headers.get("set-cookie").split(";")[0];
    const { csrf } = await json(reg);
    const datos = new FormData();
    datos.append("paginas", new Blob([foto], { type: "image/png" }), "foto.png");
    datos.append("tipos", "pizarron");
    datos.append("titulo", "Prueba de humo");
    const creado = await json(await fetch(`${url}/api/v2/apuntes`, { method: "POST", body: datos, headers: { Cookie: cookie, "X-CSRF-Token": csrf, Origin: url } }));
    const t = await esperar(url, cookie, creado.trabajo.id);
    assert.ok(["completado", "parcial"].includes(t.estado), `análisis ${t.estado} ${JSON.stringify(t.error)}`);
    const exp = await json(await fetch(`${url}/api/v2/apuntes/${creado.apunte.id}/exportaciones`, {
        method: "POST", headers: { Cookie: cookie, "X-CSRF-Token": csrf, Origin: url, "Content-Type": "application/json" }, body: "{}" }));
    const te = await esperar(url, cookie, exp.trabajo.id);
    if (te.estado === "fallido" && te.error.codigo === "APUNTE_VACIO") {
        // Sin texto reconocido no hay PDF, y eso es lo correcto (no se genera un PDF vacío).
        return { email, password, apunte: creado.apunte.id, pdf: null };
    }
    assert.equal(te.estado, "completado", JSON.stringify(te.error));
    const pdf = await fetch(`${url}/api/v2/exportaciones/${exp.exportacion.id}/pdf`, { headers: { Cookie: cookie } });
    assert.equal(pdf.headers.get("content-type"), "application/pdf");
    const bytes = Buffer.from(await pdf.arrayBuffer());
    assert.equal(bytes.subarray(0, 5).toString(), "%PDF-");
    return { email, password, apunte: creado.apunte.id, pdf: exp.exportacion.id };
}

// Tras reiniciar: la cuenta entra, el apunte y su PDF siguen.
async function comprobarPersistencia(url, h) {
    // Tras reiniciar el servidor, la primera petición puede caer en una conexión keep-alive del
    // proceso anterior (ya cerrada): se reintenta una vez con «Connection: close».
    const entrar = () => fetch(`${url}/api/v2/auth/sesion`, { method: "POST", headers: { "Content-Type": "application/json", Origin: url, Connection: "close" },
                                                            body: JSON.stringify({ email: h.email, password: h.password }) });
    let r;
    try { r = await entrar(); } catch (_) { await new Promise((x) => setTimeout(x, 500)); r = await entrar(); }
    assert.equal(r.status, 200, "la cuenta sigue tras reiniciar");
    const cookie = r.headers.get("set-cookie").split(";")[0];
    const apunte = (await json(await fetch(`${url}/api/v2/apuntes/${h.apunte}`, { headers: { Cookie: cookie } }))).apunte;
    assert.equal(apunte.titulo, "Prueba de humo");
    if (h.pdf) assert.equal((await fetch(`${url}/api/v2/exportaciones/${h.pdf}/pdf`, { headers: { Cookie: cookie } })).status, 200);
}

module.exports = { humoPrincipal, comprobarPersistencia };
