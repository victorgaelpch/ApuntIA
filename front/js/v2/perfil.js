// Perfil, preferencias, contraseña, sesiones y borrado de la cuenta (FRONT-19).
//
// - Todo se guarda en el servidor (PATCH /api/v2/perfil, PUT /auth/password…) y el
//   estado «Guardado» solo aparece tras su respuesta. La preferencia de investigación
//   la aplica el backend: sin ella, la búsqueda externa se rechaza.
// - Las contraseñas se borran de los campos tras cada envío y no se guardan.
// - Borrar la cuenta exige la contraseña y escribir «BORRAR».
(function () {
    "use strict";
    const NS = window.ApuntIA;
    const { $, pedir, requerirSesion, cabecera, cerrarSesion, confirmar, avisarError, textoDeError, sesion, fecha } = NS.v2;
    const F = NS.formularios;

    function estado(id, tipo, texto) {
        const el = $(id);
        el.dataset.tipo = tipo;
        el.textContent = texto;
    }

    function pintar(usuario) {
        const p = usuario.preferencias || {};
        $("#perfilNombre").value = usuario.nombre;
        $("#perfilEmail").value = usuario.email;
        $("#altaCuenta").textContent = usuario.creado ? `Cuenta creada el ${fecha(usuario.creado)}.` : "";
        $("#prefFuente").value = p.tipo_fuente || "auto";
        $("#prefIdioma").value = p.idioma_ocr || "spa+eng";
        $("#prefEstiloPdf").value = p.estilo_pdf || "extendido";
        $("#prefComplementosPdf").checked = p.incluir_complementos_pdf !== false;
        $("#prefOriginalesPdf").checked = Boolean(p.incluir_originales_pdf);
        $("#prefInvestigacion").checked = Boolean(p.investigacion_permitida);
    }

    async function guardarDatos(e) {
        e.preventDefault();
        const nombre = $("#perfilNombre");
        if (!F.validar([[nombre, F.reglas.nombre]])) return;
        estado("#estadoDatos", "guardando", "Guardando…");
        await F.enviando(e.currentTarget, async () => {
            try {
                const r = await pedir("/api/v2/perfil", { method: "PATCH", json: { nombre: nombre.value.trim() } });
                sesion.usuario = r.usuario;
                pintar(r.usuario);
                cabecera("perfil");
                estado("#estadoDatos", "exito", "Guardado.");
            } catch (err) {
                estado("#estadoDatos", "error", textoDeError(err));
            }
        });
    }

    async function guardarPreferencias(e) {
        e.preventDefault();
        const form = e.currentTarget;  // tras un await (confirmación) currentTarget ya es null
        const quiereInvestigar = $("#prefInvestigacion").checked;
        if (quiereInvestigar && !sesion.usuario.preferencias.investigacion_permitida) {
            const ok = await confirmar({ titulo: "¿Permitir la búsqueda externa?", aceptar: "Permitir",
                texto: "Podrás buscar información complementaria de tus apuntes. Cada búsqueda te pedirá confirmación y solo enviará las palabras clave que elijas." });
            if (!ok) { $("#prefInvestigacion").checked = false; return; }
        }
        estado("#estadoPreferencias", "guardando", "Guardando…");
        await F.enviando(form, async () => {
            try {
                const r = await pedir("/api/v2/perfil", { method: "PATCH", json: { preferencias: {
                    tipo_fuente: $("#prefFuente").value, idioma_ocr: $("#prefIdioma").value, estilo_pdf: $("#prefEstiloPdf").value,
                    incluir_complementos_pdf: $("#prefComplementosPdf").checked, incluir_originales_pdf: $("#prefOriginalesPdf").checked,
                    investigacion_permitida: quiereInvestigar } } });
                sesion.usuario = r.usuario;
                pintar(r.usuario);
                estado("#estadoPreferencias", "exito", "Preferencias guardadas.");
            } catch (err) {
                estado("#estadoPreferencias", "error", textoDeError(err));
            }
        });
    }

    async function cambiarPassword(e) {
        e.preventDefault();
        const actual = $("#passActual"), nueva = $("#passNueva"), confirmarCampo = $("#passConfirmar");
        if (!F.validar([[actual, F.reglas.requerido], [nueva, F.reglas.claveNueva, sesion.usuario.email], [confirmarCampo, F.reglas.confirmar, nueva.value]])) return;
        estado("#estadoClave", "guardando", "Cambiando…");
        await F.enviando(e.currentTarget, async () => {
            try {
                await pedir("/api/v2/auth/password", { method: "PUT", json: { actual: actual.value, nueva: nueva.value } });
                estado("#estadoClave", "exito", "Contraseña cambiada. Se cerró la sesión en los demás navegadores.");
                pintarSesiones();
            } catch (err) {
                if (err.codigo === "CREDENCIALES_INVALIDAS") { F.errorCampo(actual, err.mensaje); actual.focus(); estado("#estadoClave", "", ""); }
                else estado("#estadoClave", "error", textoDeError(err));
            } finally {
                actual.value = nueva.value = confirmarCampo.value = "";
            }
        });
    }

    async function pintarSesiones() {
        try {
            const { otras } = await pedir("/api/v2/auth/sesiones");
            $("#textoSesiones").textContent = otras === 0 ? "Solo tienes abierta la sesión de este navegador."
                : `Además de esta, tienes ${otras} ${otras === 1 ? "sesión abierta" : "sesiones abiertas"} en otros navegadores o dispositivos.`;
            $("#btCerrarOtras").disabled = otras === 0;
        } catch (err) {
            $("#textoSesiones").textContent = textoDeError(err);
        }
    }

    async function cerrarOtras() {
        try {
            const { cerradas } = await pedir("/api/v2/auth/sesiones/otras", { method: "DELETE" });
            estado("#estadoSesiones", "exito", `Se cerraron ${cerradas} ${cerradas === 1 ? "sesión" : "sesiones"}.`);
            pintarSesiones();
        } catch (err) {
            estado("#estadoSesiones", "error", textoDeError(err));
        }
    }

    async function borrarCuenta(e) {
        e.preventDefault();
        const password = $("#borrarPassword");
        if (!F.validar([[password, F.reglas.requerido]])) return;
        const ok = await confirmar({ titulo: "¿Borrar tu cuenta para siempre?", peligro: true, aceptar: "Borrar mi cuenta", escribir: "BORRAR",
                                     texto: "Se borrarán tu cuenta y todos tus apuntes, fotos, versiones y PDF. No se puede deshacer." });
        if (!ok) { password.value = ""; return; }
        try {
            await pedir("/api/v2/perfil", { method: "DELETE", json: { password: password.value } });
            password.value = "";
            location.assign("/front/cuenta.html?motivo=cuenta-borrada");
        } catch (err) {
            password.value = "";
            if (err.codigo === "CREDENCIALES_INVALIDAS") { F.errorCampo(password, err.mensaje); password.focus(); }
            else avisarError($("#avisoPerfil"), err);
        }
    }

    async function iniciar() {
        const usuario = await requerirSesion();
        cabecera("perfil");
        F.botonesVerPassword();
        pintar(usuario);
        $("#formDatos").addEventListener("submit", guardarDatos);
        $("#formPreferencias").addEventListener("submit", guardarPreferencias);
        $("#formPassword").addEventListener("submit", cambiarPassword);
        $("#formBorrar").addEventListener("submit", borrarCuenta);
        $("#btCerrarOtras").addEventListener("click", cerrarOtras);
        $("#btCerrarSesion").addEventListener("click", cerrarSesion);
        pintarSesiones();
    }
    iniciar();
})();
