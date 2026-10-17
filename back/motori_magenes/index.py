import io
import cv2
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import StreamingResponse,FileResponse
from PIL import Image, ImageDraw


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def holamundo():
    return {"message": "Hola Mundo"}
RUTA= "/home/yane/imagenes"
@app.post("/analisis")
def motori_magenes(file: UploadFile = File(...)):
    print(f"Nombre del archivo: {file.filename}")   
    nombre_archivo = file.filename
    ruta_archivo = f"{RUTA}/{nombre_archivo}"
    with open(ruta_archivo, "wb") as f:
        f.write(file.file.read())

    imagen = Image.open(ruta_archivo)
    imgGris = imagen.convert("L")
    imgGris.save(ruta_archivo)
    cv2.imwrite(ruta_archivo, cv2.imread(ruta_archivo))
    return FileResponse(ruta_archivo, media_type="image/png", filename=nombre_archivo)
@app.post("/imagen-memoria")
def obtener_imagen_memoria():
    # 1. Creamos una imagen de ejemplo en memoria con Pillow
    imagen = Image.new("RGB", (300, 100), color="blue")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.text((10, 40), "Hola FastAPI", fill="white")
    
    # 2. Guardamos la imagen en un buffer de bytes (BytesIO)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0) # Volvemos al inicio del buffer
    
    # 3. Retornamos el flujo de datos
    return StreamingResponse(buffer, media_type="image/png")