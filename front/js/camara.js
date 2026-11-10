// Captura de fotografías con la cámara (FRONT-03).
//
// Estrategia según el dispositivo:
//   1. Si hay getUserMedia y el contexto es seguro (https o localhost), se abre
//      un visor en vivo dentro de la página. Así se elige el encuadre y se pide
//      permiso de forma explícita.
//   2. Si no (http desde el celular en la red local, navegadores antiguos), se
//      usa <input type="file" capture="environment">: abre la app de cámara en
//      el móvil, o el selector de archivos en un ordenador.
//   3. Si se deniega el permiso o no hay cámara, se explica el motivo y se
//      ofrecen dos alternativas: la app de cámara (input capture) o «Cargar imagen».
(function (global) {
    "use strict";

    const NS = (global.ApuntIA = global.ApuntIA || {});

    function disponible() {
        return Boolean(global.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    // Traduce los errores de getUserMedia a códigos propios.
    function codigoError(error) {
        switch (error && error.name) {
            case "NotAllowedError":
            case "SecurityError":
                return "CAMARA_PERMISO_DENEGADO";
            case "NotFoundError":
            case "OverconstrainedError":
                return "CAMARA_NO_DISPONIBLE";
            case "NotReadableError":
            case "AbortError":
                return "CAMARA_OCUPADA";
            default:
                return "CAMARA_ERROR";
        }
    }

    function nombreFoto() {
        const d = new Date();
        const p = (n) => String(n).padStart(2, "0");
        return `foto-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}.jpg`;
    }

    /**
     * Controla el diálogo de cámara.
     * @param {{dialogo: HTMLDialogElement, video: HTMLVideoElement, mensaje: HTMLElement,
     *          btCapturar: HTMLButtonElement, btCerrar: HTMLButtonElement, flash?: HTMLElement}} el
     */
    function crearVisor(el) {
        let flujo = null;
        let alFoto = null;
        let alError = null;

        function detener() {
            if (flujo) flujo.getTracks().forEach((t) => t.stop());
            flujo = null;
            el.video.srcObject = null;
        }

        function cerrar() {
            detener();
            if (el.dialogo.open) el.dialogo.close();
        }

        async function abrir({ onFoto, onError }) {
            alFoto = onFoto;
            alError = onError;
            el.btCapturar.disabled = true;
            el.mensaje.textContent = "Solicitando permiso para usar la cámara...";
            el.dialogo.showModal();
            try {
                flujo = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
                    audio: false,
                });
                if (!el.dialogo.open) { detener(); return; } // se cerró mientras se pedía permiso
                el.video.srcObject = flujo;
                await el.video.play();
                el.mensaje.textContent = "Alinea el pizarrón o la hoja dentro del marco y pulsa el botón";
                el.btCapturar.disabled = false;
                el.btCapturar.focus();
            } catch (error) {
                cerrar();
                if (alError) alError(codigoError(error), error);
            }
        }

        async function capturar() {
            const { videoWidth: w, videoHeight: h } = el.video;
            if (!w || !h) return;
            el.btCapturar.disabled = true;
            const lienzo = document.createElement("canvas");
            lienzo.width = w;
            lienzo.height = h;
            lienzo.getContext("2d").drawImage(el.video, 0, 0, w, h);
            if (el.flash) { el.flash.classList.remove("go"); void el.flash.offsetWidth; el.flash.classList.add("go"); }
            const blob = await new Promise((r) => lienzo.toBlob(r, "image/jpeg", 0.92));
            cerrar();
            if (blob && alFoto) alFoto(new File([blob], nombreFoto(), { type: "image/jpeg", lastModified: Date.now() }));
        }

        el.btCapturar.addEventListener("click", capturar);
        el.btCerrar.addEventListener("click", cerrar);
        el.dialogo.addEventListener("close", detener); // también al pulsar Esc

        return { abrir, cerrar, capturar, activa: () => Boolean(flujo) };
    }

    NS.camara = { disponible, crearVisor, codigoError };
})(window);
