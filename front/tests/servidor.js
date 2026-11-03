// Servidor estático mínimo para las pruebas (sirve la raíz del repositorio).
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const RAIZ = path.resolve(__dirname, "..", "..");
const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml" };

function iniciar(puerto = 0) {
    const servidor = http.createServer((req, res) => {
        const ruta = path.normalize(decodeURIComponent(new URL(req.url, "http://x").pathname));
        const archivo = path.join(RAIZ, ruta === "/" ? "index.html" : ruta);
        if (!archivo.startsWith(RAIZ) || !fs.existsSync(archivo) || fs.statSync(archivo).isDirectory()) {
            res.writeHead(404).end("no encontrado");
            return;
        }
        res.writeHead(200, { "Content-Type": TIPOS[path.extname(archivo)] || "application/octet-stream" });
        fs.createReadStream(archivo).pipe(res);
    });
    return new Promise((resolve) => servidor.listen(puerto, "127.0.0.1", () => resolve({
        url: `http://localhost:${servidor.address().port}`,
        cerrar: () => new Promise((r) => servidor.close(r)),
    })));
}

module.exports = { iniciar };
