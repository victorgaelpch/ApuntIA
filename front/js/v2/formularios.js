// Validación común de formularios (FRONT-17, FRONT-19, FRONT-20).
// El backend es la autoridad: esto solo evita envíos inútiles y explica el error
// junto al campo (aria-invalid + texto enlazado con aria-describedby).
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const MIN_PASSWORD = 10;
    const EMAIL = /^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$/;

    function errorCampo(input, texto) {
        const caja = document.getElementById(`${input.id}Error`);
        if (caja) caja.textContent = texto || "";
        if (texto) input.setAttribute("aria-invalid", "true");
        else input.removeAttribute("aria-invalid");
        return !texto;
    }

    function limpiarErrores(form) {
        form.querySelectorAll("input, select, textarea").forEach((i) => errorCampo(i, ""));
    }

    const reglas = {
        email: (v) => (!v.trim() ? "Escribe tu email." : EMAIL.test(v.trim()) ? "" : "Escribe un email válido, como nombre@ejemplo.com."),
        nombre: (v) => (!v.trim() ? "Escribe tu nombre." : v.trim().length > 80 ? "Máximo 80 caracteres." : ""),
        requerido: (v) => (v ? "" : "Este campo es obligatorio."),
        claveNueva: (v, email = "") => (
            v.length < MIN_PASSWORD ? `Usa al menos ${MIN_PASSWORD} caracteres.`
                : v.length > 256 ? "La contraseña es demasiado larga."
                    : email && v.toLowerCase() === email.trim().toLowerCase() ? "No uses tu email como contraseña." : ""),
        confirmar: (v, original) => (v === original ? "" : "Las contraseñas no coinciden."),
    };

    // Valida [input, regla, ...args] y enfoca el primero con error.
    function validar(pares) {
        let primero = null;
        for (const [input, regla, ...args] of pares) {
            const ok = errorCampo(input, (typeof regla === "function" ? regla : reglas[regla])(input.value, ...args));
            if (!ok && !primero) primero = input;
        }
        if (primero) primero.focus();
        return !primero;
    }

    // Botones «Mostrar/Ocultar» de las contraseñas.
    function botonesVerPassword(raiz = document) {
        raiz.querySelectorAll(".ver-password").forEach((b) => {
            b.addEventListener("click", () => {
                const input = document.getElementById(b.getAttribute("aria-controls"));
                const ver = input.type === "password";
                input.type = ver ? "text" : "password";
                b.setAttribute("aria-pressed", String(ver));
                b.textContent = ver ? "Ocultar" : "Mostrar";
                b.setAttribute("aria-label", ver ? "Ocultar la contraseña" : "Mostrar la contraseña");
            });
            b.setAttribute("aria-label", "Mostrar la contraseña");
        });
    }

    // Bloquea el formulario mientras se envía (evita dobles envíos).
    async function enviando(form, fn) {
        const controles = [...form.querySelectorAll("button, input, select, textarea")];
        const previos = controles.map((c) => c.disabled);
        controles.forEach((c) => { c.disabled = true; });
        form.setAttribute("aria-busy", "true");
        try {
            return await fn();
        } finally {
            controles.forEach((c, i) => { c.disabled = previos[i]; });
            form.removeAttribute("aria-busy");
        }
    }

    NS.formularios = { errorCampo, limpiarErrores, validar, reglas, botonesVerPassword, enviando, MIN_PASSWORD };
})(window);
