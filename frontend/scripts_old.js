// === CONFIGURAÇÕES ===
const API_BASE_URL = 'http://localhost:8000';
const ITEMS_PER_PAGE = 10;

// === ESTADO GLOBAL ===
let currentState = {
    alunos: [],
    turmas: [],
    filteredAlunos: [],
    currentPage: 1,
    totalPages: 1,
    sortBy: 'nome',
    sortOrder: 'asc',
    filters: {
        search: '',
        turma_id: '',
        status: ''
    },
    editingAluno: null
};

// === UTILITÁRIOS ===
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
};

const calculateAge = (birthDate) => {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    return age;
};

// === TOAST SYSTEM ===
const showToast = (message, type = 'info', title = null) => {
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const titleText = title || {
        'success': 'Sucesso',
        'error': 'Erro',
        'warning': 'Atenção',
        'info': 'Informação'
    }[type];
    
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${titleText}</span>
            <button type="button" class="toast-close" aria-label="Fechar notificação">×</button>
        </div>
        <div class="toast-message">${message}</div>
    `;
    
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    toastContainer.appendChild(toast);
    
    // Auto-remove após 5 segundos
    setTimeout(() => removeToast(toast), 5000);
    
    // Anunciar para screen readers
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
};

const removeToast = (toast) => {
    if (toast && toast.parentNode) {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            toast.parentNode.removeChild(toast);
        }, 300);
    }
};

// === API CALLS ===
const api = {
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData.detail || 
                               errorData.message || 
                               `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(message);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            
            // Mapeamento de erros HTTP
            const errorMessages = {
                400: 'Dados inválidos enviados',
                401: 'Não autorizado',
                404: 'Recurso não encontrado',
                422: 'Dados de validação inválidos',
                500: 'Erro interno do servidor'
            };
            
            if (error.message.includes('fetch')) {
                showToast('Erro de conexão. Verifique se o servidor está rodando.', 'error');
            } else {
                showToast(error.message, 'error');
            }
            
            throw error;
        }
    },
    
    // Alunos
    async getAlunos(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/alunos${queryString ? '?' + queryString : ''}`);
    },
    
    async createAluno(data) {
        return this.request('/alunos', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async updateAluno(id, data) {
        return this.request(`/alunos/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async deleteAluno(id) {
        return this.request(`/alunos/${id}`, {
            method: 'DELETE'
        });
    },
    
    // Turmas
    async getTurmas() {
        return this.request('/turmas');
    },
    
    async createTurma(data) {
        return this.request('/turmas', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // Matrículas
    async matricularAluno(data) {
        return this.request('/matriculas', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // Estatísticas
    async getEstatisticas() {
        return this.request('/estatisticas');
    }
};

// === VALIDAÇÕES CLIENT-SIDE ===
const validators = {
    nome: (value) => {
        if (!value || value.trim().length < 3) {
            return 'Nome deve ter pelo menos 3 caracteres';
        }
        if (value.trim().length > 80) {
            return 'Nome deve ter no máximo 80 caracteres';
        }
        return null;
    },
    
    data_nascimento: (value) => {
        if (!value) {
            return 'Data de nascimento é obrigatória';
        }
        
        const date = new Date(value);
        const today = new Date();
        const minDate = new Date(today.getFullYear() - 5, today.getMonth(), today.getDate());
        
        if (date > minDate) {
            return 'Aluno deve ter pelo menos 5 anos';
        }
        
        return null;
    },
    
    email: (value) => {
        if (value && value.trim()) {
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(value.trim())) {
                return 'Email inválido';
            }
        }
        return null;
    },
    
    status: (value) => {
        if (!['ativo', 'inativo'].includes(value)) {
            return 'Status deve ser "ativo" ou "inativo"';
        }
        return null;
    }
};

const validateForm = (formData, requiredFields = []) => {
    const errors = {};
    
    for (const [field, value] of Object.entries(formData)) {
        if (validators[field]) {
            const error = validators[field](value);
            if (error) {
                errors[field] = error;
            }
        }
    }
    
    // Verificar campos obrigatórios
    requiredFields.forEach(field => {
        if (!formData[field] || formData[field].toString().trim() === '') {
            errors[field] = `${field.replace('_', ' ')} é obrigatório`;
        }
    });
    
    return errors;
};

// === RENDERIZAÇÃO ===
const renderAlunos = () => {
    const container = document.getElementById('alunosList');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    
    // Aplicar filtros
    applyFilters();
    
    // Calcular paginação
    const startIndex = (currentState.currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const paginatedAlunos = currentState.filteredAlunos.slice(startIndex, endIndex);
    
    // Atualizar informações de resultado
    const resultsCount = document.getElementById('resultsCount');
    resultsCount.textContent = `${currentState.filteredAlunos.length} aluno(s) encontrado(s)`;
    
    // Mostrar/ocultar estados
    loadingState.style.display = 'none';
    
    if (currentState.filteredAlunos.length === 0) {
        emptyState.style.display = 'block';
        container.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        container.style.display = 'grid';
        
        container.innerHTML = paginatedAlunos.map(aluno => `
            <div class="aluno-card" data-aluno-id="${aluno.id}">
                <div class="aluno-header">
                    <h3 class="aluno-nome">${aluno.nome}</h3>
                    <span class="aluno-status ${aluno.status}">${aluno.status}</span>
                </div>
                
                <div class="aluno-info">
                    <div class="aluno-info-item">
                        <span class="aluno-info-label">Idade:</span>
                        <span class="aluno-info-value">${aluno.idade} anos</span>
                    </div>
                    <div class="aluno-info-item">
                        <span class="aluno-info-label">Data de Nasc:</span>
                        <span class="aluno-info-value">${formatDate(aluno.data_nascimento)}</span>
                    </div>
                    <div class="aluno-info-item">
                        <span class="aluno-info-label">Email:</span>
                        <span class="aluno-info-value">${aluno.email || 'Não informado'}</span>
                    </div>
                    <div class="aluno-info-item">
                        <span class="aluno-info-label">Turma:</span>
                        <span class="aluno-info-value">${aluno.turma_nome || 'Sem turma'}</span>
                    </div>
                </div>
                
                <div class="aluno-actions">
                    <button type="button" class="btn btn-secondary btn-edit" data-aluno-id="${aluno.id}">
                        Editar
                    </button>
                    ${!aluno.turma_id ? `
                        <button type="button" class="btn btn-primary btn-matricula" data-aluno-id="${aluno.id}">
                            Matricular
                        </button>
                    ` : ''}
                    <button type="button" class="btn btn-danger btn-delete" data-aluno-id="${aluno.id}">
                        Excluir
                    </button>
                </div>
            </div>
        `).join('');
        
        // Adicionar event listeners para os botões
        addAlunoActionListeners();
    }
    
    // Atualizar paginação
    updatePagination();
};

const renderTurmas = () => {
    const container = document.getElementById('turmasList');
    
    if (currentState.turmas.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma turma cadastrada</p>';
        return;
    }
    
    container.innerHTML = currentState.turmas.map(turma => {
        const ocupacao = turma.capacidade > 0 ? (turma.alunos_count / turma.capacidade) * 100 : 0;
        
        return `
            <div class="turma-card">
                <div class="turma-header">
                    <h3 class="turma-nome">${turma.nome}</h3>
                    <span class="turma-ocupacao">${turma.alunos_count}/${turma.capacidade}</span>
                </div>
                
                <div class="ocupacao-bar">
                    <div class="ocupacao-fill" style="width: ${ocupacao}%"></div>
                </div>
                
                <p class="text-muted">Ocupação: ${ocupacao.toFixed(1)}%</p>
            </div>
        `;
    }).join('');
};

const updateStatistics = async () => {
    try {
        const stats = await api.getEstatisticas();
        
        document.getElementById('totalAlunos').textContent = stats.total_alunos;
        document.getElementById('alunosAtivos').textContent = stats.alunos_ativos;
        document.getElementById('totalTurmas').textContent = stats.total_turmas;
        
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
};

// === FILTROS E ORDENAÇÃO ===
const applyFilters = () => {
    let filtered = [...currentState.alunos];
    
    // Filtro de busca por nome
    if (currentState.filters.search) {
        const searchTerm = currentState.filters.search.toLowerCase();
        filtered = filtered.filter(aluno => 
            aluno.nome.toLowerCase().includes(searchTerm)
        );
    }
    
    // Filtro por turma
    if (currentState.filters.turma_id) {
        filtered = filtered.filter(aluno => 
            aluno.turma_id == currentState.filters.turma_id
        );
    }
    
    // Filtro por status
    if (currentState.filters.status) {
        filtered = filtered.filter(aluno => 
            aluno.status === currentState.filters.status
        );
    }
    
    // Aplicar ordenação
    filtered.sort((a, b) => {
        let aValue, bValue;
        
        switch (currentState.sortBy) {
            case 'nome':
                aValue = a.nome.toLowerCase();
                bValue = b.nome.toLowerCase();
                break;
            case 'idade':
                aValue = a.idade;
                bValue = b.idade;
                break;
            case 'status':
                aValue = a.status;
                bValue = b.status;
                break;
            case 'turma':
                aValue = a.turma_nome || '';
                bValue = b.turma_nome || '';
                break;
            default:
                aValue = a.nome.toLowerCase();
                bValue = b.nome.toLowerCase();
        }
        
        if (aValue < bValue) return currentState.sortOrder === 'asc' ? -1 : 1;
        if (aValue > bValue) return currentState.sortOrder === 'asc' ? 1 : -1;
        return 0;
    });
    
    currentState.filteredAlunos = filtered;
    
    // Recalcular paginação
    currentState.totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
    if (currentState.currentPage > currentState.totalPages) {
        currentState.currentPage = Math.max(1, currentState.totalPages);
    }
    
    // Salvar ordenação no localStorage
    localStorage.setItem('gestaoEscolar_sort', JSON.stringify({
        sortBy: currentState.sortBy,
        sortOrder: currentState.sortOrder
    }));
};

const updatePagination = () => {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    prevBtn.disabled = currentState.currentPage <= 1;
    nextBtn.disabled = currentState.currentPage >= currentState.totalPages;
    
    pageInfo.textContent = `Página ${currentState.currentPage} de ${currentState.totalPages}`;
};

// === MODAIS ===
const openModal = (modalId) => {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    
    // Focar no primeiro elemento focável
    const firstFocusable = modal.querySelector('input, select, textarea, button');
    if (firstFocusable) {
        setTimeout(() => firstFocusable.focus(), 100);
    }
    
    // Trap focus no modal
    trapFocus(modal);
};

const closeModal = (modalId) => {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    
    // Limpar formulários
    const form = modal.querySelector('form');
    if (form) {
        form.reset();
        clearFormErrors(form);
    }
    
    currentState.editingAluno = null;
};

const trapFocus = (element) => {
    const focusableElements = element.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    const handleTabKey = (e) => {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    lastFocusable.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    firstFocusable.focus();
                    e.preventDefault();
                }
            }
        }
        
        if (e.key === 'Escape') {
            const modal = e.target.closest('.modal');
            if (modal) {
                const modalId = modal.id;
                closeModal(modalId);
            }
        }
    };
    
    element.addEventListener('keydown', handleTabKey);
};

// === FORMULÁRIOS ===
const showFormErrors = (form, errors) => {
    clearFormErrors(form);
    
    Object.keys(errors).forEach(field => {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('error');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'form-error';
            errorDiv.textContent = errors[field];
            errorDiv.setAttribute('role', 'alert');
            
            input.parentNode.appendChild(errorDiv);
        }
    });
};

const clearFormErrors = (form) => {
    form.querySelectorAll('.error').forEach(input => {
        input.classList.remove('error');
    });
    
    form.querySelectorAll('.form-error').forEach(error => {
        error.remove();
    });
};

// === EVENT LISTENERS ===
const addAlunoActionListeners = () => {
    // Botões de editar
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alunoId = parseInt(e.target.dataset.alunoId);
            const aluno = currentState.alunos.find(a => a.id === alunoId);
            if (aluno) {
                openEditAlunoModal(aluno);
            }
        });
    });
    
    // Botões de excluir
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alunoId = parseInt(e.target.dataset.alunoId);
            const aluno = currentState.alunos.find(a => a.id === alunoId);
            if (aluno) {
                if (confirm(`Tem certeza que deseja excluir o aluno "${aluno.nome}"?`)) {
                    deleteAluno(alunoId);
                }
            }
        });
    });
    
    // Botões de matrícula
    document.querySelectorAll('.btn-matricula').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alunoId = parseInt(e.target.dataset.alunoId);
            const aluno = currentState.alunos.find(a => a.id === alunoId);
            if (aluno) {
                openMatriculaModal(aluno);
            }
        });
    });
};

