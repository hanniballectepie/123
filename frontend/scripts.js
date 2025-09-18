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
    editingAluno: null,
    currentUser: null,
    isAuthenticated: false,
    currentAlunoDetalhes: null
};

// === AUTENTICAÇÃO ===
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.userMeta = JSON.parse(localStorage.getItem('userMeta') || '{}');
    }

    async login(credentials) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erro ao fazer login');
            }

            const data = await response.json();
            this.setAuth(data.access_token, data.user);
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erro ao criar conta');
            }

            const data = await response.json();
            this.setAuth(data.access_token, data.user);
            return data;
        } catch (error) {
            console.error('Register error:', error);
            throw error;
        }
    }

    setAuth(token, user) {
        this.token = token;
        this.userMeta = user;
        localStorage.setItem('authToken', token);
        localStorage.setItem('userMeta', JSON.stringify(user));
        currentState.currentUser = user;
        currentState.isAuthenticated = true;
    }

    logout() {
        this.token = null;
        this.userMeta = {};
        localStorage.removeItem('authToken');
        localStorage.removeItem('userMeta');
        currentState.currentUser = null;
        currentState.isAuthenticated = false;
    }

    isLoggedIn() {
        return !!this.token;
    }

    getAuthHeaders() {
        return this.token ? {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }

    async getCurrentUser() {
        if (!this.token) return null;
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    return null;
                }
                throw new Error('Erro ao obter dados do usuário');
            }

            const user = await response.json();
            this.userMeta = user;
            localStorage.setItem('userMeta', JSON.stringify(user));
            currentState.currentUser = user;
            return user;
        } catch (error) {
            console.error('Get current user error:', error);
            return null;
        }
    }
}

const auth = new AuthManager();

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

const formatEndereco = (aluno) => {
    const partes = [];
    if (aluno.endereco_rua) partes.push(aluno.endereco_rua);
    if (aluno.endereco_numero) partes.push(aluno.endereco_numero);
    if (aluno.endereco_complemento) partes.push(aluno.endereco_complemento);
    
    let endereco = partes.join(', ');
    
    if (aluno.endereco_bairro) endereco += `\n${aluno.endereco_bairro}`;
    if (aluno.endereco_cidade && aluno.endereco_estado) {
        endereco += `\n${aluno.endereco_cidade} - ${aluno.endereco_estado}`;
    }
    if (aluno.endereco_cep) endereco += `\nCEP: ${aluno.endereco_cep}`;
    
    return endereco || 'Não informado';
};

const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
};

// === TOAST SYSTEM ===
const showToast = (message, type = 'info', duration = 5000) => {
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
    
    const iconMap = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${iconMap[type] || iconMap.info}</span>
            <span class="toast-message">${message}</span>
            <button type="button" class="toast-close" aria-label="Fechar notificação">×</button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove
    const timeoutId = setTimeout(() => {
        removeToast(toast);
    }, duration);
    
    // Close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        clearTimeout(timeoutId);
        removeToast(toast);
    });
    
    // Animate in
    requestAnimationFrame(() => {
        toast.classList.add('toast-show');
    });
};

const removeToast = (toast) => {
    toast.classList.add('toast-hide');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
};

// === API CALLS ===
const apiCall = async (endpoint, options = {}) => {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: auth.getAuthHeaders(),
            ...options
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            if (response.status === 401) {
                auth.logout();
                showLoginScreen();
                throw new Error('Sessão expirada. Faça login novamente.');
            }
            
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erro HTTP ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
};

// === MODAL MANAGEMENT ===
const openModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus primeiro input
        const firstInput = modal.querySelector('input, select, textarea, button');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Trap focus
        trapFocus(modal);
    }
};

const closeModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        
        // Clear forms
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => form.reset());
        
        // Clear errors
        const errors = modal.querySelectorAll('.error-message');
        errors.forEach(error => error.style.display = 'none');
    }
};

const trapFocus = (modal) => {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    lastElement.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastElement) {
                    firstElement.focus();
                    e.preventDefault();
                }
            }
        }
        
        if (e.key === 'Escape') {
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) closeBtn.click();
        }
    };

    modal.addEventListener('keydown', handleTabKey);
};

// === CONTROLE DE TELAS ===
const showLoginScreen = () => {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('appMain').style.display = 'none';
    currentState.isAuthenticated = false;
};

