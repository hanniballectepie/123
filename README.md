# Sistema de Gestão Escolar - Thales de Tarsis

![Versão](https://img.shields.io/badge/version-1.0.0-orange)
![Status](https://img.shields.io/badge/status-production-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📖 Resumo do Projeto

Sistema web completo de gestão escolar desenvolvido para demonstrar competências em desenvolvimento full-stack. O sistema possui tema **dark** com paleta de cores inspirada no design moderno, focando em alta acessibilidade e usabilidade.

### 🎯 Funcionalidades Principais

- **CRUD Completo de Alunos**: Cadastro, edição, listagem e exclusão
- **Gestão de Turmas**: Controle de capacidade e ocupação
- **Sistema de Matrículas**: Matricular alunos em turmas com validação de capacidade
- **Filtros Avançados**: Busca por nome, filtro por turma e status
- **Paginação**: 10 itens por página para melhor performance
- **Export de Dados**: Exportação em CSV e JSON dos dados filtrados
- **Estatísticas em Tempo Real**: Dashboard com métricas do sistema
- **Interface Acessível**: Navegação por teclado, screen readers, contrastes adequados

### 🎨 Design e Acessibilidade

- **Tema Dark**: Paleta escura profissional com acentos laranjas
- **Contraste 4.5:1**: Garantindo legibilidade para todos os usuários
- **Navegação por Teclado**: Suporte completo a atalhos e tab navigation
- **ARIA Labels**: Semântica correta para tecnologias assistivas
- **Responsive Design**: Funciona perfeitamente em desktop, tablet e mobile

## 🚀 Como Executar

### 📋 Pré-requisitos

- **Python 3.8+**
- **pip** (gerenciador de pacotes Python)
- **Navegador moderno** (Chrome, Firefox, Edge, Safari)

### ⚙️ Instalação e Execução

#### 1️⃣ Clone/Baixe o repositório
```bash
git clone <url-do-repositorio>
cd dw2-Thales-de-Tarsis-Escola
```

#### 2️⃣ Configure o Backend
```bash
# Navegue para a pasta do backend
cd backend

# Instale as dependências
pip install -r requirements.txt

# Execute o seed para popular o banco com dados de exemplo
python seed.py

# Inicie o servidor da API
uvicorn app:app --reload
```

O servidor estará rodando em: **http://localhost:8000**

#### 3️⃣ Configure o Frontend
```bash
# Em outro terminal, navegue para a pasta do frontend
cd frontend

# Opção 1: Usando Python (simples)
python -m http.server 3000

# Opção 2: Usando Node.js (se disponível)
npx http-server -p 3000

# Opção 3: Usando Live Server do VS Code
# Abra index.html e use a extensão Live Server
```

O frontend estará disponível em: **http://localhost:3000**

### 🧪 Executando Testes

Use o arquivo `tests.http` com Thunder Client (VS Code) ou Insomnia:

1. Abra o VS Code
2. Instale a extensão "Thunder Client"
3. Abra o arquivo `tests.http`
4. Execute os testes clicando em "Send Request"

## 📚 API Endpoints

### 👥 Alunos
- `GET /alunos` - Lista alunos com filtros opcionais
- `POST /alunos` - Cria novo aluno
- `PUT /alunos/{id}` - Atualiza aluno existente
- `DELETE /alunos/{id}` - Remove aluno

### 🏫 Turmas
- `GET /turmas` - Lista todas as turmas
- `POST /turmas` - Cria nova turma

### 📝 Matrículas
- `POST /matriculas` - Matricula aluno em turma

### 📊 Estatísticas
- `GET /estatisticas` - Retorna estatísticas do sistema

### Parâmetros de Consulta (Alunos)
- `search` - Busca por nome
- `turma_id` - Filtra por turma
- `status` - Filtra por status (ativo/inativo)

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para banco de dados
- **SQLite**: Banco de dados leve e portátil
- **Pydantic**: Validação de dados e serialização
- **Uvicorn**: Servidor ASGI de alta performance

### Frontend
- **HTML5**: Estrutura semântica e acessível
- **CSS3**: Styling moderno com CSS Grid e Flexbox
- **JavaScript (ES6+)**: Interatividade e comunicação com API
- **Fetch API**: Requisições HTTP assíncronas

### Desenvolvimento
- **VS Code**: Editor de código
- **Thunder Client**: Testes de API
- **Git**: Controle de versão

## 📱 Capturas de Tela

### 🖥️ Dashboard Principal
![Dashboard](https://via.placeholder.com/800x400/1b1b1b/ffa31a?text=Dashboard+Principal)
*Interface principal com listagem de alunos, filtros e estatísticas*

### 📋 Formulário de Cadastro
![Formulário](https://via.placeholder.com/600x400/292929/ffffff?text=Formulario+de+Cadastro)
*Modal para cadastro/edição de alunos com validação em tempo real*

### 📊 Gestão de Turmas
![Turmas](https://via.placeholder.com/800x300/1b1b1b/ffa31a?text=Gestao+de+Turmas)
*Visualização de turmas com indicadores de ocupação*

## 🔧 Estrutura do Projeto

```
dw2-Thales-de-Tarsis-Escola/
├── frontend/
│   ├── index.html          # Interface principal
│   ├── styles.css          # Estilos CSS com tema dark
│   └── scripts.js          # Lógica JavaScript
├── backend/
│   ├── app.py              # API FastAPI
│   ├── models.py           # Modelos SQLAlchemy
│   ├── database.py         # Configuração do banco
│   ├── seed.py             # População de dados
│   └── requirements.txt    # Dependências Python
├── tests.http              # Testes da API
├── README.md               # Documentação principal
├── REPORT.md               # Relatório técnico
└── ChatIA.md               # Histórico de prompts
```

## ⚡ Funcionalidades Especiais

### 🔍 Busca e Filtros
- Busca em tempo real por nome (com debounce)
- Filtro combinado por turma e status
- Ordenação por múltiplos campos
- Persistência da ordenação no localStorage

### 📄 Export de Dados
- **CSV**: Formato compatível com Excel
- **JSON**: Dados estruturados com metadados
- Export apenas dos dados filtrados/visíveis

### ♿ Acessibilidade
- Navegação completa por teclado
- Atalhos: Alt+N para novo aluno
- ARIA labels e roles apropriados
- Contraste mínimo de 4.5:1
- Suporte a screen readers

### 📱 Responsividade
- Layout adaptativo para diferentes telas
- Mobile-first approach
- Breakpoints: 480px, 768px, 1024px

## 🔒 Validações Implementadas

### Frontend (JavaScript)
- Nome: 3-80 caracteres
- Idade: Mínimo 5 anos
- Email: Regex de validação
- Status: Apenas "ativo" ou "inativo"

### Backend (FastAPI/Pydantic)
- Validação de tipos de dados
- Verificação de capacidade de turmas
- Validação de existência de recursos
- Tratamento de erros com códigos HTTP apropriados

## 🚀 Release Notes - v1.0.0

### ✨ Novas Funcionalidades
- Sistema completo de gestão de alunos e turmas
- Interface dark theme profissional
- Sistema de matrículas com validação de capacidade
- Export de dados em CSV e JSON
- Dashboard com estatísticas em tempo real

### 🔧 Melhorias
- Performance otimizada com paginação
- Validações client-side e server-side
- Toast notifications para feedback
- Navegação acessível por teclado

### 🛡️ Correções
- Tratamento robusto de erros de API
- Validação de formulários em tempo real
- Controle de estado consistente

## 📞 Suporte e Contato

- **Desenvolvedor**: Thales de Tarsis
- **Email**: thales@escola.com
- **GitHub**: [github.com/thales-tarsis](https://github.com)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

### 🎓 Sobre o Desenvolvedor

Sistema desenvolvido por **Thales de Tarsis** como demonstração de competências em desenvolvimento full-stack, focando em:

- ✅ Arquitetura limpa e organizada
- ✅ Código maintível e documentado
- ✅ Interface acessível e responsiva
- ✅ API RESTful robusta
- ✅ Boas práticas de desenvolvimento

---

**© 2024 Thales de Tarsis - Sistema de Gestão Escolar v1.0.0**