// FRONT-13: revisar y corregir el texto reconocido por bloques, con el OCR real.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte, fotoApunte } = require("./v2-apuntes-ayuda");

describe("FRONT-13 editor de texto", () => {
    let navegador, backend;
    before(async () => { navegador = await chromium.launch(); backend = await iniciarBackendV2(); });
    after(async () => { await navegador.close(); await backend.detener(); });

    async function abrir(opciones = {}, viewport) {
        const contexto = await navegador.newContext(viewport ? { viewport } : {});
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        const creado = await crearApunte(contexto, backend.url, pagina, opciones);
        await pagina.goto(`${backend.url}/front/editor.html?id=${creado.id}`);
        if (opciones.esperar !== false) await pagina.waitForSelector(".bloque");
        // Guardado explícito en estas pruebas (el automático se prueba en v2-versiones.test.js).
        if (opciones.esperar !== false) await pagina.uncheck("#chkAutoguardado");
        return { contexto, pagina, errores, ...creado };
    }
    const documento = async (contexto, id) => (await (await contexto.request.get(`${backend.url}/api/v2/apuntes/${id}`)).json()).apunte;
    const estadoGuardado = (pagina) => pagina.textContent("#estadoGuardado");

    test("muestra el progreso del análisis y luego los bloques con su región", async () => {
        const { contexto, pagina, errores } = await abrir({ esperar: false });
        await pagina.waitForSelector("#panelAnalisis:not([hidden])", { timeout: 5000 }).catch(() => { /* puede terminar antes */ });
        await pagina.waitForSelector(".bloque", { timeout: 60000 });
        assert.equal(await pagina.isHidden("#panelAnalisis"), true);
        const regiones = await pagina.locator(".region").count();
        const bloques = await pagina.locator(".bloque").count();
        assert.ok(bloques >= 2 && regiones === bloques, `${regiones} regiones para ${bloques} bloques`);
        // Pulsar una región selecciona y enfoca su bloque
        const id = await pagina.getAttribute(".region >> nth=1", "data-bloque");
        await pagina.click(".region >> nth=1");
        assert.equal(await pagina.getAttribute(`.bloque[data-bloque="${id}"]`, "aria-current"), "true");
        assert.equal(await pagina.evaluate(() => document.activeElement.closest(".bloque").dataset.bloque), id);
        assert.match(await pagina.textContent(".bloque .estado-chip"), /Reconocido \d+ %/);
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("corregir con tildes, guardar y ver la corrección tras recargar", async () => {
        const { contexto, pagina, id } = await abrir();
        assert.equal(await pagina.isDisabled("#btGuardar"), true);
        await pagina.fill(".bloque >> nth=1 >> textarea", "Ejemplo: la función crece más rápido, ¿verdad? Ñandú");
        assert.equal(await estadoGuardado(pagina), "Cambios sin guardar");
        assert.match(await pagina.title(), /^• /);
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado · versión 3/.test(document.getElementById("estadoGuardado").textContent));
        await pagina.reload();
        await pagina.waitForSelector(".bloque");
        assert.equal(await pagina.inputValue(".bloque >> nth=1 >> textarea"), "Ejemplo: la función crece más rápido, ¿verdad? Ñandú");
        assert.equal(await pagina.isVisible(".bloque >> nth=1 >> .etiqueta-editado"), true);
        const apunte = await documento(contexto, id);
        const b = apunte.documento.bloques[1];
        assert.equal(b.editado, true);
        assert.match(b.texto_original, /^Ejemplo: la funci/, "el texto reconocido se conserva");
        await contexto.close();
    });

    test("un texto con <script> se muestra como texto y no se ejecuta", async () => {
        const { contexto, pagina } = await abrir();
        const malicioso = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>';
        await pagina.fill(".bloque >> nth=0 >> textarea", malicioso);
        await pagina.fill("#inpTituloApunte", "<b>título</b>");
        await pagina.keyboard.press("Control+s");
        await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
        await pagina.reload();
        await pagina.waitForSelector(".bloque");
        assert.equal(await pagina.inputValue(".bloque >> nth=0 >> textarea"), malicioso);
        assert.equal(await pagina.inputValue("#inpTituloApunte"), "<b>título</b>");
        assert.equal(await pagina.evaluate(() => window.__xss), undefined);
        assert.equal(await pagina.locator("#main img[src=x], #panel-transcripcion b, .editor-cabecera b").count(), 0);
        await contexto.close();
    });

    test("dividir, unir, añadir, reordenar y borrar con deshacer", async () => {
        const { contexto, pagina, id } = await abrir();
        const area = pagina.locator(".bloque >> nth=0 >> textarea");
        const texto = await area.inputValue();
        const corte = texto.indexOf("\n");
        await area.focus();
        await area.evaluate((a, c) => a.setSelectionRange(c, c), corte);
        await pagina.click(".bloque >> nth=0 >> [data-accion=dividir]");
        assert.equal(await pagina.locator(".bloque").count(), 3);
        assert.equal(await pagina.inputValue(".bloque >> nth=0 >> textarea"), texto.slice(0, corte));
        await pagina.selectOption(".bloque >> nth=0 >> select", "titulo");
        // Unir los bloques 2 y 3
        await pagina.click(".bloque >> nth=1 >> [data-accion=unir]");
        assert.equal(await pagina.locator(".bloque").count(), 2);
        // Añadir uno a mano y subirlo
        await pagina.click("#btAnadirBloque");
        await pagina.keyboard.type("Nota añadida por mí");
        await pagina.click(".bloque >> nth=2 >> [data-accion=subir]");
        assert.equal(await pagina.inputValue(".bloque >> nth=1 >> textarea"), "Nota añadida por mí");
        // Borrar y deshacer
        await pagina.click(".bloque >> nth=1 >> [data-accion=borrar]");
        assert.equal(await pagina.locator(".bloque").count(), 2);
        await pagina.click("#avisoEditor >> text=Deshacer");
        assert.equal(await pagina.locator(".bloque").count(), 3);
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
        const doc = (await documento(contexto, id)).documento;
        // Al unir, el resultado es el bloque de arriba (la parte dividida, de origen «usuario»).
        assert.deepEqual(doc.bloques.map((b) => [b.tipo, b.origen]), [["titulo", "ocr"], ["texto", "usuario"], ["texto", "usuario"]]);
        assert.match(doc.bloques[2].texto, /La derivada[\s\S]*Ejemplo/);
        assert.equal(doc.bloques[1].texto, "Nota añadida por mí");
        assert.equal(doc.bloques[0].texto_original, texto, "el original de la foto no cambia");
        await contexto.close();
    });

    test("conflicto 409: otra pestaña guardó antes y no se pisa en silencio", async () => {
        const { contexto, pagina, id, cuenta } = await abrir();
        await pagina.fill(".bloque >> nth=0 >> textarea", "Mi cambio en esta pestaña");
        // Otra pestaña guarda la versión 3
        const otra = await contexto.newPage();
        await otra.goto(`${backend.url}/front/editor.html?id=${id}`);
        await otra.waitForSelector(".bloque");
        await otra.fill(".bloque >> nth=1 >> textarea", "Cambio de la otra pestaña");
        await otra.click("#btGuardar");
        await otra.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
        await pagina.click("#btGuardar");
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoEditor"), /otra pestaña/);
        assert.equal(await estadoGuardado(pagina), "Cambios sin guardar");
        assert.equal(await pagina.inputValue(".bloque >> nth=0 >> textarea"), "Mi cambio en esta pestaña", "no se pierde");
        await pagina.click("#avisoEditor >> text=Ver la versión guardada (descarta mis cambios)");
        await pagina.waitForFunction(() => document.querySelectorAll(".bloque textarea")[1].value === "Cambio de la otra pestaña");
        assert.match(await estadoGuardado(pagina), /Versión 3/);
        await contexto.close();
        assert.ok(cuenta);
    });

    test("sesión caducada al guardar: los cambios se quedan y se avisa", async () => {
        const { contexto, pagina } = await abrir();
        await contexto.clearCookies();
        await pagina.fill(".bloque >> nth=0 >> textarea", "Cambio con la sesión caducada");
        await pagina.click("#btGuardar");
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoEditor"), /sesión caducó/);
        assert.match(pagina.url(), /editor\.html/, "no se fue de la página");
        assert.equal(await pagina.inputValue(".bloque >> nth=0 >> textarea"), "Cambio con la sesión caducada");
        await contexto.close();
    });

    test("aviso antes de salir con cambios sin guardar", async () => {
        const { contexto, pagina } = await abrir();
        await pagina.fill(".bloque >> nth=0 >> textarea", "Sin guardar");
        let dialogo = null;
        pagina.on("dialog", async (d) => { dialogo = d.type(); await d.dismiss(); });
        await pagina.close({ runBeforeUnload: true });
        await new Promise((r) => setTimeout(r, 500));
        assert.equal(dialogo, "beforeunload");
        await contexto.close();
    });

    test("manuscrito ilegible: recorte, texto pendiente y conservar imagen", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const cuenta = await registrar(contexto, backend.url);
        await pagina.goto(`${backend.url}/front/ayuda.html`);
        // Garabatos: el OCR no puede leerlos y debe dejar el bloque sin texto y con su recorte.
        const garabato = await pagina.evaluate(() => {
            const c = document.createElement("canvas"); c.width = 1400; c.height = 900;
            const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, 1400, 900);
            g.fillStyle = "#111"; g.font = "bold 80px sans-serif"; g.fillText("Tarea de física", 80, 150);
            g.strokeStyle = "#111"; g.lineWidth = 9;
            for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(120 + i * 180, 520); g.bezierCurveTo(200 + i * 180, 300, 60 + i * 180, 700, 260 + i * 180, 480); g.stroke(); }
            return c.toDataURL("image/png").split(",")[1];
        });
        const { id } = await crearApunte(contexto, backend.url, pagina, { cuenta, fotos: [Buffer.from(garabato, "base64")] });
        await pagina.goto(`${backend.url}/front/editor.html?id=${id}`);
        await pagina.waitForSelector(".bloque");
        const sinLeer = pagina.locator('.bloque[data-estado=no_reconocido], .bloque:has(.estado-chip.estado-incierto)');
        if (await sinLeer.count()) {
            const tarjeta = sinLeer.first();
            assert.equal(await tarjeta.locator(".bloque__recorte").count(), 1, "muestra el recorte para comparar");
            if (await tarjeta.locator("input[type=checkbox]").count()) {
                await tarjeta.locator("input[type=checkbox]").click();
                assert.equal(await pagina.isDisabled("#btGuardar"), false);
                await pagina.click("#btGuardar");
                await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
            }
        } else {
            // Si el OCR no generó ningún bloque dudoso, al menos no inventó texto para los garabatos.
            const textos = await pagina.$$eval(".bloque textarea", (t) => t.map((x) => x.value).join(" "));
            assert.ok(textos.length < 80, `texto inesperado: ${textos}`);
        }
        await contexto.close();
    });

    test("móvil: una columna, sin desbordamiento", async () => {
        const { contexto, pagina } = await abrir({}, { width: 360, height: 780 });
        assert.ok(await sinDesbordamiento(pagina));
        await contexto.close();
    });

    test("apunte ajeno o inexistente: mensaje sin datos", async () => {
        const a = await abrir();
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await pagina.goto(`${backend.url}/front/editor.html?id=${a.id}`);
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoEditor"), /no existe o no es tuyo/);
        assert.equal(await pagina.locator(".bloque").count(), 0);
        await contexto.close();
        await a.contexto.close();
        void fotoApunte;
    });

    // BACK-28: el servidor marca por qué revisar un bloque y ofrece otras lecturas reales de la foto.
    // La respuesta se intercepta para inyectar una alternativa conocida (el OCR de una imagen
    // dibujada en el navegador no es reproducible al detalle); el guardado sí va al backend real.
    test("motivo de revisión, avisos de la foto y alternativa con un clic", async () => {
        const { contexto, pagina, id, errores } = await abrir({ esperar: true });
        const apunte = await documento(contexto, id);
        const objetivo = apunte.documento.bloques[1];
        await pagina.route(`**/api/v2/apuntes/${id}`, async (ruta) => {
            if (ruta.request().method() !== "GET") return ruta.continue();
            const r = await ruta.fetch();
            const cuerpo = await r.json();
            const b = cuerpo.apunte.documento.bloques[1];
            Object.assign(b, { estado: "incierto", revision: "lecturas_distintas",
                               alternativas: [{ texto: "Lectura alternativa del motor", confianza: 0.88, variante: "ampliada" }] });
            cuerpo.apunte.documento.paginas[0].advertencias = ["IMAGEN_GIRADA", "REPETIR_FOTO"];
            await ruta.fulfill({ response: r, json: cuerpo });
        });
        await pagina.reload();
        await pagina.waitForSelector(".bloque");
        await pagina.uncheck("#chkAutoguardado");
        const tarjeta = pagina.locator(`.bloque[data-bloque="${objetivo.id}"]`);
        assert.match(await tarjeta.locator(".bloque__motivo").textContent(), /Dos lecturas de la foto no coinciden/);
        const avisos = await pagina.textContent("#visorAvisos");
        assert.match(avisos, /vuelve a tomarla/);
        assert.match(avisos, /foto girada \(se enderezó\)/);
        await tarjeta.getByRole("button", { name: /Usar la lectura «Lectura alternativa del motor»/ }).click();
        assert.equal(await tarjeta.locator("textarea").inputValue(), "Lectura alternativa del motor");
        assert.equal(await estadoGuardado(pagina), "Cambios sin guardar");
        await pagina.unroute(`**/api/v2/apuntes/${id}`);
        await pagina.click("#btGuardar");
        await pagina.waitForFunction(() => /Guardado/.test(document.getElementById("estadoGuardado").textContent));
        const guardado = (await documento(contexto, id)).documento.bloques[1];
        // Es una corrección del usuario: el texto reconocido se conserva y el cliente no pudo inventar alternativas
        assert.equal(guardado.texto, "Lectura alternativa del motor");
        assert.equal(guardado.editado, true);
        assert.equal(guardado.texto_original, objetivo.texto_original);
        assert.deepEqual(guardado.alternativas, objetivo.alternativas);
        assert.deepEqual(errores, []);
        await contexto.close();
    });
});
