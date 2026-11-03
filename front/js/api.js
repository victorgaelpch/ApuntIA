// Cliente de la API de ApuntIA (FRONT-05). Sigue el contrato de docs/api.md.
//
// Uso:
//   const { blob, perspectiva } = await ApuntIA.api.procesarImagen(archivo, { ruido: "mediana" }, { signal });
//   const salud = await ApuntIA.api.obtenerSalud();
//
// Todas las funciones lanzan ApuntIA.api.ApiError con:
//   tipo:    "red" | "tiempo" | "cancelado" | "http" | "respuesta"
//   codigo:  el código del contrato (p. ej. "TIPO_NO_PERMITIDO") o uno propio
//            del cliente (SIN_CONEXION, TIEMPO_AGOTADO, CANCELADO, RESPUESTA_INVALIDA)
//   mensaje: texto del servidor apto para el usuario, si lo hay
//   status:  código HTTP (0 si no hubo respuesta)
//
// Script clásico (sin módulos ES) para que la página funcione también al abrir
// index.html con doble clic (file://).
(function (global) {
    "use strict";

    const NS = (global.ApuntIA = global.ApuntIA || {});
    const CAMPO_ARCHIVO = "file";

    class ApiError extends Error {
        constructor({ tipo, codigo, mensaje = "", status = 0, errorId = null, causa = null }) {
            super(`${codigo}${mensaje ? ": " + mensaje : ""}`);
            this.name = "ApiError";
            this.tipo = tipo;
            this.codigo = codigo;
            this.mensaje = mensaje;
            this.status = status;
            this.errorId = errorId;
            this.causa = causa;
        }
    }

    function config() {
        return NS.config || {};
    }

    function urlBase() {
        const desdeQuery = new URLSearchParams(global.location.search).get("api");
        const base = desdeQuery || config().apiUrl;
        if (base) return String(base).replace(/\/+$/, "");
        const host = global.location.hostname || "localhost";
        const protocolo = global.location.protocol === "https:" ? "https:" : "http:";
        return `${protocolo}//${host}:${config().apiPuerto || 8000}`;
    }

    // fetch con tiempo máximo y cancelación externa combinados.
    async function solicitar(ruta, { method = "GET", body, signal, timeoutMs } = {}) {
        const controlador = new AbortController();
        let porTiempo = false;
        const limite = timeoutMs ?? config().timeoutMs ?? 60000;
        const temporizador = setTimeout(() => { porTiempo = true; controlador.abort(); }, limite);
        const alCancelar = () => controlador.abort();
        if (signal) {
            if (signal.aborted) controlador.abort();
            else signal.addEventListener("abort", alCancelar, { once: true });
        }

        try {
            return await fetch(urlBase() + ruta, { method, body, signal: controlador.signal });
        } catch (e) {
            if (porTiempo) throw new ApiError({ tipo: "tiempo", codigo: "TIEMPO_AGOTADO", causa: e });
            if (controlador.signal.aborted) throw new ApiError({ tipo: "cancelado", codigo: "CANCELADO", causa: e });
            // fetch solo rechaza por fallos de red, servidor apagado o bloqueo CORS.
            throw new ApiError({ tipo: "red", codigo: "SIN_CONEXION", causa: e });
        } finally {
            clearTimeout(temporizador);
            if (signal) signal.removeEventListener("abort", alCancelar);
        }
    }

    // Convierte una respuesta no 2xx en ApiError, leyendo {"error": {codigo, mensaje}}.
    async function errorDesdeRespuesta(respuesta) {
        let codigo = `HTTP_${respuesta.status}`;
        let mensaje = "";
        try {
            const cuerpo = await respuesta.json();
            if (cuerpo && cuerpo.error) {
                codigo = cuerpo.error.codigo || codigo;
                mensaje = cuerpo.error.mensaje || "";
            }
        } catch (_) { /* cuerpo no JSON: se queda el código HTTP */ }
        return new ApiError({
            tipo: "http", codigo, mensaje, status: respuesta.status,
            errorId: respuesta.headers.get("X-ApuntIA-Error-Id"),
        });
    }

    function construirQuery(opciones) {
        const params = new URLSearchParams();
        for (const clave of ["perspectiva", "ruido", "mejorar", "grises"]) {
            if (opciones[clave] !== undefined && opciones[clave] !== null) params.set(clave, String(opciones[clave]));
        }
        const texto = params.toString();
        return texto ? `?${texto}` : "";
    }

    function decodificarCabecera(valor) {
        if (!valor) return null;
        try { return decodeURIComponent(valor); } catch (_) { return valor; }
    }

    function nombreDescarga(respuesta, archivo) {
        const disposicion = respuesta.headers.get("Content-Disposition") || "";
        const m = disposicion.match(/filename\*=UTF-8''([^;]+)/i) || disposicion.match(/filename="?([^";]+)"?/i);
        if (m) return decodificarCabecera(m[1]);
        const base = (archivo && archivo.name ? archivo.name : "imagen").replace(/\.[^.]+$/, "");
        return `${base}_apuntia.png`;
    }

    /**
     * Envía una imagen a POST /analisis.
     * @param {File|Blob} archivo
     * @param {{perspectiva?: boolean, ruido?: string, mejorar?: boolean, grises?: boolean}} opciones
     * @param {{signal?: AbortSignal, timeoutMs?: number}} control
     * @returns {Promise<{blob: Blob, perspectiva: string|null, dimensiones: {ancho:number, alto:number}|null,
     *                    tiempoMs: number|null, archivoRecibido: string|null, nombreDescarga: string}>}
     */
    async function procesarImagen(archivo, opciones = {}, control = {}) {
        const datos = new FormData();
        // No se fija Content-Type: el navegador añade el boundary del multipart.
        datos.append(CAMPO_ARCHIVO, archivo, archivo.name || "imagen");

        const respuesta = await solicitar(`/analisis${construirQuery(opciones)}`, {
            method: "POST", body: datos, signal: control.signal, timeoutMs: control.timeoutMs,
        });
        if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);

        const blob = await respuesta.blob();
        if (!blob.size || !(blob.type || "").startsWith("image/")) {
            throw new ApiError({ tipo: "respuesta", codigo: "RESPUESTA_INVALIDA", status: respuesta.status });
        }
        const dim = (respuesta.headers.get("X-ApuntIA-Dimensiones") || "").match(/^(\d+)x(\d+)$/);
        const tiempo = Number(respuesta.headers.get("X-ApuntIA-Tiempo-Ms"));
        return {
            blob,
            perspectiva: respuesta.headers.get("X-ApuntIA-Perspectiva"),
            dimensiones: dim ? { ancho: Number(dim[1]), alto: Number(dim[2]) } : null,
            tiempoMs: Number.isFinite(tiempo) && respuesta.headers.has("X-ApuntIA-Tiempo-Ms") ? tiempo : null,
            archivoRecibido: decodificarCabecera(respuesta.headers.get("X-ApuntIA-Archivo")),
            nombreDescarga: nombreDescarga(respuesta, archivo),
        };
    }

    /** GET /salud: estado y límites del servicio. */
    async function obtenerSalud(control = {}) {
        const respuesta = await solicitar("/salud", { signal: control.signal, timeoutMs: control.timeoutMs ?? 5000 });
        if (!respuesta.ok) throw await errorDesdeRespuesta(respuesta);
        try {
            return await respuesta.json();
        } catch (e) {
            throw new ApiError({ tipo: "respuesta", codigo: "RESPUESTA_INVALIDA", status: respuesta.status, causa: e });
        }
    }

    NS.api = { urlBase, procesarImagen, obtenerSalud, ApiError, CAMPO_ARCHIVO };
})(window);
