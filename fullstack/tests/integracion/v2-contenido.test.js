// FRONT-14: fórmulas, tablas y esquemas en el editor, hasta el PDF.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require("playwright");
const { iniciarBackendV2, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte, esperarTrabajo } = require("./v2-apuntes-ayuda");

function textoPdf(buffer) {
    const archivo = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "apuntia-pdf-")), "a.pdf");
    fs.writeFileSync(archivo, buffer);
    try { return execFileSync("pdftotext", ["-layout", archivo, "-"], { encoding: "utf8" }); }
    finally { fs.rmSync(path.dirname(archivo), { recursive: true, force: true }); }
}

describe("FRONT-14 fórmulas, tablas y esquemas", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function abrir(opciones = {}, viewport) {
        const contexto = await navegador.newContext(viewport ? { viewport } : {});
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        const creado = await crearApunte(contexto, backend.url, pagina, opciones);
        await pagina.goto(`${backend.url}/front/editor.html?id=${creado.id}`);
        await pagina.waitForSelector(".bloque");
        await pagina.uncheck("#chkAutoguardado");  // guardado explícito (el automático: v2-versiones)
        return { contexto, pagina, errores, ...creado };
    }
    async function guardar(pagina) {
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
    }
    async function pdf(contexto, pagina, id, cuenta) {
        const r = await contexto.request.post(`${backend.url}/api/v2/apuntes/${id}/exportaciones`, {
            data: {}, headers: { "X-CSRF-Token": cuenta.csrf, Origin: backend.url } });
        const { exportacion, trabajo } = await r.json();
        if (trabajo) assert.equal((await esperarTrabajo(contexto, backend.url, trabajo.id)).estado, "completado");
        return Buffer.from(await (await contexto.request.get(`${backend.url}/api/v2/exportaciones/${exportacion.id}/pdf`)).body());
    }

    test("fórmula: fracción, raíz, potencia y subíndice con vista previa, errores y LaTeX peligroso", async () => {
        const { contexto, pagina, errores, id } = await abrir();
        await pagina.click("#btAnadirFormula");
        const tarjeta = pagina.locator(".bloque", { has: pagina.locator("textarea.latex") }).first();
        const latex = tarjeta.locator("textarea.latex");
        await latex.fill("\\frac{a}{b} + \\sqrt{x} + x^{2} + a_{i}");
        await tarjeta.locator(".formula-estado[data-tipo=exito]").waitFor();
        assert.match(await tarjeta.locator(".formula-vista img").getAttribute("src"), /^data:image\/png;base64,/);
        // Sintaxis inválida
        await latex.fill("\\frac{a");
        await tarjeta.locator(".formula-estado[data-tipo=error]").waitFor();
        assert.match(await tarjeta.locator(".formula-estado").textContent(), /No se puede dibujar/);
        assert.equal(await latex.getAttribute("aria-invalid"), "true");
        // Comandos peligrosos y HTML: se rechazan y no se ejecuta nada
        for (const malo of ["\\input{/etc/passwd}", '<img src=x onerror="window.__xss=1">']) {
            await latex.fill(malo);
            await pagina.waitForFunction((el) => el.dataset.tipo === "error" && !/Comprobando/.test(el.textContent),
                                         await tarjeta.locator(".formula-estado").elementHandle());
        }
        assert.equal(await pagina.evaluate(() => window.__xss), undefined);
        // Texto normal → LaTeX
        await tarjeta.locator("summary").click();
        await tarjeta.locator("input[id^=lineal-]").fill("sqrt(x + 1) + x^2");
        await tarjeta.locator("text=Convertir").click();
        await tarjeta.locator(".formula-estado[data-tipo=exito]").waitFor();
        const convertido = await latex.inputValue();
        assert.match(convertido, /\\sqrt\{x \+ 1\}/);
        await guardar(pagina);
        await pagina.reload();
        await pagina.waitForSelector("textarea.latex");
        assert.equal(await pagina.inputValue("textarea.latex"), convertido);
        await pagina.waitForSelector(".formula-estado[data-tipo=exito]");
        assert.equal(await pagina.textContent("#estadoGuardado").then((t) => /sin guardar/.test(t)), false, "cargar no ensucia");
        const doc = (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte.documento;
        const f = doc.bloques.find((b) => b.tipo === "formula");
        assert.equal(f.latex, convertido);
        assert.equal(f.latex_valido, true);
        assert.deepEqual(errores.filter((e) => !/400/.test(e)), []);
        await contexto.close();
    });

    test("tabla 3×4: editar celdas, filas y columnas; se conserva al recargar y en el PDF", async () => {
        const { contexto, pagina, id, cuenta } = await abrir();
        await pagina.click("#btAnadirTabla");
        const tabla = pagina.locator(".tabla-editable").first();
        await tabla.locator("[data-accion=columna]").click();          // 3 columnas
        for (let i = 0; i < 3; i++) await tabla.locator("[data-accion=fila]").click();  // 4 filas
        const encabezados = ["Concepto", "Símbolo", "Unidad"];
        for (const [c, v] of encabezados.entries()) await tabla.locator(`[data-celda=c${c}]`).fill(v);
        const datos = [["Fuerza", "F", "N"], ["Masa", "m", "kg"], ["Tiempo", "t", "s"], ["Energía", "E", "J"]];
        for (const [f, fila] of datos.entries()) for (const [c, v] of fila.entries()) await tabla.locator(`[data-celda=f${f}c${c}]`).fill(v);
        // Quitar y volver a poner una fila (control de filas)
        await tabla.locator('[aria-label="Quitar la fila 4"]').click();
        await tabla.locator("[data-accion=fila]").click();
        for (const [c, v] of datos[3].entries()) await pagina.locator(`.tabla-editable [data-celda=f3c${c}]`).fill(v);
        await guardar(pagina);
        await pagina.reload();
        await pagina.waitForSelector(".tabla-editable");
        assert.equal(await pagina.inputValue(".tabla-editable [data-celda=f1c2]"), "kg");
        const doc = (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte.documento;
        const t = doc.bloques.find((b) => b.tipo === "tabla").tabla;
        assert.deepEqual(t, { encabezados, filas: datos });
        const texto = textoPdf(await pdf(contexto, pagina, id, cuenta));
        for (const v of ["Concepto", "Símbolo", "Energía", "kg"]) assert.ok(texto.includes(v), `${v} en el PDF`);
        await contexto.close();
    });

    test("convertir un texto con columnas en tabla", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.fill(".bloque >> nth=1 >> textarea", "Nombre | Valor\npi | 3.14\ne | 2.71");
        await pagina.click(".bloque >> nth=1 >> [data-accion=a-tabla]");
        await pagina.waitForSelector(".tabla-editable");
        assert.equal(await pagina.inputValue(".tabla-editable [data-celda=c1]"), "Valor");
        assert.equal(await pagina.inputValue(".tabla-editable [data-celda=f1c0]"), "e");
        await contexto.close();
    });

    test("esquema difícil: se conserva como imagen, con descripción opcional", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/front/ayuda.html`);
        const dibujo = await pagina.evaluate(() => {
            const c = document.createElement("canvas"); c.width = 1600; c.height = 1100;
            const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, 1600, 1100);
            g.fillStyle = "#111"; g.font = "bold 80px sans-serif"; g.fillText("Ciclo del agua", 90, 140);
            g.strokeStyle = "#111"; g.lineWidth = 10;
            g.beginPath(); g.arc(500, 640, 220, 0, Math.PI * 2); g.stroke();
            g.strokeRect(950, 430, 420, 420);
            g.beginPath(); g.moveTo(720, 640); g.lineTo(940, 640); g.moveTo(900, 600); g.lineTo(940, 640); g.lineTo(900, 680); g.stroke();
            return c.toDataURL("image/png").split(",")[1];
        });
        const { id } = await crearApunte(contexto, backend.url, pagina, { fotos: [Buffer.from(dibujo, "base64")] });
        await pagina.goto(`${backend.url}/front/editor.html?id=${id}`);
        await pagina.waitForSelector(".bloque");
        const imagenes = pagina.locator(".bloque", { has: pagina.locator(".bloque__recorte--grande") });
        assert.ok(await imagenes.count() >= 1, "el dibujo queda como bloque de imagen");
        await imagenes.first().locator("textarea").fill("Esquema: evaporación y condensación");
        await guardar(pagina);
        const doc = (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte.documento;
        const img = doc.bloques.find((b) => b.tipo === "imagen");
        assert.ok(img.recorte && img.texto === "Esquema: evaporación y condensación");
        await contexto.close();
    });

    test("móvil: editores de fórmula y tabla sin desbordar la página", async () => {
        const { contexto, pagina } = await abrir({}, { width: 360, height: 780 });
        await pagina.click("#btAnadirTabla");
        for (let i = 0; i < 5; i++) await pagina.click(".tabla-editable [data-accion=columna]");
        await pagina.click("#btAnadirFormula");
        assert.ok(await sinDesbordamiento(pagina), "la tabla ancha se desplaza dentro de su caja");
        await contexto.close();
    });
});
