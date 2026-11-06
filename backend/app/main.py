import re
import time
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import criar_token, exigir_admin, senha_correta
from app.database import Base, engine, get_db
from app.images import processar
from app.models import Photo
from app.schemas import LoginIn, VisibilidadeIn

app = FastAPI(title="CarpeDiem")

# Permite que o frontend (Vite) converse com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

Base.metadata.create_all(engine)  # cria a tabela se ainda não existir
app.mount("/media", StaticFiles(directory=UPLOAD_DIR), name="media")

TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
TAMANHO_MAXIMO = 15 * 1024 * 1024  # 15 MB


def foto_para_dict(f: Photo) -> dict:
    return {
        "id": f.id,
        "author_name": f.author_name,
        "width": f.width,
        "height": f.height,
        "orientation": f.orientation,
        "url": f"/media/{f.id}.jpg",
        "thumb_url": f"/media/{f.id}_thumb.jpg",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/photos")
async def enviar_foto(
    author_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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

    foto = Photo(
        id=base,
        author_name=nome,
        width=resultado["largura"],
        height=resultado["altura"],
        orientation=resultado["orientacao"],
    )
    db.add(foto)
    db.commit()

    return {
        "id": base,
        "author_name": nome,
        "width": resultado["largura"],
        "height": resultado["altura"],
        "orientation": resultado["orientacao"],
    }


@app.get("/photos")
def listar_fotos(db: Session = Depends(get_db)):
    consulta = (
        select(Photo)
        .where(Photo.deleted.is_(False))
        .order_by(Photo.created_at.desc())
    )
    return [foto_para_dict(f) for f in db.scalars(consulta).all()]


# ---------- Painel da aniversariante ----------


@app.post("/admin/login")
def login(dados: LoginIn):
    if not senha_correta(dados.password):
        time.sleep(1)  # atrapalha quem tenta adivinhar a senha
        raise HTTPException(status_code=401, detail="Senha incorreta.")
    return {"token": criar_token()}


@app.get("/admin/photos", dependencies=[Depends(exigir_admin)])
def listar_todas(db: Session = Depends(get_db)):
    consulta = select(Photo).order_by(Photo.created_at.desc())
    return [
        {**foto_para_dict(f), "deleted": f.deleted}
        for f in db.scalars(consulta).all()
    ]


@app.patch("/admin/photos/{foto_id}", dependencies=[Depends(exigir_admin)])
def alterar_visibilidade(
    foto_id: str, dados: VisibilidadeIn, db: Session = Depends(get_db)
):
    foto = db.get(Photo, foto_id)
    if foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada.")
    foto.deleted = dados.deleted
    db.commit()
    return {"ok": True}


@app.delete("/admin/photos/{foto_id}", dependencies=[Depends(exigir_admin)])
def apagar_foto(foto_id: str, db: Session = Depends(get_db)):
    foto = db.get(Photo, foto_id)
    if foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada.")
    for sufixo in (".jpg", "_thumb.jpg"):
        (UPLOAD_DIR / f"{foto.id}{sufixo}").unlink(missing_ok=True)
    db.delete(foto)
    db.commit()
    return {"ok": True}


@app.get("/admin/download", dependencies=[Depends(exigir_admin)])
def baixar_tudo(db: Session = Depends(get_db)):
    consulta = (
        select(Photo).where(Photo.deleted.is_(False)).order_by(Photo.created_at)
    )
    memoria = BytesIO()
    # JPEG já é comprimido, então ZIP_STORED evita gastar CPU à toa
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_STORED) as pacote:
        for numero, f in enumerate(db.scalars(consulta).all(), start=1):
            caminho = UPLOAD_DIR / f"{f.id}.jpg"
            if caminho.exists():
                autor = re.sub(r"[^\w\-]+", "_", f.author_name)
                pacote.write(caminho, f"{numero:04d}_{autor}.jpg")
    memoria.seek(0)
    return StreamingResponse(
        memoria,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="album-anna-lua.zip"'},
    )