const showMainApp = async () => {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appMain').style.display = 'block';
    currentState.isAuthenticated = true;
    
    // Carregar dados do usuário
    await auth.getCurrentUser();
    updateUserInterface();
    
    // Carregar dados iniciais
    await Promise.all([
        loadTurmas(),
        loadAlunos(),
        loadEstatisticas()
    ]);
};

const updateUserInterface = () => {
    const user = currentState.currentUser;
    if (!user) return;

    // Atualizar avatar
    const userAvatarImg = document.getElementById('userAvatarImg');
    const userInitials = document.getElementById('userInitials');
    const avatarFallback = userInitials.parentElement;

    if (user.profile_photo) {
        userAvatarImg.src = `${API_BASE_URL}${user.profile_photo}`;
        userAvatarImg.style.display = 'block';
        avatarFallback.style.display = 'none';
    } else {
        userAvatarImg.style.display = 'none';
        avatarFallback.style.display = 'flex';
        userInitials.textContent = getInitials(user.display_name || user.username);
    }

    // Atualizar informações do dropdown
    document.getElementById('userDisplayName').textContent = user.display_name || user.username;
    document.getElementById('userRole').textContent = user.role;

    // Aplicar tema
    if (user.theme_preference === 'light') {
        document.body.setAttribute('data-theme', 'light');
    }

    // Mostrar/ocultar botões baseado no role
    const adminOnlyElements = document.querySelectorAll('[data-admin-only]');
    adminOnlyElements.forEach(el => {
        el.style.display = user.role === 'admin' ? '' : 'none';
    });
};

// === AUTHENTICATION HANDLERS ===
const setupAuthenticationHandlers = () => {
    // Login tabs
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginPanel = document.getElementById('login-panel');
    const registerPanel = document.getElementById('register-panel');

    loginTab.addEventListener('click', () => {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginTab.setAttribute('aria-selected', 'true');
        registerTab.setAttribute('aria-selected', 'false');
        loginPanel.style.display = 'block';
        registerPanel.style.display = 'none';
        loginPanel.classList.add('active');
        registerPanel.classList.remove('active');
    });

    registerTab.addEventListener('click', () => {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerTab.setAttribute('aria-selected', 'true');
        loginTab.setAttribute('aria-selected', 'false');
        registerPanel.style.display = 'block';
        loginPanel.style.display = 'none';
        registerPanel.classList.add('active');
        loginPanel.classList.remove('active');
    });

    // Login form
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(loginForm);
        const credentials = {
            username_or_email: formData.get('username_or_email'),
            password: formData.get('password')
        };

        const errorDiv = document.getElementById('loginError');
        errorDiv.style.display = 'none';

        try {
            await auth.login(credentials);
            showToast('Login realizado com sucesso!', 'success');
            await showMainApp();
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });

    // Register form
    const registerForm = document.getElementById('registerForm');
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(registerForm);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            confirm_password: formData.get('confirm_password')
        };

        const errorDiv = document.getElementById('registerError');
        errorDiv.style.display = 'none';

        try {
            await auth.register(userData);
            showToast('Conta criada com sucesso!', 'success');
            await showMainApp();
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });

    // User menu
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    userMenuBtn.addEventListener('click', () => {
        const isExpanded = userMenuBtn.getAttribute('aria-expanded') === 'true';
        userMenuBtn.setAttribute('aria-expanded', !isExpanded);
        userDropdown.style.display = isExpanded ? 'none' : 'block';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
            userMenuBtn.setAttribute('aria-expanded', 'false');
            userDropdown.style.display = 'none';
        }
    });

    // Perfil button
    document.getElementById('perfilBtn').addEventListener('click', () => {
        userDropdown.style.display = 'none';
        openPerfilModal();
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', () => {
        auth.logout();
        showToast('Logout realizado com sucesso!', 'info');
        showLoginScreen();
    });
};

