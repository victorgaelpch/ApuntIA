"""Servidor de inferencia de IA de ApuntIA (BACK-35).

Servicio independiente que corre en la PC con GPU: recibe UNA imagen, la valida, mide su
calidad con el OpenCV del backend (sin copiarlo) y pide a un modelo visual local de Ollama
(Qwen3-VL) una transcripción estructurada. No guarda imágenes, no tiene usuarios ni base de
datos: eso sigue en el ApuntIA del cliente. Guía: fullstack/docs/servidor-ia.md.
"""

API_VERSION = "1.0"          # contrato HTTP de este servicio (fullstack/docs/servidor-ia.md §3)
PIPELINE_VERSION = "1.0.0"   # validación + calidad + una inferencia VLM por imagen
