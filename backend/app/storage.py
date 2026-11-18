import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
CHAVE = os.environ.get("SUPABASE_SECRET_KEY", "")
BUCKET = os.environ.get("SUPABASE_BUCKET", "fotos")


class ErroArmazenamento(Exception):
    pass


def _cabecalhos(extras: dict[str, str] | None = None) -> dict[str, str]:
    cabecalhos = {"apikey": CHAVE, "Authorization": f"Bearer {CHAVE}"}
    if extras:
        cabecalhos.update(extras)
    return cabecalhos


def url_publica(caminho: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{caminho}"


def enviar(caminho: str, conteudo: bytes, tipo: str = "image/jpeg") -> None:
    resposta = httpx.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{caminho}",
        content=conteudo,
        headers=_cabecalhos(
            {
                "Content-Type": tipo,
                "Cache-Control": "max-age=31536000",  # o navegador guarda por 1 ano
                "x-upsert": "false",
            }
        ),
        timeout=30,
    )
    if resposta.status_code >= 300:
        raise ErroArmazenamento(f"enviar {caminho}: {resposta.status_code}")


def apagar(caminhos: list[str]) -> None:
    resposta = httpx.request(
        "DELETE",
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}",
        json={"prefixes": caminhos},
        headers=_cabecalhos(),
        timeout=30,
    )
    if resposta.status_code >= 300:
        raise ErroArmazenamento(f"apagar: {resposta.status_code}")


def baixar(caminho: str) -> bytes | None:
    resposta = httpx.get(url_publica(caminho), timeout=30)
    return resposta.content if resposta.status_code == 200 else None