# Referencias (FULL-32)

Fuentes de los algoritmos, modelos y herramientas que usa ApuntIA 3.0. Revisadas el 14/11/2026.
«Usado» = está en el código; «Consultado» = documentación de diseño o despliegue; «No usado» = se
evaluó o se pidió, pero no está integrado ([algoritmos.md §5](algoritmos.md)).

## Algoritmos de visión por computador (usados)

| Referencia | Para |
|------------|------|
| Canny, J. (1986). *A Computational Approach to Edge Detection*. IEEE TPAMI 8(6), 679–698. doi:10.1109/TPAMI.1986.4767851 | bordes del pizarrón/hoja |
| Otsu, N. (1979). *A Threshold Selection Method from Gray-Level Histograms*. IEEE Trans. SMC 9(1), 62–66. doi:10.1109/TSMC.1979.4310076 | umbral global |
| Zuiderveld, K. (1994). *Contrast Limited Adaptive Histogram Equalization*. En *Graphics Gems IV*, 474–485. Academic Press | CLAHE |
| Suzuki, S. y Abe, K. (1985). *Topological Structural Analysis of Digitized Binary Images by Border Following*. CVGIP 30(1), 32–46 | `findContours` |
| Douglas, D. y Peucker, T. (1973). *Algorithms for the Reduction of the Number of Points Required to Represent a Digitized Line or its Caricature*. Cartographica 10(2), 112–122 | `approxPolyDP` (cuadrilátero) |
| Tomasi, C. y Manduchi, R. (1998). *Bilateral Filtering for Gray and Color Images*. ICCV 1998, 839–846 | filtro bilateral |
| Pech-Pacheco, J. L. et al. (2000). *Diatom Autofocusing in Brightfield Microscopy: a Comparative Study*. ICPR 2000 | varianza del laplaciano como medida de nitidez |
| Hartley, R. y Zisserman, A. (2004). *Multiple View Geometry in Computer Vision*, 2.ª ed. Cambridge University Press | homografía de 4 puntos |
| Documentación de OpenCV: <https://docs.opencv.org/> (módulos `imgproc`: umbralización, morfología, transformaciones geométricas, componentes conexas) | parámetros y funciones |

## OCR y fórmulas (usados)

| Referencia | Para |
|------------|------|
| Smith, R. (2007). *An Overview of the Tesseract OCR Engine*. ICDAR 2007. doi:10.1109/ICDAR.2007.4376991 | OCR local |
| Tesseract: <https://github.com/tesseract-ocr/tesseract> (Apache-2.0) · instalador Windows: <https://github.com/UB-Mannheim/tesseract/wiki> | instalación, `tessdata` |
| Matplotlib mathtext: <https://matplotlib.org/stable/users/explain/text/mathtext.html> | dibujar y validar LaTeX sin motor TeX |

## Modelos y servidor de inferencia (usados)

| Referencia | Para |
|------------|------|
| Qwen3-VL en Ollama: <https://ollama.com/library/qwen3-vl> · repositorio: <https://github.com/QwenLM/Qwen3-VL> · licencia Apache-2.0 (leída con `ollama show --license`) | VLM del servidor IA |
| API de Ollama: <https://docs.ollama.com/api/introduction> | `/api/chat`, `/api/ps`, `/api/show`, `keep_alive`, `options` |
| FastAPI: <https://fastapi.tiangolo.com/> · Pydantic: <https://docs.pydantic.dev/> | servidores y validación |
| ReportLab: <https://docs.reportlab.com/> | PDF |

## Conexión y seguridad (consultados)

| Referencia | Para |
|------------|------|
| Cloudflare Tunnel: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/> | túnel HTTPS sin abrir puertos |
| Tailscale: <https://tailscale.com/kb/> (Serve) | alternativa por VPN |
| OWASP API Security Top 10: <https://owasp.org/API-Security/> | revisión de la API (IDOR, SSRF, límites) |
| Windows DPAPI (`CryptProtectData`): <https://learn.microsoft.com/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata> | cifrado de la credencial en la laptop (llamada directa con `ctypes`) |
| GitHub Actions: <https://docs.github.com/en/actions> | CI |

## Investigación (usados)

| Referencia | Para |
|------------|------|
| API REST de Wikimedia: <https://www.mediawiki.org/wiki/API:REST_API> · TextExtracts: <https://www.mediawiki.org/wiki/Extension:TextExtracts> | Wikipedia y Wikilibros |
| Licencia del contenido: CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/> | atribución en el PDF |

## No usados (evaluados o pedidos)

| Referencia | Estado |
|------------|--------|
| PaddleOCR / PaddleOCR-VL: <https://github.com/PaddlePaddle/PaddleOCR> | no integrado: sin verificar en Windows/RTX 3060 |
| SymPy: <https://docs.sympy.org/latest/index.html> | no usado en producción: su `parse_expr` evalúa la entrada; la validación de fórmulas es sintáctica |
