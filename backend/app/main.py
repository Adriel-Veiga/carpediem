import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CarpeDiem")

# Permite que o frontend (Vite, porta 5173) converse com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

TIPOS_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}
TAMANHO_MAXIMO = 15 * 1024 * 1024  # 15 MB


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/photos")
async def enviar_foto(
    author_name: str = Form(...),
    file: UploadFile = File(...),
):
    nome = author_name.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe seu nome.")

    extensao = TIPOS_PERMITIDOS.get(file.content_type)
    if extensao is None:
        raise HTTPException(status_code=400, detail="Envie uma imagem válida.")

    conteudo = await file.read()
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(status_code=413, detail="Foto muito grande.")

    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (UPLOAD_DIR / nome_arquivo).write_bytes(conteudo)

    return {"id": nome_arquivo, "author_name": nome}