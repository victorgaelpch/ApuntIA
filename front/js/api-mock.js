// Respuestas simuladas de la API (FRONT-05).
//
// Se activa añadiendo ?mock=<escenario> a la URL de la página. Sustituye fetch
// solo para las peticiones dirigidas a la API, así que el cliente real
// (api.js) se ejecuta igual que contra el backend. Escenarios:
//
//   ok              200 con la imagen convertida a grises en el navegador
//   ok-sin-perspectiva  igual que ok, con X-ApuntIA-Perspectiva: no_detectada
//   lento           ok, tras 3 s (para ver los indicadores de carga)
//   colgado         nunca responde (para probar el tiempo agotado y la cancelación)
//   tipo            415 TIPO_NO_PERMITIDO
//   grande          413 ARCHIVO_DEMASIADO_GRANDE
//   corrupta        400 IMAGEN_CORRUPTA
//   servidor        500 ERROR_INTERNO
//   red             fallo de red (como un servidor apagado)
//   vacia           200 con cuerpo vacío (respuesta inválida)
(function (global) {
    "use strict";

    const escenario = new URLSearchParams(global.location.search).get("mock");
    if (!escenario) return;

    const NS = (global.ApuntIA = global.ApuntIA || {});
    const fetchReal = global.fetch.bind(global);
    const esperar = (ms, signal) => new Promise((resolve, reject) => {
        const t = setTimeout(resolve, ms);
        if (signal) signal.addEventListener("abort", () => { clearTimeout(t); reject(new DOMException("Abortado", "AbortError")); }, { once: true });
    });

    const ERRORES = {
        tipo: [415, "TIPO_NO_PERMITIDO", "Formato no admitido. Usa una imagen JPEG, PNG o WEBP."],
        grande: [413, "ARCHIVO_DEMASIADO_GRANDE", "La imagen pesa más de 10 MB. Elige una más ligera."],
        corrupta: [400, "IMAGEN_CORRUPTA", "No se pudo leer la imagen; puede estar dañada. Elige otra."],
        servidor: [500, "ERROR_INTERNO", "Ocurrió un error inesperado en el servidor. Inténtalo más tarde."],
    };

    function jsonError([status, codigo, mensaje]) {
        return new Response(JSON.stringify({ error: { codigo, mensaje } }), {
            status, headers: { "Content-Type": "application/json", "X-ApuntIA-Error-Id": "mock000000" },
        });
    }

    async function aGrises(archivo) {
        const bitmap = await createImageBitmap(archivo);
        const lienzo = document.createElement("canvas");
        lienzo.width = bitmap.width;
        lienzo.height = bitmap.height;
        const ctx = lienzo.getContext("2d");
        ctx.filter = "grayscale(1) contrast(1.2)";
        ctx.drawImage(bitmap, 0, 0);
        const blob = await new Promise((r) => lienzo.toBlob(r, "image/png"));
        return { blob, ancho: bitmap.width, alto: bitmap.height };
    }

    async function responder(url, init) {
        const signal = init && init.signal;
        if (url.pathname === "/salud") {
            return new Response(JSON.stringify({ estado: "ok", version: "mock", formatos: ["image/jpeg", "image/png", "image/webp"], max_mb: 10, max_megapixeles: 50 }), { headers: { "Content-Type": "application/json" } });
        }
        if (url.pathname !== "/analisis") return jsonError([404, "RUTA_NO_ENCONTRADA", "La ruta solicitada no existe."]);

        await esperar(escenario === "lento" ? 3000 : 400, signal);
        if (escenario === "colgado") await esperar(10 * 60 * 1000, signal);
        if (escenario === "red") throw new TypeError("Failed to fetch (simulado)");
        if (ERRORES[escenario]) return jsonError(ERRORES[escenario]);
        if (escenario === "vacia") return new Response(new Blob([]), { headers: { "Content-Type": "image/png" } });

        const archivo = init.body.get(NS.api ? NS.api.CAMPO_ARCHIVO : "file");
        if (!archivo) return jsonError([400, "ARCHIVO_AUSENTE", "No se recibió ninguna imagen."]);
        const { blob, ancho, alto } = await aGrises(archivo);
        const base = (archivo.name || "imagen").replace(/\.[^.]+$/, "");
        return new Response(blob, {
            status: 200,
            headers: {
                "Content-Type": "image/png",
                "Content-Disposition": `inline; filename*=UTF-8''${encodeURIComponent(base + "_apuntia.png")}`,
                "X-ApuntIA-Archivo": encodeURIComponent(archivo.name || "imagen"),
                "X-ApuntIA-Perspectiva": escenario === "ok-sin-perspectiva" ? "no_detectada" : "corregida",
                "X-ApuntIA-Dimensiones": `${ancho}x${alto}`,
                "X-ApuntIA-Tiempo-Ms": "123",
            },
        });
    }

    global.fetch = function (entrada, init) {
        const url = new URL(typeof entrada === "string" ? entrada : entrada.url, global.location.href);
        const base = NS.api ? new URL(NS.api.urlBase()) : null;
        if (base && url.origin === base.origin) return responder(url, init || {});
        return fetchReal(entrada, init);
    };
    NS.mock = { escenario };
    console.info(`[ApuntIA] API simulada activa: escenario «${escenario}»`);
})(window);
