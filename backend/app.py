from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from datetime import date, datetime
from typing import Optional, List
import re

from database import get_db, init_db
from models import Aluno, Turma

# Schemas Pydantic
class TurmaBase(BaseModel):
    nome: str
    capacidade: int

class TurmaCreate(TurmaBase):
    pass

class TurmaResponse(TurmaBase):
    id: int
    alunos_count: int = 0
    
    class Config:
        from_attributes = True

class AlunoBase(BaseModel):
    nome: str
    data_nascimento: date
    email: Optional[str] = None
    status: str = "ativo"
    turma_id: Optional[int] = None

class AlunoCreate(AlunoBase):
    @validator('nome')
    def validate_nome(cls, v):
        if len(v.strip()) < 3 or len(v.strip()) > 80:
            raise ValueError('Nome deve ter entre 3 e 80 caracteres')
        return v.strip()
    
    @validator('data_nascimento')
    def validate_data_nascimento(cls, v):
        hoje = date.today()
        idade_minima = date(hoje.year - 5, hoje.month, hoje.day)
        if v > idade_minima:
            raise ValueError('Aluno deve ter pelo menos 5 anos')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Email inválido')
            return v.strip()
        return None
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['ativo', 'inativo']:
            raise ValueError('Status deve ser "ativo" ou "inativo"')
        return v

class AlunoUpdate(AlunoBase):
    @validator('nome')
    def validate_nome(cls, v):
        if len(v.strip()) < 3 or len(v.strip()) > 80:
            raise ValueError('Nome deve ter entre 3 e 80 caracteres')
        return v.strip()
    
    @validator('data_nascimento')
    def validate_data_nascimento(cls, v):
        hoje = date.today()
        idade_minima = date(hoje.year - 5, hoje.month, hoje.day)
        if v > idade_minima:
            raise ValueError('Aluno deve ter pelo menos 5 anos')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Email inválido')
            return v.strip()
        return None
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['ativo', 'inativo']:
            raise ValueError('Status deve ser "ativo" ou "inativo"')
        return v

class AlunoResponse(AlunoBase):
    id: int
    turma_nome: Optional[str] = None
    idade: int
    
    class Config:
        from_attributes = True

class MatriculaRequest(BaseModel):
    aluno_id: int
    turma_id: int