// === PERFIL MODAL ===
const openPerfilModal = async () => {
    openModal('modalPerfil');
    
    const user = currentState.currentUser;
    if (!user) return;

    // Preencher dados
    document.getElementById('perfilDisplayName').value = user.display_name || '';
    document.getElementById('perfilEmail').value = user.email || '';
    document.getElementById('perfilTheme').value = user.theme_preference || 'dark';
    document.getElementById('perfilLocale').value = user.locale || 'pt-BR';
    document.getElementById('perfilTimezone').value = user.timezone || 'America/Sao_Paulo';
    document.getElementById('perfilNotifications').checked = user.notifications_email;

    // Foto atual
    const currentPhoto = document.getElementById('currentProfilePhoto');
    const photoInitials = document.getElementById('photoInitials');
    const photoPlaceholder = photoInitials.parentElement;

    if (user.profile_photo) {
        currentPhoto.src = `${API_BASE_URL}${user.profile_photo}`;
        currentPhoto.style.display = 'block';
        photoPlaceholder.style.display = 'none';
    } else {
        currentPhoto.style.display = 'none';
        photoPlaceholder.style.display = 'flex';
        photoInitials.textContent = getInitials(user.display_name || user.username);
    }
};

const setupPerfilHandlers = () => {
    // Tabs do perfil
    const tabs = ['dadosPerfilTab', 'senhaPerfilTab', 'fotoPerfilTab'];
    const panels = ['dadosPerfilPanel', 'senhaPerfilPanel', 'fotoPerfilPanel'];

    tabs.forEach((tabId, index) => {
        document.getElementById(tabId).addEventListener('click', () => {
            // Remove active de todas as tabs
            tabs.forEach(t => document.getElementById(t).classList.remove('active'));
            panels.forEach(p => {
                const panel = document.getElementById(p);
                panel.style.display = 'none';
                panel.classList.remove('active');
            });

            // Ativa a tab clicada
            document.getElementById(tabId).classList.add('active');
            const activePanel = document.getElementById(panels[index]);
            activePanel.style.display = 'block';
            activePanel.classList.add('active');
        });
    });

    // Form dados perfil
    document.getElementById('formDadosPerfil').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const updateData = {
            display_name: formData.get('display_name'),
            theme_preference: formData.get('theme_preference'),
            locale: formData.get('locale'),
            timezone: formData.get('timezone'),
            notifications_email: formData.get('notifications_email') === 'on'
        };

        try {
            const updatedUser = await apiCall('/auth/me', {
                method: 'PUT',
                body: JSON.stringify(updateData)
            });

            currentState.currentUser = updatedUser;
            localStorage.setItem('userMeta', JSON.stringify(updatedUser));
            
            updateUserInterface();
            showToast('Perfil atualizado com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    // Form alterar senha
    document.getElementById('formAlterarSenha').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const passwordData = {
            current_password: formData.get('current_password'),
            new_password: formData.get('new_password')
        };

        try {
            await apiCall('/auth/me/password', {
                method: 'PATCH',
                body: JSON.stringify(passwordData)
            });

            e.target.reset();
            showToast('Senha alterada com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    // Form foto perfil
    document.getElementById('formFotoPerfil').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const file = formData.get('file');

        if (!file || file.size === 0) {
            showToast('Selecione uma foto', 'warning');
            return;
        }

        try {
            const result = await fetch(`${API_BASE_URL}/auth/me/photo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${auth.token}`
                },
                body: formData
            });

            if (!result.ok) {
                const error = await result.json();
                throw new Error(error.detail || 'Erro ao fazer upload');
            }

            const response = await result.json();
            
            // Atualizar usuário atual
            currentState.currentUser.profile_photo = response.photo_url;
            localStorage.setItem('userMeta', JSON.stringify(currentState.currentUser));
            
            updateUserInterface();
            
            // Atualizar foto no modal
            const currentPhoto = document.getElementById('currentProfilePhoto');
            const photoPlaceholder = document.getElementById('photoInitials').parentElement;
            currentPhoto.src = `${API_BASE_URL}${response.photo_url}`;
            currentPhoto.style.display = 'block';
            photoPlaceholder.style.display = 'none';
            
            e.target.reset();
            showToast('Foto atualizada com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
};

// === DATA LOADING ===
const loadAlunos = async () => {
    try {
        showLoading(true);
        const params = new URLSearchParams(currentState.filters);
        const alunos = await apiCall(`/alunos?${params}`);
        
        currentState.alunos = alunos;
        applyFiltersAndSort();
        renderAlunos();
        updateResultsCount();
    } catch (error) {
        showToast(error.message, 'error');
        console.error('Erro ao carregar alunos:', error);
    } finally {
        showLoading(false);
    }
};

const loadTurmas = async () => {
    try {
        const turmas = await apiCall('/turmas');
        currentState.turmas = turmas;
        populateTurmaSelects();
    } catch (error) {
        showToast(error.message, 'error');
        console.error('Erro ao carregar turmas:', error);
    }
};

const loadEstatisticas = async () => {
    try {
        const stats = await apiCall('/estatisticas');
        updateStatsDisplay(stats);
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
};

const loadAlunoDetalhes = async (alunoId) => {
    try {
        const aluno = await apiCall(`/alunos/${alunoId}`);
        currentState.currentAlunoDetalhes = aluno;
        return aluno;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
};

// === RENDER FUNCTIONS ===
const renderAlunos = () => {
    const container = document.getElementById('alunosList');
    const emptyState = document.getElementById('emptyState');
    
    if (currentState.filteredAlunos.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    const startIndex = (currentState.currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const pageAlunos = currentState.filteredAlunos.slice(startIndex, endIndex);
    
    container.innerHTML = pageAlunos.map(aluno => `
        <div class="aluno-card" data-id="${aluno.id}">
            <button type="button" class="btn-detalhes" onclick="openDetalhesModal(${aluno.id})" title="Ver detalhes">
                👁️ Detalhes
            </button>
            
            <div class="aluno-header">
                <h3 class="aluno-nome">${aluno.nome}</h3>
                <span class="aluno-status ${aluno.status}">${aluno.status}</span>
            </div>
            
            <div class="aluno-info">
                <div class="info-item">
                    <span class="info-label">Idade:</span>
                    <span class="info-value">${aluno.idade} anos</span>
                </div>
                
                <div class="info-item">
                    <span class="info-label">Turma:</span>
                    <span class="info-value">${aluno.turma_nome || 'Sem turma'}</span>
                </div>
                
                ${aluno.telefone ? `
                <div class="info-item">
                    <span class="info-label">Telefone:</span>
                    <span class="info-value">${aluno.telefone}</span>
                </div>
                ` : ''}
                
                ${aluno.email ? `
                <div class="info-item">
                    <span class="info-label">Email:</span>
                    <span class="info-value">${aluno.email}</span>
                </div>
                ` : ''}
            </div>
            
            <div class="aluno-actions">
                <button type="button" class="btn btn-secondary btn-sm" onclick="editarAluno(${aluno.id})" title="Editar aluno">
                    ✏️ Editar
                </button>
                
                ${aluno.status === 'inativo' ? `
                <button type="button" class="btn btn-success btn-sm" onclick="matricularAluno(${aluno.id})" title="Matricular aluno">
                    📝 Matricular
                </button>
                ` : ''}
                
                ${currentState.currentUser?.role === 'admin' ? `
                <button type="button" class="btn btn-danger btn-sm" onclick="confirmarExclusao(${aluno.id}, '${aluno.nome}')" title="Excluir aluno">
                    🗑️ Excluir
                </button>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    updatePagination();
};

const updateStatsDisplay = (stats) => {
    document.getElementById('totalAlunos').textContent = stats.total_alunos;
    document.getElementById('alunosAtivos').textContent = stats.alunos_ativos;
    document.getElementById('totalTurmas').textContent = stats.total_turmas;
};

const populateTurmaSelects = () => {
    const selects = document.querySelectorAll('select[name="turma_id"], #filterTurma, #matriculaTurma');
    
    selects.forEach(select => {
        const currentValue = select.value;
        const isFilter = select.id === 'filterTurma';
        
        select.innerHTML = isFilter ? '<option value="">Todas as turmas</option>' : '<option value="">Selecione uma turma</option>';
        
        currentState.turmas.forEach(turma => {
            const option = document.createElement('option');
            option.value = turma.id;
            option.textContent = `${turma.nome} (${turma.alunos_count}/${turma.capacidade})`;
            select.appendChild(option);
        });
        
        if (currentValue) {
            select.value = currentValue;
        }
    });
};

// === DETALHES DO ALUNO ===
const openDetalhesModal = async (alunoId) => {
    try {
        const aluno = await loadAlunoDetalhes(alunoId);
        
        // Preencher dados gerais
        document.getElementById('detalheNome').textContent = aluno.nome;
        document.getElementById('detalheStatus').textContent = aluno.status;
        document.getElementById('detalheStatus').className = `status-badge ${aluno.status}`;
        document.getElementById('detalheDataNascimento').textContent = formatDate(aluno.data_nascimento);
        document.getElementById('detalheIdade').textContent = `${aluno.idade} anos`;
        document.getElementById('detalheEmail').textContent = aluno.email || 'Não informado';
        document.getElementById('detalheTurma').textContent = aluno.turma_nome || 'Sem turma';
        document.getElementById('detalheTelefone').textContent = aluno.telefone || 'Não informado';
        document.getElementById('detalheTelefoneEmergencia').textContent = aluno.telefone_emergencia || 'Não informado';
        document.getElementById('detalheEndereco').textContent = formatEndereco(aluno);
        document.getElementById('detalheObservacoes').textContent = aluno.observacoes || 'Nenhuma observação';
        
        // Renderizar responsáveis
        renderResponsaveis(aluno.responsaveis);
        
        // Renderizar notas
        renderNotas(aluno.notas);
        
        // Foto do aluno
        const currentPhoto = document.getElementById('currentAlunoPhoto');
        const photoPlaceholder = document.getElementById('alunoPhotoInitials').parentElement;
        
        if (aluno.foto_url) {
            currentPhoto.src = `${API_BASE_URL}${aluno.foto_url}`;
            currentPhoto.style.display = 'block';
            photoPlaceholder.style.display = 'none';
        } else {
            currentPhoto.style.display = 'none';
            photoPlaceholder.style.display = 'flex';
            document.getElementById('alunoPhotoInitials').textContent = getInitials(aluno.nome);
        }
        
        openModal('modalDetalhesAluno');
    } catch (error) {
        showToast('Erro ao carregar detalhes do aluno', 'error');
    }
};

const renderResponsaveis = (responsaveis) => {
    const container = document.getElementById('responsaveisList');
    
    if (!responsaveis || responsaveis.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum responsável cadastrado</p>';
        return;
    }
    
    container.innerHTML = responsaveis.map(resp => `
        <div class="responsavel-card">
            <div class="responsavel-header">
                <div>
                    <div class="responsavel-nome">${resp.nome}</div>
                    <div class="responsavel-parentesco">${resp.parentesco}</div>
                </div>
                <div class="responsavel-actions">
                    <button type="button" class="btn btn-secondary btn-icon-sm" onclick="editarResponsavel(${resp.id})" title="Editar">
                        ✏️
                    </button>
                    <button type="button" class="btn btn-danger btn-icon-sm" onclick="excluirResponsavel(${resp.id})" title="Excluir">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="responsavel-info">
                ${resp.telefone ? `<div>📞 ${resp.telefone}</div>` : ''}
                ${resp.email ? `<div>✉️ ${resp.email}</div>` : ''}
                ${resp.documento ? `<div>📄 ${resp.documento}</div>` : ''}
            </div>
        </div>
    `).join('');
};

const renderNotas = (notas) => {
    const tbody = document.getElementById('notasTableBody');
    const mediaElement = document.getElementById('mediaGeral');
    
    if (!notas || notas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhuma nota cadastrada</td></tr>';
        mediaElement.textContent = '-';
        return;
    }
    
    // Calcular média
    const media = notas.reduce((sum, nota) => sum + nota.nota, 0) / notas.length;
    mediaElement.textContent = media.toFixed(1);
    mediaElement.className = media < 6 ? 'text-warning' : 'text-success';
    
    // Mapear etapas para nomes legíveis
    const etapaNames = {
        '1B': '1º Bimestre',
        '2B': '2º Bimestre', 
        '3B': '3º Bimestre',
        '4B': '4º Bimestre',
        'FINAL': 'Final'
    };
    
    tbody.innerHTML = notas.map(nota => `
        <tr>
            <td>${nota.disciplina}</td>
            <td><span class="nota-etapa">${etapaNames[nota.etapa] || nota.etapa}</span></td>
            <td><span class="nota-valor ${nota.nota < 6 ? 'nota-baixa' : 'nota-boa'}">${nota.nota.toFixed(1)}</span></td>
            <td><span class="nota-data">${formatDate(nota.data_registro)}</span></td>
            <td>
                <div class="table-actions">
                    <button type="button" class="btn btn-secondary btn-icon-sm" onclick="editarNota(${nota.id})" title="Editar">
                        ✏️
                    </button>
                    ${currentState.currentUser?.role === 'admin' ? `
                    <button type="button" class="btn btn-danger btn-icon-sm" onclick="excluirNota(${nota.id})" title="Excluir">
                        🗑️
                    </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
};

// === RESPONSÁVEIS ===
const adicionarResponsavel = () => {
    if (!currentState.currentAlunoDetalhes) return;
    
    document.getElementById('modalResponsavelTitle').textContent = 'Adicionar Responsável';
    document.getElementById('formResponsavel').onsubmit = async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const responsavelData = {
            nome: formData.get('nome'),
            parentesco: formData.get('parentesco'),
            telefone: formData.get('telefone') || null,
            email: formData.get('email') || null,
            documento: formData.get('documento') || null
        };

        try {
            await apiCall(`/alunos/${currentState.currentAlunoDetalhes.id}/responsaveis`, {
                method: 'POST',
                body: JSON.stringify(responsavelData)
            });

            closeModal('modalResponsavel');
            await openDetalhesModal(currentState.currentAlunoDetalhes.id);
            showToast('Responsável adicionado com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    };
    
    openModal('modalResponsavel');
};

const editarResponsavel = async (responsavelId) => {
    const responsavel = currentState.currentAlunoDetalhes.responsaveis.find(r => r.id === responsavelId);
    if (!responsavel) return;
    
    document.getElementById('modalResponsavelTitle').textContent = 'Editar Responsável';
    
    // Preencher form
    document.getElementById('responsavelNome').value = responsavel.nome;
    document.getElementById('responsavelParentesco').value = responsavel.parentesco;
    document.getElementById('responsavelTelefone').value = responsavel.telefone || '';
    document.getElementById('responsavelEmail').value = responsavel.email || '';
    document.getElementById('responsavelDocumento').value = responsavel.documento || '';
    
    document.getElementById('formResponsavel').onsubmit = async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const responsavelData = {
            nome: formData.get('nome'),
            parentesco: formData.get('parentesco'),
            telefone: formData.get('telefone') || null,
            email: formData.get('email') || null,
            documento: formData.get('documento') || null
        };

        try {
            await apiCall(`/responsaveis/${responsavelId}`, {
                method: 'PUT',
                body: JSON.stringify(responsavelData)
            });

            closeModal('modalResponsavel');
            await openDetalhesModal(currentState.currentAlunoDetalhes.id);
            showToast('Responsável atualizado com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    };
    
    openModal('modalResponsavel');
};

const excluirResponsavel = async (responsavelId) => {
    if (!confirm('Tem certeza que deseja excluir este responsável?')) return;
    
    try {
        await apiCall(`/responsaveis/${responsavelId}`, { method: 'DELETE' });
        await openDetalhesModal(currentState.currentAlunoDetalhes.id);
        showToast('Responsável excluído com sucesso!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// === NOTAS ===
const adicionarNota = () => {
    if (!currentState.currentAlunoDetalhes) return;
    
    document.getElementById('modalNotaTitle').textContent = 'Adicionar Nota';
    document.getElementById('formNota').reset();
    
    document.getElementById('formNota').onsubmit = async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const notaData = {
            disciplina: formData.get('disciplina'),
            etapa: formData.get('etapa'),
            nota: parseFloat(formData.get('nota'))
        };

        try {
            await apiCall(`/alunos/${currentState.currentAlunoDetalhes.id}/notas`, {
                method: 'POST',
                body: JSON.stringify(notaData)
            });

            closeModal('modalNota');
            await openDetalhesModal(currentState.currentAlunoDetalhes.id);
            showToast('Nota adicionada com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    };
    
    openModal('modalNota');
};

const editarNota = async (notaId) => {
    const nota = currentState.currentAlunoDetalhes.notas.find(n => n.id === notaId);
    if (!nota) return;
    
    document.getElementById('modalNotaTitle').textContent = 'Editar Nota';
    
    // Preencher form
    document.getElementById('notaDisciplina').value = nota.disciplina;
    document.getElementById('notaEtapa').value = nota.etapa;
    document.getElementById('notaNota').value = nota.nota;
    
    document.getElementById('formNota').onsubmit = async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const notaData = {
            disciplina: formData.get('disciplina'),
            etapa: formData.get('etapa'),
            nota: parseFloat(formData.get('nota'))
        };

        try {
            await apiCall(`/notas/${notaId}`, {
                method: 'PUT',
                body: JSON.stringify(notaData)
            });

            closeModal('modalNota');
            await openDetalhesModal(currentState.currentAlunoDetalhes.id);
            showToast('Nota atualizada com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    };
    
    openModal('modalNota');
};

const excluirNota = async (notaId) => {
    if (!confirm('Tem certeza que deseja excluir esta nota?')) return;
    
    try {
        await apiCall(`/notas/${notaId}`, { method: 'DELETE' });
        await openDetalhesModal(currentState.currentAlunoDetalhes.id);
        showToast('Nota excluída com sucesso!', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// === FOTO DO ALUNO ===
const setupFotoAlunoHandler = () => {
    document.getElementById('formFotoAluno').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!currentState.currentAlunoDetalhes) return;
        
        const formData = new FormData(e.target);
        const file = formData.get('file');

        if (!file || file.size === 0) {
            showToast('Selecione uma foto', 'warning');
            return;
        }

        try {
            const result = await fetch(`${API_BASE_URL}/alunos/${currentState.currentAlunoDetalhes.id}/foto`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${auth.token}`
                },
                body: formData
            });

            if (!result.ok) {
                const error = await result.json();
                throw new Error(error.detail || 'Erro ao fazer upload');
            }

            const response = await result.json();
            
            // Atualizar foto no modal
            const currentPhoto = document.getElementById('currentAlunoPhoto');
            const photoPlaceholder = document.getElementById('alunoPhotoInitials').parentElement;
            currentPhoto.src = `${API_BASE_URL}${response.foto_url}`;
            currentPhoto.style.display = 'block';
            photoPlaceholder.style.display = 'none';
            
            // Atualizar dados do aluno
            currentState.currentAlunoDetalhes.foto_url = response.foto_url;
            
            e.target.reset();
            showToast('Foto atualizada com sucesso!', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
};

// === EXISTING FUNCTIONS (updated) ===
const applyFiltersAndSort = () => {
    let filtered = [...currentState.alunos];
    
    // Apply filters
    if (currentState.filters.search) {
        const search = currentState.filters.search.toLowerCase();
        filtered = filtered.filter(aluno => 
            aluno.nome.toLowerCase().includes(search)
        );
    }
    
    if (currentState.filters.turma_id) {
        filtered = filtered.filter(aluno => 
            aluno.turma_id == currentState.filters.turma_id
        );
    }
    
    if (currentState.filters.status) {
        filtered = filtered.filter(aluno => 
            aluno.status === currentState.filters.status
        );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
        let aValue = a[currentState.sortBy];
        let bValue = b[currentState.sortBy];
        
        if (currentState.sortBy === 'turma') {
            aValue = a.turma_nome || '';
            bValue = b.turma_nome || '';
        }
        
        if (typeof aValue === 'string') {
            aValue = aValue.toLowerCase();
            bValue = bValue.toLowerCase();
        }
        
        let comparison = 0;
        if (aValue > bValue) comparison = 1;
        if (aValue < bValue) comparison = -1;
        
        return currentState.sortOrder === 'desc' ? -comparison : comparison;
    });
    
    currentState.filteredAlunos = filtered;
    currentState.totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
    currentState.currentPage = 1;
};

const updatePagination = () => {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    prevBtn.disabled = currentState.currentPage <= 1;
    nextBtn.disabled = currentState.currentPage >= currentState.totalPages;
    
    pageInfo.textContent = `Página ${currentState.currentPage} de ${currentState.totalPages}`;
};

const updateResultsCount = () => {
    const count = currentState.filteredAlunos.length;
    const plural = count === 1 ? 'aluno encontrado' : 'alunos encontrados';
    document.getElementById('resultsCount').textContent = `${count} ${plural}`;
};

const showLoading = (show) => {
    const loadingState = document.getElementById('loadingState');
    const alunosList = document.getElementById('alunosList');
    
    if (show) {
        loadingState.style.display = 'flex';
        alunosList.style.display = 'none';
    } else {
        loadingState.style.display = 'none';
        alunosList.style.display = 'grid';
    }
};

// === SETUP HANDLERS ===
const setupEventHandlers = () => {
    // Search
    const searchInput = document.getElementById('searchInput');
    const debouncedSearch = debounce((value) => {
        currentState.filters.search = value;
        applyFiltersAndSort();
        renderAlunos();
        updateResultsCount();
    }, 300);
    
    searchInput.addEventListener('input', (e) => {
        debouncedSearch(e.target.value);
    });
    
    // Filters
    document.getElementById('filterTurma').addEventListener('change', (e) => {
        currentState.filters.turma_id = e.target.value;
        applyFiltersAndSort();
        renderAlunos();
        updateResultsCount();
    });
    
    document.getElementById('filterStatus').addEventListener('change', (e) => {
        currentState.filters.status = e.target.value;
        applyFiltersAndSort();
        renderAlunos();
        updateResultsCount();
    });
    
    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', () => {
        currentState.filters = { search: '', turma_id: '', status: '' };
        searchInput.value = '';
        document.getElementById('filterTurma').value = '';
        document.getElementById('filterStatus').value = '';
        applyFiltersAndSort();
        renderAlunos();
        updateResultsCount();
    });
    
    // Sort
    document.getElementById('sortBy').addEventListener('change', (e) => {
        currentState.sortBy = e.target.value;
        applyFiltersAndSort();
        renderAlunos();
    });
    
    document.getElementById('sortOrder').addEventListener('click', (e) => {
        currentState.sortOrder = currentState.sortOrder === 'asc' ? 'desc' : 'asc';
        e.target.textContent = currentState.sortOrder === 'asc' ? '↑ ASC' : '↓ DESC';
        e.target.setAttribute('aria-pressed', currentState.sortOrder === 'desc');
        applyFiltersAndSort();
        renderAlunos();
    });
    
    // Pagination
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
    
    // Modal handlers
    document.querySelectorAll('.modal-close, .modal-backdrop').forEach(element => {
        element.addEventListener('click', (e) => {
            if (e.target === element) {
                const modal = element.closest('.modal');
                if (modal) {
                    closeModal(modal.id);
                }
            }
        });
    });
    
    // Tab handlers nos detalhes
    const detalheTabs = ['dadosGeraisTab', 'responsaveisTab', 'notasTab', 'fotoAlunoTab'];
    const detalhePanels = ['dadosGeraisPanel', 'responsaveisPanel', 'notasPanel', 'fotoAlunoPanel'];

    detalheTabs.forEach((tabId, index) => {
        document.getElementById(tabId).addEventListener('click', () => {
            // Remove active de todas as tabs
            detalheTabs.forEach(t => document.getElementById(t).classList.remove('active'));
            detalhePanels.forEach(p => {
                const panel = document.getElementById(p);
                panel.style.display = 'none';
                panel.classList.remove('active');
            });

            // Ativa a tab clicada
            document.getElementById(tabId).classList.add('active');
            const activePanel = document.getElementById(detalhePanels[index]);
            activePanel.style.display = 'block';
            activePanel.classList.add('active');
        });
    });
    
    // Buttons nos detalhes
    document.getElementById('adicionarResponsavelBtn').addEventListener('click', adicionarResponsavel);
    document.getElementById('adicionarNotaBtn').addEventListener('click', adicionarNota);
    
    // Cancel buttons
    document.getElementById('cancelarResponsavel').addEventListener('click', () => closeModal('modalResponsavel'));
    document.getElementById('cancelarNota').addEventListener('click', () => closeModal('modalNota'));
    
    // Other existing handlers...
    // (Manter os handlers existentes para novo aluno, nova turma, etc.)
};

// === GLOBAL FUNCTIONS (for onclick handlers) ===
window.openDetalhesModal = openDetalhesModal;
window.editarResponsavel = editarResponsavel;
window.excluirResponsavel = excluirResponsavel;
window.editarNota = editarNota;
window.excluirNota = excluirNota;

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (auth.isLoggedIn()) {
        const user = await auth.getCurrentUser();
        if (user) {
            await showMainApp();
        } else {
            showLoginScreen();
        }
    } else {
        showLoginScreen();
    }
    
    // Setup all handlers
    setupAuthenticationHandlers();
    setupPerfilHandlers();
    setupFotoAlunoHandler();
    setupEventHandlers();
});

// === EXPORT FOR EXISTING FUNCTIONS ===
// Keep existing functions working...
const editarAluno = (id) => {
    // Existing implementation
    console.log('Editar aluno:', id);
};

const matricularAluno = (id) => {
    // Existing implementation  
    console.log('Matricular aluno:', id);
};

const confirmarExclusao = (id, nome) => {
    // Existing implementation
    console.log('Confirmar exclusão:', id, nome);
};

window.editarAluno = editarAluno;
window.matricularAluno = matricularAluno;
window.confirmarExclusao = confirmarExclusao;
