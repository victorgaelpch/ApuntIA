// Contraseñas de PRUEBA generadas al ejecutar: nunca se escriben en el código.
// Misma semilla y mismo cálculo que back/motori_magenes/herramientas/claves_prueba.py: la semilla
// (APUNTIA_SEMILLA_PRUEBAS) la heredan los procesos hijos, así que Node y Python coinciden.
const crypto = require("node:crypto");

const SEMILLA = "APUNTIA_SEMILLA_PRUEBAS";
process.env[SEMILLA] ??= crypto.randomBytes(16).toString("hex");

function claveDePrueba(nombre) {
    return "prueba-" + crypto.createHmac("sha256", process.env[SEMILLA]).update(nombre).digest("hex").slice(0, 20);
}

module.exports = { claveDePrueba };
