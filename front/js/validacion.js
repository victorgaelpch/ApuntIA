// Validación de imágenes en el navegador (FRONT-02).
//
// Avisa al usuario antes de enviar, con los mismos criterios que el backend
// (docs/api.md): formato real JPEG/PNG/WEBP por firma binaria, archivo no
// vacío y tamaño máximo. El atributo accept del <input> solo filtra el
// selector y se puede saltar (arrastrar, "Todos los archivos", extensión
// cambiada), y el backend vuelve a validarlo todo.
(function (global) {
    "use strict";

    const NS = (global.ApuntIA = global.ApuntIA || {});

    const FIRMAS = [
        { formato: "image/jpeg", prueba: (b) => b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff },
        { formato: "image/png", prueba: (b) => [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a].every((v, i) => b[i] === v) },
        {
            formato: "image/webp",
            prueba: (b) => String.fromCharCode(...b.slice(0, 4)) === "RIFF" && String.fromCharCode(...b.slice(8, 12)) === "WEBP",
        },
    ];

    function detectarFormato(bytes) {
        const firma = FIRMAS.find((f) => bytes.length >= 12 && f.prueba(bytes));
        return firma ? firma.formato : null;
    }

    async function leerCabecera(archivo) {
        const buffer = await archivo.slice(0, 16).arrayBuffer();
        return new Uint8Array(buffer);
    }

    function formatearTamano(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
        return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    }

    /**
     * @param {File} archivo
     * @returns {Promise<{ok: true, formato: string} | {ok: false, codigo: string}>}
     *   codigo: ARCHIVO_AUSENTE | ARCHIVO_VACIO | ARCHIVO_DEMASIADO_GRANDE | TIPO_NO_PERMITIDO
     */
    async function validarArchivo(archivo) {
        const cfg = NS.config || {};
        const maxBytes = (cfg.maxMb || 10) * 1024 * 1024;
        if (!archivo) return { ok: false, codigo: "ARCHIVO_AUSENTE" };
        if (archivo.size === 0) return { ok: false, codigo: "ARCHIVO_VACIO" };
        if (archivo.size > maxBytes) return { ok: false, codigo: "ARCHIVO_DEMASIADO_GRANDE" };
        let formato = null;
        try {
            formato = detectarFormato(await leerCabecera(archivo));
        } catch (_) {
            return { ok: false, codigo: "TIPO_NO_PERMITIDO" };
        }
        if (!formato || !(cfg.formatos || []).includes(formato)) return { ok: false, codigo: "TIPO_NO_PERMITIDO" };
        return { ok: true, formato };
    }

    NS.validacion = { validarArchivo, detectarFormato, formatearTamano };
})(window);
