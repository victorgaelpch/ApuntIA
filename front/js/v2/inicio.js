// Navegación de la página de inicio (FRONT-11).
//
// La página funciona igual abierta con doble clic (file://) o servida por el
// backend en /inicio. Los enlaces a las páginas con cuenta apuntan al servidor
// de la API, y los privados (Crear apuntes, Mis apuntes, Perfil) solo se
// muestran si hay sesión, que únicamente se puede saber desde el mismo origen.
(function (global) {
    "use strict";
    const api = global.ApuntIA.api;
    const mismoOrigen = api.servidaPorBackend();
    const base = mismoOrigen ? "" : api.urlBase();
    const nav = document.getElementById("navPrincipal");

    function enlace(texto, ruta, clase) {
        const a = document.createElement("a");
        a.href = base + ruta;
        a.textContent = texto;
        if (clase) a.className = clase;
        return a;
    }

    document.querySelectorAll("[data-enlace-app]").forEach((a) => { a.href = base + a.dataset.enlaceApp; });

    async function sesion() {
        if (!mismoOrigen) return null;
        try {
            const r = await fetch("/api/v2/auth/estado", { credentials: "same-origin", cache: "no-store" });
            return r.ok ? (await r.json()).usuario : null;
        } catch (_) {
            return null;
        }
    }

    sesion().then((usuario) => {
        if (usuario) {
            nav.append(enlace("Crear apuntes", "/front/nuevo.html"), enlace("Mis apuntes", "/front/apuntes.html"),
                       enlace("Perfil", "/front/perfil.html"));
        } else {
            nav.append(enlace("Entrar", "/front/cuenta.html", "btn sm primary"));
        }
        nav.dataset.sesion = usuario ? "activa" : "sin-sesion";
    });
})(window);