# Criar aplicação FastAPI
app = FastAPI(title="Sistema de Gestão Escolar - Thales de Tarsis", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios exatos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicialização
@app.on_event("startup")
def startup_event():
    init_db()

# Helper functions
def calcular_idade(data_nascimento: date) -> int:
    hoje = date.today()
    idade = hoje.year - data_nascimento.year
    if hoje.month < data_nascimento.month or (hoje.month == data_nascimento.month and hoje.day < data_nascimento.day):
        idade -= 1
    return idade

# ROTAS - ALUNOS
@app.get("/alunos", response_model=List[AlunoResponse])
def listar_alunos(
    search: str = Query("", description="Buscar por nome do aluno"),
    turma_id: Optional[int] = Query(None, description="Filtrar por turma"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db)
):
    """Lista alunos com filtros opcionais"""
    query = db.query(Aluno)
    
    if search:
        query = query.filter(Aluno.nome.ilike(f"%{search}%"))
    
    if turma_id is not None:
        query = query.filter(Aluno.turma_id == turma_id)
    
    if status:
        if status not in ['ativo', 'inativo']:
            raise HTTPException(status_code=400, detail="Status deve ser 'ativo' ou 'inativo'")
        query = query.filter(Aluno.status == status)
    
    alunos = query.all()
    
    # Converter para response model
    alunos_response = []
    for aluno in alunos:
        aluno_dict = {
            "id": aluno.id,
            "nome": aluno.nome,
            "data_nascimento": aluno.data_nascimento,
            "email": aluno.email,
            "status": aluno.status,
            "turma_id": aluno.turma_id,
            "turma_nome": aluno.turma.nome if aluno.turma else None,
            "idade": calcular_idade(aluno.data_nascimento)
        }
        alunos_response.append(AlunoResponse(**aluno_dict))
    
    return alunos_response

@app.post("/alunos", response_model=AlunoResponse, status_code=201)
def criar_aluno(aluno: AlunoCreate, db: Session = Depends(get_db)):
    """Cria um novo aluno"""
    try:
        # Verificar se turma existe (se informada)
        if aluno.turma_id:
            turma = db.query(Turma).filter(Turma.id == aluno.turma_id).first()
            if not turma:
                raise HTTPException(status_code=404, detail="Turma não encontrada")
            
            # Verificar capacidade da turma
            alunos_na_turma = db.query(Aluno).filter(Aluno.turma_id == aluno.turma_id).count()
            if alunos_na_turma >= turma.capacidade:
                raise HTTPException(status_code=400, detail="Turma já está na capacidade máxima")
        
        # Criar aluno
        db_aluno = Aluno(**aluno.dict())
        db.add(db_aluno)
        db.commit()
        db.refresh(db_aluno)
        
        # Retornar response
        aluno_dict = {
            "id": db_aluno.id,
            "nome": db_aluno.nome,
            "data_nascimento": db_aluno.data_nascimento,
            "email": db_aluno.email,
            "status": db_aluno.status,
            "turma_id": db_aluno.turma_id,
            "turma_nome": db_aluno.turma.nome if db_aluno.turma else None,
            "idade": calcular_idade(db_aluno.data_nascimento)
        }
        
        return AlunoResponse(**aluno_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.put("/alunos/{aluno_id}", response_model=AlunoResponse)
def atualizar_aluno(aluno_id: int, aluno: AlunoUpdate, db: Session = Depends(get_db)):
    """Atualiza um aluno existente"""
    try:
        db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not db_aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Verificar se turma existe (se informada)
        if aluno.turma_id:
            turma = db.query(Turma).filter(Turma.id == aluno.turma_id).first()
            if not turma:
                raise HTTPException(status_code=404, detail="Turma não encontrada")
            
            # Verificar capacidade da turma (só se mudou de turma)
            if db_aluno.turma_id != aluno.turma_id:
                alunos_na_turma = db.query(Aluno).filter(Aluno.turma_id == aluno.turma_id).count()
                if alunos_na_turma >= turma.capacidade:
                    raise HTTPException(status_code=400, detail="Turma já está na capacidade máxima")
        
        # Atualizar campos
        for field, value in aluno.dict().items():
            setattr(db_aluno, field, value)
        
        db.commit()
        db.refresh(db_aluno)
        
        # Retornar response
        aluno_dict = {
            "id": db_aluno.id,
            "nome": db_aluno.nome,
            "data_nascimento": db_aluno.data_nascimento,
            "email": db_aluno.email,
            "status": db_aluno.status,
            "turma_id": db_aluno.turma_id,
            "turma_nome": db_aluno.turma.nome if db_aluno.turma else None,
            "idade": calcular_idade(db_aluno.data_nascimento)
        }
        
        return AlunoResponse(**aluno_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.delete("/alunos/{aluno_id}")
def excluir_aluno(aluno_id: int, db: Session = Depends(get_db)):
    """Exclui um aluno"""
    db_aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not db_aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    try:
        db.delete(db_aluno)
        db.commit()
        return {"message": f"Aluno {db_aluno.nome} excluído com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir aluno: {str(e)}")

# ROTAS - TURMAS
@app.get("/turmas", response_model=List[TurmaResponse])
def listar_turmas(db: Session = Depends(get_db)):
    """Lista todas as turmas com contagem de alunos"""
    turmas = db.query(Turma).all()
    
    turmas_response = []
    for turma in turmas:
        alunos_count = db.query(Aluno).filter(Aluno.turma_id == turma.id).count()
        turma_dict = {
            "id": turma.id,
            "nome": turma.nome,
            "capacidade": turma.capacidade,
            "alunos_count": alunos_count
        }
        turmas_response.append(TurmaResponse(**turma_dict))
    
    return turmas_response

@app.post("/turmas", response_model=TurmaResponse, status_code=201)
def criar_turma(turma: TurmaCreate, db: Session = Depends(get_db)):
    """Cria uma nova turma"""
    try:
        if len(turma.nome.strip()) < 2:
            raise HTTPException(status_code=422, detail="Nome da turma deve ter pelo menos 2 caracteres")
        
        if turma.capacidade <= 0:
            raise HTTPException(status_code=422, detail="Capacidade deve ser maior que zero")
        
        db_turma = Turma(**turma.dict())
        db.add(db_turma)
        db.commit()
        db.refresh(db_turma)
        
        turma_dict = {
            "id": db_turma.id,
            "nome": db_turma.nome,
            "capacidade": db_turma.capacidade,
            "alunos_count": 0
        }
        
        return TurmaResponse(**turma_dict)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

# ROTA - MATRÍCULAS
@app.post("/matriculas")
def matricular_aluno(matricula: MatriculaRequest, db: Session = Depends(get_db)):
    """Matricula um aluno em uma turma"""
    try:
        # Verificar se aluno existe
        aluno = db.query(Aluno).filter(Aluno.id == matricula.aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Verificar se turma existe
        turma = db.query(Turma).filter(Turma.id == matricula.turma_id).first()
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada")
        
        # Verificar capacidade da turma
        alunos_na_turma = db.query(Aluno).filter(Aluno.turma_id == matricula.turma_id).count()
        if alunos_na_turma >= turma.capacidade:
            raise HTTPException(status_code=400, detail="Turma já está na capacidade máxima")
        
        # Matricular aluno (ativar e definir turma)
        aluno.turma_id = matricula.turma_id
        aluno.status = "ativo"
        
        db.commit()
        
        return {
            "message": f"Aluno {aluno.nome} matriculado com sucesso na turma {turma.nome}",
            "aluno_id": aluno.id,
            "turma_id": turma.id,
            "status": aluno.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

# ROTA - ESTATÍSTICAS
@app.get("/estatisticas")
def obter_estatisticas(db: Session = Depends(get_db)):
    """Retorna estatísticas gerais do sistema"""
    total_alunos = db.query(Aluno).count()
    alunos_ativos = db.query(Aluno).filter(Aluno.status == "ativo").count()
    alunos_inativos = db.query(Aluno).filter(Aluno.status == "inativo").count()
    total_turmas = db.query(Turma).count()
    
    # Estatísticas por turma
    turmas_stats = []
    turmas = db.query(Turma).all()
    for turma in turmas:
        alunos_count = db.query(Aluno).filter(Aluno.turma_id == turma.id).count()
        turmas_stats.append({
            "turma_id": turma.id,
            "nome": turma.nome,
            "capacidade": turma.capacidade,
            "alunos": alunos_count,
            "ocupacao_percentual": round((alunos_count / turma.capacidade) * 100, 1) if turma.capacidade > 0 else 0
        })
    
    return {
        "total_alunos": total_alunos,
        "alunos_ativos": alunos_ativos,
        "alunos_inativos": alunos_inativos,
        "total_turmas": total_turmas,
        "turmas": turmas_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)