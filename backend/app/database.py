import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./album.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool pequeno: o plano gratuito do Supabase limita as conexões
    engine = create_engine(
        DATABASE_URL,
        pool_size=3,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def preparar_banco() -> None:
    """Cria as tabelas e, no Postgres, tranca o acesso pela API pública."""
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as con:
            con.execute(text("ALTER TABLE photos ENABLE ROW LEVEL SECURITY"))