// Configuración del frontend de ApuntIA.
//
// URL de la API, por orden de prioridad:
//   1. Parámetro ?api=  en la URL de la página  (p. ej. index.html?api=http://192.168.1.20:8000)
//   2. apiUrl de este archivo                   (déjalo en null para desarrollo)
//   3. Mismo host que la página, puerto apiPuerto (http://localhost:8000 al abrir el archivo
//      directamente o desde localhost; http://<ip>:8000 al abrirla desde el celular en la red)
//
// Respuestas simuladas (sin backend): añade ?mock=ok a la URL. Ver front/js/api-mock.js.
window.ApuntIA = window.ApuntIA || {};
window.ApuntIA.config = {
    apiUrl: null,
    apiPuerto: 8000,
    // Tiempo máximo de espera de una petición de procesamiento.
    timeoutMs: 60000,
    // Límites para avisar antes de enviar. El backend es la fuente de verdad (GET /salud).
    formatos: ["image/jpeg", "image/png", "image/webp"],
    maxMb: 10,
};
