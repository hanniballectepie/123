from sqlalchemy.orm import Session
from datetime import date, datetime
import random
from database import SessionLocal, init_db
from models import Turma, Aluno, User, Responsavel, Nota
from security import get_password_hash

def criar_usuarios(db: Session):
    """Cria usuários de exemplo"""
    usuarios_data = [
        {
            "username": "admin",
            "email": "admin@escola.com",
            "password": "Admin123!",
            "display_name": "Administrador",
            "role": "admin"
        },
        {
            "username": "usuario",
            "email": "usuario@escola.com", 
            "password": "User123!",
            "display_name": "Usuário Padrão",
            "role": "user"
        },
        {
            "username": "thales",
            "email": "thales@escola.com",
            "password": "Thales123!",
            "display_name": "Thales de Tarsis",
            "role": "admin"
        }
    ]
    
    usuarios_criados = []
    for user_info in usuarios_data:
        # Verificar se já existe
        existing = db.query(User).filter(User.username == user_info["username"]).first()
        if not existing:
            user = User(
                username=user_info["username"],
                email=user_info["email"],
                password_hash=get_password_hash(user_info["password"]),
                display_name=user_info["display_name"],
                role=user_info["role"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            usuarios_criados.append(user)
            print(f"Usuário criado: {user.username} ({user.role})")
        else:
            usuarios_criados.append(existing)
            print(f"Usuário já existe: {existing.username}")
    
    return usuarios_criados

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
    
    telefones = [
        "(11) 9 9999-0001", "(11) 9 9999-0002", "(11) 9 9999-0003", "(11) 9 9999-0004", "(11) 9 9999-0005",
        "(11) 9 9999-0006", "(11) 9 9999-0007", "(11) 9 9999-0008", "(11) 9 9999-0009", "(11) 9 9999-0010",
        "(11) 9 9999-0011", "(11) 9 9999-0012", "(11) 9 9999-0013", "(11) 9 9999-0014", "(11) 9 9999-0015",
        "(11) 9 9999-0016", "(11) 9 9999-0017", "(11) 9 9999-0018", "(11) 9 9999-0019", "(11) 9 9999-0020"
    ]
    
    enderecos = [
        {"rua": "Rua das Flores", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP", "cep": "01234-567"},
        {"rua": "Av. Brasil", "bairro": "Vila Nova", "cidade": "São Paulo", "estado": "SP", "cep": "01234-568"},
        {"rua": "Rua da Paz", "bairro": "Jardim América", "cidade": "São Paulo", "estado": "SP", "cep": "01234-569"},
        {"rua": "Av. Paulista", "bairro": "Bela Vista", "cidade": "São Paulo", "estado": "SP", "cep": "01234-570"},
        {"rua": "Rua Augusta", "bairro": "Consolação", "cidade": "São Paulo", "estado": "SP", "cep": "01234-571"}
    ]
    
    # Gerar datas de nascimento (idades entre 6 e 18 anos)
    hoje = date.today()
    alunos_criados = []
    
    for i, nome in enumerate(nomes):
        # Verificar se já existe
        existing = db.query(Aluno).filter(Aluno.nome == nome).first()
        if existing:
            print(f"Aluno já existe: {nome}")
            alunos_criados.append(existing)
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
        
        # Telefone opcional (80% dos alunos têm telefone)
        telefone = telefones[i] if i < len(telefones) and random.random() < 0.8 else None
        telefone_emergencia = telefones[(i + 10) % len(telefones)] if telefone and random.random() < 0.5 else None
        
        # Endereço
        endereco = random.choice(enderecos)
        numero = str(random.randint(10, 999))
        
        aluno = Aluno(
            nome=nome,
            data_nascimento=data_nascimento,
            email=email,
            status=status,
            turma_id=turma_id,
            telefone=telefone,
            telefone_emergencia=telefone_emergencia,
            endereco_rua=endereco["rua"],
            endereco_numero=numero,
            endereco_bairro=endereco["bairro"],
            endereco_cidade=endereco["cidade"],
            endereco_estado=endereco["estado"],
            endereco_cep=endereco["cep"]
        )
        
        db.add(aluno)
        db.commit()
        db.refresh(aluno)
        alunos_criados.append(aluno)
        
        turma_nome = aluno.turma.nome if aluno.turma else "Sem turma"
        print(f"Aluno criado: {aluno.nome} - {aluno.status} - {turma_nome}")
    
    return alunos_criados

def criar_responsaveis(db: Session, alunos):
    """Cria responsáveis de exemplo"""
    parentescos = ["Pai", "Mãe", "Responsável", "Tutor", "Avô", "Avó"]
    nomes_responsaveis = [
        "João Silva", "Maria Santos", "José Oliveira", "Ana Costa", "Carlos Lima",
        "Fernanda Sousa", "Roberto Pereira", "Lucia Martins", "Antonio Rodrigues", "Clara Alves",
        "Fernando Ferreira", "Patricia Gomes", "Ricardo Barbosa", "Silvia Ribeiro", "Marcos Carvalho",
        "Isabel Dias", "Paulo Nascimento", "Claudia Moura", "Daniel Araújo", "Beatriz Cardoso"
    ]
    
    responsaveis_criados = []
    
    for aluno in alunos:
        # Criar 1-2 responsáveis por aluno
        num_responsaveis = random.randint(1, 2)
        
        for _ in range(num_responsaveis):
            nome = random.choice(nomes_responsaveis)
            parentesco = random.choice(parentescos)
            
            # Evitar responsáveis duplicados para o mesmo aluno
            existing = db.query(Responsavel).filter(
                Responsavel.aluno_id == aluno.id,
                Responsavel.nome == nome
            ).first()
            
            if existing:
                continue
            
            # Telefone (90% têm telefone)
            telefone = f"(11) 9 {random.randint(1000, 9999)}-{random.randint(1000, 9999)}" if random.random() < 0.9 else None
            
            # Email (60% têm email)
            email = f"{nome.lower().replace(' ', '.')}@email.com" if random.random() < 0.6 else None
            
            # CPF (70% têm CPF)
            documento = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}" if random.random() < 0.7 else None
            
            responsavel = Responsavel(
                aluno_id=aluno.id,
                nome=nome,
                parentesco=parentesco,
                telefone=telefone,
                email=email,
                documento=documento
            )
            
            db.add(responsavel)
            responsaveis_criados.append(responsavel)
    
    db.commit()
    print(f"Responsáveis criados: {len(responsaveis_criados)}")
    return responsaveis_criados

def criar_notas(db: Session, alunos):
    """Cria notas de exemplo"""
    disciplinas = ["Matemática", "Português", "Ciências", "História", "Geografia", "Inglês", "Educação Física"]
    etapas = ["1B", "2B", "3B", "4B"]
    
    notas_criadas = []
    
    for aluno in alunos:
        # Alunos ativos têm mais notas
        if aluno.status == "ativo":
            num_disciplinas = random.randint(3, 5)  # 3-5 disciplinas
        else:
            num_disciplinas = random.randint(1, 3)  # 1-3 disciplinas
        
        disciplinas_aluno = random.sample(disciplinas, num_disciplinas)
        
        for disciplina in disciplinas_aluno:
            # Cada disciplina pode ter 1-3 etapas
            num_etapas = random.randint(1, 3)
            etapas_disciplina = random.sample(etapas, num_etapas)
            
            for etapa in etapas_disciplina:
                # Verificar se já existe
                existing = db.query(Nota).filter(
                    Nota.aluno_id == aluno.id,
                    Nota.disciplina == disciplina,
                    Nota.etapa == etapa
                ).first()
                
                if existing:
                    continue
                
                # Gerar nota (média 7.0, com variação)
                nota_base = random.uniform(4.0, 10.0)
                # Arredondar para 1 casa decimal
                nota = round(nota_base, 1)
                
                nota_obj = Nota(
                    aluno_id=aluno.id,
                    disciplina=disciplina,
                    etapa=etapa,
                    nota=nota
                )
                
                db.add(nota_obj)
                notas_criadas.append(nota_obj)
    
    db.commit()
    print(f"Notas criadas: {len(notas_criadas)}")
    return notas_criadas

def seed_database():
    """Função principal para popular o banco de dados"""
    print("Iniciando seed do banco de dados...")
    
    # Inicializar banco
    init_db()
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Criar usuários
        print("\n=== CRIANDO USUÁRIOS ===")
        usuarios = criar_usuarios(db)
        
        # Criar turmas
        print("\n=== CRIANDO TURMAS ===")
        turmas = criar_turmas(db)
        
        # Criar alunos
        print("\n=== CRIANDO ALUNOS ===")
        alunos = criar_alunos(db, turmas)
        
        # Criar responsáveis
        print("\n=== CRIANDO RESPONSÁVEIS ===")
        responsaveis = criar_responsaveis(db, alunos)
        
        # Criar notas
        print("\n=== CRIANDO NOTAS ===")
        notas = criar_notas(db, alunos)
        
        print("\n=== SEED CONCLUÍDO ===")
        print(f"Total de usuários: {db.query(User).count()}")
        print(f"Total de turmas: {db.query(Turma).count()}")
        print(f"Total de alunos: {db.query(Aluno).count()}")
        print(f"Alunos ativos: {db.query(Aluno).filter(Aluno.status == 'ativo').count()}")
        print(f"Alunos inativos: {db.query(Aluno).filter(Aluno.status == 'inativo').count()}")
        print(f"Total de responsáveis: {db.query(Responsavel).count()}")
        print(f"Total de notas: {db.query(Nota).count()}")
        
        # Estatísticas por turma
        print("\n=== ESTATÍSTICAS POR TURMA ===")
        for turma in turmas:
            alunos_count = db.query(Aluno).filter(Aluno.turma_id == turma.id).count()
            ocupacao = (alunos_count / turma.capacidade) * 100 if turma.capacidade > 0 else 0
            print(f"{turma.nome}: {alunos_count}/{turma.capacidade} alunos ({ocupacao:.1f}% ocupação)")
        
        # Estatísticas de notas
        print("\n=== ESTATÍSTICAS DE NOTAS ===")
        for disciplina in ["Matemática", "Português", "Ciências"]:
            media = db.query(Nota).filter(Nota.disciplina == disciplina).count()
            if media > 0:
                notas_disciplina = db.query(Nota.nota).filter(Nota.disciplina == disciplina).all()
                media_notas = sum([n[0] for n in notas_disciplina]) / len(notas_disciplina)
                print(f"{disciplina}: {media} notas, média {media_notas:.1f}")
            
    except Exception as e:
        print(f"Erro durante o seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()