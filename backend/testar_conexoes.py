from sqlalchemy import text

from app import storage
from app.database import engine

print("1) Banco de dados...")
with engine.connect() as con:
    print("   ok:", con.execute(text("select 1")).scalar())

print("2) Armazenamento...")
caminho = "teste_conexao.txt"
storage.enviar(caminho, b"ola", "text/plain")
print("   enviado")
print("   baixado:", storage.baixar(caminho))
storage.apagar([caminho])
print("   apagado")