import sqlite3
from pathlib import Path

BANCO = "album.db"
PASTA = Path("uploads")

con = sqlite3.connect(BANCO)
fotos = con.execute("SELECT id, author_name, created_at FROM photos").fetchall()

orfas = [f for f in fotos if not (PASTA / f"{f[0]}.jpg").exists()]

print(f"{len(fotos)} foto(s) no banco, {len(orfas)} sem arquivo:")
for id_, autor, criada in orfas:
    print(f"  - {id_}  ({autor}, {criada})")

if orfas and input("Apagar esses registros? (s/n) ").strip().lower() == "s":
    con.executemany("DELETE FROM photos WHERE id = ?", [(f[0],) for f in orfas])
    con.commit()
    print(f"{len(orfas)} registro(s) apagado(s).")
else:
    print("Nada foi apagado.")

con.close()
