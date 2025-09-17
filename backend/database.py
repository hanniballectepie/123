from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Caminho para o banco SQLite
DATABASE_URL = "sqlite:///./app.db"

# Criar engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário para SQLite
)

# Criar SessionLocal para interações com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class para modelos
Base = declarative_base()

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()