// Arranque del editor (FRONT-13): se carga el último, cuando todas las partes
// del editor ya registraron sus pestañas y tipos de bloque.
(function (global) {
    "use strict";
    const NS = global.ApuntIA;
    const { $, requerirSesion, cabecera, avisar, avisarError } = NS.v2;
    const ed = NS.editor;

    async function iniciar() {
        await requerirSesion();
        cabecera("apuntes");
        ed.E.id = new URLSearchParams(location.search).get("id");
        if (!ed.E.id) { avisar($("#avisoEditor"), "error", "Falta el apunte que quieres abrir.", [{ texto: "Ir a Mis apuntes", alHacer: () => location.assign("/front/apuntes.html") }]); return; }
        // Si la sesión caduca mientras se edita no se sale de la página: se perderían los cambios.
        global.addEventListener("apuntia:sesion-expirada", (e) => { if (ed.hayCambios()) e.preventDefault(); });
        global.addEventListener("beforeunload", (e) => { if (ed.hayCambios()) { e.preventDefault(); e.returnValue = ""; } });
        global.addEventListener("online", () => ed.actualizarEstadoGuardado());
        global.addEventListener("offline", () => ed.actualizarEstadoGuardado());
        document.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); ed.guardar(); }
        });
        $("#btGuardar").addEventListener("click", () => ed.guardar());
        let apunte;
        try {
            apunte = await ed.cargar();
        } catch (err) {
            $("#estadoGuardado").textContent = "";
            if (err.status === 404) {
                avisar($("#avisoEditor"), "error", "Este apunte no existe o no es tuyo.", [{ texto: "Ir a Mis apuntes", alHacer: () => location.assign("/front/apuntes.html") }]);
            } else {
                avisarError($("#avisoEditor"), err, [{ texto: "Reintentar", alHacer: () => location.reload() }]);
            }
            return;
        }
        ed.pintarTodo();
        ed.E.alCargar.forEach((fn) => fn(apunte));
        const t = apunte.ultimo_trabajo;
        if (t && t.tipo === "analisis" && ["pendiente", "procesando"].includes(t.estado)) ed.seguirAnalisis(t);
        else if (t && t.tipo === "analisis" && ["fallido", "cancelado", "parcial"].includes(t.estado)) ed.informarAnalisis(t);
    }
    iniciar();
})(window);
