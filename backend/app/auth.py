import hashlib
import hmac
import os
import time

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
VALIDADE_SEGUNDOS = 12 * 3600  # a sessão dura 12 horas


def _assinar(texto: str) -> str:
    return hmac.new(SECRET_KEY.encode(), texto.encode(), hashlib.sha256).hexdigest()


def senha_correta(tentativa: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(tentativa.encode(), ADMIN_PASSWORD.encode())


def criar_token() -> str:
    expira = str(int(time.time()) + VALIDADE_SEGUNDOS)
    return f"{expira}.{_assinar(expira)}"


def exigir_admin(authorization: str = Header(default="")) -> None:
    token = authorization.removeprefix("Bearer ").strip()
    expira, _, assinatura = token.partition(".")
    valido = (
        bool(SECRET_KEY)
        and expira.isdigit()
        and hmac.compare_digest(assinatura.encode(), _assinar(expira).encode())
        and int(expira) > time.time()
    )
    if not valido:
        raise HTTPException(status_code=401, detail="Não autorizado.")