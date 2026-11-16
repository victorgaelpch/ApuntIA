// Página «Servidor IA» (FRONT-25): estado, conexión, vinculación y diagnóstico.
//
// - Todo pasa por el backend LOCAL (/api/v2/ia/*): el navegador nunca recibe ni guarda el token
//   del equipo, ni la URL en localStorage. Las acciones que cambian algo solo funcionan en el
//   propio equipo donde corre ApuntIA (el backend responde SOLO_EQUIPO_LOCAL si no).
// - Sin sondeos agresivos: el estado se comprueba al abrir la página y al pulsar «Comprobar ahora»;
//   solo mientras hay un código de vinculación pendiente se consulta cada 3 s, hasta que caduca.
// - El estado se muestra con texto (no solo color) en una región aria-live.
(function () {
    "use strict";
    const NS = window.ApuntIA;
    const { h, $, vaciar, pedir, requerirSesion, cabecera, avisar, avisarError, confirmar } = NS.v2;
    const aviso = () => $("#avisoIA");
    const E = { estado: null, sondeo: null, caduca: 0, reloj: null, local: true };

    const TEXTOS = {
        cargando: "Comprobando…",
        local: "Sin servidor IA: modo local",
        sin_vincular: "Servidor configurado, este equipo aún no está vinculado",
        vinculado: "Vinculado (pulsa «Comprobar ahora» para ver si responde)",
        conectado: "Conectado y listo",
        no_listo: "Conectado, pero el modelo o la GPU no están listos",
        sin_conexion: "Sin conexión con el servidor IA: se usa el modo local",
        no_autorizado: "El servidor no reconoce este equipo: vuelve a vincularlo",
        solo_local: "Solo se puede consultar en el equipo donde corre ApuntIA",
    };

    function indicador(estado, detalle = "") {
        const p = $("#estadoIA");
        p.dataset.estado = estado;
        $("#estadoIATexto").textContent = TEXTOS[estado] || estado;
        $("#estadoIADetalle").textContent = detalle;
    }

    function pintarEstado(e) {
        E.estado = e;
        $("#urlIAActual").textContent = e.url || "ninguna (modo local)";
        const modo = e.configuracion || "auto";
        for (const r of document.querySelectorAll("input[name=modoIA]")) r.checked = r.value === modo;
        $("#formUrlIA").hidden = modo !== "manual";
        if (modo === "manual" && e.url) $("#inpUrlIA").value = e.url;
        $("#btVincularIA").hidden = !e.url || e.vinculado;
        $("#btDesvincularIA").hidden = !e.vinculado;
        if (!e.url) indicador("local", "Puedes seguir editando, consultar el historial y generar PDFs.");
        else if (!e.vinculado) indicador("sin_vincular", "Pide un código abajo y que el administrador lo apruebe.");
        else if (e.circuito_abierto) indicador("sin_conexion", "Varios intentos fallaron hace poco; se reintentará en unos segundos.");
        else indicador("vinculado", e.proteccion_credencial === "dpapi" ? "Credencial guardada cifrada en este equipo." : "");
        if (e.vinculacion_en_curso && e.vinculacion_en_curso.codigo && !E.sondeo) mostrarCodigo(e.vinculacion_en_curso);
    }

    async function cargar() {
        try {
            pintarEstado(await pedir("/api/v2/ia/estado"));
        } catch (err) {
            avisarError(aviso(), err);
        }
    }

    // ---------------------------------------------------------------- comprobar / diagnosticar
    const NOMBRES = { configuracion: "Dirección configurada", dns: "Nombre del servidor (DNS)",
                      salud_tls_y_version: "Conexión segura y versión", credencial: "Autorización de este equipo",
                      modelo_y_gpu: "Modelo y GPU" };

    async function diagnosticar(mostrarLista) {
        const lista = $("#listaDiagnosticoIA");
        if (mostrarLista) vaciar(lista).append(h("li", { text: "Comprobando…" }));
        indicador("cargando");
        try {
            const d = await pedir("/api/v2/ia/diagnostico", { timeoutMs: 60000 });
            pintarEstado(d.estado);
            const fallo = d.pasos.find((p) => !p.ok);
            if (!d.estado.url) indicador("local");
            else if (d.ok) indicador("conectado");
            else if (fallo && ["AI_AUTH", "AI_REVOCADO", "AI_NO_VINCULADO"].includes(fallo.codigo)) indicador("no_autorizado", fallo.solucion);
            else if (fallo && fallo.paso === "modelo_y_gpu") indicador("no_listo", String(fallo.detalle || ""));
            else if (fallo) indicador("sin_conexion", fallo.solucion || "");
            if (mostrarLista) {
                vaciar(lista);
                for (const p of d.pasos) {
                    lista.append(h("li", { class: p.ok ? "diag-ok" : "diag-error" },
                        h("strong", { text: `${p.ok ? "✓ Correcto" : "✗ Falla"}: ${NOMBRES[p.paso] || p.paso}` }),
                        h("span", { text: ` — ${p.ok ? (Array.isArray(p.detalle) ? p.detalle.join(", ") : p.detalle) : p.detalle}` }),
                        !p.ok && p.solucion ? h("p", { class: "ayuda", text: `Qué hacer: ${p.solucion}` }) : null));
                }
            }
        } catch (err) {
            if (err.codigo === "SOLO_EQUIPO_LOCAL") { E.local = false; indicador("solo_local"); bloquearAcciones(); vaciar(lista); return; }
            avisarError(aviso(), err);
            if (mostrarLista) vaciar(lista);
            if (E.estado) pintarEstado(E.estado);
        }
    }

    function bloquearAcciones() {
        for (const id of ["#btVincularIA", "#btDesvincularIA", "#btDiagnosticoIA", "#btComprobarIA"]) $(id).disabled = true;
        for (const r of document.querySelectorAll("input[name=modoIA]")) r.disabled = true;
        avisar(aviso(), "info", "Estás usando ApuntIA desde otro dispositivo de la red: la conexión con el servidor IA solo se configura en el equipo donde está instalado.");
    }

    // ---------------------------------------------------------------- modo y URL
    async function guardarModo(modo, url) {
        try {
            pintarEstado(await pedir("/api/v2/ia/configuracion", { method: "PUT", json: { modo, url } }));
            avisar(aviso(), "exito", modo === "local" ? "Modo local: no se usará el servidor IA."
                : modo === "manual" ? "Dirección guardada. Si es un servidor nuevo, vincula este equipo." : "Se usa la dirección configurada al instalar.");
            return true;
        } catch (err) {
            if (err.codigo === "SOLO_EQUIPO_LOCAL") { bloquearAcciones(); return false; }
            if (err.codigo === "AI_URL_INVALIDA") {
                $("#inpUrlIAError").textContent = NS.v2.textoDeError(err);
                $("#inpUrlIA").setAttribute("aria-invalid", "true");
                $("#inpUrlIA").focus();
            } else avisarError(aviso(), err);
            return false;
        }
    }

    // ---------------------------------------------------------------- vinculación
    function mostrarCodigo(v) {
        $("#cajaCodigoIA").hidden = false;
        $("#codigoIA").textContent = v.codigo;
        E.caduca = v.expira ? v.expira * 1000 : Date.now() + (v.expira_en_s || 600) * 1000;
        clearInterval(E.reloj);
        const pintarReloj = () => {
            const s = Math.max(0, Math.round((E.caduca - Date.now()) / 1000));
            $("#codigoIACaduca").textContent = `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`;
        };
        pintarReloj();
        E.reloj = setInterval(pintarReloj, 1000);
        $("#estadoVinculoIA").textContent = "Esperando la aprobación del administrador…";
        sondear();
    }

    function terminarVinculo(texto) {
        clearTimeout(E.sondeo);
        clearInterval(E.reloj);
        E.sondeo = null;
        $("#cajaCodigoIA").hidden = true;
        $("#estadoVinculoIA").textContent = texto;
    }

    function sondear() {
        clearTimeout(E.sondeo);
        E.sondeo = setTimeout(async () => {
            if (Date.now() > E.caduca) { terminarVinculo("El código caducó. Pide otro."); return; }
            try {
                const r = await pedir("/api/v2/ia/vinculacion");
                if (r.estado === "vinculado") {
                    terminarVinculo("¡Equipo vinculado! A partir de ahora la conexión es automática.");
                    await cargar();
                    diagnosticar(false);
                    return;
                }
                if (["rechazada", "expirada", "anulada"].includes(r.estado)) {
                    terminarVinculo(r.estado === "rechazada" ? "El administrador rechazó la solicitud." : "El código ya no es válido. Pide otro.");
                    return;
                }
                sondear();
            } catch (err) {
                if (err.codigo === "AI_VINCULACION") { terminarVinculo(NS.v2.textoDeError(err)); return; }
                $("#estadoVinculoIA").textContent = "No se pudo consultar ahora; se reintentará…";
                sondear();
            }
        }, 3000);
    }

    async function pedirCodigo() {
        $("#btVincularIA").disabled = true;
        try {
            const v = await pedir("/api/v2/ia/vinculacion", { method: "POST", timeoutMs: 30000 });
            avisar(aviso(), "info", "");
            mostrarCodigo(v);
        } catch (err) {
            if (err.codigo === "SOLO_EQUIPO_LOCAL") bloquearAcciones();
            else avisarError(aviso(), err);
        } finally {
            $("#btVincularIA").disabled = false;
        }
    }

    async function desvincular() {
        const ok = await confirmar({ titulo: "Desvincular este equipo", peligro: true, aceptar: "Desvincular",
            texto: "Se borrará la credencial de este equipo. Para volver a usar el servidor IA habrá que vincularlo otra vez. "
                 + "Si el equipo se perdió, pide también al administrador que lo revoque en el servidor." });
        if (!ok) return;
        try {
            const r = await pedir("/api/v2/ia/vinculacion", { method: "DELETE" });
            pintarEstado(r);
            avisar(aviso(), "exito", "Equipo desvinculado.");
        } catch (err) { avisarError(aviso(), err); }
    }

    // ---------------------------------------------------------------- inicio
    async function iniciar() {
        await requerirSesion();
        cabecera("perfil");
        $("#btComprobarIA").addEventListener("click", () => diagnosticar(false));
        $("#btDiagnosticoIA").addEventListener("click", () => diagnosticar(true));
        $("#btVincularIA").addEventListener("click", pedirCodigo);
        $("#btDesvincularIA").addEventListener("click", desvincular);
        for (const r of document.querySelectorAll("input[name=modoIA]")) {
            r.addEventListener("change", () => {
                $("#formUrlIA").hidden = r.value !== "manual";
                if (r.value === "manual") $("#inpUrlIA").focus();
                else guardarModo(r.value, null);
            });
        }
        $("#inpUrlIA").addEventListener("input", () => { $("#inpUrlIAError").textContent = ""; $("#inpUrlIA").removeAttribute("aria-invalid"); });
        $("#formUrlIA").addEventListener("submit", (e) => { e.preventDefault(); guardarModo("manual", $("#inpUrlIA").value.trim()); });
        window.addEventListener("pagehide", () => { clearTimeout(E.sondeo); clearInterval(E.reloj); });
        await cargar();
        if (E.estado && E.estado.puede_configurar === false) bloquearAcciones();       // otro dispositivo de la red
        else if (E.estado && E.estado.vinculado) diagnosticar(false);   // una comprobación al abrir, no sondeo continuo
    }

    document.addEventListener("DOMContentLoaded", iniciar);
})();
