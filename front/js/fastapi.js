const btEnviar= document.getElementById("btEnviar");
const inputImagen= document.getElementById("inpImagen");  


inputImagen.addEventListener("change", () => {
    const file = inpImagen.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imgPreview = document.getElementById("imagenEnviada");
            imgPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});




async function enviarImagen() {
    console.log("Enviando imagen...");
    const formData = new FormData();
    formData.append("file", inpImagen.files[0]);
    
    const response = await fetch("http://localhost:8000/analisis", {
        method: "POST",
        body: formData
    });

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const imgResult = document.getElementById("imagenResultado");
    imgResult.src = url;
}



btEnviar.addEventListener("click", async () => {
    enviarImagen();
});     