const openEditAlunoModal = (aluno) => {
    currentState.editingAluno = aluno;
    
    // Preencher formulário
    document.getElementById('alunoNome').value = aluno.nome;
    document.getElementById('alunoDataNascimento').value = aluno.data_nascimento;
    document.getElementById('alunoEmail').value = aluno.email || '';
    document.getElementById('alunoStatus').value = aluno.status;
    document.getElementById('alunoTurma').value = aluno.turma_id || '';
    
    // Alterar título do modal
    document.getElementById('modalAlunoTitle').textContent = 'Editar Aluno';
    
    openModal('modalNovoAluno');
};

const openMatriculaModal = (aluno) => {
    document.getElementById('matriculaAluno').value = aluno.nome;
    document.getElementById('formMatricula').dataset.alunoId = aluno.id;
    openModal('modalMatricula');
};

// === CRUD OPERATIONS ===
const loadAlunos = async () => {
    try {
        document.getElementById('loadingState').style.display = 'block';
        
        const params = {};
        if (currentState.filters.search) params.search = currentState.filters.search;
        if (currentState.filters.turma_id) params.turma_id = currentState.filters.turma_id;
        if (currentState.filters.status) params.status = currentState.filters.status;
        
        currentState.alunos = await api.getAlunos(params);
        renderAlunos();
        
    } catch (error) {
        console.error('Erro ao carregar alunos:', error);
        document.getElementById('loadingState').style.display = 'none';
    }
};

