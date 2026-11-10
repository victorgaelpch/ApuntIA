// Ayuda (FRONT-11): estado real de las funciones según GET /salud.
(function () {
    "use strict";
    const { h, $, vaciar, cabecera, cargarSesion, avisarError } = window.ApuntIA.v2;

    function fila(funcion, ok, nota) {
        return h("tr", {},
            h("td", { text: funcion }),
            h("td", {}, h("span", { class: `estado-chip estado-${ok ? "listo" : "fallido"}`, text: ok ? "Disponible" : "No disponible" })),
            h("td", { text: nota }));
    }

    async function iniciar() {
        try { await cargarSesion(); } catch (_) { /* la ayuda funciona sin sesión */ }
        cabecera("ayuda");
        const tabla = $("#tablaFunciones");
        try {
            const r = await fetch("/salud", { cache: "no-store" });
            const s = await r.json();
            const ocr = s.ocr || {};
            const inv = s.investigacion || {};
            vaciar(tabla).append(
                fila("Mejorar una foto (PNG)", true, `JPEG, PNG o WEBP de hasta ${s.max_mb} MB.`),
                fila("Reconocer texto (OCR)", Boolean(ocr.disponible),
                     ocr.disponible ? `Motor ${ocr.motor} ${ocr.version || ""}; idiomas: ${(ocr.idiomas || []).join(", ")}.`
                                    : "Sin OCR los apuntes no se pueden analizar (falta Tesseract en el servidor)."),
                fila("Fórmulas a LaTeX", Boolean(ocr.disponible), "Las fórmulas que no se reconocen con seguridad se conservan como imagen."),
                fila("Apuntes de varias páginas", true, `Hasta ${s.max_paginas || 20} fotos por apunte.`),
                fila("PDF del apunte", true, "Se genera en el servidor, sin Internet."),
                fila("Información complementaria", Boolean(inv.disponible),
                     inv.disponible ? `Fuente: ${inv.proveedor}. Opcional y con tu consentimiento.`
                                    : "Desactivada en este servidor: puedes crear el PDF solo con tu apunte."),
            );
        } catch (e) {
            vaciar(tabla);
            avisarError($("#avisoFunciones"), { codigo: "SIN_CONEXION" });
        }
    }
    iniciar();
})();
