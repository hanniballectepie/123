from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional, List
import re, os, shutil
from PIL import Image

from database import get_db, init_db
from models import Aluno, Turma, User, Responsavel, Nota
from schemas import *
from security import verify_password, get_password_hash, create_access_token, validate_password
from dependencies import get_current_user, get_current_admin

# Criar aplicação FastAPI
app = FastAPI(title="Sistema de Gestão Escolar - Thales de Tarsis", version="2.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios exatos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (uploads)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

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

def save_upload_file(file: UploadFile, directory: str, filename: str) -> str:
    """Salva arquivo de upload e retorna o caminho"""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def validate_image_file(file: UploadFile) -> bool:
    """Valida se o arquivo é uma imagem válida"""
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in allowed_types:
        return False
    
    # Verificar tamanho (2MB máximo)
    file.file.seek(0, 2)  # Vai para o final do arquivo
    file_size = file.file.tell()
    file.file.seek(0)  # Volta para o início
    
    max_size = 2 * 1024 * 1024  # 2MB
    if file_size > max_size:
        return False
    
    return True

# ===== ROTAS DE AUTENTICAÇÃO =====

@app.post("/auth/register", response_model=Token, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário"""
    # Verificar se username já existe
    if db.query(User).filter(User.username == user_data.username.lower()).first():
        raise HTTPException(status_code=400, detail="Username já está em uso")
    
    # Verificar se email já existe
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email já está em uso")
    
    # Validar senha
    if not validate_password(user_data.password):
        raise HTTPException(status_code=422, detail="Senha não atende aos critérios de segurança")
    
    # Primeiro usuário criado é admin
    total_users = db.query(User).count()
    role = "admin" if total_users == 0 else "user"
    
    # Criar usuário
    password_hash = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username.lower(),
        email=user_data.email,
        password_hash=password_hash,
        role=role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Criar token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    user_out = UserOut.from_orm(db_user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_out
    )

@app.post("/auth/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Autentica usuário e retorna token"""
    # Buscar por username ou email
    user = db.query(User).filter(
        (User.username == user_credentials.username_or_email.lower()) |
        (User.email == user_credentials.username_or_email)
    ).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    # Criar token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    user_out = UserOut.from_orm(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_out
    )

@app.get("/auth/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Retorna informações do usuário atual"""
    return UserOut.from_orm(current_user)

@app.put("/auth/me", response_model=UserOut)
def update_profile(user_data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Atualiza perfil do usuário atual"""
    # Atualizar campos fornecidos
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserOut.from_orm(current_user)

@app.patch("/auth/me/password")
def change_password(password_data: UserPasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Altera senha do usuário atual"""
    # Verificar senha atual
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    # Validar nova senha
    if not validate_password(password_data.new_password):
        raise HTTPException(status_code=422, detail="Nova senha não atende aos critérios de segurança")
    
    # Atualizar senha
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Senha alterada com sucesso"}

@app.post("/auth/me/photo")
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload da foto de perfil do usuário"""
    if not validate_image_file(file):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem PNG ou JPEG de até 2MB")
    
    # Determinar extensão
    extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
    filename = f"user_{current_user.id}.{extension}"
    
    # Salvar arquivo
    file_path = save_upload_file(file, "uploads/users", filename)
    
    # Redimensionar imagem
    try:
        with Image.open(file_path) as img:
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(file_path, optimize=True, quality=85)
    except Exception:
        # Se falhar, manter original
        pass
    
    # Atualizar usuário
    current_user.profile_photo = f"/static/users/{filename}"
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Foto de perfil atualizada com sucesso", "photo_url": current_user.profile_photo}

# ===== ROTAS - ALUNOS (ATUALIZADAS) =====

@app.get("/alunos", response_model=List[AlunoResponse])
def listar_alunos(
    search: str = Query("", description="Buscar por nome do aluno"),
    turma_id: Optional[int] = Query(None, description="Filtrar por turma"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    current_user: User = Depends(get_current_user),
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
            "telefone": aluno.telefone,
            "telefone_emergencia": aluno.telefone_emergencia,
            "endereco_rua": aluno.endereco_rua,
            "endereco_numero": aluno.endereco_numero,
            "endereco_complemento": aluno.endereco_complemento,
            "endereco_bairro": aluno.endereco_bairro,
            "endereco_cidade": aluno.endereco_cidade,
            "endereco_estado": aluno.endereco_estado,
            "endereco_cep": aluno.endereco_cep,
            "foto_url": aluno.foto_url,
            "observacoes": aluno.observacoes,
            "data_criacao": aluno.data_criacao,
            "data_atualizacao": aluno.data_atualizacao,
            "turma_nome": aluno.turma.nome if aluno.turma else None,
            "idade": calcular_idade(aluno.data_nascimento)
        }
        alunos_response.append(AlunoResponse(**aluno_dict))
    
    return alunos_response

@app.get("/alunos/{aluno_id}", response_model=AlunoDetalhado)
def obter_aluno_detalhado(aluno_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtém dados detalhados de um aluno incluindo responsáveis e notas"""
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    # Montar dados básicos
    aluno_dict = {
        "id": aluno.id,
        "nome": aluno.nome,
        "data_nascimento": aluno.data_nascimento,
        "email": aluno.email,
        "status": aluno.status,
        "turma_id": aluno.turma_id,
        "telefone": aluno.telefone,
        "telefone_emergencia": aluno.telefone_emergencia,
        "endereco_rua": aluno.endereco_rua,
        "endereco_numero": aluno.endereco_numero,
        "endereco_complemento": aluno.endereco_complemento,
        "endereco_bairro": aluno.endereco_bairro,
        "endereco_cidade": aluno.endereco_cidade,
        "endereco_estado": aluno.endereco_estado,
        "endereco_cep": aluno.endereco_cep,
        "foto_url": aluno.foto_url,
        "observacoes": aluno.observacoes,
        "data_criacao": aluno.data_criacao,
        "data_atualizacao": aluno.data_atualizacao,
        "turma_nome": aluno.turma.nome if aluno.turma else None,
        "idade": calcular_idade(aluno.data_nascimento),
        "responsaveis": [ResponsavelOut.from_orm(r) for r in aluno.responsaveis],
        "notas": [NotaOut.from_orm(n) for n in aluno.notas]
    }
    
    return AlunoDetalhado(**aluno_dict)

@app.post("/alunos", response_model=AlunoResponse, status_code=201)
def criar_aluno(aluno: AlunoCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
            "telefone": db_aluno.telefone,
            "telefone_emergencia": db_aluno.telefone_emergencia,
            "endereco_rua": db_aluno.endereco_rua,
            "endereco_numero": db_aluno.endereco_numero,
            "endereco_complemento": db_aluno.endereco_complemento,
            "endereco_bairro": db_aluno.endereco_bairro,
            "endereco_cidade": db_aluno.endereco_cidade,
            "endereco_estado": db_aluno.endereco_estado,
            "endereco_cep": db_aluno.endereco_cep,
            "foto_url": db_aluno.foto_url,
            "observacoes": db_aluno.observacoes,
            "data_criacao": db_aluno.data_criacao,
            "data_atualizacao": db_aluno.data_atualizacao,
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
def atualizar_aluno(aluno_id: int, aluno: AlunoUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        
        db_aluno.data_atualizacao = datetime.utcnow()
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
            "telefone": db_aluno.telefone,
            "telefone_emergencia": db_aluno.telefone_emergencia,
            "endereco_rua": db_aluno.endereco_rua,
            "endereco_numero": db_aluno.endereco_numero,
            "endereco_complemento": db_aluno.endereco_complemento,
            "endereco_bairro": db_aluno.endereco_bairro,
            "endereco_cidade": db_aluno.endereco_cidade,
            "endereco_estado": db_aluno.endereco_estado,
            "endereco_cep": db_aluno.endereco_cep,
            "foto_url": db_aluno.foto_url,
            "observacoes": db_aluno.observacoes,
            "data_criacao": db_aluno.data_criacao,
            "data_atualizacao": db_aluno.data_atualizacao,
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
def excluir_aluno(aluno_id: int, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Exclui um aluno (apenas admin)"""
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

@app.post("/alunos/{aluno_id}/foto")
def upload_aluno_foto(
    aluno_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload da foto do aluno"""
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    if not validate_image_file(file):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem PNG ou JPEG de até 2MB")
    
    # Determinar extensão
    extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
    filename = f"aluno_{aluno_id}.{extension}"
    
    # Salvar arquivo
    file_path = save_upload_file(file, "uploads/alunos", filename)
    
    # Redimensionar imagem
    try:
        with Image.open(file_path) as img:
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            img.save(file_path, optimize=True, quality=85)
    except Exception:
        # Se falhar, manter original
        pass
    
    # Atualizar aluno
    aluno.foto_url = f"/static/alunos/{filename}"
    aluno.data_atualizacao = datetime.utcnow()
    db.commit()
    
    return {"message": "Foto do aluno atualizada com sucesso", "foto_url": aluno.foto_url}

# ===== ROTAS - RESPONSÁVEIS =====

@app.post("/alunos/{aluno_id}/responsaveis", response_model=ResponsavelOut, status_code=201)
def criar_responsavel(aluno_id: int, responsavel: ResponsavelBase, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Adiciona um responsável ao aluno"""
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    db_responsavel = Responsavel(**responsavel.dict(), aluno_id=aluno_id)
    db.add(db_responsavel)
    db.commit()
    db.refresh(db_responsavel)
    
    return ResponsavelOut.from_orm(db_responsavel)

@app.put("/responsaveis/{responsavel_id}", response_model=ResponsavelOut)
def atualizar_responsavel(responsavel_id: int, responsavel: ResponsavelUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Atualiza dados de um responsável"""
    db_responsavel = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
    if not db_responsavel:
        raise HTTPException(status_code=404, detail="Responsável não encontrado")
    
    for field, value in responsavel.dict(exclude_unset=True).items():
        setattr(db_responsavel, field, value)
    
    db.commit()
    db.refresh(db_responsavel)
    
    return ResponsavelOut.from_orm(db_responsavel)

@app.delete("/responsaveis/{responsavel_id}")
def excluir_responsavel(responsavel_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Exclui um responsável"""
    db_responsavel = db.query(Responsavel).filter(Responsavel.id == responsavel_id).first()
    if not db_responsavel:
        raise HTTPException(status_code=404, detail="Responsável não encontrado")
    
    db.delete(db_responsavel)
    db.commit()
    
    return {"message": "Responsável excluído com sucesso"}

# ===== ROTAS - NOTAS =====

@app.post("/alunos/{aluno_id}/notas", response_model=NotaOut, status_code=201)
def criar_nota(aluno_id: int, nota: NotaBase, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Adiciona uma nota ao aluno"""
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    # Verificar se já existe nota para esta disciplina/etapa
    nota_existente = db.query(Nota).filter(
        Nota.aluno_id == aluno_id,
        Nota.disciplina == nota.disciplina,
        Nota.etapa == nota.etapa
    ).first()
    
    if nota_existente:
        raise HTTPException(status_code=400, detail="Já existe uma nota para esta disciplina e etapa")
    
    db_nota = Nota(**nota.dict(), aluno_id=aluno_id)
    db.add(db_nota)
    db.commit()
    db.refresh(db_nota)
    
    return NotaOut.from_orm(db_nota)

@app.put("/notas/{nota_id}", response_model=NotaOut)
def atualizar_nota(nota_id: int, nota: NotaUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Atualiza uma nota"""
    db_nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    # Verificar duplicidade se mudou disciplina/etapa
    if nota.disciplina != db_nota.disciplina or nota.etapa != db_nota.etapa:
        nota_existente = db.query(Nota).filter(
            Nota.aluno_id == db_nota.aluno_id,
            Nota.disciplina == nota.disciplina,
            Nota.etapa == nota.etapa,
            Nota.id != nota_id
        ).first()
        
        if nota_existente:
            raise HTTPException(status_code=400, detail="Já existe uma nota para esta disciplina e etapa")
    
    for field, value in nota.dict().items():
        setattr(db_nota, field, value)
    
    db.commit()
    db.refresh(db_nota)
    
    return NotaOut.from_orm(db_nota)

@app.delete("/notas/{nota_id}")
def excluir_nota(nota_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Exclui uma nota (apenas admin pode excluir)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir notas")
        
    db_nota = db.query(Nota).filter(Nota.id == nota_id).first()
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    
    db.delete(db_nota)
    db.commit()
    
    return {"message": "Nota excluída com sucesso"}

@app.get("/alunos/{aluno_id}/notas", response_model=List[NotaOut])
def listar_notas_aluno(aluno_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lista todas as notas de um aluno"""
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    notas = db.query(Nota).filter(Nota.aluno_id == aluno_id).order_by(Nota.disciplina, Nota.etapa).all()
    
    return [NotaOut.from_orm(nota) for nota in notas]

# ===== ROTAS - TURMAS (ATUALIZADAS) =====

@app.get("/turmas", response_model=List[TurmaResponse])
def listar_turmas(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def criar_turma(turma: TurmaCreate, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Cria uma nova turma (apenas admin)"""
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

# ===== ROTA - MATRÍCULAS (ATUALIZADO) =====

@app.post("/matriculas")
def matricular_aluno(matricula: MatriculaRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        aluno.data_atualizacao = datetime.utcnow()
        
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

# ===== ROTA - ESTATÍSTICAS (ATUALIZADO) =====

@app.get("/estatisticas")
def obter_estatisticas(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna estatísticas gerais do sistema"""
    total_alunos = db.query(Aluno).count()
    alunos_ativos = db.query(Aluno).filter(Aluno.status == "ativo").count()
    alunos_inativos = db.query(Aluno).filter(Aluno.status == "inativo").count()
    total_turmas = db.query(Turma).count()
    total_usuarios = db.query(User).count()
    total_responsaveis = db.query(Responsavel).count()
    total_notas = db.query(Nota).count()
    
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
        "total_usuarios": total_usuarios,
        "total_responsaveis": total_responsaveis,
        "total_notas": total_notas,
        "turmas": turmas_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)