const loadTurmas = async () => {
    try {
        currentState.turmas = await api.getTurmas();
        
        // Atualizar selects de turma
        const turmaSelects = document.querySelectorAll('#filterTurma, #alunoTurma, #matriculaTurma');
        turmaSelects.forEach(select => {
            const isFilter = select.id === 'filterTurma';
            const currentValue = select.value;
            
            // Preservar opções padrão
            const defaultOptions = Array.from(select.querySelectorAll('option[value=""]'));
            select.innerHTML = '';
            defaultOptions.forEach(option => select.appendChild(option));
            
            // Adicionar turmas
            currentState.turmas.forEach(turma => {
                const option = document.createElement('option');
                option.value = turma.id;
                
                if (isFilter) {
                    option.textContent = `${turma.nome} (${turma.alunos_count}/${turma.capacidade})`;
                } else {
                    option.textContent = `${turma.nome} (${turma.alunos_count}/${turma.capacidade} alunos)`;
                    
                    // Desabilitar turmas cheias
                    if (turma.alunos_count >= turma.capacidade) {
                        option.disabled = true;
                        option.textContent += ' - LOTADA';
                    }
                }
                
                select.appendChild(option);
            });
            
            // Restaurar valor selecionado
            select.value = currentValue;
        });
        
        renderTurmas();
        
    } catch (error) {
        console.error('Erro ao carregar turmas:', error);
    }
};

