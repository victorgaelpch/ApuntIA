// Servidor IA FALSO para pruebas de interfaz (FRONT-26, BACK-38): habla el MISMO contrato que
// ia_servidor (fullstack/docs/servidor-ia.md §3 y trabajos-remotos.md) sin GPU ni modelo.
// Aprueba cualquier vinculación al instante y devuelve bloques fijos: una fórmula con una duda
// [?], un texto y una región sin leer. Solo para pruebas: nunca escucha fuera de 127.0.0.1.
const http = require("node:http");
const crypto = require("node:crypto");

const BLOQUES = [
    { id: "p1b1", tipo: "formula", bbox: [10, 10, 200, 60], estado: "incierto", texto: "\\frac{a}{b} = c[?]",
      latex: "\\frac{a}{b} = c", descripcion: null, dudas: ["1 fragmento(s) que el modelo marcó como no legibles ([?])"],
      procedencia: { motor: "ollama", version: "modelo-falso", reconocimiento: "documento/opencv" } },
    { id: "p1b2", tipo: "texto", bbox: [10, 80, 300, 120], estado: "reconocido", texto: "Derivadas parciales",
      latex: null, descripcion: null, dudas: [], procedencia: { motor: "ollama", version: "modelo-falso", reconocimiento: "documento/opencv" } },
    { id: "p1b3", tipo: "manuscrito", bbox: [10, 130, 120, 170], estado: "no_reconocido", texto: "", latex: null,
      descripcion: null, dudas: ["el modelo no dio una respuesta válida para esta región: revísala en el recorte"],
      procedencia: { motor: "ollama", version: "modelo-falso", reconocimiento: "documento/opencv" } },
];

function iniciarIAFalsa() {
    const trabajos = new Map();
    const token = crypto.randomBytes(24).toString("hex");
    const servidor = http.createServer((req, res) => {
        const json = (estado, cuerpo) => { res.writeHead(estado, { "Content-Type": "application/json" }); res.end(JSON.stringify(cuerpo)); };
        let cuerpo = [];
        req.on("data", (c) => cuerpo.push(c));
        req.on("end", () => {
            const url = new URL(req.url, "http://x");
            if (url.pathname === "/salud") return json(200, { estado: "ok", servicio: "apuntia-ia", api_version: "1.0" });
            if (req.method === "POST" && url.pathname === "/api/v1/vinculacion/solicitudes") {
                return json(201, { solicitud_id: "s1", secreto: crypto.randomBytes(16).toString("hex"), codigo: "PRUE-BA01", expira_en_s: 600 });
            }
            if (req.method === "POST" && url.pathname === "/api/v1/vinculacion/solicitudes/s1/estado") {
                return json(200, { estado: "aprobada", token, dispositivo_id: "laptop-falsa" });
            }
            if (req.headers.authorization !== `Bearer ${token}`) return json(401, { error: { codigo: "NO_AUTENTICADO", mensaje: "x", reintentable: false } });
            if (url.pathname === "/api/v1/yo") return json(200, { dispositivo_id: "laptop-falsa", nombre: "Laptop", api_version: "1.0" });
            if (url.pathname === "/listo") return json(200, { listo: true, api_version: "1.0", componentes: {} });
            if (req.method === "POST" && url.pathname === "/api/v1/trabajos") {
                const id = crypto.randomBytes(8).toString("hex");
                trabajos.set(id, 0);
                return json(202, { trabajo_id: id, tarea: "documento", estado: "en_cola", progreso: 0, posicion: 1 });
            }
            const m = url.pathname.match(/^\/api\/v1\/trabajos\/(\w+)$/);
            if (m && trabajos.has(m[1])) {
                const consultas = trabajos.get(m[1]) + 1;
                trabajos.set(m[1], consultas);
                if (consultas < 2) return json(200, { trabajo_id: m[1], estado: "procesando", progreso: 50 });
                return json(200, { trabajo_id: m[1], estado: "completado", progreso: 100, resultado: {
                    api_version: "1.0", modelo: { nombre: "modelo-falso", respaldo_usado: false },
                    resultado: { estado: "propuesta", revision_requerida: true, bloques: BLOQUES } } });
            }
            return json(404, { error: { codigo: "RUTA_NO_ENCONTRADA", mensaje: "x", reintentable: false } });
        });
    });
    return new Promise((resolver) => servidor.listen(0, "127.0.0.1", () => resolver({
        url: `http://127.0.0.1:${servidor.address().port}`, cerrar: () => new Promise((r) => servidor.close(r)) })));
}

module.exports = { iniciarIAFalsa, BLOQUES };
