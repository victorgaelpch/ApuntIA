// Registro, inicio de sesión y recuperación de contraseña (FRONT-17).
//
// - Las contraseñas nunca se guardan: se envían y se borran de los campos.
// - El token de recuperación llega en el fragmento (#recuperar=…), que el
//   navegador no envía al servidor ni a terceros; se quita de la barra de
//   direcciones en cuanto se lee.
// - «volver» solo acepta rutas propias (/front/… o /inicio): sin redirecciones abiertas.
(function () {
    "use strict";
    const { $, pedir, fijarSesion, cargarSesion, cerrarSesion, cabecera, avisar, avisarError } = window.ApuntIA.v2;
    const F = window.ApuntIA.formularios;
    const aviso = $("#avisoCuenta");
    const params = new URLSearchParams(location.search);

    function destino() {
        const volver = params.get("volver") || "";
        return /^\/(front\/[A-Za-z0-9_-]+\.html(\?[^#\s]*)?|inicio)$/.test(volver) ? volver : "/front/apuntes.html";
    }

    // ---------------------------------------------------------------- pestañas
    const pestanas = ["Entrar", "Registro", "Olvido"];
    function mostrar(nombre, enfocar = true) {
        for (const p of pestanas) {
            const activa = p === nombre;
            const tab = $(`#tab${p}`);
            tab.setAttribute("aria-selected", String(activa));
            tab.tabIndex = activa ? 0 : -1;
            $(`#panel${p}`).hidden = !activa;
        }
        if (enfocar) $(`#panel${nombre} input`).focus();
    }
    pestanas.forEach((p, i) => {
        const tab = $(`#tab${p}`);
        tab.addEventListener("click", () => mostrar(p));
        tab.addEventListener("keydown", (e) => {
            const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
            if (!d) return;
            const sig = pestanas[(i + d + pestanas.length) % pestanas.length];
            mostrar(sig, false);
            $(`#tab${sig}`).focus();
        });
    });

    // ---------------------------------------------------------------- envíos
    async function entrar(e) {
        e.preventDefault();
        const form = e.currentTarget;
        const email = $("#entrarEmail"), password = $("#entrarPassword");
        if (!F.validar([[email, F.reglas.email], [password, F.reglas.requerido]])) return;
        await F.enviando(form, async () => {
            try {
                const r = await pedir("/api/v2/auth/sesion", { method: "POST", sinAvisoSesion: true,
                                                              json: { email: email.value.trim(), password: password.value } });
                password.value = "";
                fijarSesion(r);
                avisar(aviso, "exito", `Hola, ${r.usuario.nombre}. Entrando…`);
                location.assign(destino());
            } catch (err) {
                password.value = "";
                avisarError(aviso, err);
                password.focus();
            }
        });
    }

    async function registrarse(e) {
        e.preventDefault();
        const form = e.currentTarget;
        const nombre = $("#regNombre"), email = $("#regEmail"), password = $("#regPassword"), confirmar = $("#regConfirmar");
        if (!F.validar([[nombre, F.reglas.nombre], [email, F.reglas.email], [password, F.reglas.claveNueva, email.value],
                        [confirmar, F.reglas.confirmar, password.value]])) return;
        await F.enviando(form, async () => {
            try {
                const r = await pedir("/api/v2/auth/registro", { method: "POST", sinAvisoSesion: true,
                    json: { nombre: nombre.value.trim(), email: email.value.trim(), password: password.value } });
                password.value = confirmar.value = "";
                fijarSesion(r);
                avisar(aviso, "exito", "Cuenta creada. Entrando…");
                location.assign(params.get("volver") ? destino() : "/front/nuevo.html");
            } catch (err) {
                password.value = confirmar.value = "";
                if (err.codigo === "EMAIL_EN_USO") {
                    // No se confirma de quién es la cuenta: se ofrecen los caminos posibles.
                    avisar(aviso, "error", "No se pudo crear la cuenta con ese email. Si ya tienes cuenta, inicia sesión o recupera tu contraseña.",
                           [{ texto: "Iniciar sesión", alHacer: () => { $("#entrarEmail").value = email.value; mostrar("Entrar"); } },
                            { texto: "Recuperar contraseña", alHacer: () => { $("#olvidoEmail").value = email.value; mostrar("Olvido"); } }]);
                } else {
                    avisarError(aviso, err);
                }
            }
        });
    }

    async function olvide(e) {
        e.preventDefault();
        const form = e.currentTarget;
        const email = $("#olvidoEmail");
        if (!F.validar([[email, F.reglas.email]])) return;
        await F.enviando(form, async () => {
            try {
                const r = await pedir("/api/v2/auth/recuperacion", { method: "POST", sinAvisoSesion: true,
                                                                    json: { email: email.value.trim() } });
                avisar(aviso, "exito", r.mensaje);
            } catch (err) {
                avisarError(aviso, err);
            }
        });
    }

    let tokenRecuperacion = "";
    async function restablecer(e) {
        e.preventDefault();
        const form = e.currentTarget;
        const password = $("#restPassword"), confirmar = $("#restConfirmar");
        if (!F.validar([[password, F.reglas.claveNueva], [confirmar, F.reglas.confirmar, password.value]])) return;
        await F.enviando(form, async () => {
            try {
                await pedir("/api/v2/auth/recuperacion/confirmar", { method: "POST", sinAvisoSesion: true,
                                                                   json: { token: tokenRecuperacion, password: password.value } });
                tokenRecuperacion = "";
                password.value = confirmar.value = "";
                $("#panelRestablecer").hidden = true;
                $("#formularios").hidden = false;
                mostrar("Entrar");
                avisar(aviso, "exito", "Contraseña cambiada. Inicia sesión con la nueva; las demás sesiones se cerraron.");
            } catch (err) {
                password.value = confirmar.value = "";
                if (err.codigo === "TOKEN_INVALIDO") {
                    avisar(aviso, "error", err.mensaje, [{ texto: "Pedir otro enlace", alHacer: () => {
                        $("#panelRestablecer").hidden = true; $("#formularios").hidden = false; mostrar("Olvido"); } }]);
                } else {
                    avisarError(aviso, err);
                }
            }
        });
    }

    // ---------------------------------------------------------------- inicio
    function revisarFragmento() {
        const fragmento = new URLSearchParams(location.hash.slice(1));
        if (!fragmento.get("recuperar")) return false;
        tokenRecuperacion = fragmento.get("recuperar");
        history.replaceState(null, "", location.pathname + location.search);  // el token no se queda en la barra
        $("#formularios").hidden = true;
        $("#yaConectado").hidden = true;
        $("#panelRestablecer").hidden = false;
        $("#tituloCuenta").textContent = "Recupera tu cuenta";
        avisar(aviso, "info", "");
        cabecera("cuenta");
        $("#restPassword").focus();
        return true;
    }

    async function iniciar() {
        F.botonesVerPassword();
        $("#formEntrar").addEventListener("submit", entrar);
        $("#formRegistro").addEventListener("submit", registrarse);
        $("#formOlvido").addEventListener("submit", olvide);
        $("#formRestablecer").addEventListener("submit", restablecer);
        $("#btSalirCuenta").addEventListener("click", cerrarSesion);

        window.addEventListener("hashchange", revisarFragmento);  // enlace abierto con esta página ya cargada
        if (revisarFragmento()) return;

        const motivo = params.get("motivo");
        if (motivo === "expirada") avisar(aviso, "aviso", "Tu sesión caducó. Inicia sesión de nuevo para continuar donde estabas.");
        else if (motivo === "salida") avisar(aviso, "exito", "Cerraste la sesión en este navegador.");
        else if (params.get("volver")) avisar(aviso, "info", "Inicia sesión para continuar.");
        if (params.get("modo") === "registro") mostrar("Registro", false);

        let usuario = null;
        try { usuario = await cargarSesion(); } catch (err) { avisarError(aviso, err); }
        cabecera("cuenta");
        if (usuario) {
            $("#formularios").hidden = true;
            $("#yaConectado").hidden = false;
            $("#yaTexto").textContent = `Sesión iniciada como ${usuario.nombre} (${usuario.email}).`;
        }
    }
    iniciar();
})();
