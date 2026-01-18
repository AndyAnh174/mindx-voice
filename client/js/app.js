/**
 * Main App - Page Controllers and Initialization
 */

const App = {
    // Current state
    state: {
        personas: [],
        selectedPersona: null,
        currentStep: 1,
        customPrompt: '',
        currentSession: null,
        messages: [],
    },

    /**
     * Render a template into the app container
     */
    render(templateId) {
        const template = document.getElementById(templateId);
        const app = document.getElementById('app');
        app.innerHTML = '';
        app.appendChild(template.content.cloneNode(true));
    },

    /**
     * Hide loading screen
     */
    hideLoading() {
        const loading = document.getElementById('loading-screen');
        if (loading) {
            loading.classList.add('fade-out');
            setTimeout(() => loading.remove(), 300);
        }
    },

    /**
     * Get difficulty badge class
     */
    getDifficultyBadge(level) {
        const classes = {
            easy: 'badge-easy',
            medium: 'badge-medium',
            hard: 'badge-hard',
            expert: 'badge-expert',
        };
        return classes[level] || 'badge-secondary';
    },

    /**
     * Get difficulty label
     */
    getDifficultyLabel(level) {
        const labels = {
            easy: 'Dễ',
            medium: 'Trung bình',
            hard: 'Khó',
            expert: 'Chuyên gia',
        };
        return labels[level] || level;
    },

    /**
     * Get personality label
     */
    getPersonalityLabel(type) {
        const labels = {
            friendly: 'Thân thiện',
            strict: 'Nghiêm khắc',
            anxious: 'Lo lắng',
            demanding: 'Đòi hỏi cao',
            supportive: 'Hỗ trợ',
            skeptical: 'Hoài nghi',
            busy: 'Bận rộn',
        };
        return labels[type] || type;
    },

    /**
     * Format date
     */
    formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('vi-VN');
    },

    /**
     * Format time
     */
    formatTime(date) {
        return new Date(date).toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
        });
    },

    // ==================== LOGIN PAGE ====================

    async showLoginPage() {
        this.render('login-template');
        this.hideLoading();

        const form = document.getElementById('login-form');
        const btn = document.getElementById('login-btn');
        const errorDiv = document.getElementById('login-error');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Show loading
            btn.disabled = true;
            btn.querySelector('.spinner-border').classList.remove('d-none');
            errorDiv.classList.add('d-none');

            try {
                await Auth.login(email, password);
                Router.navigate('/dashboard');
            } catch (error) {
                errorDiv.textContent = error.detail || 'Email hoặc mật khẩu không đúng';
                errorDiv.classList.remove('d-none');
            } finally {
                btn.disabled = false;
                btn.querySelector('.spinner-border').classList.add('d-none');
            }
        });
    },

    // ==================== DASHBOARD PAGE ====================

    async showDashboardPage() {
        this.render('dashboard-template');
        this.hideLoading();

        const user = Auth.getUser();

        // Set user info
        document.getElementById('user-name').textContent = user?.username || user?.email || 'User';
        document.getElementById('welcome-name').textContent = user?.username || 'bạn';

        // Load data
        this.loadPersonas();
        this.loadSessions();

        // Event listeners
        document.getElementById('logout-btn').addEventListener('click', async () => {
            await Auth.logout();
            Router.navigate('/login');
        });

        document.getElementById('start-session-btn').addEventListener('click', () => {
            Router.navigate('/scenario-setup');
        });
    },

    async loadPersonas() {
        const grid = document.getElementById('personas-grid');

        try {
            const data = await API.get('/personas/');
            const personas = data.results || data;
            this.state.personas = personas;

            if (personas.length === 0) {
                grid.innerHTML = `
                    <div class="col-12 text-center py-4">
                        <i class="bi bi-people fs-1 text-secondary"></i>
                        <p class="text-secondary mt-2">Chưa có persona nào</p>
                    </div>
                `;
                return;
            }

            grid.innerHTML = personas.map(p => `
                <div class="col-12 col-sm-6 col-lg-4">
                    <div class="card persona-card h-100" data-id="${p.id}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div class="avatar-sm">
                                    <i class="bi bi-person-fill"></i>
                                </div>
                                <span class="badge ${this.getDifficultyBadge(p.difficulty_level)}">
                                    ${this.getDifficultyLabel(p.difficulty_level)}
                                </span>
                            </div>
                            <h6 class="fw-semibold mb-2">${p.name}</h6>
                            <p class="small text-muted mb-2" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                ${p.description}
                            </p>
                            <span class="small text-primary">
                                <i class="bi bi-stars me-1"></i>${this.getPersonalityLabel(p.personality_type)}
                            </span>
                        </div>
                    </div>
                </div>
            `).join('');

            // Add click handlers
            grid.querySelectorAll('.persona-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = card.dataset.id;
                    const persona = personas.find(p => p.id === id);
                    this.state.selectedPersona = persona;
                    Router.navigate('/scenario-setup');
                });
            });

        } catch (error) {
            grid.innerHTML = `
                <div class="col-12 text-center py-4">
                    <i class="bi bi-exclamation-circle fs-1 text-danger"></i>
                    <p class="text-danger mt-2">Không thể tải dữ liệu</p>
                </div>
            `;
        }
    },

    async loadSessions() {
        const list = document.getElementById('sessions-list');

        try {
            const data = await API.get('/sessions/');
            const sessions = (data.results || data).slice(0, 5);

            if (sessions.length === 0) {
                list.innerHTML = `
                    <div class="list-group-item bg-transparent text-center py-4">
                        <i class="bi bi-chat-square-text fs-3 text-secondary"></i>
                        <p class="text-secondary mb-0 mt-2">Chưa có phiên luyện tập nào</p>
                    </div>
                `;
                return;
            }

            // Update stats
            const completed = sessions.filter(s => s.status === 'completed');
            const avgScore = completed.length > 0
                ? completed.reduce((acc, s) => acc + (s.rating || 0), 0) / completed.length
                : 0;

            document.getElementById('stat-total').textContent = sessions.length;
            document.getElementById('stat-completed').textContent = completed.length;
            document.getElementById('stat-score').textContent = Math.round(avgScore * 10) / 10;

            list.innerHTML = sessions.map(s => `
                <div class="list-group-item session-item" data-id="${s.id}">
                    <div class="d-flex align-items-center justify-content-between">
                        <div class="d-flex align-items-center gap-3">
                            <span class="session-status ${s.status}"></span>
                            <div>
                                <p class="mb-0 fw-medium">${s.persona?.name || 'Phiên luyện tập'}</p>
                                <small class="text-muted">${this.formatDate(s.started_at)}</small>
                            </div>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            ${s.rating ? `<span class="text-primary fw-semibold">${s.rating}/10</span>` : ''}
                            <i class="bi bi-chevron-right text-secondary"></i>
                        </div>
                    </div>
                </div>
            `).join('');

            // Click handlers
            list.querySelectorAll('.session-item').forEach(item => {
                item.addEventListener('click', () => {
                    Router.navigate(`/session/${item.dataset.id}`);
                });
            });

        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    },

    // ==================== SCENARIO SETUP PAGE ====================

    async showScenarioSetupPage() {
        this.render('scenario-setup-template');
        this.hideLoading();

        // Reset state
        this.state.currentStep = 1;
        this.state.customPrompt = '';

        // Load personas if not already loaded
        if (this.state.personas.length === 0) {
            try {
                const data = await API.get('/personas/');
                this.state.personas = data.results || data;
            } catch (e) {
                console.error('Failed to load personas:', e);
            }
        }

        this.renderPersonaSelection();
        this.updateStepUI();

        // Event listeners
        document.getElementById('back-btn').addEventListener('click', () => {
            if (this.state.currentStep > 1) {
                this.state.currentStep--;
                this.updateStepUI();
            } else {
                Router.navigate('/dashboard');
            }
        });

        document.getElementById('prev-step-btn').addEventListener('click', () => {
            if (this.state.currentStep > 1) {
                this.state.currentStep--;
                this.updateStepUI();
            }
        });

        document.getElementById('next-step-btn').addEventListener('click', () => {
            if (this.state.currentStep < 3) {
                if (this.state.currentStep === 2) {
                    this.state.customPrompt = document.getElementById('custom-prompt')?.value || '';
                }
                this.state.currentStep++;
                this.updateStepUI();
            }
        });

        document.getElementById('start-chat-btn')?.addEventListener('click', () => {
            this.startSession();
        });
    },

    renderPersonaSelection() {
        const grid = document.getElementById('persona-selection');
        const personas = this.state.personas;

        if (personas.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                </div>
            `;
            return;
        }

        grid.innerHTML = personas.map(p => `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card persona-card h-100 position-relative ${this.state.selectedPersona?.id === p.id ? 'selected' : ''}" data-id="${p.id}">
                    <div class="selected-check"><i class="bi bi-check"></i></div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="avatar-sm">
                                <i class="bi bi-person-fill"></i>
                            </div>
                            <span class="badge ${this.getDifficultyBadge(p.difficulty_level)}">
                                ${this.getDifficultyLabel(p.difficulty_level)}
                            </span>
                        </div>
                        <h6 class="fw-semibold mb-2">${p.name}</h6>
                        <p class="small text-muted mb-2" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            ${p.description}
                        </p>
                        <span class="small text-primary">
                            <i class="bi bi-stars me-1"></i>${this.getPersonalityLabel(p.personality_type)}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');

        // Click handlers
        grid.querySelectorAll('.persona-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                this.state.selectedPersona = personas.find(p => p.id === id);

                // Update UI
                grid.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');

                // Enable next button
                document.getElementById('next-step-btn').disabled = false;
            });
        });
    },

    updateStepUI() {
        const step = this.state.currentStep;
        const titles = ['Chọn Persona', 'Tùy chỉnh', 'Xác nhận'];

        // Update title
        document.getElementById('step-title').textContent = titles[step - 1];

        // Update step indicators
        document.querySelectorAll('.step-indicator .step').forEach((el, i) => {
            el.classList.toggle('active', i < step);
        });

        // Show/hide step content
        for (let i = 1; i <= 3; i++) {
            const content = document.getElementById(`step-${i}`);
            content?.classList.toggle('d-none', i !== step);
        }

        // Update navigation buttons
        const prevBtn = document.getElementById('prev-step-btn');
        const nextBtn = document.getElementById('next-step-btn');
        const stepNav = document.getElementById('step-nav');

        prevBtn.disabled = step === 1;
        nextBtn.disabled = step === 1 && !this.state.selectedPersona;

        // Hide nav on step 3
        stepNav.classList.toggle('d-none', step === 3);

        // Update confirmation page
        if (step === 3) {
            this.updateConfirmation();
        }
    },

    updateConfirmation() {
        const p = this.state.selectedPersona;
        if (!p) return;

        document.getElementById('confirm-persona-name').textContent = p.name;
        document.getElementById('confirm-persona-difficulty').textContent = this.getDifficultyLabel(p.difficulty_level);
        document.getElementById('confirm-persona-difficulty').className = `badge ${this.getDifficultyBadge(p.difficulty_level)}`;
        document.getElementById('confirm-persona-personality').textContent = this.getPersonalityLabel(p.personality_type);

        const promptSection = document.getElementById('confirm-prompt-section');
        const promptText = document.getElementById('confirm-prompt');

        if (this.state.customPrompt) {
            promptSection.classList.remove('d-none');
            promptText.textContent = this.state.customPrompt;
        } else {
            promptSection.classList.add('d-none');
        }
    },

    async startSession() {
        const btn = document.getElementById('start-chat-btn');
        btn.disabled = true;
        btn.querySelector('.spinner-border').classList.remove('d-none');

        try {
            const data = await API.post('/sessions/', {
                persona: this.state.selectedPersona.id,
                mode: 'chat',
                custom_prompt: this.state.customPrompt || undefined,
            });

            Router.navigate(`/session/${data.id}`);
        } catch (error) {
            console.error('Failed to create session:', error);
            alert('Không thể tạo phiên. Vui lòng thử lại.');
            btn.disabled = false;
            btn.querySelector('.spinner-border').classList.add('d-none');
        }
    },

    // ==================== CHAT PAGE ====================

    async showChatPage(params) {
        this.render('chat-template');
        this.hideLoading();

        const sessionId = params.id;
        this.state.messages = [];

        // Load session
        try {
            const session = await API.get(`/sessions/${sessionId}/`);
            this.state.currentSession = session;

            document.getElementById('chat-persona-name').textContent = session.persona?.name || 'Phiên luyện tập';
            document.getElementById('chat-welcome-text').textContent =
                `Hãy bắt đầu bằng cách gửi lời chào đến ${session.persona?.name || 'phụ huynh'}. Họ sẽ phản hồi theo tính cách đã được thiết lập.`;

            // Load existing messages
            const messagesData = await API.get(`/sessions/${sessionId}/messages/`);
            const messages = messagesData.results || messagesData || [];

            if (messages.length > 0) {
                document.getElementById('chat-welcome').remove();
                messages.filter(m => m.role !== 'system').forEach(m => {
                    this.addMessage(m.role, m.content, new Date(m.created_at));
                });
            }

        } catch (error) {
            console.error('Failed to load session:', error);
            alert('Không thể tải phiên');
            Router.navigate('/dashboard');
            return;
        }

        // Event listeners
        document.getElementById('chat-back-btn').addEventListener('click', () => {
            Router.navigate('/dashboard');
        });

        document.getElementById('end-session-btn').addEventListener('click', () => {
            this.endSession();
        });

        const form = document.getElementById('message-form');
        const input = document.getElementById('message-input');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });

        // Shift+Enter for new line, Enter to send
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Close error
        document.querySelector('#chat-error .btn-close')?.addEventListener('click', () => {
            document.getElementById('chat-error').classList.add('d-none');
        });
    },

    addMessage(role, content, timestamp = new Date()) {
        const list = document.getElementById('messages-list');
        const welcome = document.getElementById('chat-welcome');
        if (welcome) welcome.remove();

        const messageHtml = `
            <div class="message ${role}">
                <div class="message-avatar">
                    <i class="bi bi-${role === 'user' ? 'person-fill' : 'robot'}"></i>
                </div>
                <div class="message-bubble">
                    <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
                    <div class="message-time">${this.formatTime(timestamp)}</div>
                </div>
            </div>
        `;

        list.insertAdjacentHTML('beforeend', messageHtml);

        // Scroll to bottom
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    },

    addTypingIndicator() {
        const list = document.getElementById('messages-list');
        const html = `
            <div class="message assistant" id="typing-indicator">
                <div class="message-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        list.insertAdjacentHTML('beforeend', html);

        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    },

    removeTypingIndicator() {
        document.getElementById('typing-indicator')?.remove();
    },

    async sendMessage() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();

        if (!content || !this.state.currentSession) return;

        const sendBtn = document.getElementById('send-btn');
        const sendIcon = document.getElementById('send-icon');
        const sendSpinner = document.getElementById('send-spinner');

        // Disable input
        input.disabled = true;
        sendBtn.disabled = true;
        sendIcon.classList.add('d-none');
        sendSpinner.classList.remove('d-none');

        // Add user message
        this.addMessage('user', content);
        input.value = '';
        input.style.height = 'auto';

        // Show typing indicator
        this.addTypingIndicator();

        try {
            const response = await API.post(`/sessions/${this.state.currentSession.id}/add_message/`, {
                role: 'user',
                content: content,
                message_type: 'text',
            });

            this.removeTypingIndicator();

            // Add AI response if available
            if (response.assistant_message) {
                this.addMessage('assistant', response.assistant_message);
            }

        } catch (error) {
            console.error('Failed to send message:', error);
            this.removeTypingIndicator();

            const errorDiv = document.getElementById('chat-error');
            document.getElementById('chat-error-text').textContent = 'Không thể gửi tin nhắn. Vui lòng thử lại.';
            errorDiv.classList.remove('d-none');
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            sendIcon.classList.remove('d-none');
            sendSpinner.classList.add('d-none');
            input.focus();
        }
    },

    async endSession() {
        if (!confirm('Bạn có chắc muốn kết thúc phiên này?')) return;

        try {
            await API.post(`/sessions/${this.state.currentSession.id}/end/`, {});
            Router.navigate('/dashboard');
        } catch (error) {
            console.error('Failed to end session:', error);
        }
    },
};

// ==================== INITIALIZE APP ====================

// Setup routes
Router
    .on('/login', () => App.showLoginPage())
    .on('/dashboard', () => App.showDashboardPage())
    .on('/scenario-setup', () => App.showScenarioSetupPage())
    .on('/session/:id', (params) => App.showChatPage(params))
    .init();

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(err => {
            console.log('SW registration failed:', err);
        });
    });
}

// Make App available globally
window.App = App;
