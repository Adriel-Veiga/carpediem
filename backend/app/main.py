import os
import re
import tempfile
import time
import uuid
import zipfile
from contextlib import suppress

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import storage
from app.auth import criar_token, exigir_admin, senha_correta
from app.database import get_db, preparar_banco
from app.images import processar
from app.models import Photo
from app.schemas import LoginIn, VisibilidadeIn

app = FastAPI(title="CarpeDiem")

# Endereços do site em produção, separados por vírgula (definido no Render)
ORIGENS = ["https://adriel-veiga.github.io"] + [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

preparar_banco()

TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
TAMANHO_MAXIMO = 15 * 1024 * 1024  # 15 MB


def foto_para_dict(f: Photo) -> dict:
    return {
        "id": f.id,
        "author_name": f.author_name,
        "width": f.width,
        "height": f.height,
        "orientation": f.orientation,
        "url": storage.url_publica(f"{f.id}.jpg"),
        "thumb_url": storage.url_publica(f"{f.id}_thumb.jpg"),
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("select 1"))  # também mantém o banco ativo
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
    principal, miniatura = f"{base}.jpg", f"{base}_thumb.jpg"
    try:
        await run_in_threadpool(storage.enviar, principal, resultado["principal"])
        await run_in_threadpool(storage.enviar, miniatura, resultado["miniatura"])
    except storage.ErroArmazenamento:
        with suppress(storage.ErroArmazenamento):
            await run_in_threadpool(storage.apagar, [principal, miniatura])
        raise HTTPException(
            status_code=502, detail="Não foi possível salvar a foto. Tente de novo."
        )

    db.add(
        Photo(
            id=base,
            author_name=nome,
            width=resultado["largura"],
            height=resultado["altura"],
            orientation=resultado["orientacao"],
        )
    )
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
    try:
        storage.apagar([f"{foto.id}.jpg", f"{foto.id}_thumb.jpg"])
    except storage.ErroArmazenamento:
        raise HTTPException(
            status_code=502, detail="Não foi possível apagar os arquivos. Tente de novo."
        )
    db.delete(foto)
    db.commit()
    return {"ok": True}


@app.get("/admin/download", dependencies=[Depends(exigir_admin)])
def baixar_tudo(db: Session = Depends(get_db)):
    consulta = (
        select(Photo).where(Photo.deleted.is_(False)).order_by(Photo.created_at)
    )
    # O .zip é montado em arquivo temporário (e não na memória), porque o
    # plano gratuito do servidor tem pouca RAM.
    arquivo = tempfile.TemporaryFile()
    with zipfile.ZipFile(arquivo, "w", zipfile.ZIP_STORED) as pacote:
        for numero, f in enumerate(db.scalars(consulta).all(), start=1):
            dados = storage.baixar(f"{f.id}.jpg")
            if dados is not None:
                autor = re.sub(r"[^\w\-]+", "_", f.author_name)
                pacote.writestr(f"{numero:04d}_{autor}.jpg", dados)
    arquivo.seek(0)

    def pedacos():
        try:
            while bloco := arquivo.read(1024 * 1024):
                yield bloco
        finally:
            arquivo.close()

    return StreamingResponse(
        pedacos(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="album-anna-lua.zip"'},
    )