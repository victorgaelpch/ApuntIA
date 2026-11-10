// FRONT-18: panel «Mis apuntes» con el backend real: aislamiento entre cuentas,
// paginación, búsqueda, filtros, estados, descarga del último PDF y borrado.
const { test, describe, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { chromium } = require("playwright");
const { iniciarBackendV2, registrar, vigilarConsola, sinDesbordamiento } = require("./v2-entorno");
const { crearApunte, fotoApunte, esperarTrabajo } = require("./v2-apuntes-ayuda");

describe("FRONT-18 Mis apuntes", () => {
    let navegador, backend, sinOcr;
    let ana; // { contexto, pagina, cuenta, ids }
    before(async () => {
        navegador = await chromium.launch();
        backend = await iniciarBackendV2();
        sinOcr = await iniciarBackendV2({ OCR_MOTOR: "ninguno" });
        const contexto = await navegador.newContext({ acceptDownloads: true });
        const pagina = await contexto.newPage();
        const cuenta = await registrar(contexto, backend.url, { email: "ana@example.com" });
        const ids = [];
        await pagina.goto(`${backend.url}/front/ayuda.html`);
        const foto = await fotoApunte(pagina);
        for (let i = 1; i <= 13; i++) {
            const titulo = i === 7 ? "Física: Óptica geométrica" : `Clase ${String(i).padStart(2, "0")}`;
            ids.push((await crearApunte(contexto, backend.url, pagina, { cuenta, titulo, fotos: [foto] })).id);
        }
        ana = { contexto, pagina, cuenta, ids };
    });
    after(async () => { await navegador.close(); await backend.detener(); await sinOcr.detener(); });

    const resumen = (p) => p.textContent("#resumenLista");
    const titulos = (p) => p.$$eval(".apunte h2", (l) => l.map((x) => x.textContent));
    async function irLista(pagina, consulta = "") {
        await pagina.goto(`${backend.url}/front/apuntes.html${consulta}`);
        await pagina.waitForSelector("#listaApuntes[aria-busy=false]");
    }

    test("cuenta nueva: estado vacío con acceso a crear el primero", async () => {
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        const errores = vigilarConsola(pagina);
        await irLista(pagina);
        assert.match(await resumen(pagina), /Todavía no tienes apuntes/);
        assert.equal(await pagina.getAttribute(".vacio a", "href"), "/front/nuevo.html");
        assert.deepEqual(errores, []);
        await contexto.close();
    });

    test("otra cuenta no ve nada de Ana, ni buscando ni con su URL", async () => {
        const contexto = await navegador.newContext();
        await registrar(contexto, backend.url, { email: "beto@example.com" });
        const pagina = await contexto.newPage();
        await irLista(pagina, "?q=%C3%93ptica");
        assert.equal(await pagina.locator(".apunte").count(), 0);
        await pagina.goto(`${backend.url}/front/editor.html?id=${ana.ids[0]}`);
        await pagina.waitForSelector("#avisoEditor[data-tipo=error]");
        assert.match(await pagina.textContent("#avisoEditor"), /no existe o no es tuyo/);
        await contexto.close();
    });

    test("paginación, búsqueda en el texto, filtros y estado en la URL", async () => {
        const { pagina } = ana;
        await irLista(pagina);
        assert.match(await resumen(pagina), /^13 apuntes\./);
        assert.equal(await pagina.locator(".apunte").count(), 12);
        assert.equal(await pagina.textContent("#textoPaginacion"), "Página 1 de 2");
        await pagina.click("#btSiguiente");
        await pagina.waitForFunction(() => document.querySelectorAll(".apunte").length === 1);
        assert.match(pagina.url(), /pagina=2/);
        assert.deepEqual(await titulos(pagina), ["Clase 01"], "orden: más recientes primero");
        // Búsqueda por título
        await pagina.fill("#inpBuscar", "Óptica");
        await pagina.click("#formFiltros button[type=submit]");
        await pagina.waitForFunction(() => document.querySelectorAll(".apunte").length === 1);
        assert.deepEqual(await titulos(pagina), ["Física: Óptica geométrica"]);
        assert.equal(await pagina.isHidden("#paginacion"), true);
        // Búsqueda en el texto reconocido (no en el título)
        await pagina.fill("#inpBuscar", "razón de cambio");
        await pagina.click("#formFiltros button[type=submit]");
        await pagina.waitForFunction(() => /13 apuntes con estos filtros/.test(document.getElementById("resumenLista").textContent));
        // Filtro sin resultados y limpiar
        await pagina.fill("#inpBuscar", "");
        await pagina.selectOption("#selEstado", "fallido");
        await pagina.waitForFunction(() => /Ningún apunte coincide/.test(document.getElementById("resumenLista").textContent));
        await pagina.click(".vacio >> text=Limpiar filtros");
        await pagina.waitForFunction(() => document.querySelectorAll(".apunte").length === 12);
        // Fechas: hasta ayer → nada; orden por título
        const ayer = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
        await pagina.fill("#inpHasta", ayer);
        await pagina.dispatchEvent("#inpHasta", "change");
        await pagina.waitForFunction(() => /Ningún apunte coincide/.test(document.getElementById("resumenLista").textContent));
        await pagina.click("#btLimpiar");
        await pagina.selectOption("#selOrden", "titulo");
        await pagina.waitForFunction(() => (document.querySelector(".apunte h2") || {}).textContent === "Clase 01");
    });

    test("volver del editor conserva la búsqueda", async () => {
        const { pagina } = ana;
        await irLista(pagina, "?q=%C3%93ptica");
        assert.equal(await pagina.inputValue("#inpBuscar"), "Óptica");
        await pagina.click(".apunte [data-accion=abrir]");
        await pagina.waitForSelector(".bloque");
        await pagina.goBack();
        await pagina.waitForSelector("#listaApuntes[aria-busy=false] .apunte");
        assert.equal(await pagina.inputValue("#inpBuscar"), "Óptica");
        assert.deepEqual(await titulos(pagina), ["Física: Óptica geométrica"]);
    });

    test("descargar el último PDF desde la lista", async () => {
        const { contexto, pagina, cuenta, ids } = ana;
        const r = await contexto.request.post(`${backend.url}/api/v2/apuntes/${ids[6]}/exportaciones`, {
            data: {}, headers: { "X-CSRF-Token": cuenta.csrf, Origin: backend.url } });
        await esperarTrabajo(contexto, backend.url, (await r.json()).trabajo.id);
        await irLista(pagina, "?q=%C3%93ptica");
        assert.match(await pagina.textContent(".apunte"), /1 PDF/);
        const [descarga] = await Promise.all([pagina.waitForEvent("download"), pagina.click("[data-accion=descargar]")]);
        assert.equal(descarga.suggestedFilename(), "fisica-optica-geometrica-v2.pdf");
        assert.equal(fs.readFileSync(await descarga.path()).subarray(0, 5).toString(), "%PDF-");
    });

    test("eliminar pide confirmación y no borra al cancelar", async () => {
        const { pagina } = ana;
        await irLista(pagina, "?orden=titulo");
        await pagina.click('.apunte:has-text("Clase 01") [data-accion=eliminar]');
        assert.match(await pagina.textContent(".dlg-app"), /No se puede deshacer/);
        await pagina.click(".dlg-app >> text=Cancelar");
        assert.equal(await pagina.locator('.apunte:has-text("Clase 01")').count(), 1);
        await pagina.click('.apunte:has-text("Clase 01") [data-accion=eliminar]');
        await pagina.click(".dlg-app button[type=submit]");
        await pagina.waitForSelector("#avisoLista[data-tipo=exito]");
        assert.match(await pagina.textContent("#avisoLista"), /«Clase 01» se eliminó/);
        assert.match(await resumen(pagina), /^12 apuntes/);
    });

    test("estados en curso y fallidos se muestran como tales", async () => {
        const contexto = await navegador.newContext();
        const pagina = await contexto.newPage();
        const { id, trabajo } = await crearApunte(contexto, sinOcr.url, pagina, { titulo: "Sin OCR" });
        assert.equal(trabajo.estado, "fallido");
        await pagina.goto(`${sinOcr.url}/front/apuntes.html`);
        await pagina.waitForSelector(".apunte");
        assert.match(await pagina.textContent(".apunte .estado-chip"), /Falló/);
        assert.equal(await pagina.textContent(".apunte [data-accion=abrir]"), "Revisar y reintentar");
        assert.equal(await pagina.locator(".apunte [data-accion=exportar]").count(), 0, "no ofrece PDF de un apunte fallido");
        assert.ok(id);
        // En curso
        await crearApunte(contexto, backend.url, pagina, { titulo: "En curso", esperar: false });
        await pagina.goto(`${backend.url}/front/apuntes.html`);
        await pagina.waitForSelector(".apunte");
        const primero = await pagina.textContent(".apunte");
        assert.ok(/En cola|Procesando|Listo/.test(primero));
        if (/En cola|Procesando/.test(primero)) assert.equal(await pagina.textContent(".apunte [data-accion=abrir]"), "Ver progreso");
        await contexto.close();
    });

    test("móvil y teclado", async () => {
        const contexto = await navegador.newContext({ viewport: { width: 360, height: 780 } });
        await registrar(contexto, backend.url);
        const pagina = await contexto.newPage();
        await irLista(pagina);
        assert.ok(await sinDesbordamiento(pagina));
        await pagina.focus("#inpBuscar");
        await pagina.keyboard.type("algo");
        await pagina.keyboard.press("Enter");
        await pagina.waitForFunction(() => /q=algo/.test(location.search));
        await contexto.close();
    });
});
