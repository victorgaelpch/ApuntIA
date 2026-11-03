// Controlador de la pantalla principal de ApuntIA: selección de imagen, vista
// previa y presentación del resultado. La comunicación con FastAPI está en
// api.js (FRONT-05); este archivo no conoce URLs ni el formato de la petición.

const api = window.ApuntIA.api;

const btEnviar = document.getElementById("btEnviar");
const inputs = [document.getElementById("inpImagen"), document.getElementById("inpCamara")];
const imgPreview = document.getElementById("imagenEnviada");
const imgResult = document.getElementById("imagenResultado");
const estado = document.getElementById("estado");
const zonaResultados = document.getElementById("resultados");

let archivoSeleccionado = null;

function mostrarEstado(tipo, mensaje) {
    estado.dataset.estado = tipo;
    estado.textContent = mensaje;
}

function seleccionarArchivo(file) {
    if (!file) return;
    archivoSeleccionado = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imgPreview.src = e.target.result;
        imgPreview.hidden = false;
    };
    reader.readAsDataURL(file);

    imgResult.hidden = true;
    imgResult.removeAttribute("src");
    btEnviar.disabled = false;
    mostrarEstado("listo", `Imagen lista: ${file.name}. Pulsa «Procesar imagen».`);
    zonaResultados.scrollIntoView({ block: "start" });
}

inputs.forEach((input) => {
    input.addEventListener("change", () => {
        seleccionarArchivo(input.files[0]);
        input.value = ""; // permite volver a elegir el mismo archivo
    });
});

async function enviarImagen() {
    if (!archivoSeleccionado) return;
    btEnviar.disabled = true;
    zonaResultados.setAttribute("aria-busy", "true");
    mostrarEstado("cargando", "Procesando imagen...");

    try {
        const resultado = await api.procesarImagen(archivoSeleccionado);
        imgResult.src = URL.createObjectURL(resultado.blob);
        imgResult.hidden = false;
        mostrarEstado("hecho", "Listo. Compara la imagen original con la procesada.");
    } catch (error) {
        console.error(error);
        const texto = error.tipo === "red"
            ? `No se pudo conectar con el servidor (${api.urlBase()}). Verifica que esté activo e inténtalo de nuevo.`
            : error.mensaje || "No se pudo procesar la imagen. Inténtalo de nuevo.";
        mostrarEstado("error", texto);
    } finally {
        zonaResultados.removeAttribute("aria-busy");
        btEnviar.disabled = false;
    }
}

btEnviar.addEventListener("click", enviarImagen);

// Marca en la navegación la sección visible.
const enlaces = [...document.querySelectorAll(".site-nav a")];
const secciones = enlaces.map((a) => document.querySelector(a.getAttribute("href")));
if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entradas) => {
        entradas.forEach((entrada) => {
            if (!entrada.isIntersecting) return;
            enlaces.forEach((a) => {
                if (a.getAttribute("href") === `#${entrada.target.id}`) a.setAttribute("aria-current", "page");
                else a.removeAttribute("aria-current");
            });
        });
    }, { rootMargin: "-40% 0px -55% 0px" });
    secciones.forEach((s) => s && observer.observe(s));
}
