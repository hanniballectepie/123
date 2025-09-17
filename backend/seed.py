from sqlalchemy.orm import Session
from datetime import date, datetime
import random
from database import SessionLocal, init_db
from models import Turma, Aluno

def criar_turmas(db: Session):
    """Cria turmas de exemplo"""
    turmas_data = [
        {"nome": "1º Ano A", "capacidade": 25},
        {"nome": "2º Ano B", "capacidade": 30},
        {"nome": "3º Ano C", "capacidade": 28},
        {"nome": "4º Ano A", "capacidade": 32},
        {"nome": "5º Ano B", "capacidade": 26},
    ]
    
    turmas_criadas = []
    for turma_info in turmas_data:
        # Verificar se já existe
        existing = db.query(Turma).filter(Turma.nome == turma_info["nome"]).first()
        if not existing:
            turma = Turma(**turma_info)
            db.add(turma)
            db.commit()
            db.refresh(turma)
            turmas_criadas.append(turma)
            print(f"Turma criada: {turma.nome}")
        else:
            turmas_criadas.append(existing)
            print(f"Turma já existe: {existing.nome}")
    
    return turmas_criadas

def criar_alunos(db: Session, turmas):
    """Cria alunos de exemplo"""
    nomes = [
        "Ana Silva", "Bruno Santos", "Carlos Oliveira", "Diana Costa", "Eduardo Lima",
        "Fernanda Sousa", "Gabriel Pereira", "Helena Martins", "Igor Rodrigues", "Juliana Alves",
        "Leonardo Ferreira", "Mariana Gomes", "Nicolas Barbosa", "Olivia Ribeiro", "Pedro Carvalho",
        "Rafaela Dias", "Samuel Nascimento", "Tatiana Moura", "Vitor Araújo", "Yasmin Cardoso"
    ]
    
    emails = [
        "ana.silva@escola.com", "bruno.santos@escola.com", "carlos.oliveira@escola.com",
        "diana.costa@escola.com", "eduardo.lima@escola.com", "fernanda.sousa@escola.com",
        "gabriel.pereira@escola.com", "helena.martins@escola.com", "igor.rodrigues@escola.com",
        "juliana.alves@escola.com", "leonardo.ferreira@escola.com", "mariana.gomes@escola.com",
        "nicolas.barbosa@escola.com", "olivia.ribeiro@escola.com", "pedro.carvalho@escola.com",
        "rafaela.dias@escola.com", "samuel.nascimento@escola.com", "tatiana.moura@escola.com",
        "vitor.araujo@escola.com", "yasmin.cardoso@escola.com"
    ]
    
    # Gerar datas de nascimento (idades entre 6 e 18 anos)
    hoje = date.today()
    
    for i, nome in enumerate(nomes):
        # Verificar se já existe
        existing = db.query(Aluno).filter(Aluno.nome == nome).first()
        if existing:
            print(f"Aluno já existe: {nome}")
            continue
        
        # Gerar idade aleatória entre 6 e 18 anos
        idade = random.randint(6, 18)
        ano_nascimento = hoje.year - idade
        mes_nascimento = random.randint(1, 12)
        dia_nascimento = random.randint(1, 28)  # Para evitar problemas com fevereiro
        
        data_nascimento = date(ano_nascimento, mes_nascimento, dia_nascimento)
        
        # Determinar status (90% ativo, 10% inativo)
        status = "ativo" if random.random() < 0.9 else "inativo"
        
        # Atribuir turma (80% dos alunos têm turma, 20% não têm)
        turma_id = None
        if random.random() < 0.8 and turmas:
            turma = random.choice(turmas)
            # Verificar se a turma não está cheia
            alunos_na_turma = db.query(Aluno).filter(Aluno.turma_id == turma.id).count()
            if alunos_na_turma < turma.capacidade:
                turma_id = turma.id
        
        # Email opcional (70% dos alunos têm email)
        email = emails[i] if i < len(emails) and random.random() < 0.7 else None
        
        aluno = Aluno(
            nome=nome,
            data_nascimento=data_nascimento,
            email=email,
            status=status,
            turma_id=turma_id
        )
        
        db.add(aluno)
        db.commit()
        db.refresh(aluno)
        
        turma_nome = aluno.turma.nome if aluno.turma else "Sem turma"
        print(f"Aluno criado: {aluno.nome} - {aluno.status} - {turma_nome}")

def seed_database():
    """Função principal para popular o banco de dados"""
    print("Iniciando seed do banco de dados...")
    
    # Inicializar banco
    init_db()
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Criar turmas
        print("\n=== CRIANDO TURMAS ===")
        turmas = criar_turmas(db)
        
        # Criar alunos
        print("\n=== CRIANDO ALUNOS ===")
        criar_alunos(db, turmas)
        
        print("\n=== SEED CONCLUÍDO ===")
        print(f"Total de turmas: {db.query(Turma).count()}")
        print(f"Total de alunos: {db.query(Aluno).count()}")
        print(f"Alunos ativos: {db.query(Aluno).filter(Aluno.status == 'ativo').count()}")
        print(f"Alunos inativos: {db.query(Aluno).filter(Aluno.status == 'inativo').count()}")
        
        # Estatísticas por turma
        print("\n=== ESTATÍSTICAS POR TURMA ===")
        for turma in turmas:
            alunos_count = db.query(Aluno).filter(Aluno.turma_id == turma.id).count()
            ocupacao = (alunos_count / turma.capacidade) * 100 if turma.capacidade > 0 else 0
            print(f"{turma.nome}: {alunos_count}/{turma.capacidade} alunos ({ocupacao:.1f}% ocupação)")
            
    except Exception as e:
        print(f"Erro durante o seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()