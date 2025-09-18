from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Float, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, date

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(40), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="user")  # admin, user
    theme_preference = Column(String(20), nullable=False, default="dark")  # dark, light
    locale = Column(String(10), nullable=True, default="pt-BR")
    timezone = Column(String(50), nullable=True, default="America/Sao_Paulo")
    notifications_email = Column(Boolean, nullable=False, default=True)
    profile_photo = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

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
    
    # Novos campos
    telefone = Column(String(20), nullable=True)
    telefone_emergencia = Column(String(20), nullable=True)
    endereco_rua = Column(String(200), nullable=True)
    endereco_numero = Column(String(20), nullable=True)
    endereco_complemento = Column(String(100), nullable=True)
    endereco_bairro = Column(String(100), nullable=True)
    endereco_cidade = Column(String(100), nullable=True)
    endereco_estado = Column(String(50), nullable=True)
    endereco_cep = Column(String(10), nullable=True)
    foto_url = Column(String(255), nullable=True)
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    turma = relationship("Turma", back_populates="alunos")
    responsaveis = relationship("Responsavel", back_populates="aluno", cascade="all, delete-orphan")
    notas = relationship("Nota", back_populates="aluno", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Aluno(id={self.id}, nome='{self.nome}', status='{self.status}')>"

class Responsavel(Base):
    __tablename__ = "responsaveis"
    
    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    nome = Column(String(80), nullable=False)
    parentesco = Column(String(40), nullable=False)  # Pai, Mãe, Responsável, Tutor
    telefone = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    documento = Column(String(20), nullable=True)  # CPF
    
    # Relationship
    aluno = relationship("Aluno", back_populates="responsaveis")
    
    def __repr__(self):
        return f"<Responsavel(id={self.id}, nome='{self.nome}', parentesco='{self.parentesco}')>"

class Nota(Base):
    __tablename__ = "notas"
    
    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    disciplina = Column(String(60), nullable=False)
    etapa = Column(String(20), nullable=False)  # 1B, 2B, 3B, 4B, FINAL
    nota = Column(Float, nullable=False)  # 0.0 - 10.0
    data_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    aluno = relationship("Aluno", back_populates="notas")
    
    def __repr__(self):
        return f"<Nota(id={self.id}, aluno_id={self.aluno_id}, disciplina='{self.disciplina}', etapa='{self.etapa}', nota={self.nota})>"