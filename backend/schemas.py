from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
import re

# === USER SCHEMAS ===

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 40:
            raise ValueError('Username deve ter entre 3 e 40 caracteres')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username deve conter apenas letras, números e underscore')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Senhas não coincidem')
        return v

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    theme_preference: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    notifications_email: Optional[bool] = None
    
    @validator('theme_preference')
    def validate_theme(cls, v):
        if v and v not in ['dark', 'light']:
            raise ValueError('Tema deve ser "dark" ou "light"')
        return v

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Nova senha deve ter pelo menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Nova senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Nova senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Nova senha deve conter pelo menos um número')
        return v

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str]
    role: str
    theme_preference: str
    locale: Optional[str]
    timezone: Optional[str]
    notifications_email: bool
    profile_photo: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# === TURMA SCHEMAS ===

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

# === RESPONSAVEL SCHEMAS ===

class ResponsavelBase(BaseModel):
    nome: str
    parentesco: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    documento: Optional[str] = None
    
    @validator('nome')
    def validate_nome(cls, v):
        if len(v.strip()) < 3 or len(v.strip()) > 80:
            raise ValueError('Nome deve ter entre 3 e 80 caracteres')
        return v.strip()
    
    @validator('parentesco')
    def validate_parentesco(cls, v):
        if len(v.strip()) < 3 or len(v.strip()) > 40:
            raise ValueError('Parentesco deve ter entre 3 e 40 caracteres')
        return v.strip()
    
    @validator('telefone')
    def validate_telefone(cls, v):
        if v and v.strip():
            # Remove formatação e verifica se tem pelo menos 10 dígitos
            digits = re.sub(r'[^\d]', '', v)
            if len(digits) < 10:
                raise ValueError('Telefone deve ter pelo menos 10 dígitos')
            return v.strip()
        return None
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Email inválido')
            return v.strip()
        return None
    
    @validator('documento')
    def validate_documento(cls, v):
        if v and v.strip():
            # Remove formatação e verifica CPF (11 dígitos)
            digits = re.sub(r'[^\d]', '', v)
            if len(digits) != 11:
                raise ValueError('CPF deve ter 11 dígitos')
            return v.strip()
        return None

class ResponsavelCreate(ResponsavelBase):
    aluno_id: int

class ResponsavelUpdate(ResponsavelBase):
    pass

class ResponsavelOut(ResponsavelBase):
    id: int
    aluno_id: int
    
    class Config:
        from_attributes = True

# === NOTA SCHEMAS ===

class NotaBase(BaseModel):
    disciplina: str
    etapa: str
    nota: float
    
    @validator('disciplina')
    def validate_disciplina(cls, v):
        if len(v.strip()) < 2 or len(v.strip()) > 60:
            raise ValueError('Disciplina deve ter entre 2 e 60 caracteres')
        return v.strip()
    
    @validator('etapa')
    def validate_etapa(cls, v):
        etapas_validas = ['1B', '2B', '3B', '4B', 'FINAL']
        if v not in etapas_validas:
            raise ValueError(f'Etapa deve ser uma das opções: {", ".join(etapas_validas)}')
        return v
    
    @validator('nota')
    def validate_nota(cls, v):
        if v < 0.0 or v > 10.0:
            raise ValueError('Nota deve estar entre 0.0 e 10.0')
        return round(v, 1)

class NotaCreate(NotaBase):
    aluno_id: int

class NotaUpdate(NotaBase):
    pass

class NotaOut(NotaBase):
    id: int
    aluno_id: int
    data_registro: datetime
    
    class Config:
        from_attributes = True

# === ALUNO SCHEMAS ===

class AlunoBase(BaseModel):
    nome: str
    data_nascimento: date
    email: Optional[str] = None
    status: str = "ativo"
    turma_id: Optional[int] = None
    telefone: Optional[str] = None
    telefone_emergencia: Optional[str] = None
    endereco_rua: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    endereco_cep: Optional[str] = None
    observacoes: Optional[str] = None

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
    
    @validator('telefone', 'telefone_emergencia')
    def validate_telefone(cls, v):
        if v and v.strip():
            digits = re.sub(r'[^\d]', '', v)
            if len(digits) < 10:
                raise ValueError('Telefone deve ter pelo menos 10 dígitos')
            return v.strip()
        return None
    
    @validator('endereco_cep')
    def validate_cep(cls, v):
        if v and v.strip():
            if not re.match(r'^\d{5}-?\d{3}$', v.strip()):
                raise ValueError('CEP deve estar no formato 00000-000')
            return v.strip()
        return None

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
    
    @validator('telefone', 'telefone_emergencia')
    def validate_telefone(cls, v):
        if v and v.strip():
            digits = re.sub(r'[^\d]', '', v)
            if len(digits) < 10:
                raise ValueError('Telefone deve ter pelo menos 10 dígitos')
            return v.strip()
        return None
    
    @validator('endereco_cep')
    def validate_cep(cls, v):
        if v and v.strip():
            if not re.match(r'^\d{5}-?\d{3}$', v.strip()):
                raise ValueError('CEP deve estar no formato 00000-000')
            return v.strip()
        return None

class AlunoResponse(AlunoBase):
    id: int
    turma_nome: Optional[str] = None
    idade: int
    foto_url: Optional[str] = None
    data_criacao: datetime
    data_atualizacao: datetime
    
    class Config:
        from_attributes = True

class AlunoDetalhado(AlunoResponse):
    responsaveis: List[ResponsavelOut] = []
    notas: List[NotaOut] = []
    
    class Config:
        from_attributes = True

# === MATRÍCULA SCHEMA ===

class MatriculaRequest(BaseModel):
    aluno_id: int
    turma_id: int

# === TOKEN SCHEMAS ===

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
