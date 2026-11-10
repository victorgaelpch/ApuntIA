// Crea apuntes reales (fotos generadas en el navegador + análisis con Tesseract) para las
// pruebas del editor, el historial y la exportación.
const { registrar } = require("./v2-entorno");

const LINEAS = ["Derivadas", "La derivada mide la razón de cambio.", "Ejemplo: la función crece más rápido."];

async function fotoApunte(pagina, { lineas = LINEAS, ancho = 1600, alto = 1000 } = {}) {
    const b64 = await pagina.evaluate(({ lineas, ancho, alto }) => {
        const c = document.createElement("canvas");
        c.width = ancho; c.height = alto;
        const g = c.getContext("2d");
        g.fillStyle = "#ffffff"; g.fillRect(0, 0, ancho, alto);
        g.fillStyle = "#111111";
        lineas.forEach((l, i) => { g.font = `${i === 0 ? "bold 84" : "52"}px sans-serif`; g.fillText(l, 90, 160 + i * 170); });
        return c.toDataURL("image/png").split(",")[1];
    }, { lineas, ancho, alto });
    return Buffer.from(b64, "base64");
}

// Margen amplio: el OCR real tarda más en equipos lentos o en CI.
async function esperarTrabajo(contexto, url, id, ms = 180000) {
    const fin = Date.now() + ms;
    for (;;) {
        const t = (await (await contexto.request.get(`${url}/api/v2/trabajos/${id}`)).json()).trabajo;
        if (!["pendiente", "procesando"].includes(t.estado)) return t;
        if (Date.now() > fin) throw new Error("el trabajo no terminó");
        await new Promise((r) => setTimeout(r, 300));
    }
}

// Crea (y opcionalmente espera) un apunte con una o varias fotos; devuelve {id, trabajo, cuenta}.
// Se envía desde el navegador (misma origen y cookie de la sesión), como lo haría la interfaz.
async function crearApunte(contexto, url, pagina, { titulo = "Clase de cálculo", fotos = null, tipos = "cuaderno", esperar = true, cuenta } = {}) {
    cuenta = cuenta || await registrar(contexto, url);
    if (!pagina.url().startsWith(url)) await pagina.goto(`${url}/front/ayuda.html`);
    fotos = fotos || [await fotoApunte(pagina)];
    const cuerpo = await pagina.evaluate(async ({ csrf, titulo, tipos, fotos }) => {
        const datos = new FormData();
        fotos.forEach((b64, i) => datos.append("paginas", new Blob([Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))], { type: "image/png" }), `p${i + 1}.png`));
        fotos.forEach(() => datos.append("tipos", tipos));
        datos.append("titulo", titulo);
        const resp = await fetch("/api/v2/apuntes", { method: "POST", body: datos, headers: { "X-CSRF-Token": csrf } });
        return { status: resp.status, ...(await resp.json()) };
    }, { csrf: cuenta.csrf, titulo, tipos, fotos: fotos.map((f) => f.toString("base64")) });
    if (cuerpo.status !== 202) throw new Error(`crear apunte: ${JSON.stringify(cuerpo)}`);
    const trabajo = esperar ? await esperarTrabajo(contexto, url, cuerpo.trabajo.id) : cuerpo.trabajo;
    return { id: cuerpo.apunte.id, trabajo, cuenta };
}

module.exports = { fotoApunte, crearApunte, esperarTrabajo, LINEAS };
