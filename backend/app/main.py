import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.images import processar
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

TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
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

    if file.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(status_code=400, detail="Envie uma imagem válida.")

    conteudo = await file.read()
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(status_code=413, detail="Foto muito grande.")

    try:
        resultado = await run_in_threadpool(processar, conteudo)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))

    base = uuid.uuid4().hex
    (UPLOAD_DIR / f"{base}.jpg").write_bytes(resultado["principal"])
    (UPLOAD_DIR / f"{base}_thumb.jpg").write_bytes(resultado["miniatura"])

    return {
        "id": base,
        "author_name": nome,
        "width": resultado["largura"],
        "height": resultado["altura"],
        "orientation": resultado["orientacao"],
    }