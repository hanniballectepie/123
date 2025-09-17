from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, date

class Turma(Base):
    __tablename__ = "turmas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    capacidade = Column(Integer, nullable=False)
    
    # Relationship com alunos
    alunos = relationship("Aluno", back_populates="turma")
    
    def __repr__(self):
        return f"<Turma(id={self.id}, nome='{self.nome}', capacidade={self.capacidade})>"

class Aluno(Base):
    __tablename__ = "alunos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(80), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    email = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="ativo")  # ativo ou inativo
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=True)
    
    # Relationship com turma
    turma = relationship("Turma", back_populates="alunos")
    
    def __repr__(self):
        return f"<Aluno(id={self.id}, nome='{self.nome}', status='{self.status}')>"