const createAluno = async (formData) => {
    try {
        const errors = validateForm(formData, ['nome', 'data_nascimento', 'status']);
        if (Object.keys(errors).length > 0) {
            showFormErrors(document.getElementById('formNovoAluno'), errors);
            return;
        }
        
        await api.createAluno(formData);
        
        showToast('Aluno cadastrado com sucesso!', 'success');
        closeModal('modalNovoAluno');
        
        // Recarregar dados
        await Promise.all([loadAlunos(), loadTurmas(), updateStatistics()]);
        
    } catch (error) {
        console.error('Erro ao criar aluno:', error);
    }
};

const updateAluno = async (id, formData) => {
    try {
        const errors = validateForm(formData, ['nome', 'data_nascimento', 'status']);
        if (Object.keys(errors).length > 0) {
            showFormErrors(document.getElementById('formNovoAluno'), errors);
            return;
        }
        
        await api.updateAluno(id, formData);
        
        showToast('Aluno atualizado com sucesso!', 'success');
        closeModal('modalNovoAluno');
        
        // Recarregar dados
        await Promise.all([loadAlunos(), loadTurmas(), updateStatistics()]);
        
    } catch (error) {
        console.error('Erro ao atualizar aluno:', error);
    }
};

const deleteAluno = async (id) => {
    try {
        await api.deleteAluno(id);
        
        showToast('Aluno excluído com sucesso!', 'success');
        
        // Recarregar dados
        await Promise.all([loadAlunos(), loadTurmas(), updateStatistics()]);
        
    } catch (error) {
        console.error('Erro ao excluir aluno:', error);
    }
};

