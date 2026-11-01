from io import BytesIO

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()  # ensina o Pillow a abrir HEIC

LADO_PRINCIPAL = 2000
LADO_MINIATURA = 600


def classificar(largura: int, altura: int) -> str:
    proporcao = largura / altura
    if proporcao > 1.15:
        return "horizontal"
    if proporcao < 0.87:
        return "vertical"
    return "quadrada"


def _para_jpeg(imagem: Image.Image, lado_maximo: int) -> bytes:
    copia = imagem.copy()
    copia.thumbnail((lado_maximo, lado_maximo))  # mantém a proporção
    saida = BytesIO()
    copia.save(saida, format="JPEG", quality=85, optimize=True)
    return saida.getvalue()


def processar(conteudo: bytes) -> dict:
    try:
        imagem = Image.open(BytesIO(conteudo))
        imagem.load()
    except Exception:
        raise ValueError("Arquivo de imagem inválido.")

    imagem = ImageOps.exif_transpose(imagem)  # corrige a rotação
    imagem = imagem.convert("RGB")

    principal = _para_jpeg(imagem, LADO_PRINCIPAL)
    miniatura = _para_jpeg(imagem, LADO_MINIATURA)

    # Medidas finais, depois de endireitar a foto
    largura, altura = imagem.size
    return {
        "principal": principal,
        "miniatura": miniatura,
        "largura": largura,
        "altura": altura,
        "orientacao": classificar(largura, altura),
    }