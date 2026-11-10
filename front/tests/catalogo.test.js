// Catálogo único de mensajes y reglas de seguridad de la interfaz (FRONT-20).
// Pruebas sin navegador: se carga mensajes.js en un contexto aislado.
//   node --test front/tests/catalogo.test.js
const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const RAIZ = path.resolve(__dirname, "..", "..");
const FRONT = path.join(RAIZ, "front");
const BACKEND = path.join(RAIZ, "back", "motori_magenes", "app");

function cargarCatalogo(config = {}) {
    const ventana = { ApuntIA: { config }, navigator: { onLine: true } };
    vm.runInNewContext(fs.readFileSync(path.join(FRONT, "js", "mensajes.js"), "utf8"), { window: ventana });
    return ventana.ApuntIA.mensajes;
}

function archivos(carpeta, extension) {
    return fs.readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
        const ruta = path.join(carpeta, e.name);
        if (e.isDirectory()) return e.name === "__pycache__" ? [] : archivos(ruta, extension);
        return ruta.endsWith(extension) ? [ruta] : [];
    });
}

// Todos los códigos que el backend puede devolver (ApiError, errores de trabajos, OCR y PDF).
function codigosBackend() {
    const codigos = new Set();
    const patron = /(?:ApiError\(\s*\d+,\s*|ErrorTrabajo\(|ErrorOCR\(|ErrorPDF\(|codigo=)"([A-Z][A-Z_]+)"/g;
    for (const archivo of archivos(BACKEND, ".py")) {
        for (const m of fs.readFileSync(archivo, "utf8").matchAll(patron)) codigos.add(m[1]);
    }
    // Códigos que salen de tablas o de los manejadores genéricos
    ["PAGINAS_INVALIDAS", "CARGA_DEMASIADO_GRANDE", "DATOS_INVALIDOS", "PARAMETRO_INVALIDO", "RUTA_NO_ENCONTRADA",
     "METODO_NO_PERMITIDO", "ERROR_INTERNO"].forEach((c) => codigos.add(c));
    return codigos;
}

describe("FRONT-20 catálogo de mensajes", () => {
    const m = cargarCatalogo({ maxMb: 10, formatos: ["image/jpeg", "image/png", "image/webp"] });

    test("todos los códigos del backend (v1 y v2) tienen mensaje", () => {
        const codigos = codigosBackend();
        assert.ok(codigos.size >= 40, `solo se encontraron ${codigos.size} códigos`);
        const faltan = [...codigos].filter((c) => !m.CATALOGO[c]);
        assert.deepEqual(faltan, []);
    });

    test("cada entrada tiene un texto en español no vacío, acciones y un tipo válido", () => {
        for (const [codigo, entrada] of Object.entries(m.CATALOGO)) {
            const r = m.paraUsuario(codigo, {});
            assert.ok(r.texto && r.texto.length > 10, codigo);
            assert.ok(!/undefined|null|\$\{/.test(r.texto), `${codigo}: ${r.texto}`);
            assert.ok(Array.isArray(entrada.acciones), codigo);
            assert.ok(["error", "aviso", "info", "listo"].includes(r.tipo), `${codigo}: ${r.tipo}`);
        }
    });

    test("código desconocido: genérico, o error del servidor si es 5xx", () => {
        assert.equal(m.paraUsuario("CODIGO_INVENTADO", { status: 400 }).texto, m.GENERICO.texto);
        assert.equal(m.paraUsuario("CODIGO_INVENTADO", { status: 503 }).texto, m.CATALOGO.ERROR_INTERNO.texto);
        assert.equal(m.tipoDe("CODIGO_INVENTADO"), "error");
        assert.equal(m.tipoDe("DEMASIADAS_PETICIONES"), "aviso");
    });

    test("el detalle técnico solo lleva código, HTTP y referencia (sin trazas)", () => {
        const r = m.paraUsuario("ERROR_INTERNO", { status: 500, errorId: "abc123", causa: new Error("/home/x Traceback") });
        assert.equal(r.detalle, "Código: ERROR_INTERNO · HTTP 500 · Referencia: abc123");
    });

    test("los textos usan los límites configurados", () => {
        const otro = cargarCatalogo({ maxMb: 3, formatos: ["image/png"] });
        assert.match(otro.paraUsuario("ARCHIVO_DEMASIADO_GRANDE").texto, /más de 3 MB/);
        assert.match(otro.paraUsuario("TIPO_NO_PERMITIDO").texto, /PNG/);
    });
});

describe("FRONT-20 seguridad de la interfaz", () => {
    test("las páginas con cuenta no insertan HTML: nada de innerHTML, outerHTML, insertAdjacentHTML ni document.write", () => {
        const peligrosos = /\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML|document\.write\(|new Function\(|\beval\(/;
        const encontrados = [...archivos(path.join(FRONT, "js", "v2"), ".js"), path.join(FRONT, "js", "app.js"),
                             path.join(FRONT, "js", "api.js"), path.join(FRONT, "js", "camara.js")]
            .flatMap((a) => fs.readFileSync(a, "utf8").split("\n").map((l, i) => [a, i + 1, l]))
            .filter(([, , l]) => peligrosos.test(l) && !l.trim().startsWith("//"))
            .map(([a, n, l]) => `${path.relative(RAIZ, a)}:${n}: ${l.trim()}`);
        assert.deepEqual(encontrados, []);
    });

    test("las páginas servidas cumplen la CSP: sin scripts ni estilos en línea", () => {
        const paginas = [path.join(RAIZ, "index.html"), ...fs.readdirSync(FRONT).filter((f) => f.endsWith(".html") && f !== "maqueta.html").map((f) => path.join(FRONT, f))];
        assert.ok(paginas.length >= 7);
        for (const p of paginas) {
            const html = fs.readFileSync(p, "utf8");
            assert.ok(!/<script(?![^>]*\bsrc=)[^>]*>/i.test(html), `${path.basename(p)}: script en línea`);
            assert.ok(!/\sstyle="/i.test(html), `${path.basename(p)}: atributo style`);
            assert.ok(!/\son[a-z]+="/i.test(html), `${path.basename(p)}: manejador en línea`);
            assert.ok(!/<script[^>]+src="https?:/i.test(html), `${path.basename(p)}: script externo`);
        }
    });

    test("los enlaces externos que abre la interfaz llevan rel=noopener", () => {
        const fuentes = archivos(path.join(FRONT, "js", "v2"), ".js").map((a) => fs.readFileSync(a, "utf8")).join("\n");
        for (const m of fuentes.matchAll(/target:\s*"_blank"[^}]*/g)) assert.match(m[0], /rel:\s*"noopener/, m[0]);
    });

    test("no se guardan secretos en el almacenamiento del navegador", () => {
        const fuentes = archivos(path.join(FRONT, "js"), ".js").filter((a) => !a.endsWith("index.js"))
            .map((a) => [a, fs.readFileSync(a, "utf8")]);
        for (const [a, texto] of fuentes) {
            for (const m of texto.matchAll(/(localStorage|sessionStorage)\.setItem\(([^)]*)\)/g)) {
                assert.ok(!/csrf|password|token|sesion\b/i.test(m[2]), `${path.relative(RAIZ, a)}: ${m[0]}`);
            }
        }
    });
});