const createTurma = async (formData) => {
    try {
        if (!formData.nome || formData.nome.trim().length < 2) {
            showFormErrors(document.getElementById('formNovaTurma'), {
                nome: 'Nome da turma deve ter pelo menos 2 caracteres'
            });
            return;
        }
        
        if (!formData.capacidade || formData.capacidade < 1) {
            showFormErrors(document.getElementById('formNovaTurma'), {
                capacidade: 'Capacidade deve ser maior que zero'
            });
            return;
        }
        
        await api.createTurma(formData);
        
        showToast('Turma criada com sucesso!', 'success');
        closeModal('modalNovaTurma');
        
        // Recarregar dados
        await Promise.all([loadTurmas(), updateStatistics()]);
        
    } catch (error) {
        console.error('Erro ao criar turma:', error);
    }
};

const matricularAluno = async (alunoId, turmaId) => {
    try {
        const matriculaData = {
            aluno_id: parseInt(alunoId),
            turma_id: parseInt(turmaId)
        };
        
        const result = await api.matricularAluno(matriculaData);
        
        showToast(result.message, 'success');
        closeModal('modalMatricula');
        
        // Recarregar dados
        await Promise.all([loadAlunos(), loadTurmas(), updateStatistics()]);
        
    } catch (error) {
        console.error('Erro ao matricular aluno:', error);
    }
};

// === EXPORT FUNCTIONS ===
const exportToCSV = () => {
    if (currentState.filteredAlunos.length === 0) {
        showToast('Nenhum aluno para exportar', 'warning');
        return;
    }
    
    const headers = ['ID', 'Nome', 'Idade', 'Data de Nascimento', 'Email', 'Status', 'Turma'];
    const rows = currentState.filteredAlunos.map(aluno => [
        aluno.id,
        `"${aluno.nome}"`,
        aluno.idade,
        aluno.data_nascimento,
        `"${aluno.email || ''}"`,
        aluno.status,
        `"${aluno.turma_nome || ''}"`
    ]);
    
    const csvContent = [headers, ...rows]
        .map(row => row.join(','))
        .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `alunos_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    showToast(`${currentState.filteredAlunos.length} alunos exportados para CSV`, 'success');
};

const exportToJSON = () => {
    if (currentState.filteredAlunos.length === 0) {
        showToast('Nenhum aluno para exportar', 'warning');
        return;
    }
    
    const exportData = {
        exported_at: new Date().toISOString(),
        total_records: currentState.filteredAlunos.length,
        filters_applied: currentState.filters,
        alunos: currentState.filteredAlunos
    };
    
    const jsonContent = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `alunos_${new Date().toISOString().split('T')[0]}.json`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    showToast(`${currentState.filteredAlunos.length} alunos exportados para JSON`, 'success');
};

// === INICIALIZAÇÃO ===
const initializeApp = async () => {
    // Restaurar ordenação do localStorage
    const savedSort = localStorage.getItem('gestaoEscolar_sort');
    if (savedSort) {
        try {
            const { sortBy, sortOrder } = JSON.parse(savedSort);
            currentState.sortBy = sortBy;
            currentState.sortOrder = sortOrder;
            
            document.getElementById('sortBy').value = sortBy;
            document.getElementById('sortOrder').textContent = sortOrder === 'asc' ? '↑ ASC' : '↓ DESC';
            document.getElementById('sortOrder').setAttribute('aria-pressed', sortOrder === 'desc');
        } catch (e) {
            console.error('Erro ao restaurar ordenação:', e);
        }
    }
    
    // Carregar dados iniciais
    await Promise.all([
        loadAlunos(),
        loadTurmas(),
        updateStatistics()
    ]);
    
    // Event Listeners
    
    // Busca com debounce
    const searchInput = document.getElementById('searchInput');
    const debouncedSearch = debounce((value) => {
        currentState.filters.search = value;
        currentState.currentPage = 1;
        renderAlunos();
    }, 300);
    
    searchInput.addEventListener('input', (e) => {
        debouncedSearch(e.target.value);
    });
    
    // Filtros
    document.getElementById('filterTurma').addEventListener('change', (e) => {
        currentState.filters.turma_id = e.target.value;
        currentState.currentPage = 1;
        renderAlunos();
    });
    
    document.getElementById('filterStatus').addEventListener('change', (e) => {
        currentState.filters.status = e.target.value;
        currentState.currentPage = 1;
        renderAlunos();
    });
    
    document.getElementById('clearFilters').addEventListener('click', () => {
        currentState.filters = { search: '', turma_id: '', status: '' };
        currentState.currentPage = 1;
        
        document.getElementById('searchInput').value = '';
        document.getElementById('filterTurma').value = '';
        document.getElementById('filterStatus').value = '';
        
        renderAlunos();
    });
    
    // Ordenação
    document.getElementById('sortBy').addEventListener('change', (e) => {
        currentState.sortBy = e.target.value;
        renderAlunos();
    });
    
    document.getElementById('sortOrder').addEventListener('click', () => {
        currentState.sortOrder = currentState.sortOrder === 'asc' ? 'desc' : 'asc';
        const btn = document.getElementById('sortOrder');
        btn.textContent = currentState.sortOrder === 'asc' ? '↑ ASC' : '↓ DESC';
        btn.setAttribute('aria-pressed', currentState.sortOrder === 'desc');
        renderAlunos();
    });
    
    // Paginação
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentState.currentPage > 1) {
            currentState.currentPage--;
            renderAlunos();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentState.currentPage < currentState.totalPages) {
            currentState.currentPage++;
            renderAlunos();
        }
    });
    
    // Tabs
    document.getElementById('alunosTab').addEventListener('click', () => {
        document.getElementById('alunosTab').classList.add('active');
        document.getElementById('turmasTab').classList.remove('active');
        document.getElementById('alunosTab').setAttribute('aria-selected', 'true');
        document.getElementById('turmasTab').setAttribute('aria-selected', 'false');
        
        document.getElementById('alunos-panel').classList.add('active');
        document.getElementById('turmas-panel').classList.remove('active');
        document.getElementById('alunos-panel').style.display = 'block';
        document.getElementById('turmas-panel').style.display = 'none';
    });
    
    document.getElementById('turmasTab').addEventListener('click', () => {
        document.getElementById('turmasTab').classList.add('active');
        document.getElementById('alunosTab').classList.remove('active');
        document.getElementById('turmasTab').setAttribute('aria-selected', 'true');
        document.getElementById('alunosTab').setAttribute('aria-selected', 'false');
        
        document.getElementById('turmas-panel').classList.add('active');
        document.getElementById('alunos-panel').classList.remove('active');
        document.getElementById('turmas-panel').style.display = 'block';
        document.getElementById('alunos-panel').style.display = 'none';
    });
    
    // Botões de modal
    document.getElementById('novoAlunoBtn').addEventListener('click', () => {
        currentState.editingAluno = null;
        document.getElementById('modalAlunoTitle').textContent = 'Novo Aluno';
        openModal('modalNovoAluno');
    });
    
    document.getElementById('addFirstAlunoBtn').addEventListener('click', () => {
        currentState.editingAluno = null;
        document.getElementById('modalAlunoTitle').textContent = 'Novo Aluno';
        openModal('modalNovoAluno');
    });
    
    document.getElementById('novaTurmaBtn').addEventListener('click', () => {
        openModal('modalNovaTurma');
    });
    
    // Fechar modais
    document.querySelectorAll('.modal-close, #cancelarAluno, #cancelarTurma, #cancelarMatricula').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Fechar modal clicando no backdrop
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Formulários
    document.getElementById('formNovoAluno').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            nome: formData.get('nome'),
            data_nascimento: formData.get('data_nascimento'),
            email: formData.get('email') || null,
            status: formData.get('status'),
            turma_id: formData.get('turma_id') ? parseInt(formData.get('turma_id')) : null
        };
        
        if (currentState.editingAluno) {
            await updateAluno(currentState.editingAluno.id, data);
        } else {
            await createAluno(data);
        }
    });
    
    document.getElementById('formNovaTurma').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            nome: formData.get('nome'),
            capacidade: parseInt(formData.get('capacidade'))
        };
        
        await createTurma(data);
    });
    
    document.getElementById('formMatricula').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const alunoId = e.target.dataset.alunoId;
        const turmaId = formData.get('turma_id');
        
        if (!turmaId) {
            showToast('Selecione uma turma', 'error');
            return;
        }
        
        await matricularAluno(alunoId, turmaId);
    });
    
    // Export
    document.getElementById('exportCsvBtn').addEventListener('click', exportToCSV);
    document.getElementById('exportJsonBtn').addEventListener('click', exportToJSON);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Alt+N para novo aluno
        if (e.altKey && e.key === 'n') {
            e.preventDefault();
            document.getElementById('novoAlunoBtn').click();
        }
        
        // Esc para fechar modais
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
    
    console.log('Sistema de Gestão Escolar inicializado com sucesso!');
    showToast('Sistema carregado com sucesso!', 'success');
};

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initializeApp);