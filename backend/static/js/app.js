// Main application JavaScript

class ArticleMigrationApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentTab = 'dashboard';
        this.refreshInterval = null;

        console.log('🚀 ArticleApp初始化中...');
        console.log('📡 API基础URL:', this.apiBase);

        // 清除可能的失效URL缓存
        this.clearInvalidUrlCache();

        this.init();
    }

    clearInvalidUrlCache() {
        try {
            // 清除可能的无效缓存数据
            console.log('🧹 清理缓存数据...');

            // 清除可能的临时数据
            const keysToRemove = [];
            for (let key in localStorage) {
                const value = localStorage.getItem(key);
                if (value && (key.includes('temp_') || key.includes('cache_'))) {
                    keysToRemove.push(key);
                }
            }

            keysToRemove.forEach(key => {
                localStorage.removeItem(key);
                console.log('🗑️ 清除缓存项:', key);
            });

            console.log('✅ 缓存清理完成');
        } catch (error) {
            console.warn('⚠️ 清理缓存时出错:', error);
        }
    }

    setupNetworkMonitoring() {
        // 设置网络请求监控（用于调试）
        const originalFetch = window.fetch;
        let requestCount = 0;

        window.fetch = function(url, options) {
            requestCount++;
            console.log(`📡 网络请求 #${requestCount}:`, url);

            // 正常执行请求
            return originalFetch.call(this, url, options);
        };

        console.log('🌐 网络监控已启用');
    }
    
    init() {
        console.log('🚀 初始化ArticleMigrationApp...');
        try {
            // 设置网络监控
            this.setupNetworkMonitoring();

            // 异步测试API连接，但不阻塞初始化
            this.testApiConnection().catch(error => {
                console.warn('⚠️ API连接测试失败，但不影响应用初始化:', error);
            });

            this.setupEventListeners();
            this.startAutoRefresh();
            this.loadInitialData();
            this.handleUrlParams();
            console.log('✅ ArticleMigrationApp初始化完成');
        } catch (error) {
            console.error('❌ ArticleMigrationApp初始化失败:', error);
            throw error; // 重新抛出错误以便调试
        }
    }

    async testApiConnection() {
        try {
            console.log('🔍 Testing API connection...');
            console.log('🌐 API Base URL:', this.apiBase);
            console.log('🔗 Full URL:', `${this.apiBase}/status`);

            const response = await fetch(`${this.apiBase}/status`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors',
                credentials: 'same-origin'
            });

            console.log('📡 Response received:', response.url, response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ API连接成功:', data);
            } else {
                console.error('❌ API连接失败:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('❌ API连接测试失败:', error);
            console.error('❌ Error details:', error.message, error.stack);
        }
    }
    
    setupEventListeners() {
        console.log('🔧 设置事件监听器...');

        try {
            // Tab navigation
            const tabLinks = document.querySelectorAll('.nav-link[data-tab]');
            console.log(`📋 找到 ${tabLinks.length} 个标签页链接`);
            tabLinks.forEach(link => {
                link.addEventListener('click', (e) => this.handleTabClick(e));
            });

            // Refresh button
            const refreshButtons = document.querySelectorAll('[data-action="refresh"]');
            console.log(`🔄 找到 ${refreshButtons.length} 个刷新按钮`);
            refreshButtons.forEach(btn => {
                btn.addEventListener('click', () => this.refreshCurrentTab());
            });

            // Search form
            const searchForm = document.getElementById('search-form');
            if (searchForm) {
                searchForm.addEventListener('submit', (e) => this.handleSearchSubmit(e));
                console.log('✅ 搜索表单事件监听器已设置');
            } else {
                console.log('ℹ️ 搜索表单不存在');
            }

            // Search mode change
            const searchMode = document.getElementById('search-mode');
            if (searchMode) {
                searchMode.addEventListener('change', (e) => this.handleSearchModeChange(e));
                console.log('✅ 搜索模式事件监听器已设置');
            } else {
                console.log('ℹ️ 搜索模式选择器不存在');
            }

            console.log('✅ 事件监听器设置完成');
        } catch (error) {
            console.error('❌ 设置事件监听器失败:', error);
        }
    }
    
    handleTabClick(e) {
        e.preventDefault();
        const tabName = e.target.getAttribute('data-tab');
        this.switchTab(tabName);
    }

    handleSearchSubmit(e) {
        e.preventDefault();
        this.performSearch();
    }

    handleSearchModeChange(e) {
        const mode = e.target.value;
        const keywordsInput = document.getElementById('keywords-input');
        const categoryInput = document.getElementById('category-input');

        if (mode === 'keyword') {
            keywordsInput.style.display = 'block';
            categoryInput.style.display = 'none';
        } else {
            keywordsInput.style.display = 'none';
            categoryInput.style.display = 'block';
        }
    }
    
    switchTab(tabName) {
        console.log(`🔄 切换到标签页: ${tabName}`);

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
            console.log(`✅ 激活标签页: ${tabName}`);
        } else {
            console.error(`❌ 找不到标签页元素: [data-tab="${tabName}"]`);
        }

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });

        const contentElement = document.getElementById(`${tabName}-content`);
        if (contentElement) {
            contentElement.style.display = 'block';
            console.log(`✅ 显示内容区域: ${tabName}-content`);
        } else {
            console.error(`❌ 找不到内容区域: ${tabName}-content`);
        }
        
        this.currentTab = tabName;
        this.loadTabData(tabName);
    }
    
    async loadTabData(tabName) {
        switch (tabName) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'articles':
                await this.loadArticlesData();
                break;
            case 'prompts':
                await this.loadPromptsData();
                break;
            case 'api-config':
                await this.loadAPIConfigData();
                break;
            case 'processing-config':
                await this.loadProcessingRules();
                break;
            case 'detection':
                await this.loadDetectionData();
                break;
            case 'publish':
                await this.loadPublishData();
                break;
            case 'settings':
                await this.loadSettingsData();
                break;
        }
    }
    
    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            const data = await response.json();
            
            this.updateDashboardMetrics(data.statistics || {});
            this.updateTaskStatus(data.tasks || {});
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    updateDashboardMetrics(stats) {
        const elements = {
            'today-count': stats.processed_today || 0,
            'success-rate': `${(stats.success_rate || 0).toFixed(1)}%`,
            'queue-count': stats.active_tasks || 0,
            'ai-detection-rate': `${(stats.ai_detection_rate || 0).toFixed(1)}%`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                // Add animation effect
                try {
                    element.classList.add('loading');
                    setTimeout(() => {
                        if (element && element.classList) {
                            element.classList.remove('loading');
                        }
                    }, 500);
                } catch (error) {
                    console.warn(`⚠️ 无法为元素 ${id} 添加动画效果:`, error);
                }
            } else {
                console.warn(`⚠️ 找不到元素: ${id}`);
            }
        });

        // Update system status indicators
        this.updateSystemStatus();
    }

    updateSystemStatus() {
        // Update API status
        const apiStatus = document.getElementById('api-status');
        if (apiStatus) {
            apiStatus.textContent = '正常';
            apiStatus.className = 'badge bg-success';
        }

        // Update database status
        const dbStatus = document.getElementById('db-status');
        if (dbStatus) {
            dbStatus.textContent = '正常';
            dbStatus.className = 'badge bg-success';
        }

        // Update browser status
        const browserStatus = document.getElementById('browser-status');
        if (browserStatus) {
            browserStatus.textContent = '就绪';
            browserStatus.className = 'badge bg-success';
        }
    }
    
    updateTaskStatus(tasks) {
        // Update task progress if available
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar && tasks.current_progress) {
            progressBar.style.width = `${tasks.current_progress}%`;
            progressBar.textContent = `${tasks.current_progress}%`;
        }
    }
    
    async loadArticlesData() {
        try {
            const response = await fetch(`${this.apiBase}/articles`);
            const data = await response.json();

            // Update articles display
            this.updateArticlesDisplay(data);

        } catch (error) {
            console.error('Failed to load articles:', error);
            this.showError('加载文章列表失败');
        }
    }

    async loadPromptsData() {
        try {
            const response = await fetch(`${this.apiBase}/prompts`);
            const data = await response.json();

            // Update prompts display
            this.updatePromptsDisplay(data);

        } catch (error) {
            console.error('Failed to load prompts:', error);
            this.showError('加载提示词数据失败');
        }
    }

    async loadAPIConfigData() {
        try {
            const response = await fetch(`${this.apiBase}/config/providers`);
            const data = await response.json();

            // Update API config display
            this.updateAPIConfigDisplay(data);

        } catch (error) {
            console.error('Failed to load API config:', error);
            this.showError('加载API配置失败');
        }
    }
    
    async loadDetectionData() {
        // TODO: Implement detection data loading
        console.log('Loading detection data...');
    }
    
    async loadPublishData() {
        // TODO: Implement publish data loading
        console.log('Loading publish data...');
    }
    
    async loadSettingsData() {
        console.log('Loading settings data...');
        try {
            // 加载AI优化配置
            await this.loadAIOptimizationConfig();
        } catch (error) {
            console.error('❌ 加载设置数据失败:', error);
        }
    }
    
    refreshCurrentTab() {
        this.loadTabData(this.currentTab);
    }
    
    startAutoRefresh() {
        // Refresh dashboard every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.currentTab === 'dashboard') {
                this.loadDashboardData();
            }
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    loadInitialData() {
        this.loadDashboardData();
        this.loadMediumCategories();
    }

    async loadMediumCategories() {
        try {
            console.log('📂 正在加载Medium分类...');
            const response = await fetch(`${this.apiBase}/medium/categories`);
            const data = await response.json();

            if (data.categories) {
                this.populateCategorySelect(data.categories);
                console.log(`✅ 成功加载 ${data.categories.length} 个分类`);
            } else {
                console.warn('⚠️ 未获取到分类数据');
            }
        } catch (error) {
            console.error('❌ 加载Medium分类失败:', error);
            // 使用备用分类列表
            this.populateCategorySelectFallback();
        }
    }

    populateCategorySelect(categories) {
        const categorySelect = document.getElementById('category');
        if (!categorySelect) {
            console.warn('⚠️ 未找到分类选择器元素');
            return;
        }

        // 清空现有选项（保留默认选项）
        categorySelect.innerHTML = '<option value="">请选择分类...</option>';

        // 添加分类选项
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.value;
            option.textContent = category.label;

            // 根据类型添加不同的样式
            if (category.type === 'main') {
                option.style.fontWeight = 'bold';
                option.style.backgroundColor = '#f8f9fa';
            } else if (category.type === 'sub') {
                option.style.paddingLeft = '20px';
                option.style.color = '#6c757d';
            } else if (category.type === 'child') {
                option.style.paddingLeft = '40px';
                option.style.color = '#adb5bd';
                option.style.fontSize = '0.9em';
            }

            categorySelect.appendChild(option);
        });

        console.log(`📂 已填充 ${categories.length} 个分类选项`);
    }

    populateCategorySelectFallback() {
        console.log('🔄 使用备用分类列表...');
        const fallbackCategories = [
            { value: 'artificial-intelligence', label: '🤖 人工智能 (Artificial Intelligence)', type: 'main' },
            { value: 'machine-learning', label: '🧠 机器学习 (Machine Learning)', type: 'main' },
            { value: 'data-science', label: '📊 数据科学 (Data Science)', type: 'main' },
            { value: 'deep-learning', label: '🔬 深度学习 (Deep Learning)', type: 'main' },
            { value: 'nlp', label: '💬 自然语言处理 (NLP)', type: 'main' },
            { value: 'programming', label: '💻 编程 (Programming)', type: 'main' },
            { value: 'python', label: '🐍 Python', type: 'sub' },
            { value: 'javascript', label: '📜 JavaScript', type: 'sub' },
            { value: 'web-development', label: '🌐 Web开发 (Web Development)', type: 'sub' },
            { value: 'business', label: '💼 商业 (Business)', type: 'main' },
            { value: 'entrepreneurship', label: '🚀 创业 (Entrepreneurship)', type: 'sub' },
            { value: 'startups', label: '🏢 初创公司 (Startups)', type: 'sub' },
            { value: 'technology', label: '⚙️ 技术 (Technology)', type: 'main' },
            { value: 'productivity', label: '📈 生产力 (Productivity)', type: 'main' },
            { value: 'self-improvement', label: '🌱 自我提升 (Self Improvement)', type: 'main' },
            { value: 'health', label: '🏥 健康 (Health)', type: 'main' },
            { value: 'fitness', label: '💪 健身 (Fitness)', type: 'sub' },
            { value: 'mental-health', label: '🧠 心理健康 (Mental Health)', type: 'sub' }
        ];

        this.populateCategorySelect(fallbackCategories);
    }

    handleUrlParams() {
        // 检查URL参数中是否指定了要切换的标签
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');

        if (tabParam) {
            // 切换到指定的标签
            this.switchTab(tabParam);

            // 清除URL参数，保持URL整洁
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    }
    
    updateArticlesDisplay(data) {
        const articlesContent = document.getElementById('articles-content');
        if (!articlesContent) return;

        const articles = data.articles || [];
        const total = data.total || 0;

        articlesContent.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-newspaper me-2"></i>文章管理</h2>
                <div class="page-actions">
                    <button class="btn btn-outline-primary btn-sm" onclick="app.refreshCurrentTab()">
                        <i class="fas fa-sync-alt me-1"></i>刷新
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="app.showAddArticleModal()">
                        <i class="fas fa-plus me-1"></i>添加文章
                    </button>
                    <button class="btn btn-success btn-sm" onclick="app.showTopicCreationModal()">
                        <i class="fas fa-magic me-1"></i>主题创作
                    </button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">文章列表 (共 ${total} 篇)</h5>
                </div>
                <div class="card-body">
                    ${articles.length > 0 ? this.renderArticlesTable(articles) : this.renderEmptyState('暂无文章数据')}
                </div>
            </div>
        `;
    }

    renderArticlesTable(articles) {
        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>标题</th>
                            <th>作者</th>
                            <th>状态</th>
                            <th>字数</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${articles.map(article => `
                            <tr>
                                <td>
                                    <div class="fw-bold">${article.title || '未知标题'}</div>
                                    <small class="text-muted">${article.url}</small>
                                </td>
                                <td>${article.author}</td>
                                <td>
                                    <div class="d-flex flex-column gap-1">
                                        <span class="badge ${this.getStatusBadgeClass(article.status)}">
                                            ${this.getStatusText(article.status)}
                                        </span>
                                        ${article.published_at ?
                                            '<span class="badge bg-info text-dark"><i class="fas fa-check-circle me-1"></i>已发布</span>' :
                                            '<span class="badge bg-light text-dark"><i class="fas fa-clock me-1"></i>未发布</span>'
                                        }
                                    </div>
                                </td>
                                <td>${article.word_count} 字</td>
                                <td>${this.formatDate(article.created_at)}</td>
                                <td>
                                    <div class="btn-group btn-group-sm" role="group">
                                        <button class="btn btn-outline-primary" onclick="app.viewArticleContent(${article.id})" title="查看内容">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        ${article.status === 'failed' ?
                                            `<button class="btn btn-outline-warning" onclick="app.viewErrorDetails(${article.id})" title="查看错误">
                                                <i class="fas fa-exclamation-triangle"></i>
                                            </button>
                                            <button class="btn btn-outline-success" onclick="app.retryProcessing(${article.id})" title="重新处理">
                                                <i class="fas fa-redo"></i>
                                            </button>` :
                                            `<button class="btn btn-outline-success" onclick="app.processArticle('${article.url}')" title="开始处理">
                                                <i class="fas fa-play"></i>
                                            </button>`
                                        }
                                        <button class="btn btn-outline-info" onclick="app.showTitleCreationModal(${article.id})" title="标题创作">
                                            <i class="fas fa-magic"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="app.deleteArticle(${article.id})" title="删除文章">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    updatePromptsDisplay(data) {
        const promptsContent = document.getElementById('prompts-content');
        if (!promptsContent) return;

        const templates = data.templates || [];
        const total = data.total || 0;
        const stats = data.statistics || {};

        promptsContent.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-magic me-2"></i>提示词管理</h2>
                <div class="page-actions">
                    <button class="btn btn-outline-primary btn-sm" onclick="app.refreshCurrentTab()">
                        <i class="fas fa-sync-alt me-1"></i>刷新
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="app.openPromptsPage()">
                        <i class="fas fa-external-link-alt me-1"></i>打开完整管理页面
                    </button>
                </div>
            </div>

            <!-- 统计信息 -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card metric-card text-white bg-primary">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">总提示词</h6>
                                    <h3>${stats.total_count || 0}</h3>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-magic fa-2x opacity-75"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card text-white bg-success">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">启用中</h6>
                                    <h3>${stats.active_count || 0}</h3>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-check-circle fa-2x opacity-75"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card text-white bg-warning">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">默认模板</h6>
                                    <h3>${stats.default_count || 0}</h3>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-star fa-2x opacity-75"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card metric-card text-white bg-info">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h6 class="card-title">总使用次数</h6>
                                    <h3>${stats.total_usage || 0}</h3>
                                </div>
                                <div class="align-self-center">
                                    <i class="fas fa-chart-line fa-2x opacity-75"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 提示词列表 -->
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">提示词模板 (共 ${total} 个)</h5>
                </div>
                <div class="card-body">
                    ${templates.length > 0 ? this.renderPromptsGrid(templates) : this.renderEmptyState('暂无提示词模板')}
                </div>
            </div>
        `;
    }

    updateAPIConfigDisplay(providers) {
        const apiConfigContent = document.getElementById('api-config-content');
        if (!apiConfigContent) return;

        apiConfigContent.innerHTML = `
            <div class="page-header">
                <h2><i class="fas fa-cogs me-2"></i>API配置</h2>
                <div class="page-actions">
                    <button class="btn btn-primary btn-sm me-2" onclick="app.showAddProviderModal()">
                        <i class="fas fa-plus me-1"></i>添加Provider
                    </button>
                    <div class="btn-group me-2">
                        <button class="btn btn-outline-success btn-sm" onclick="app.bulkEnableProviders()">
                            <i class="fas fa-check-circle me-1"></i>批量启用
                        </button>
                        <button class="btn btn-outline-warning btn-sm" onclick="app.bulkDisableProviders()">
                            <i class="fas fa-times-circle me-1"></i>批量禁用
                        </button>
                    </div>
                    <div class="btn-group me-2">
                        <button class="btn btn-outline-info btn-sm" onclick="app.exportProviderConfig()">
                            <i class="fas fa-download me-1"></i>导出配置
                        </button>
                        <button class="btn btn-outline-info btn-sm" onclick="app.showImportProviderModal()">
                            <i class="fas fa-upload me-1"></i>导入配置
                        </button>
                    </div>
                    <button class="btn btn-outline-primary btn-sm" onclick="app.refreshCurrentTab()">
                        <i class="fas fa-sync-alt me-1"></i>刷新
                    </button>
                </div>
            </div>

            ${this.renderProviderGroups(providers)}
        `;
    }

    renderPromptsGrid(templates) {
        return `
            <div class="row">
                ${templates.map(template => `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title">${template.name}</h6>
                                    <span class="badge ${this.getPromptTypeBadgeClass(template.type)}">
                                        ${this.getPromptTypeText(template.type)}
                                    </span>
                                </div>
                                <p class="card-text text-muted small">${template.description || '暂无描述'}</p>
                                <div class="mb-2">
                                    <span class="badge ${template.is_active ? 'bg-success' : 'bg-secondary'}">
                                        ${template.is_active ? '启用' : '禁用'}
                                    </span>
                                    ${template.is_default ? '<span class="badge bg-warning ms-1">默认</span>' : ''}
                                </div>
                                <div class="d-flex justify-content-between align-items-center">
                                    <small class="text-muted">使用 ${template.usage_count || 0} 次</small>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="app.viewPromptTemplate(${template.id})" title="查看">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-outline-${template.is_active ? 'warning' : 'success'}"
                                                onclick="app.togglePromptStatus(${template.id}, ${!template.is_active})"
                                                title="${template.is_active ? '禁用' : '启用'}">
                                            <i class="fas fa-${template.is_active ? 'pause' : 'play'}"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderAdapterGroups(data) {
        const groups = [
            { key: 'source', title: '来源平台', icon: 'fas fa-globe' },
            { key: 'ai', title: 'AI服务', icon: 'fas fa-robot' },
            { key: 'detection', title: '检测服务', icon: 'fas fa-search' },
            { key: 'publish', title: '发布平台', icon: 'fas fa-share-alt' }
        ];

        return groups.map(group => {
            const adapters = data[group.key] || [];
            return `
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="${group.icon} me-2"></i>${group.title}
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            ${adapters.map(adapter => `
                                <div class="col-md-6 col-lg-4 mb-3">
                                    <div class="card h-100">
                                        <div class="card-body">
                                            <h6 class="card-title">${adapter.display_name}</h6>
                                            <p class="card-text">
                                                <span class="badge ${this.getAdapterStatusClass(adapter.status)}">
                                                    ${this.getAdapterStatusText(adapter.status)}
                                                </span>
                                            </p>
                                            <div class="d-flex flex-wrap gap-1">
                                                ${adapter.features.map(feature =>
                                                    `<span class="badge bg-light text-dark">${feature}</span>`
                                                ).join('')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async performSearch() {
        const searchMode = document.getElementById('search-mode').value;
        const platform = document.getElementById('platform').value;
        const limit = parseInt(document.getElementById('limit').value);

        let searchData = {
            search_mode: searchMode,
            platform: platform,
            limit: limit
        };

        if (searchMode === 'keyword') {
            const keywordsText = document.getElementById('keywords').value.trim();
            if (!keywordsText) {
                this.showError('请输入搜索关键词');
                return;
            }
            searchData.keywords = keywordsText.split(',').map(k => k.trim()).filter(k => k);
        } else {
            searchData.category = document.getElementById('category').value;
        }

        try {
            this.showSearchLoading();
            const results = await this.searchArticles(searchData);
            this.displaySearchResults(results);
        } catch (error) {
            this.showError('搜索失败: ' + error.message);
        }
    }

    async searchArticles(searchData) {
        try {
            // 添加时间戳确保每次都是新的请求，避免缓存
            const searchDataWithTimestamp = {
                ...searchData,
                timestamp: Date.now(),
                force_refresh: true  // 强制刷新标志
            };

            console.log('🔍 发起搜索请求:', searchDataWithTimestamp);

            const response = await fetch(`${this.apiBase}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',  // 禁用缓存
                    'Pragma': 'no-cache'
                },
                body: JSON.stringify(searchDataWithTimestamp)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ 搜索完成，找到 ${data.total} 篇文章`);
            return data;

        } catch (error) {
            console.error('❌ 搜索失败:', error);
            throw error;
        }
    }

    showSearchLoading() {
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">搜索中...</span>
                </div>
                <p class="mt-3 text-muted">正在搜索文章...</p>
            </div>
        `;
    }

    displaySearchResults(results) {
        const resultsDiv = document.getElementById('search-results');

        if (!results.articles || results.articles.length === 0) {
            resultsDiv.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-search fa-3x mb-3 text-muted opacity-50"></i>
                    <p class="text-muted">未找到相关文章</p>
                </div>
            `;
            return;
        }

        const articlesHtml = results.articles.map(article => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${article.title}</h5>
                    <p class="card-text text-muted">${article.excerpt || '暂无摘要'}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-user me-1"></i>${article.author || '未知作者'}
                            <i class="fas fa-calendar ms-3 me-1"></i>${article.published_date || '未知日期'}
                        </small>
                        <div>
                            <a href="${article.url}" target="_blank" class="btn btn-outline-primary btn-sm me-2">
                                <i class="fas fa-external-link-alt me-1"></i>查看原文
                            </a>
                            <button class="btn btn-primary btn-sm" onclick="app.processArticle('${article.url}')">
                                <i class="fas fa-play me-1"></i>开始处理
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        resultsDiv.innerHTML = `
            <div class="mb-3">
                <h6>找到 ${results.articles.length} 篇文章</h6>
            </div>
            ${articlesHtml}
        `;
    }

    async processArticle(url) {
        try {
            this.showSuccess(`开始处理文章: ${url}`);

            // 首先创建文章
            const createResponse = await fetch(`${this.apiBase}/articles/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    source_platform: 'medium',
                    auto_process: false
                })
            });

            const createData = await createResponse.json();

            if (!createData.success) {
                throw new Error(createData.error || '创建文章失败');
            }

            const articleId = createData.data.id;
            this.showSuccess(`文章创建成功，ID: ${articleId}`);

            // 显示处理模态框
            this.showProcessingModal();

            // 开始真正的文章处理
            await this.startRealArticleProcessing(articleId);

        } catch (error) {
            this.showError('处理失败: ' + error.message);
        }
    }

    // Helper methods
    getStatusBadgeClass(status) {
        const statusClasses = {
            'pending': 'bg-secondary',
            'processing': 'bg-warning text-dark',
            'completed': 'bg-success',
            'optimized': 'bg-success',  // 绿色显示
            'failed': 'bg-danger',
            'published': 'bg-primary'
        };
        return statusClasses[status] || 'bg-secondary';
    }

    getStatusText(status) {
        const statusTexts = {
            'pending': '待处理',
            'processing': '处理中',
            'completed': '已完成',
            'optimized': '已优化',  // 中文显示
            'failed': '失败',
            'published': '已发布'
        };
        return statusTexts[status] || status;
    }

    getAdapterStatusClass(status) {
        const statusClasses = {
            'available': 'bg-success',
            'configured': 'bg-primary',
            'needs_config': 'bg-warning',
            'error': 'bg-danger'
        };
        return statusClasses[status] || 'bg-secondary';
    }

    getAdapterStatusText(status) {
        const statusTexts = {
            'available': '可用',
            'configured': '已配置',
            'needs_config': '需要配置',
            'error': '错误'
        };
        return statusTexts[status] || status;
    }

    getPromptTypeBadgeClass(type) {
        const typeClasses = {
            'translation': 'bg-primary',
            'optimization': 'bg-success',
            'title_generation': 'bg-info',
            'summary': 'bg-warning',
            'custom': 'bg-secondary'
        };
        return typeClasses[type] || 'bg-secondary';
    }

    getPromptTypeText(type) {
        const typeTexts = {
            'translation': '翻译',
            'optimization': '优化',
            'title_generation': '标题生成',
            'summary': '摘要',
            'custom': '自定义'
        };
        return typeTexts[type] || type;
    }

    renderProviderGroups(providers) {
        if (!providers || providers.length === 0) {
            return this.renderEmptyState('暂无API配置，请添加您的第一个API Provider');
        }

        // Group providers by type
        const groupedProviders = providers.reduce((groups, provider) => {
            const type = provider.provider_type;
            if (!groups[type]) {
                groups[type] = [];
            }
            groups[type].push(provider);
            return groups;
        }, {});

        const typeLabels = {
            'ai': { label: 'AI服务', icon: 'fas fa-brain', color: 'primary' },
            'detection': { label: '检测服务', icon: 'fas fa-search', color: 'warning' },
            'publish': { label: '发布服务', icon: 'fas fa-share-alt', color: 'success' }
        };

        return Object.entries(groupedProviders).map(([type, typeProviders]) => {
            const typeInfo = typeLabels[type] || { label: type, icon: 'fas fa-cog', color: 'secondary' };

            return `
                <div class="provider-group mb-4">
                    <div class="group-header mb-3">
                        <h4 class="text-${typeInfo.color}">
                            <i class="${typeInfo.icon} me-2"></i>${typeInfo.label}
                            <span class="badge bg-${typeInfo.color} ms-2">${typeProviders.length}</span>
                        </h4>
                    </div>
                    <div class="row">
                        ${typeProviders.map(provider => this.renderProviderCard(provider)).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }

    renderProviderCard(provider) {
        const statusColor = provider.is_enabled ? 'success' : 'secondary';
        const statusText = provider.is_enabled ? '已启用' : '已禁用';
        const defaultBadge = provider.is_default ? '<span class="badge bg-primary ms-2">默认</span>' : '';

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card provider-card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0">${provider.display_name}${defaultBadge}</h6>
                            <small class="text-muted">${provider.name}</small>
                        </div>
                        <span class="badge bg-${statusColor}">${statusText}</span>
                    </div>
                    <div class="card-body">
                        <div class="provider-info mb-3">
                            <div class="row text-center">
                                <div class="col-4">
                                    <div class="metric">
                                        <div class="metric-value">${provider.success_rate.toFixed(1)}%</div>
                                        <div class="metric-label">成功率</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="metric">
                                        <div class="metric-value">${provider.total_requests}</div>
                                        <div class="metric-label">总请求</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="metric">
                                        <div class="metric-value">${provider.average_response_time.toFixed(0)}ms</div>
                                        <div class="metric-label">响应时间</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="provider-details">
                            <div class="detail-item">
                                <i class="fas fa-link text-muted me-2"></i>
                                <span class="text-truncate">${provider.api_url}</span>
                            </div>
                            <div class="detail-item">
                                <i class="fas fa-key text-muted me-2"></i>
                                <span>API Key: ${provider.api_key}</span>
                            </div>
                            ${provider.description ? `
                                <div class="detail-item">
                                    <i class="fas fa-info-circle text-muted me-2"></i>
                                    <span class="text-muted">${provider.description}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-outline-primary btn-sm" onclick="app.testProviderConnection(${provider.id})">
                                <i class="fas fa-plug me-1"></i>测试
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="app.editProvider(${provider.id})">
                                <i class="fas fa-edit me-1"></i>编辑
                            </button>
                            <button class="btn btn-outline-info btn-sm" onclick="app.manageProviderModels(${provider.id})">
                                <i class="fas fa-cubes me-1"></i>模型
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="app.deleteProvider(${provider.id})">
                                <i class="fas fa-trash me-1"></i>删除
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderEmptyState(message) {
        return `
            <div class="text-center py-5">
                <i class="fas fa-inbox fa-3x mb-3 text-muted opacity-50"></i>
                <p class="text-muted">${message}</p>
            </div>
        `;
    }

    formatDate(dateString) {
        if (!dateString) return '未知';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    }

    // ==================== 文章管理方法 ====================

    async viewArticleContent(articleId) {
        try {
            const response = await fetch(`${this.apiBase}/articles/${articleId}`);
            const data = await response.json();

            if (response.ok) {
                this.showArticleContentModal(data);
            } else {
                this.showError('获取文章详情失败: ' + data.detail);
            }
        } catch (error) {
            this.showError('获取文章详情失败: ' + error.message);
        }
    }

    showArticleContentModal(article) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'articleContentModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">📄 文章内容详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-12">
                                <div class="card mb-3">
                                    <div class="card-header">
                                        <h6 class="mb-0">📋 基本信息</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <p><strong>标题:</strong> ${article.title}</p>
                                                <p><strong>作者:</strong> ${article.author || '未知'}</p>
                                                <p><strong>来源:</strong> ${article.source_platform}</p>
                                            </div>
                                            <div class="col-md-6">
                                                <p><strong>状态:</strong> <span class="badge ${this.getStatusBadgeClass(article.status)}">${this.getStatusText(article.status)}</span></p>
                                                <p><strong>字数:</strong> ${article.word_count || 0} 字</p>
                                                <p><strong>分类:</strong> ${article.category || '未分类'}</p>
                                            </div>
                                        </div>
                                        <p><strong>来源URL:</strong> <a href="${article.source_url}" target="_blank">${article.source_url}</a></p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12">
                                <ul class="nav nav-tabs" id="contentTabs" role="tablist">
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link active" id="original-tab" data-bs-toggle="tab" data-bs-target="#original" type="button" role="tab">
                                            📝 原文内容
                                        </button>
                                    </li>
                                    ${article.content_translated ? `
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="translated-tab" data-bs-toggle="tab" data-bs-target="#translated" type="button" role="tab">
                                            🌐 翻译内容
                                        </button>
                                    </li>` : ''}
                                    ${article.content_optimized ? `
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="optimized-tab" data-bs-toggle="tab" data-bs-target="#optimized" type="button" role="tab">
                                            ✨ 优化内容
                                        </button>
                                    </li>` : ''}
                                    ${article.content_final ? `
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="final-tab" data-bs-toggle="tab" data-bs-target="#final" type="button" role="tab">
                                            🎯 最终内容
                                        </button>
                                    </li>` : ''}
                                </ul>
                                <div class="tab-content" id="contentTabsContent">
                                    <div class="tab-pane fade show active" id="original" role="tabpanel">
                                        <div class="content-display">
                                            ${this.formatContentForDisplay(article.content_original)}
                                        </div>
                                    </div>
                                    ${article.content_translated ? `
                                    <div class="tab-pane fade" id="translated" role="tabpanel">
                                        <div class="content-display">
                                            ${this.formatContentForDisplay(article.content_translated)}
                                        </div>
                                    </div>` : ''}
                                    ${article.content_optimized ? `
                                    <div class="tab-pane fade" id="optimized" role="tabpanel">
                                        <div class="content-display">
                                            ${this.formatContentForDisplay(article.content_optimized)}
                                        </div>
                                    </div>` : ''}
                                    ${article.content_final ? `
                                    <div class="tab-pane fade" id="final" role="tabpanel">
                                        <div class="content-display">
                                            ${this.formatContentForDisplay(article.content_final)}
                                        </div>
                                    </div>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-success me-2" onclick="app.copyArticleContent(${article.id})">
                            <i class="fas fa-copy me-1"></i>一键复制
                        </button>
                        <button type="button" class="btn btn-info me-2" onclick="app.togglePublishStatus(${article.id}, '${article.published_at ? 'unpublish' : 'publish'}')">
                            <i class="fas fa-${article.published_at ? 'undo' : 'check'} me-1"></i>${article.published_at ? '取消发布' : '标记已发布'}
                        </button>
                        <button type="button" class="btn btn-primary" onclick="app.exportArticleContent(${article.id})">
                            <i class="fas fa-download me-1"></i>导出内容
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    formatContentForDisplay(content) {
        if (!content) return '<p class="text-muted">暂无内容</p>';

        // 简单的内容格式化
        return `<div class="content-text" style="max-height: 400px; overflow-y: auto; padding: 15px; background-color: #f8f9fa; border-radius: 5px; white-space: pre-wrap;">${content}</div>`;
    }

    async viewErrorDetails(articleId) {
        try {
            const response = await fetch(`${this.apiBase}/articles/${articleId}`);
            const data = await response.json();

            if (response.ok) {
                this.showErrorDetailsModal(data);
            } else {
                this.showError('获取错误详情失败: ' + data.detail);
            }
        } catch (error) {
            this.showError('获取错误详情失败: ' + error.message);
        }
    }

    showErrorDetailsModal(article) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'errorDetailsModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">⚠️ 错误详情</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="card mb-3">
                            <div class="card-header">
                                <h6 class="mb-0">📋 文章信息</h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>标题:</strong> ${article.title}</p>
                                        <p><strong>状态:</strong> <span class="badge bg-danger">${this.getStatusText(article.status)}</span></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>处理次数:</strong> ${article.processing_attempts || 0} 次</p>
                                        <p><strong>最后更新:</strong> ${this.formatDate(article.updated_at)}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">🔍 错误信息</h6>
                            </div>
                            <div class="card-body">
                                ${article.last_error ? `
                                    <div class="alert alert-danger">
                                        <h6 class="alert-heading">错误详情:</h6>
                                        <pre class="mb-0" style="white-space: pre-wrap; font-size: 0.9em;">${article.last_error}</pre>
                                    </div>
                                ` : `
                                    <div class="alert alert-warning">
                                        <i class="fas fa-info-circle me-2"></i>
                                        暂无详细错误信息
                                    </div>
                                `}

                                <div class="mt-3">
                                    <h6>💡 可能的解决方案:</h6>
                                    <ul class="list-unstyled">
                                        <li><i class="fas fa-check text-success me-2"></i>检查网络连接是否正常</li>
                                        <li><i class="fas fa-check text-success me-2"></i>验证源文章URL是否有效</li>
                                        <li><i class="fas fa-check text-success me-2"></i>确认API配置是否正确</li>
                                        <li><i class="fas fa-check text-success me-2"></i>检查系统资源是否充足</li>
                                        <li><i class="fas fa-check text-success me-2"></i>尝试重新处理文章</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-warning" onclick="app.retryProcessing(${article.id}); bootstrap.Modal.getInstance(document.getElementById('errorDetailsModal')).hide();">
                            <i class="fas fa-redo me-1"></i>重新处理
                        </button>
                        <button type="button" class="btn btn-info" onclick="app.copyErrorToClipboard('${article.last_error ? article.last_error.replace(/'/g, "\\'") : ''}')">
                            <i class="fas fa-copy me-1"></i>复制错误信息
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    copyErrorToClipboard(errorText) {
        if (!errorText) {
            this.showWarning('没有错误信息可复制');
            return;
        }

        navigator.clipboard.writeText(errorText).then(() => {
            this.showSuccess('错误信息已复制到剪贴板');
        }).catch(() => {
            this.showError('复制失败，请手动复制');
        });
    }

    async retryProcessing(articleId) {
        try {
            // 显示确认对话框
            const confirmed = await this.showConfirmDialog(
                '重新处理确认',
                '确定要重新处理这篇文章吗？这将重新执行完整的处理流程。',
                'warning'
            );

            if (!confirmed) return;

            this.showLoading('正在重新处理文章...');

            const response = await fetch(`${this.apiBase}/articles/${articleId}/retry`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('文章重新处理已开始');

                // 显示处理进度模态框
                this.showProcessingModal();
                this.addProcessingLog('开始重新处理文章...', 'info');
                this.updateProcessingProgress(10, '重新处理已启动...');

                // 开始监控文章进度
                await this.monitorArticleProgress(articleId);

                // 刷新文章列表
                this.refreshCurrentTab();
            } else {
                this.showError('重新处理失败: ' + result.detail);
            }
        } catch (error) {
            this.showError('重新处理失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteArticle(articleId) {
        try {
            // 显示确认对话框
            const confirmed = await this.showConfirmDialog(
                '删除文章确认',
                '确定要删除这篇文章吗？此操作不可撤销！',
                'danger'
            );

            if (!confirmed) return;

            this.showLoading('正在删除文章...');

            const response = await fetch(`${this.apiBase}/articles/${articleId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('文章删除成功');
                this.refreshCurrentTab(); // 刷新文章列表
            } else {
                this.showError('删除失败: ' + result.detail);
            }
        } catch (error) {
            this.showError('删除失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async exportArticleContent(articleId) {
        try {
            const response = await fetch(`${this.apiBase}/articles/${articleId}/export`);
            const data = await response.json();

            if (response.ok) {
                // 创建下载链接
                const content = JSON.stringify(data, null, 2);
                const blob = new Blob([content], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);

                const a = document.createElement('a');
                a.href = url;
                a.download = `article_${articleId}_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.showSuccess('文章内容导出成功');
            } else {
                this.showError('导出失败: ' + data.detail);
            }
        } catch (error) {
            this.showError('导出失败: ' + error.message);
        }
    }

    showTitleCreationModal(articleId) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'titleCreationModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">✨ AI标题创作</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="titleTopic" class="form-label">创作主题</label>
                            <input type="text" class="form-control" id="titleTopic"
                                   placeholder="请输入您想要的标题主题或关键词">
                            <div class="form-text">例如：人工智能发展趋势、Python编程教程、健康生活方式等</div>
                        </div>

                        <div class="mb-3">
                            <label for="titleStyle" class="form-label">标题风格</label>
                            <select class="form-select" id="titleStyle">
                                <option value="professional">专业严谨</option>
                                <option value="catchy">吸引眼球</option>
                                <option value="question">疑问式</option>
                                <option value="howto">教程式</option>
                                <option value="trending">热点式</option>
                                <option value="emotional">情感化</option>
                            </select>
                        </div>

                        <div class="mb-3">
                            <label for="titleCount" class="form-label">生成数量</label>
                            <select class="form-select" id="titleCount">
                                <option value="3">3个标题</option>
                                <option value="5" selected>5个标题</option>
                                <option value="8">8个标题</option>
                                <option value="10">10个标题</option>
                            </select>
                        </div>

                        <div class="mb-3">
                            <button type="button" class="btn btn-primary w-100" onclick="app.generateTitles(${articleId})">
                                <i class="fas fa-magic me-1"></i>开始创作标题
                            </button>
                        </div>

                        <div id="generatedTitles" class="mt-4" style="display: none;">
                            <h6>🎯 生成的标题:</h6>
                            <div id="titlesList"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-success" id="applySelectedTitle" style="display: none;" onclick="app.applySelectedTitle(${articleId})">
                            <i class="fas fa-check me-1"></i>应用选中标题
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async generateTitles(articleId) {
        try {
            const topic = document.getElementById('titleTopic').value.trim();
            const style = document.getElementById('titleStyle').value;
            const count = parseInt(document.getElementById('titleCount').value);

            if (!topic) {
                this.showError('请输入创作主题');
                return;
            }

            // 显示加载状态
            const generateBtn = document.querySelector('#titleCreationModal .btn-primary');
            const originalText = generateBtn.innerHTML;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>正在创作...';
            generateBtn.disabled = true;

            const response = await fetch(`${this.apiBase}/articles/${articleId}/generate-titles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    style: style,
                    count: count
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.displayGeneratedTitles(result.titles);
                this.showSuccess(`成功生成 ${result.titles.length} 个标题`);
            } else {
                this.showError('标题生成失败: ' + result.detail);
            }

            // 恢复按钮状态
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;

        } catch (error) {
            this.showError('标题生成失败: ' + error.message);

            // 恢复按钮状态
            const generateBtn = document.querySelector('#titleCreationModal .btn-primary');
            generateBtn.innerHTML = '<i class="fas fa-magic me-1"></i>开始创作标题';
            generateBtn.disabled = false;
        }
    }

    displayGeneratedTitles(titles) {
        const titlesList = document.getElementById('titlesList');
        const generatedTitles = document.getElementById('generatedTitles');
        const applyBtn = document.getElementById('applySelectedTitle');

        titlesList.innerHTML = titles.map((title, index) => `
            <div class="form-check mb-2">
                <input class="form-check-input" type="radio" name="selectedTitle" id="title${index}" value="${title}">
                <label class="form-check-label" for="title${index}">
                    ${title}
                </label>
            </div>
        `).join('');

        generatedTitles.style.display = 'block';
        applyBtn.style.display = 'inline-block';

        // 添加选择事件监听
        titlesList.addEventListener('change', () => {
            applyBtn.disabled = !document.querySelector('input[name="selectedTitle"]:checked');
        });
    }

    async applySelectedTitle(articleId) {
        try {
            const selectedTitle = document.querySelector('input[name="selectedTitle"]:checked');

            if (!selectedTitle) {
                this.showError('请选择一个标题');
                return;
            }

            const newTitle = selectedTitle.value;

            const response = await fetch(`${this.apiBase}/articles/${articleId}/update-title`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: newTitle
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('标题更新成功');
                bootstrap.Modal.getInstance(document.getElementById('titleCreationModal')).hide();
                this.refreshCurrentTab(); // 刷新文章列表
            } else {
                this.showError('标题更新失败: ' + result.detail);
            }
        } catch (error) {
            this.showError('标题更新失败: ' + error.message);
        }
    }

    // ==================== 辅助方法 ====================

    showConfirmDialog(title, message, type = 'warning') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'confirmDialog';

            const typeClass = {
                'warning': 'warning',
                'danger': 'danger',
                'info': 'info',
                'success': 'success'
            }[type] || 'warning';

            const typeIcon = {
                'warning': 'fas fa-exclamation-triangle',
                'danger': 'fas fa-exclamation-circle',
                'info': 'fas fa-info-circle',
                'success': 'fas fa-check-circle'
            }[type] || 'fas fa-exclamation-triangle';

            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-${typeClass} text-white">
                            <h5 class="modal-title">
                                <i class="${typeIcon} me-2"></i>${title}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" onclick="this.closest('.modal').confirmResult = false">取消</button>
                            <button type="button" class="btn btn-${typeClass}" onclick="this.closest('.modal').confirmResult = true" data-bs-dismiss="modal">确认</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            const bootstrapModal = new bootstrap.Modal(modal);

            modal.addEventListener('hidden.bs.modal', () => {
                const result = modal.confirmResult || false;
                document.body.removeChild(modal);
                resolve(result);
            });

            bootstrapModal.show();
        });
    }

    showAddArticleModal() {
        const modal = new bootstrap.Modal(document.getElementById('addArticleModal'));
        modal.show();
    }

    async showTopicCreationModal() {
        console.log('🎨 显示主题创作模态框...');
        try {
            // Load creation configuration
            console.log('🔧 加载创作配置...');
            const response = await fetch(`${this.apiBase}/articles/creation-config`);
            const config = await response.json();

            console.log('📊 配置响应:', { status: response.status, config });

            if (response.ok) {
                console.log('✅ 配置加载成功，渲染模态框...');
                this.renderTopicCreationModal(config);
            } else {
                console.error('❌ 配置加载失败:', config);
                this.showError('加载创作配置失败: ' + config.detail);
            }
        } catch (error) {
            console.error('💥 配置加载异常:', error);
            this.showError('加载创作配置失败: ' + error.message);
        }
    }

    renderTopicCreationModal(config) {
        console.log('🎭 渲染主题创作模态框...', config);

        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="topicCreationModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-magic me-2"></i>
                                主题创作文章
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="topic-creation-form">
                                <div class="mb-3">
                                    <label for="topic-input" class="form-label">文章主题 *</label>
                                    <input type="text" class="form-control" id="topic-input"
                                           placeholder="例如：人工智能在医疗领域的应用" required>
                                    <div class="form-text">请输入您想要创作的文章主题</div>
                                </div>

                                <div class="mb-3">
                                    <label for="keywords-input" class="form-label">关键词 <span class="text-muted">(可选)</span></label>
                                    <input type="text" class="form-control" id="keywords-input"
                                           placeholder="AI, 医疗, 机器学习, 诊断">
                                    <div class="form-text">多个关键词请用逗号分隔，可留空</div>
                                </div>

                                <div class="mb-3">
                                    <label for="requirements-input" class="form-label">创作要求 <span class="text-muted">(可选)</span></label>
                                    <textarea class="form-control" id="requirements-input" rows="3"
                                              placeholder="请描述您对文章的具体要求，如写作风格、重点内容等，可留空使用提示词默认要求"></textarea>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="creation-prompt-select" class="form-label">创作提示词 *</label>
                                            <select class="form-select" id="creation-prompt-select" required>
                                                <option value="">请选择创作提示词</option>
                                                ${config.creation_prompts.map(prompt =>
                                                    `<option value="${prompt.id}">${prompt.display_name}</option>`
                                                ).join('')}
                                            </select>
                                            <div class="form-text">从提示词库中选择合适的创作模板</div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="model-select" class="form-label">AI模型</label>
                                            <select class="form-select" id="model-select">
                                                <option value="">使用默认模型</option>
                                                ${config.available_models.map(model =>
                                                    `<option value="${model.id}">${model.display_name} (${model.provider_display_name})</option>`
                                                ).join('')}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="target-length-select" class="form-label">目标长度</label>
                                            <select class="form-select" id="target-length-select">
                                                <option value="mini" selected>微文 (300-500字)</option>
                                                <option value="short">短文 (500-800字)</option>
                                                <option value="medium">中等 (800-1500字)</option>
                                                <option value="long">长文 (1500-3000字)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="writing-style-select" class="form-label">写作风格 <span class="text-muted">(可选)</span></label>
                                            <select class="form-select" id="writing-style-select">
                                                <option value="">使用提示词默认风格</option>
                                                <option value="professional">专业</option>
                                                <option value="casual">轻松</option>
                                                <option value="academic">学术</option>
                                                <option value="popular">通俗</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="auto-process-topic-check" checked>
                                        <label class="form-check-label" for="auto-process-topic-check">
                                            自动处理（创作完成后自动进行翻译、优化、检测）
                                        </label>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="topic-creation-submit-btn">
                                <i class="fas fa-magic me-1"></i>开始创作
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('topicCreationModal');
        if (existingModal) {
            console.log('🗑️ 移除现有模态框');
            existingModal.remove();
        }

        // Add modal to body
        console.log('➕ 添加模态框到页面');
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        console.log('👁️ 显示模态框');
        const modalElement = document.getElementById('topicCreationModal');
        console.log('🔍 模态框元素:', modalElement);

        if (modalElement) {
            // 绑定提交按钮事件
            const submitBtn = document.getElementById('topic-creation-submit-btn');
            if (submitBtn) {
                console.log('🔗 绑定提交按钮事件');
                submitBtn.addEventListener('click', () => {
                    console.log('🖱️ 提交按钮被点击');
                    this.submitTopicCreation();
                });
            } else {
                console.error('❌ 找不到提交按钮');
            }

            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log('✅ 模态框已显示');
        } else {
            console.error('❌ 找不到模态框元素');
        }
    }

    async submitTopicCreation() {
        console.log('🎨 开始主题创作提交...');
        console.log('🔥 submitTopicCreation 方法被调用了！');

        // 检查表单元素是否存在
        const topicElement = document.getElementById('topic-input');
        const keywordsElement = document.getElementById('keywords-input');
        const requirementsElement = document.getElementById('requirements-input');
        const creationPromptElement = document.getElementById('creation-prompt-select');
        const modelElement = document.getElementById('model-select');
        const targetLengthElement = document.getElementById('target-length-select');
        const writingStyleElement = document.getElementById('writing-style-select');
        const autoProcessElement = document.getElementById('auto-process-topic-check');

        console.log('🔍 表单元素检查:', {
            topicElement: !!topicElement,
            keywordsElement: !!keywordsElement,
            requirementsElement: !!requirementsElement,
            creationPromptElement: !!creationPromptElement,
            modelElement: !!modelElement,
            targetLengthElement: !!targetLengthElement,
            writingStyleElement: !!writingStyleElement,
            autoProcessElement: !!autoProcessElement
        });

        if (!topicElement) {
            console.error('❌ 找不到主题输入框');
            this.showError('找不到主题输入框，请重新打开模态框');
            return;
        }

        console.log('✅ 主题输入框检查通过，开始获取表单数据...');

        console.log('📝 开始获取表单值...');
        const topic = topicElement.value.trim();
        console.log('✅ topic获取完成:', topic);

        let keywordsText, requirements, creationPromptId, modelId, targetLength, writingStyle, autoProcess;

        try {
            console.log('🔍 检查keywordsElement:', keywordsElement);
            console.log('🔍 keywordsElement类型:', keywordsElement?.tagName, keywordsElement?.type);
            if (keywordsElement && keywordsElement.tagName === 'INPUT') {
                keywordsText = keywordsElement.value.trim();
            } else {
                console.warn('⚠️ keywordsElement不是INPUT元素，使用空值');
                keywordsText = '';
            }
            console.log('✅ keywordsText获取完成:', keywordsText);

            console.log('🔍 检查requirementsElement:', requirementsElement);
            console.log('🔍 requirementsElement类型:', requirementsElement?.tagName);
            if (requirementsElement && requirementsElement.tagName === 'TEXTAREA') {
                requirements = requirementsElement.value.trim();
            } else {
                console.warn('⚠️ requirementsElement不是TEXTAREA元素，使用空值');
                requirements = '';
            }
            console.log('✅ requirements获取完成:', requirements);

            console.log('🔍 检查creationPromptElement:', creationPromptElement);
            console.log('🔍 creationPromptElement类型:', creationPromptElement?.tagName);
            if (creationPromptElement && creationPromptElement.tagName === 'SELECT') {
                creationPromptId = creationPromptElement.value;
            } else {
                console.warn('⚠️ creationPromptElement不是SELECT元素，使用空值');
                creationPromptId = '';
            }
            console.log('✅ creationPromptId获取完成:', creationPromptId);

            console.log('🔍 检查modelElement:', modelElement);
            modelId = modelElement ? modelElement.value : '';

            console.log('🔍 检查targetLengthElement:', targetLengthElement);
            targetLength = targetLengthElement ? targetLengthElement.value : 'medium';

            console.log('🔍 检查writingStyleElement:', writingStyleElement);
            writingStyle = writingStyleElement ? writingStyleElement.value : '';

            console.log('🔍 检查autoProcessElement:', autoProcessElement);
            autoProcess = autoProcessElement ? autoProcessElement.checked : false;
        } catch (error) {
            console.error('❌ 获取表单值时出错:', error);
            this.showError('获取表单数据失败: ' + error.message);
            return;
        }



        console.log('✅ 所有表单值获取完成');

        console.log('📋 表单数据:', {
            topic, keywordsText, requirements, creationPromptId, modelId, targetLength, writingStyle, autoProcess
        });

        console.log('🔍 详细值检查:', {
            'topic长度': topic.length,
            'creationPromptId值': creationPromptId,
            'creationPromptId类型': typeof creationPromptId,
            'creationPromptId是否为空字符串': creationPromptId === '',
            'creationPromptId是否为null': creationPromptId === null,
            'creationPromptId是否为undefined': creationPromptId === undefined
        });

        if (!topic) {
            console.error('❌ 验证失败: 主题为空');
            this.showError('请输入文章主题');
            return;
        }

        if (!creationPromptId) {
            console.error('❌ 验证失败: 创作提示词ID为空', creationPromptId);
            this.showError('请选择创作提示词');
            return;
        }

        console.log('✅ 表单验证通过，准备发送请求...');

        // Parse keywords
        const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k) : [];

        // 显示加载状态
        const submitBtn = document.getElementById('topic-creation-submit-btn');
        let originalText = '<i class="fas fa-magic me-1"></i>开始创作';
        if (submitBtn) {
            originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>正在创作...';
            submitBtn.disabled = true;
        } else {
            console.warn('⚠️ 找不到提交按钮，无法显示加载状态');
        }

        try {
            const requestData = {
                topic: topic,
                keywords: keywords,
                creation_requirements: requirements,
                selected_creation_prompt_id: creationPromptId ? parseInt(creationPromptId) : null,
                selected_model_id: modelId ? parseInt(modelId) : null,
                auto_process: autoProcess,
                target_length: targetLength,
                writing_style: writingStyle
            };

            console.log('📤 发送请求数据:', requestData);
            console.log('🔗 请求URL:', `${this.apiBase}/articles/create-by-topic`);

            const response = await fetch(`${this.apiBase}/articles/create-by-topic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            console.log('📡 收到响应:', response.status, response.statusText);

            const data = await response.json();
            console.log('📋 响应数据:', data);

            if (data.success) {
                this.showSuccess('主题创作文章创建成功！');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('topicCreationModal'));
                modal.hide();

                // Clear form
                document.getElementById('topic-creation-form').reset();

                // Refresh articles if on articles tab
                if (this.currentTab === 'articles') {
                    this.loadArticlesData();
                }

                // If auto process is enabled, start monitoring
                if (autoProcess && data.data.task_id) {
                    this.showProcessingModal();
                    this.monitorTaskProgress(data.data.task_id);
                }
            } else {
                this.showError('主题创作失败: ' + (data.error || '未知错误'));
                // 恢复按钮状态
                if (submitBtn) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }

        } catch (error) {
            this.showError('主题创作失败: ' + error.message);
            // 恢复按钮状态
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }
    }

    async submitAddArticle() {
        const url = document.getElementById('article-url-input').value.trim();
        const platform = document.getElementById('source-platform-select').value;
        const autoProcess = document.getElementById('auto-process-check').checked;

        if (!url) {
            this.showError('请输入文章URL');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/articles/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    source_platform: platform,
                    auto_process: autoProcess
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('文章添加成功！');

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addArticleModal'));
                modal.hide();

                // Clear form
                document.getElementById('add-article-form').reset();

                // Refresh articles if on articles tab
                if (this.currentTab === 'articles') {
                    this.loadArticlesData();
                }

                // If auto process is enabled, start processing
                if (autoProcess) {
                    this.showProcessingModal();
                    this.startRealArticleProcessing(data.data.id);
                }
            } else {
                this.showError('添加文章失败: ' + (data.error || '未知错误'));
            }

        } catch (error) {
            this.showError('添加文章失败: ' + error.message);
        }
    }

    showProcessingModal() {
        const modal = new bootstrap.Modal(document.getElementById('processingModal'));
        modal.show();

        // Reset progress
        this.updateProcessingProgress(0, '正在初始化...');
        document.getElementById('processing-log').innerHTML = '<div class="text-muted">开始处理...</div>';
    }

    updateProcessingProgress(percentage, step) {
        const progressBar = document.getElementById('processing-progress-bar');
        const percentageSpan = document.getElementById('processing-percentage');
        const currentStep = document.getElementById('processing-current-step');

        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        if (percentageSpan) {
            percentageSpan.textContent = Math.round(percentage) + '%';
        }
        if (currentStep) {
            currentStep.textContent = step;
        }
    }

    addProcessingLog(message, type = 'info') {
        const log = document.getElementById('processing-log');
        if (!log) return;

        const timestamp = new Date().toLocaleTimeString();
        const iconClass = type === 'success' ? 'text-success fas fa-check' :
                         type === 'error' ? 'text-danger fas fa-times' :
                         'text-info fas fa-info-circle';

        const entry = document.createElement('div');
        entry.className = 'mb-1';
        entry.innerHTML = `[${timestamp}] <i class="${iconClass} me-1"></i> ${message}`;

        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    async startRealArticleProcessing(articleId) {
        try {
            this.addProcessingLog('开始处理文章...', 'info');
            this.updateProcessingProgress(5, '正在初始化处理流程...');

            // 调用后端处理API，设置较短的超时时间
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

            try {
                const response = await fetch(`${this.apiBase}/articles/${articleId}/process`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        steps: ['extract', 'translate', 'optimize', 'detect'],
                        auto_publish: false,
                        priority: 'normal'
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error || '处理请求失败');
                }

                this.addProcessingLog('处理任务已提交到后端', 'success');
                this.updateProcessingProgress(10, '任务已提交，开始监控进度...');

                // 获取任务ID并开始监控
                const taskId = data.data.task_id;
                this.addProcessingLog(`任务ID: ${taskId}`, 'info');

                // 开始轮询任务状态
                await this.monitorTaskProgress(taskId);

            } catch (fetchError) {
                clearTimeout(timeoutId);

                if (fetchError.name === 'AbortError') {
                    // 请求超时，但任务可能已经开始，尝试通过文章ID监控
                    this.addProcessingLog('请求超时，但任务可能已开始，尝试监控进度...', 'warning');
                    this.updateProcessingProgress(10, '请求超时，尝试监控任务进度...');

                    // 尝试通过文章状态监控
                    await this.monitorArticleProgress(articleId);
                } else {
                    throw fetchError;
                }
            }

        } catch (error) {
            this.addProcessingLog(`处理失败: ${error.message}`, 'error');
            this.showError('文章处理失败: ' + error.message);
        }
    }

    async monitorArticleProgress(articleId) {
        const maxAttempts = 120; // 最多监控2分钟
        let attempts = 0;

        const checkProgress = async () => {
            try {
                attempts++;

                // 通过文章状态API监控进度
                const response = await fetch(`${this.apiBase}/articles/${articleId}`);
                const data = await response.json();

                if (data.success) {
                    const article = data.data;
                    const status = article.status;

                    // 根据状态更新进度
                    let progress = 0;
                    let statusText = '处理中...';

                    switch (status) {
                        case 'pending':
                            progress = 5;
                            statusText = '等待处理...';
                            break;
                        case 'extracting':
                            progress = 25;
                            statusText = '正在提取内容...';
                            break;
                        case 'translating':
                            progress = 50;
                            statusText = '正在翻译内容...';
                            break;
                        case 'optimizing':
                            progress = 75;
                            statusText = '正在优化内容...';
                            break;
                        case 'completed':
                        case 'optimized':
                            progress = 100;
                            statusText = '处理完成！';
                            this.addProcessingLog('文章处理成功完成！', 'success');
                            this.updateProcessingProgress(100, '处理完成！');
                            this.loadArticlesData(); // 刷新文章列表
                            return;
                        case 'failed':
                            this.addProcessingLog('文章处理失败', 'error');
                            this.updateProcessingProgress(progress, '处理失败');
                            return;
                    }

                    this.updateProcessingProgress(progress, statusText);
                    this.addProcessingLog(`当前状态: ${statusText}`, 'info');
                }

                // 继续监控
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 2000); // 2秒后再次检查
                } else {
                    this.addProcessingLog('监控超时，请手动刷新查看结果', 'warning');
                }

            } catch (error) {
                this.addProcessingLog(`监控进度失败: ${error.message}`, 'error');
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 3000); // 出错后3秒重试
                }
            }
        };

        setTimeout(checkProgress, 1000); // 1秒后开始第一次检查
    }

    async monitorTaskProgress(taskId) {
        const maxAttempts = 120; // 最多监控2分钟
        let attempts = 0;

        const checkProgress = async () => {
            try {
                attempts++;

                const response = await fetch(`${this.apiBase}/tasks/${taskId}/status`);
                const data = await response.json();

                if (data.success) {
                    const task = data.data;
                    const progress = task.progress || 0;
                    const status = task.status;
                    const currentStep = task.current_step || '处理中...';

                    this.updateProcessingProgress(progress, currentStep);

                    // 添加详细日志
                    if (task.logs && task.logs.length > 0) {
                        const lastLog = task.logs[task.logs.length - 1];
                        if (lastLog.message) {
                            const logType = lastLog.level === 'ERROR' ? 'error' :
                                          lastLog.level === 'WARNING' ? 'warning' : 'info';
                            this.addProcessingLog(lastLog.message, logType);
                        }
                    }

                    // 检查任务状态
                    if (status === 'completed') {
                        this.addProcessingLog('🎉 文章处理完成！', 'success');
                        this.updateProcessingProgress(100, '处理完成');
                        this.showSuccess('文章处理完成！');
                        return;
                    } else if (status === 'failed') {
                        this.addProcessingLog('❌ 文章处理失败', 'error');
                        this.showError('文章处理失败');
                        return;
                    } else if (status === 'running' || status === 'pending') {
                        // 继续监控
                        if (attempts < maxAttempts) {
                            setTimeout(checkProgress, 2000); // 每2秒检查一次
                        } else {
                            this.addProcessingLog('⏰ 监控超时，请手动检查任务状态', 'warning');
                        }
                    }
                } else {
                    this.addProcessingLog(`获取任务状态失败: ${data.error}`, 'error');
                }

            } catch (error) {
                this.addProcessingLog(`监控任务进度时出错: ${error.message}`, 'error');
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 5000); // 出错时等待5秒再试
                }
            }
        };

        // 开始监控
        setTimeout(checkProgress, 1000); // 1秒后开始第一次检查
    }

    async startArticleProcessing(articleId) {
        // 保留原有的模拟处理方法作为备用
        try {
            this.addProcessingLog('开始处理文章...', 'info');

            // Simulate processing steps
            const steps = [
                { name: '提取文章内容', duration: 2000 },
                { name: 'AI翻译处理', duration: 5000 },
                { name: '原创性检测', duration: 3000 },
                { name: '内容优化', duration: 4000 },
                { name: 'AI检测验证', duration: 2000 },
                { name: '完成处理', duration: 1000 }
            ];

            for (let i = 0; i < steps.length; i++) {
                const step = steps[i];
                const progress = ((i + 1) / steps.length) * 100;

                this.updateProcessingProgress(progress, step.name);
                this.addProcessingLog(`开始: ${step.name}`, 'info');

                // Simulate processing time
                await new Promise(resolve => setTimeout(resolve, step.duration));

                this.addProcessingLog(`完成: ${step.name}`, 'success');
            }

            this.addProcessingLog('文章处理完成！', 'success');
            this.showSuccess('文章处理完成！');

        } catch (error) {
            this.addProcessingLog(`处理失败: ${error.message}`, 'error');
            this.showError('文章处理失败');
        }
    }



    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toastId = 'toast-' + Date.now();
        const iconClass = type === 'error' ? 'fas fa-exclamation-circle text-danger' :
                         type === 'success' ? 'fas fa-check-circle text-success' :
                         'fas fa-info-circle text-info';

        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = 'toast show';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">${type === 'error' ? '错误' : type === 'success' ? '成功' : '提示'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (document.getElementById(toastId)) {
                toast.remove();
            }
        }, 5000);
    }

    // 提示词管理相关方法
    openPromptsPage() {
        // 在新标签页中打开完整的提示词管理页面
        window.open('/prompts', '_blank');
    }

    // API配置管理相关方法
    showAddProviderModal() {
        const modal = new bootstrap.Modal(document.getElementById('addProviderModal'));

        // 重置表单
        document.getElementById('addProviderForm').reset();
        document.getElementById('providerWeight').value = '1';
        document.getElementById('providerRpmLimit').value = '60';
        document.getElementById('providerRphLimit').value = '1000';
        document.getElementById('providerIsEnabled').checked = true;
        document.getElementById('providerIsDefault').checked = false;

        // 设置API Key显示/隐藏功能
        this.setupApiKeyToggle();

        modal.show();
    }

    useProviderTemplate(templateName) {
        const templates = {
            'openai': {
                name: 'openai-gpt4',
                display_name: 'OpenAI GPT-4',
                provider_type: 'ai',
                api_url: 'https://api.openai.com/v1',
                description: 'OpenAI GPT-4 API服务',
                weight: 1,
                max_requests_per_minute: 60,
                max_requests_per_hour: 1000
            },
            'claude': {
                name: 'anthropic-claude',
                display_name: 'Anthropic Claude',
                provider_type: 'ai',
                api_url: 'https://api.anthropic.com',
                description: 'Anthropic Claude API服务',
                weight: 1,
                max_requests_per_minute: 60,
                max_requests_per_hour: 1000
            },
            'gemini': {
                name: 'google-gemini',
                display_name: 'Google Gemini',
                provider_type: 'ai',
                api_url: 'https://generativelanguage.googleapis.com/v1',
                description: 'Google Gemini API服务',
                weight: 1,
                max_requests_per_minute: 60,
                max_requests_per_hour: 1000
            }
        };

        const template = templates[templateName];
        if (template) {
            document.getElementById('providerName').value = template.name;
            document.getElementById('providerDisplayName').value = template.display_name;
            document.getElementById('providerType').value = template.provider_type;
            document.getElementById('providerApiUrl').value = template.api_url;
            document.getElementById('providerDescription').value = template.description;
            document.getElementById('providerWeight').value = template.weight;
            document.getElementById('providerRpmLimit').value = template.max_requests_per_minute;
            document.getElementById('providerRphLimit').value = template.max_requests_per_hour;

            // 清空API Key，用户需要自己填写
            document.getElementById('providerApiKey').value = '';
            document.getElementById('providerApiKey').focus();
        }
    }

    setupApiKeyToggle() {
        const toggleBtn = document.getElementById('toggleApiKey');
        const apiKeyInput = document.getElementById('providerApiKey');

        toggleBtn.onclick = () => {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                apiKeyInput.type = 'password';
                toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
            }
        };
    }

    async submitAddProvider() {
        try {
            const form = document.getElementById('addProviderForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const providerData = {
                name: document.getElementById('providerName').value,
                display_name: document.getElementById('providerDisplayName').value,
                provider_type: document.getElementById('providerType').value,
                api_url: document.getElementById('providerApiUrl').value,
                api_key: document.getElementById('providerApiKey').value,
                description: document.getElementById('providerDescription').value || null,
                weight: parseInt(document.getElementById('providerWeight').value),
                max_requests_per_minute: parseInt(document.getElementById('providerRpmLimit').value),
                max_requests_per_hour: parseInt(document.getElementById('providerRphLimit').value),
                is_enabled: document.getElementById('providerIsEnabled').checked,
                is_default: document.getElementById('providerIsDefault').checked
            };

            this.showLoading('正在保存Provider...');

            const response = await fetch(`${this.apiBase}/config/providers`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(providerData)
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Provider添加成功！');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('addProviderModal'));
                modal.hide();

                // 刷新API配置页面
                this.refreshCurrentTab();
            } else {
                const error = await response.json();
                this.showError('添加失败: ' + error.detail);
            }
        } catch (error) {
            this.showError('添加失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async testProviderConnection(providerId) {
        try {
            console.log(`🧪 开始测试Provider ${providerId}连接...`);
            this.showLoading('正在测试连接...');

            const response = await fetch(`${this.apiBase}/config/providers/${providerId}/test`, {
                method: 'POST'
            });

            console.log(`📡 测试连接响应状态: ${response.status}`);
            const result = await response.json();
            console.log('📊 测试连接结果:', result);

            if (result.success) {
                const message = `连接测试成功！响应时间: ${Math.round(result.response_time)}ms`;
                console.log(`✅ ${message}`);
                this.showSuccess(message);
                if (result.model_list && result.model_list.length > 0) {
                    console.log('Available models:', result.model_list);
                }
            } else {
                const message = `连接测试失败: ${result.message}`;
                console.error(`❌ ${message}`);
                this.showError(message);
            }
        } catch (error) {
            console.error('❌ 连接测试异常:', error);
            this.showError('连接测试失败: ' + error.message);
        } finally {
            console.log('🔄 隐藏测试连接加载状态');
            this.hideLoading();
        }
    }

    async editProvider(providerId) {
        try {
            console.log(`🔧 开始编辑Provider: ${providerId}`);
            this.showLoading('正在加载Provider信息...');

            // 设置请求超时和CORS处理
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

            // 获取Provider详细信息
            const response = await fetch(`${this.apiBase}/config/providers/${providerId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors',
                credentials: 'same-origin',
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            console.log(`📡 获取Provider详情响应状态: ${response.status}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API错误响应:', errorText);
                throw new Error(`获取Provider信息失败: ${response.status} - ${errorText}`);
            }

            const provider = await response.json();
            console.log('📋 获取到Provider数据:', provider);

            // 填充编辑表单
            this.populateEditForm(provider);
            console.log('📝 表单已填充');

            // 显示编辑模态框
            const modalElement = document.getElementById('editProviderModal');
            if (!modalElement) {
                throw new Error('找不到编辑模态框元素');
            }

            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log('🎭 编辑模态框已显示');

        } catch (error) {
            console.error('❌ 编辑Provider失败:', error);
            if (error.name === 'AbortError') {
                this.showError('请求超时，请检查网络连接');
            } else if (error.message.includes('Failed to fetch')) {
                this.showError('网络连接失败，请检查服务器状态');
            } else {
                this.showError('加载Provider信息失败: ' + error.message);
            }
        } finally {
            this.hideLoading();
        }
    }

    populateEditForm(provider) {
        console.log('📝 开始填充编辑表单...');

        try {
            // 填充统计信息
            const statsElements = [
                'editStatsSuccessRate', 'editStatsTotalRequests', 'editStatsFailedRequests',
                'editStatsResponseTime', 'editStatsCurrentUsage', 'editStatsMonthlyBudget'
            ];

            statsElements.forEach(id => {
                const element = document.getElementById(id);
                if (!element) {
                    console.warn(`⚠️ 找不到统计元素: ${id}`);
                }
            });

            document.getElementById('editStatsSuccessRate').textContent = provider.success_rate.toFixed(1) + '%';
            document.getElementById('editStatsTotalRequests').textContent = provider.total_requests;
            document.getElementById('editStatsFailedRequests').textContent = provider.failed_requests;
            document.getElementById('editStatsResponseTime').textContent = provider.average_response_time.toFixed(0) + 'ms';
            document.getElementById('editStatsCurrentUsage').textContent = provider.current_usage.toFixed(2);
            document.getElementById('editStatsMonthlyBudget').textContent = provider.monthly_budget.toFixed(2);

            // 填充基本信息
            const basicElements = [
                'editProviderId', 'editProviderName', 'editProviderDisplayName',
                'editProviderType', 'editProviderApiUrl', 'editProviderDescription'
            ];

            basicElements.forEach(id => {
                const element = document.getElementById(id);
                if (!element) {
                    console.error(`❌ 找不到基本信息元素: ${id}`);
                    return;
                }
            });

            document.getElementById('editProviderId').value = provider.id;
            document.getElementById('editProviderName').value = provider.name;
            document.getElementById('editProviderDisplayName').value = provider.display_name;
            document.getElementById('editProviderType').value = provider.provider_type;
            document.getElementById('editProviderApiUrl').value = provider.api_url;
            document.getElementById('editProviderDescription').value = provider.description || '';

            // 填充配置信息
            const configElements = [
                'editProviderWeight', 'editProviderRpmLimit', 'editProviderRphLimit',
                'editProviderInputCost', 'editProviderOutputCost', 'editProviderBudget'
            ];

            configElements.forEach(id => {
                const element = document.getElementById(id);
                if (!element) {
                    console.error(`❌ 找不到配置元素: ${id}`);
                    return;
                }
            });

            document.getElementById('editProviderWeight').value = provider.weight;
            document.getElementById('editProviderRpmLimit').value = provider.max_requests_per_minute;
            document.getElementById('editProviderRphLimit').value = provider.max_requests_per_hour;
            document.getElementById('editProviderInputCost').value = provider.cost_per_1k_tokens_input;
            document.getElementById('editProviderOutputCost').value = provider.cost_per_1k_tokens_output;
            document.getElementById('editProviderBudget').value = provider.monthly_budget;

            // 填充状态
            const statusElements = ['editProviderIsEnabled', 'editProviderIsDefault'];
            statusElements.forEach(id => {
                const element = document.getElementById(id);
                if (!element) {
                    console.error(`❌ 找不到状态元素: ${id}`);
                    return;
                }
            });

            document.getElementById('editProviderIsEnabled').checked = provider.is_enabled;
            document.getElementById('editProviderIsDefault').checked = provider.is_default;

            // 清空API Key字段（安全考虑）
            const apiKeyElement = document.getElementById('editProviderApiKey');
            if (apiKeyElement) {
                apiKeyElement.value = '';
            } else {
                console.error('❌ 找不到API Key元素');
            }

            // 设置API Key显示/隐藏功能
            this.setupEditApiKeyToggle();

            console.log('✅ 表单填充完成');
        } catch (error) {
            console.error('❌ 填充表单时出错:', error);
            throw error;
        }
    }

    setupEditApiKeyToggle() {
        const toggleBtn = document.getElementById('editToggleApiKey');
        const apiKeyInput = document.getElementById('editProviderApiKey');

        toggleBtn.onclick = () => {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                apiKeyInput.type = 'password';
                toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
            }
        };
    }

    async submitEditProvider() {
        try {
            console.log('🔧 开始提交编辑Provider...');

            const form = document.getElementById('editProviderForm');
            if (!form) {
                console.error('❌ 找不到编辑表单');
                this.showError('找不到编辑表单');
                return;
            }

            if (!form.checkValidity()) {
                console.log('⚠️ 表单验证失败');
                form.reportValidity();
                return;
            }

            // 显示加载状态
            this.showLoading('正在保存修改...');

            const providerId = document.getElementById('editProviderId').value;
            const apiKey = document.getElementById('editProviderApiKey').value;

            console.log(`📝 编辑Provider ID: ${providerId}`);

            // 构建更新数据（只包含修改的字段）
            const updateData = {
                display_name: document.getElementById('editProviderDisplayName').value,
                api_url: document.getElementById('editProviderApiUrl').value,
                description: document.getElementById('editProviderDescription').value || null,
                weight: parseInt(document.getElementById('editProviderWeight').value),
                max_requests_per_minute: parseInt(document.getElementById('editProviderRpmLimit').value),
                max_requests_per_hour: parseInt(document.getElementById('editProviderRphLimit').value),
                cost_per_1k_tokens_input: parseFloat(document.getElementById('editProviderInputCost').value),
                cost_per_1k_tokens_output: parseFloat(document.getElementById('editProviderOutputCost').value),
                monthly_budget: parseFloat(document.getElementById('editProviderBudget').value),
                is_enabled: document.getElementById('editProviderIsEnabled').checked,
                is_default: document.getElementById('editProviderIsDefault').checked
            };

            // 如果提供了新的API Key，则包含在更新中
            if (apiKey && apiKey.trim()) {
                updateData.api_key = apiKey;
                console.log('🔑 包含API Key更新');
            }

            console.log('📤 发送更新数据:', updateData);

            this.showLoading('正在保存修改...');

            // 设置请求超时
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15秒超时

            const response = await fetch(`${this.apiBase}/config/providers/${providerId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors',
                credentials: 'same-origin',
                body: JSON.stringify(updateData),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            console.log(`📡 API响应状态: ${response.status}`);

            if (response.ok) {
                const result = await response.json();
                console.log('✅ 编辑成功:', result);
                this.showSuccess('Provider修改成功！');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProviderModal'));
                if (modal) {
                    modal.hide();
                    console.log('🔒 模态框已关闭');
                } else {
                    console.warn('⚠️ 无法获取模态框实例');
                }

                // 刷新API配置页面
                this.refreshCurrentTab();
                console.log('🔄 页面已刷新');
            } else {
                const errorText = await response.text();
                console.error('❌ API错误响应:', errorText);
                try {
                    const error = JSON.parse(errorText);
                    this.showError('修改失败: ' + error.detail);
                } catch (e) {
                    this.showError('修改失败: ' + errorText);
                }
            }
        } catch (error) {
            console.error('❌ 编辑Provider异常:', error);
            if (error.name === 'AbortError') {
                this.showError('请求超时，请检查网络连接或API服务状态');
            } else {
                this.showError('修改失败: ' + error.message);
            }
        } finally {
            this.hideLoading();
        }
    }

    async bulkEnableProviders() {
        if (!confirm('确定要启用所有当前禁用的Provider吗？')) {
            return;
        }

        try {
            this.showLoading('正在批量启用Provider...');

            // 获取所有Provider
            const response = await fetch(`${this.apiBase}/config/providers`);
            const providers = await response.json();

            // 找到所有禁用的Provider
            const disabledProviders = providers.filter(p => !p.is_enabled);

            if (disabledProviders.length === 0) {
                this.showInfo('没有需要启用的Provider');
                return;
            }

            // 批量启用
            let successCount = 0;
            for (const provider of disabledProviders) {
                try {
                    const updateResponse = await fetch(`${this.apiBase}/config/providers/${provider.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ is_enabled: true })
                    });

                    if (updateResponse.ok) {
                        successCount++;
                    }
                } catch (error) {
                    console.error(`Failed to enable provider ${provider.id}:`, error);
                }
            }

            this.showSuccess(`成功启用 ${successCount}/${disabledProviders.length} 个Provider`);
            this.refreshCurrentTab();

        } catch (error) {
            this.showError('批量启用失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async bulkDisableProviders() {
        if (!confirm('确定要禁用所有当前启用的Provider吗？这可能会影响系统功能。')) {
            return;
        }

        try {
            this.showLoading('正在批量禁用Provider...');

            // 获取所有Provider
            const response = await fetch(`${this.apiBase}/config/providers`);
            const providers = await response.json();

            // 找到所有启用的Provider
            const enabledProviders = providers.filter(p => p.is_enabled);

            if (enabledProviders.length === 0) {
                this.showInfo('没有需要禁用的Provider');
                return;
            }

            // 批量禁用
            let successCount = 0;
            for (const provider of enabledProviders) {
                try {
                    const updateResponse = await fetch(`${this.apiBase}/config/providers/${provider.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ is_enabled: false })
                    });

                    if (updateResponse.ok) {
                        successCount++;
                    }
                } catch (error) {
                    console.error(`Failed to disable provider ${provider.id}:`, error);
                }
            }

            this.showSuccess(`成功禁用 ${successCount}/${enabledProviders.length} 个Provider`);
            this.refreshCurrentTab();

        } catch (error) {
            this.showError('批量禁用失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async exportProviderConfig() {
        try {
            this.showLoading('正在导出配置...');

            // 获取所有Provider配置
            const response = await fetch(`${this.apiBase}/config/providers`);
            const providers = await response.json();

            // 创建导出数据
            const exportData = {
                version: "1.0",
                exported_at: new Date().toISOString(),
                providers: providers.map(provider => ({
                    name: provider.name,
                    display_name: provider.display_name,
                    description: provider.description,
                    provider_type: provider.provider_type,
                    api_url: provider.api_url,
                    api_version: provider.api_version,
                    weight: provider.weight,
                    max_requests_per_minute: provider.max_requests_per_minute,
                    max_requests_per_hour: provider.max_requests_per_hour,
                    max_concurrent_requests: provider.max_concurrent_requests,
                    cost_per_1k_tokens_input: provider.cost_per_1k_tokens_input,
                    cost_per_1k_tokens_output: provider.cost_per_1k_tokens_output,
                    monthly_budget: provider.monthly_budget,
                    is_enabled: provider.is_enabled,
                    is_default: provider.is_default,
                    extra_config: provider.extra_config
                    // 注意：不导出API密钥和统计数据
                }))
            };

            // 创建下载链接
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `api-providers-config-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showSuccess(`成功导出 ${providers.length} 个Provider配置`);

        } catch (error) {
            this.showError('导出配置失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showImportProviderModal() {
        // 创建文件输入元素
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (event) => {
            const file = event.target.files[0];
            if (file) {
                this.importProviderConfig(file);
            }
        };
        input.click();
    }

    async importProviderConfig(file) {
        try {
            this.showLoading('正在导入配置...');

            // 读取文件内容
            const text = await file.text();
            const importData = JSON.parse(text);

            // 验证导入数据格式
            if (!importData.providers || !Array.isArray(importData.providers)) {
                throw new Error('无效的配置文件格式');
            }

            // 确认导入
            if (!confirm(`确定要导入 ${importData.providers.length} 个Provider配置吗？\n注意：同名Provider将被跳过。`)) {
                return;
            }

            let successCount = 0;
            let skipCount = 0;
            let errorCount = 0;

            for (const providerConfig of importData.providers) {
                try {
                    // 检查是否已存在同名Provider
                    const checkResponse = await fetch(`${this.apiBase}/config/providers`);
                    const existingProviders = await checkResponse.json();
                    const exists = existingProviders.some(p => p.name === providerConfig.name);

                    if (exists) {
                        skipCount++;
                        continue;
                    }

                    // 创建新Provider（需要用户手动添加API Key）
                    const createData = {
                        ...providerConfig,
                        api_key: 'PLEASE_UPDATE_API_KEY' // 占位符，用户需要手动更新
                    };

                    const createResponse = await fetch(`${this.apiBase}/config/providers`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(createData)
                    });

                    if (createResponse.ok) {
                        successCount++;
                    } else {
                        errorCount++;
                    }

                } catch (error) {
                    console.error(`Failed to import provider ${providerConfig.name}:`, error);
                    errorCount++;
                }
            }

            let message = `导入完成！成功: ${successCount}, 跳过: ${skipCount}, 失败: ${errorCount}`;
            if (successCount > 0) {
                message += '\n\n注意：导入的Provider使用占位符API Key，请手动更新为真实的API Key。';
            }

            this.showSuccess(message);
            this.refreshCurrentTab();

        } catch (error) {
            this.showError('导入配置失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    manageProviderModels(providerId) {
        // TODO: 实现模型管理功能
        this.showInfo('模型管理功能开发中...');
    }

    async deleteProvider(providerId) {
        if (!confirm('确定要删除这个API Provider吗？此操作不可撤销。')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/config/providers/${providerId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Provider删除成功');
                this.refreshCurrentTab();
            } else {
                const error = await response.json();
                this.showError('删除失败: ' + error.detail);
            }
        } catch (error) {
            this.showError('删除失败: ' + error.message);
        }
    }

    async viewPromptTemplate(templateId) {
        try {
            const response = await fetch(`${this.apiBase}/prompts/${templateId}`);
            const data = await response.json();

            if (data.success) {
                // TODO: 显示提示词详情模态框
                this.showSuccess(`查看提示词: ${data.data.name}`);
            } else {
                this.showError('获取提示词详情失败');
            }
        } catch (error) {
            this.showError('获取提示词详情失败: ' + error.message);
        }
    }

    async togglePromptStatus(templateId, isActive) {
        try {
            const response = await fetch(`${this.apiBase}/prompts/${templateId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: isActive })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(`提示词已${isActive ? '启用' : '禁用'}`);
                // 刷新提示词数据
                this.loadPromptsData();
            } else {
                this.showError('操作失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            this.showError('操作失败: ' + error.message);
        }
    }

    // 测试处理功能
    async testProcessing() {
        const testUrl = 'https://medium.com/@example/test-article';
        this.showSuccess('开始测试文章处理流程...');
        await this.processArticle(testUrl);
    }

    // 测试Toast功能
    testToast() {
        console.log('🧪 测试Toast功能...');
        this.showSuccess('这是一个成功消息测试');
        setTimeout(() => {
            this.showError('这是一个错误消息测试');
        }, 1000);
        setTimeout(() => {
            this.showToast('这是一个信息消息测试', 'info');
        }, 2000);
    }

    // ==================== 处理配置管理 ====================

    async loadProcessingRules() {
        try {
            console.log('📋 加载处理配置...');

            // 加载处理规则
            const rulesResponse = await fetch(`${this.apiBase}/processing-config/rules`);
            const rules = await rulesResponse.json();
            console.log('📊 处理规则数据:', rules);
            this.renderProcessingRules(rules);

            // 加载分类规则
            const classificationResponse = await fetch(`${this.apiBase}/processing-config/classification-rules`);
            const classificationRules = await classificationResponse.json();
            console.log('📊 分类规则数据:', classificationRules);
            this.renderClassificationRules(classificationRules);

        } catch (error) {
            console.error('❌ 加载处理配置失败:', error);
            this.showError('加载处理配置失败: ' + error.message);
        }
    }

    renderProcessingRules(rules) {
        const container = document.getElementById('processing-rules-container');
        if (!container) return;

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5>处理规则配置</h5>
                <button class="btn btn-primary btn-sm" onclick="app.showCreateRuleModal()">
                    <i class="fas fa-plus"></i> 添加规则
                </button>
            </div>

            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>规则名称</th>
                            <th>内容类别</th>
                            <th>处理策略</th>
                            <th>AI阈值</th>
                            <th>优先级</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rules.map(rule => `
                            <tr>
                                <td>
                                    <strong>${rule.display_name}</strong>
                                    <br><small class="text-muted">${rule.description || ''}</small>
                                </td>
                                <td>
                                    <span class="badge bg-info">${rule.content_category}</span>
                                    ${rule.is_default ? '<span class="badge bg-warning ms-1">默认</span>' : ''}
                                </td>
                                <td>${rule.processing_strategy}</td>
                                <td>${rule.ai_detection_threshold}%</td>
                                <td>${rule.priority}</td>
                                <td>
                                    <span class="badge ${rule.is_active ? 'bg-success' : 'bg-secondary'}">
                                        ${rule.is_active ? '启用' : '禁用'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary me-1"
                                            onclick="app.editProcessingRule(${rule.id})">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger"
                                            onclick="app.deleteProcessingRule(${rule.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderClassificationRules(rules) {
        const container = document.getElementById('classification-rules-container');
        if (!container) return;

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5>分类规则配置</h5>
                <button class="btn btn-primary btn-sm" onclick="app.showCreateClassificationRuleModal()">
                    <i class="fas fa-plus"></i> 添加分类规则
                </button>
            </div>

            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>规则名称</th>
                            <th>目标类别</th>
                            <th>关键词</th>
                            <th>阈值</th>
                            <th>优先级</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rules.map(rule => `
                            <tr>
                                <td>
                                    <strong>${rule.name}</strong>
                                    <br><small class="text-muted">${rule.description || ''}</small>
                                </td>
                                <td>
                                    <span class="badge bg-info">${rule.target_category}</span>
                                </td>
                                <td>
                                    <div class="small">
                                        ${rule.title_keywords && rule.title_keywords.length > 0 ?
                                            `<div><strong>标题:</strong> ${rule.title_keywords.slice(0, 3).join(', ')}${rule.title_keywords.length > 3 ? '...' : ''}</div>` : ''}
                                        ${rule.content_keywords && rule.content_keywords.length > 0 ?
                                            `<div><strong>内容:</strong> ${rule.content_keywords.slice(0, 3).join(', ')}${rule.content_keywords.length > 3 ? '...' : ''}</div>` : ''}
                                    </div>
                                </td>
                                <td>${(rule.classification_threshold * 100).toFixed(1)}%</td>
                                <td>${rule.priority}</td>
                                <td>
                                    <span class="badge ${rule.is_active ? 'bg-success' : 'bg-secondary'}">
                                        ${rule.is_active ? '启用' : '禁用'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary me-1"
                                            onclick="app.editClassificationRule(${rule.id})">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger"
                                            onclick="app.deleteClassificationRule(${rule.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // ==================== 处理规则编辑删除 ====================

    async editProcessingRule(ruleId) {
        try {
            console.log(`🔧 编辑处理规则: ${ruleId}`);
            this.showLoading('正在加载规则信息...');

            const response = await fetch(`${this.apiBase}/processing-config/rules/${ruleId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const rule = await response.json();
            console.log('📊 规则数据:', rule);
            this.showEditProcessingRuleModal(rule);

        } catch (error) {
            console.error('❌ 加载规则失败:', error);
            this.showError('加载规则失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteProcessingRule(ruleId) {
        if (!confirm('确定要删除这个处理规则吗？此操作不可撤销。')) {
            return;
        }

        try {
            console.log(`🗑️ 删除处理规则: ${ruleId}`);
            this.showLoading('正在删除规则...');

            const response = await fetch(`${this.apiBase}/processing-config/rules/${ruleId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('处理规则删除成功');
                await this.loadProcessingRules(); // 重新加载列表
            } else {
                const error = await response.json();
                this.showError('删除失败: ' + error.detail);
            }

        } catch (error) {
            console.error('❌ 删除规则失败:', error);
            this.showError('删除失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showEditProcessingRuleModal(rule) {
        // 创建编辑模态框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'editProcessingRuleModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">编辑处理规则</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editProcessingRuleForm">
                            <input type="hidden" id="editRuleId" value="${rule.id}">

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="editRuleName" class="form-label">规则名称</label>
                                        <input type="text" class="form-control" id="editRuleName" value="${rule.name}" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="editRuleDisplayName" class="form-label">显示名称</label>
                                        <input type="text" class="form-control" id="editRuleDisplayName" value="${rule.display_name}" required>
                                    </div>
                                </div>
                            </div>

                            <div class="mb-3">
                                <label for="editRuleDescription" class="form-label">描述</label>
                                <textarea class="form-control" id="editRuleDescription" rows="2">${rule.description || ''}</textarea>
                            </div>

                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRuleCategory" class="form-label">内容类别</label>
                                        <select class="form-select" id="editRuleCategory" required>
                                            <option value="technical" ${rule.content_category === 'technical' ? 'selected' : ''}>技术类</option>
                                            <option value="tutorial" ${rule.content_category === 'tutorial' ? 'selected' : ''}>教程类</option>
                                            <option value="news" ${rule.content_category === 'news' ? 'selected' : ''}>新闻类</option>
                                            <option value="general" ${rule.content_category === 'general' ? 'selected' : ''}>通用类</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRuleStrategy" class="form-label">处理策略</label>
                                        <select class="form-select" id="editRuleStrategy" required>
                                            <option value="basic" ${rule.processing_strategy === 'basic' ? 'selected' : ''}>基础</option>
                                            <option value="standard" ${rule.processing_strategy === 'standard' ? 'selected' : ''}>标准</option>
                                            <option value="advanced" ${rule.processing_strategy === 'advanced' ? 'selected' : ''}>高级</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRuleThreshold" class="form-label">AI检测阈值(%)</label>
                                        <input type="number" class="form-control" id="editRuleThreshold"
                                               value="${rule.ai_detection_threshold}" min="0" max="100" step="0.1" required>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRulePriority" class="form-label">优先级</label>
                                        <input type="number" class="form-control" id="editRulePriority"
                                               value="${rule.priority}" min="1" max="1000" required>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRuleMaxRounds" class="form-label">最大优化轮数</label>
                                        <input type="number" class="form-control" id="editRuleMaxRounds"
                                               value="${rule.max_optimization_rounds}" min="1" max="10" required>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="editRuleQualityThreshold" class="form-label">质量阈值</label>
                                        <input type="number" class="form-control" id="editRuleQualityThreshold"
                                               value="${rule.quality_threshold}" min="0" max="1" step="0.1" required>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="editRuleIsActive"
                                               ${rule.is_active ? 'checked' : ''}>
                                        <label class="form-check-label" for="editRuleIsActive">启用规则</label>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="editRuleIsDefault"
                                               ${rule.is_default ? 'checked' : ''}>
                                        <label class="form-check-label" for="editRuleIsDefault">设为默认规则</label>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="app.submitEditProcessingRule()">保存</button>
                    </div>
                </div>
            </div>
        `;

        // 添加到页面并显示
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        // 模态框关闭时移除元素
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async submitEditProcessingRule() {
        try {
            const form = document.getElementById('editProcessingRuleForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const ruleId = document.getElementById('editRuleId').value;
            const ruleData = {
                name: document.getElementById('editRuleName').value,
                display_name: document.getElementById('editRuleDisplayName').value,
                description: document.getElementById('editRuleDescription').value,
                content_category: document.getElementById('editRuleCategory').value,
                processing_strategy: document.getElementById('editRuleStrategy').value,
                ai_detection_threshold: parseFloat(document.getElementById('editRuleThreshold').value),
                priority: parseInt(document.getElementById('editRulePriority').value),
                max_optimization_rounds: parseInt(document.getElementById('editRuleMaxRounds').value),
                quality_threshold: parseFloat(document.getElementById('editRuleQualityThreshold').value),
                is_active: document.getElementById('editRuleIsActive').checked,
                is_default: document.getElementById('editRuleIsDefault').checked
            };

            console.log('📤 提交规则更新:', ruleData);
            this.showLoading('正在保存规则...');

            const response = await fetch(`${this.apiBase}/processing-config/rules/${ruleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ruleData)
            });

            if (response.ok) {
                this.showSuccess('处理规则更新成功');

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProcessingRuleModal'));
                modal.hide();

                // 重新加载列表
                await this.loadProcessingRules();
            } else {
                const error = await response.json();
                this.showError('保存失败: ' + error.detail);
            }

        } catch (error) {
            console.error('❌ 保存规则失败:', error);
            this.showError('保存失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ==================== 分类测试和准确率分析 ====================

    showTestClassificationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'testClassificationModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">测试文章分类</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="testArticleTitle" class="form-label">文章标题</label>
                            <input type="text" class="form-control" id="testArticleTitle"
                                   placeholder="输入文章标题进行分类测试">
                        </div>
                        <div class="mb-3">
                            <label for="testArticleContent" class="form-label">文章内容（前500字）</label>
                            <textarea class="form-control" id="testArticleContent" rows="6"
                                      placeholder="输入文章内容进行分类测试"></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="testArticleUrl" class="form-label">文章URL（可选）</label>
                            <input type="url" class="form-control" id="testArticleUrl"
                                   placeholder="https://example.com/article">
                        </div>
                        <div id="classificationResult" class="mt-3" style="display: none;">
                            <h6>分类结果：</h6>
                            <div id="resultContent"></div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="app.performTestClassification()">开始分类</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    async performTestClassification() {
        try {
            const title = document.getElementById('testArticleTitle').value;
            const content = document.getElementById('testArticleContent').value;
            const url = document.getElementById('testArticleUrl').value;

            if (!title && !content) {
                this.showError('请至少输入标题或内容');
                return;
            }

            this.showLoading('正在分析文章分类...');

            // 模拟文章对象进行分类测试
            const testArticle = {
                title: title,
                content_original: content,
                source_url: url || 'https://example.com/test'
            };

            // 调用分类逻辑
            const result = await this.classifyTestArticle(testArticle);
            this.displayClassificationResult(result);

        } catch (error) {
            console.error('❌ 分类测试失败:', error);
            this.showError('分类测试失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async classifyTestArticle(article) {
        // 获取分类规则
        const rulesResponse = await fetch(`${this.apiBase}/processing-config/classification-rules?active_only=true`);
        const rules = await rulesResponse.json();

        const categoryScores = {};

        for (const rule of rules) {
            const score = this.calculateClassificationScore(article, rule);

            if (score >= rule.classification_threshold) {
                if (!categoryScores[rule.target_category] || score > categoryScores[rule.target_category]) {
                    categoryScores[rule.target_category] = score;
                }
            }
        }

        if (Object.keys(categoryScores).length > 0) {
            const bestCategory = Object.entries(categoryScores).reduce((a, b) => a[1] > b[1] ? a : b);
            return {
                category: bestCategory[0],
                confidence: bestCategory[1],
                allScores: categoryScores,
                rulesApplied: rules.length
            };
        } else {
            return {
                category: 'general',
                confidence: 0.3,
                allScores: {},
                rulesApplied: rules.length
            };
        }
    }

    calculateClassificationScore(article, rule) {
        let totalScore = 0.0;

        // 标题关键词匹配
        if (rule.title_keywords && article.title) {
            const titleScore = this.calculateKeywordScore(
                article.title.toLowerCase(), rule.title_keywords
            );
            totalScore += titleScore * rule.title_weight;
        }

        // 内容关键词匹配
        if (rule.content_keywords && article.content_original) {
            const contentScore = this.calculateKeywordScore(
                article.content_original.toLowerCase().substring(0, 1000), rule.content_keywords
            );
            totalScore += contentScore * rule.content_weight;
        }

        // URL模式匹配
        if (rule.url_patterns && article.source_url) {
            const urlScore = this.calculatePatternScore(
                article.source_url.toLowerCase(), rule.url_patterns
            );
            totalScore += urlScore * rule.url_weight;
        }

        // 域名匹配
        if (rule.source_domains && article.source_url) {
            const domainScore = this.calculateDomainScore(
                article.source_url, rule.source_domains
            );
            totalScore += domainScore * rule.domain_weight;
        }

        return Math.min(totalScore, 1.0);
    }

    calculateKeywordScore(text, keywords) {
        if (!keywords || !text) return 0.0;
        const matches = keywords.filter(keyword => text.includes(keyword.toLowerCase())).length;
        return matches / keywords.length;
    }

    calculatePatternScore(text, patterns) {
        if (!patterns || !text) return 0.0;
        const matches = patterns.filter(pattern => {
            try {
                return new RegExp(pattern, 'i').test(text);
            } catch (e) {
                return text.includes(pattern.toLowerCase());
            }
        }).length;
        return matches / patterns.length;
    }

    calculateDomainScore(url, domains) {
        if (!domains || !url) return 0.0;
        const matches = domains.filter(domain => url.toLowerCase().includes(domain.toLowerCase())).length;
        return matches > 0 ? 1.0 : 0.0;
    }

    displayClassificationResult(result) {
        const resultDiv = document.getElementById('classificationResult');
        const contentDiv = document.getElementById('resultContent');

        const categoryNames = {
            'technical': '技术类',
            'tutorial': '教程类',
            'news': '新闻类',
            'business': '商业类',
            'lifestyle': '生活类',
            'entertainment': '娱乐类',
            'general': '通用类'
        };

        let html = `
            <div class="alert alert-info">
                <h6><i class="fas fa-tag"></i> 分类结果：${categoryNames[result.category] || result.category}</h6>
                <p><strong>置信度：</strong>${(result.confidence * 100).toFixed(1)}%</p>
                <p><strong>应用规则数：</strong>${result.rulesApplied}</p>
            </div>
        `;

        if (Object.keys(result.allScores).length > 0) {
            html += `
                <h6>所有类别得分：</h6>
                <div class="row">
            `;

            for (const [category, score] of Object.entries(result.allScores)) {
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex justify-content-between">
                            <span>${categoryNames[category] || category}:</span>
                            <span class="badge bg-primary">${(score * 100).toFixed(1)}%</span>
                        </div>
                        <div class="progress" style="height: 8px;">
                            <div class="progress-bar" style="width: ${score * 100}%"></div>
                        </div>
                    </div>
                `;
            }

            html += `</div>`;
        }

        contentDiv.innerHTML = html;
        resultDiv.style.display = 'block';
    }

    async testArticleClassification(articleId) {
        try {
            console.log(`🔍 测试文章分类: ${articleId}`);
            this.showLoading('正在分析文章...');

            const response = await fetch(`${this.apiBase}/processing-config/classify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    article_id: parseInt(articleId)
                })
            });

            const result = await response.json();
            console.log('📊 分类结果:', result);

            this.showClassificationResult(result);

        } catch (error) {
            console.error('❌ 文章分类失败:', error);
            this.showError('文章分类失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async showClassificationAccuracyReport() {
        try {
            this.showLoading('正在生成准确率报告...');

            // 获取所有文章和分类规则
            const [articlesResponse, rulesResponse] = await Promise.all([
                fetch(`${this.apiBase}/articles`),
                fetch(`${this.apiBase}/processing-config/classification-rules?active_only=true`)
            ]);

            const articles = await articlesResponse.json();
            const rules = await rulesResponse.json();

            // 分析分类准确率
            const report = this.generateAccuracyReport(articles, rules);
            this.displayAccuracyReport(report);

        } catch (error) {
            console.error('❌ 生成准确率报告失败:', error);
            this.showError('生成准确率报告失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    generateAccuracyReport(articles, rules) {
        const categoryStats = {
            'technical': { total: 0, classified: 0, correct: 0 },
            'tutorial': { total: 0, classified: 0, correct: 0 },
            'news': { total: 0, classified: 0, correct: 0 },
            'business': { total: 0, classified: 0, correct: 0 },
            'lifestyle': { total: 0, classified: 0, correct: 0 },
            'entertainment': { total: 0, classified: 0, correct: 0 },
            'general': { total: 0, classified: 0, correct: 0 }
        };

        const classificationResults = [];

        for (const article of articles) {
            // 模拟分类
            const result = this.classifyTestArticleSync(article, rules);

            // 基于标题和内容推测实际类别（简单启发式）
            const actualCategory = this.guessActualCategory(article);

            categoryStats[actualCategory].total++;

            if (result.category) {
                categoryStats[result.category].classified++;

                if (result.category === actualCategory) {
                    categoryStats[actualCategory].correct++;
                }
            }

            classificationResults.push({
                title: article.title,
                predicted: result.category,
                actual: actualCategory,
                confidence: result.confidence,
                correct: result.category === actualCategory
            });
        }

        // 计算总体准确率
        const totalArticles = articles.length;
        const totalCorrect = Object.values(categoryStats).reduce((sum, stat) => sum + stat.correct, 0);
        const overallAccuracy = totalArticles > 0 ? (totalCorrect / totalArticles) * 100 : 0;

        return {
            overallAccuracy,
            categoryStats,
            classificationResults: classificationResults.slice(0, 20), // 只显示前20个
            totalArticles,
            rulesCount: rules.length
        };
    }

    classifyTestArticleSync(article, rules) {
        const categoryScores = {};

        for (const rule of rules) {
            const score = this.calculateClassificationScore(article, rule);

            if (score >= rule.classification_threshold) {
                if (!categoryScores[rule.target_category] || score > categoryScores[rule.target_category]) {
                    categoryScores[rule.target_category] = score;
                }
            }
        }

        if (Object.keys(categoryScores).length > 0) {
            const bestCategory = Object.entries(categoryScores).reduce((a, b) => a[1] > b[1] ? a : b);
            return {
                category: bestCategory[0],
                confidence: bestCategory[1]
            };
        } else {
            return {
                category: 'general',
                confidence: 0.3
            };
        }
    }

    guessActualCategory(article) {
        const title = (article.title || '').toLowerCase();
        const content = (article.content_original || '').toLowerCase().substring(0, 500);
        const text = title + ' ' + content;

        // 技术类关键词
        const techKeywords = ['api', 'python', 'javascript', 'react', 'vue', '技术', '编程', '开发', '代码', '算法'];
        const techCount = techKeywords.filter(keyword => text.includes(keyword)).length;

        // 教程类关键词
        const tutorialKeywords = ['教程', '指南', '如何', '步骤', 'tutorial', 'guide', 'how to'];
        const tutorialCount = tutorialKeywords.filter(keyword => text.includes(keyword)).length;

        // 新闻类关键词
        const newsKeywords = ['新闻', '报道', '发布', '最新', 'news', 'breaking', 'announcement'];
        const newsCount = newsKeywords.filter(keyword => text.includes(keyword)).length;

        if (techCount >= 2) return 'technical';
        if (tutorialCount >= 1) return 'tutorial';
        if (newsCount >= 1) return 'news';
        return 'general';
    }

    displayAccuracyReport(report) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'accuracyReportModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">分类准确率报告</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h4 class="text-primary">${report.overallAccuracy.toFixed(1)}%</h4>
                                        <p class="card-text">总体准确率</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h4 class="text-info">${report.totalArticles}</h4>
                                        <p class="card-text">测试文章数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h4 class="text-success">${report.rulesCount}</h4>
                                        <p class="card-text">分类规则数</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h4 class="text-warning">${Object.values(report.categoryStats).reduce((sum, stat) => sum + stat.correct, 0)}</h4>
                                        <p class="card-text">正确分类数</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <h6>各类别准确率：</h6>
                        <div class="table-responsive mb-4">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>类别</th>
                                        <th>总数</th>
                                        <th>正确分类</th>
                                        <th>准确率</th>
                                        <th>进度</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(report.categoryStats).map(([category, stats]) => {
                                        const accuracy = stats.total > 0 ? (stats.correct / stats.total) * 100 : 0;
                                        const categoryNames = {
                                            'technical': '技术类',
                                            'tutorial': '教程类',
                                            'news': '新闻类',
                                            'business': '商业类',
                                            'lifestyle': '生活类',
                                            'entertainment': '娱乐类',
                                            'general': '通用类'
                                        };
                                        return `
                                            <tr>
                                                <td>${categoryNames[category] || category}</td>
                                                <td>${stats.total}</td>
                                                <td>${stats.correct}</td>
                                                <td>${accuracy.toFixed(1)}%</td>
                                                <td>
                                                    <div class="progress" style="height: 20px;">
                                                        <div class="progress-bar ${accuracy >= 80 ? 'bg-success' : accuracy >= 60 ? 'bg-warning' : 'bg-danger'}"
                                                             style="width: ${accuracy}%">${accuracy.toFixed(1)}%</div>
                                                    </div>
                                                </td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>

                        <h6>分类详情（前20条）：</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>文章标题</th>
                                        <th>预测类别</th>
                                        <th>实际类别</th>
                                        <th>置信度</th>
                                        <th>结果</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${report.classificationResults.map(result => `
                                        <tr class="${result.correct ? 'table-success' : 'table-danger'}">
                                            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${result.title}</td>
                                            <td><span class="badge bg-primary">${result.predicted}</span></td>
                                            <td><span class="badge bg-secondary">${result.actual}</span></td>
                                            <td>${(result.confidence * 100).toFixed(1)}%</td>
                                            <td>
                                                <i class="fas ${result.correct ? 'fa-check text-success' : 'fa-times text-danger'}"></i>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="app.exportAccuracyReport()">导出报告</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    exportAccuracyReport() {
        // 简单的导出功能
        this.showToast('导出功能开发中...', 'info');
    }

    // ==================== AI智能分类测试 ====================

    showAIClassificationTest() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'aiClassificationTestModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">🤖 AI智能翻译和分类测试</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>输入文章信息</h6>
                                <div class="mb-3">
                                    <label for="aiTestTitle" class="form-label">文章标题</label>
                                    <input type="text" class="form-control" id="aiTestTitle"
                                           placeholder="输入英文或中文标题">
                                </div>
                                <div class="mb-3">
                                    <label for="aiTestContent" class="form-label">文章内容</label>
                                    <textarea class="form-control" id="aiTestContent" rows="8"
                                              placeholder="输入文章内容（支持英文和中文）"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="aiTestUrl" class="form-label">来源URL（可选）</label>
                                    <input type="url" class="form-control" id="aiTestUrl"
                                           placeholder="https://example.com/article">
                                </div>
                                <div class="mb-3">
                                    <label for="aiTestLanguage" class="form-label">目标语言</label>
                                    <select class="form-select" id="aiTestLanguage">
                                        <option value="中文">中文</option>
                                        <option value="English">English</option>
                                    </select>
                                </div>
                                <button type="button" class="btn btn-primary w-100" onclick="app.performAIClassificationTest()">
                                    <i class="fas fa-robot me-1"></i>开始AI智能分析
                                </button>
                            </div>
                            <div class="col-md-6">
                                <h6>AI分析结果</h6>
                                <div id="aiTestResults" class="border rounded p-3" style="min-height: 400px; background-color: #f8f9fa;">
                                    <div class="text-center text-muted">
                                        <i class="fas fa-robot fa-3x mb-3"></i>
                                        <p>等待AI分析...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-4">
                            <h6>预设测试用例</h6>
                            <div class="row">
                                <div class="col-md-4">
                                    <button class="btn btn-outline-primary btn-sm w-100 mb-2"
                                            onclick="app.loadTestCase('technical')">技术类文章</button>
                                </div>
                                <div class="col-md-4">
                                    <button class="btn btn-outline-success btn-sm w-100 mb-2"
                                            onclick="app.loadTestCase('tutorial')">教程类文章</button>
                                </div>
                                <div class="col-md-4">
                                    <button class="btn btn-outline-info btn-sm w-100 mb-2"
                                            onclick="app.loadTestCase('news')">新闻类文章</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-success" onclick="app.compareWithTraditionalClassification()">
                            <i class="fas fa-balance-scale me-1"></i>对比传统分类
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    loadTestCase(type) {
        const testCases = {
            'technical': {
                title: 'Building a REST API with Python Flask',
                content: `In this tutorial, we'll learn how to build a REST API using Python Flask framework. Flask is a lightweight web framework that makes it easy to create web applications and APIs.

First, let's install Flask:
pip install flask

Then we'll create a simple API endpoint:

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'users': ['Alice', 'Bob', 'Charlie']})

if __name__ == '__main__':
    app.run(debug=True)

This creates a basic API that returns a list of users when you make a GET request to /api/users.`,
                url: 'https://medium.com/python-tutorial'
            },
            'tutorial': {
                title: 'How to Cook Perfect Pasta: A Step-by-Step Guide',
                content: `Cooking perfect pasta is easier than you think! Follow these simple steps to get restaurant-quality results at home.

Step 1: Choose the right pasta
Different pasta shapes work better with different sauces. Long pasta like spaghetti pairs well with oil-based sauces.

Step 2: Use plenty of water
Use at least 4 quarts of water for every pound of pasta. This prevents the pasta from sticking together.

Step 3: Salt the water generously
Add about 1 tablespoon of salt per quart of water. The water should taste like seawater.

Step 4: Don't add oil to the water
Contrary to popular belief, adding oil to pasta water doesn't prevent sticking and can actually make sauce slide off the pasta.`,
                url: 'https://example.com/cooking-guide'
            },
            'news': {
                title: 'OpenAI Announces GPT-5 with Revolutionary Capabilities',
                content: `San Francisco, CA - OpenAI today announced the release of GPT-5, the latest iteration of their groundbreaking language model. The new model demonstrates significant improvements in reasoning, coding, and multimodal understanding.

Key features of GPT-5 include:
- Enhanced reasoning capabilities
- Better code generation and debugging
- Improved factual accuracy
- Advanced multimodal processing

CEO Sam Altman stated: "GPT-5 represents a major leap forward in AI capabilities. We're excited to see how developers and researchers will use these new features."

The model will be available to API users starting next month, with ChatGPT Plus subscribers getting early access.`,
                url: 'https://techcrunch.com/ai-news'
            }
        };

        const testCase = testCases[type];
        if (testCase) {
            document.getElementById('aiTestTitle').value = testCase.title;
            document.getElementById('aiTestContent').value = testCase.content;
            document.getElementById('aiTestUrl').value = testCase.url;
        }
    }

    async performAIClassificationTest() {
        try {
            const title = document.getElementById('aiTestTitle').value;
            const content = document.getElementById('aiTestContent').value;
            const url = document.getElementById('aiTestUrl').value;
            const language = document.getElementById('aiTestLanguage').value;

            if (!title && !content) {
                this.showError('请至少输入标题或内容');
                return;
            }

            const resultsDiv = document.getElementById('aiTestResults');
            resultsDiv.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">AI正在分析中...</p>
                </div>
            `;

            // 调用AI智能翻译和分类API
            const response = await fetch('/api/test-ai-classification', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    source_url: url || 'https://example.com/test',
                    target_language: language
                })
            });

            const result = await response.json();
            this.displayAITestResults(result);

        } catch (error) {
            console.error('❌ AI分类测试失败:', error);
            document.getElementById('aiTestResults').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    测试失败: ${error.message}
                </div>
            `;
        }
    }

    displayAITestResults(result) {
        const resultsDiv = document.getElementById('aiTestResults');

        if (result.success) {
            const classification = result.classification;
            const categoryNames = {
                'technical': '技术类',
                'tutorial': '教程类',
                'news': '新闻类',
                'business': '商业类',
                'lifestyle': '生活类',
                'entertainment': '娱乐类',
                'general': '通用类'
            };

            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle"></i> AI分析完成</h6>
                </div>

                <div class="mb-3">
                    <h6>🏷️ 分类结果</h6>
                    <div class="card">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-6">
                                    <strong>类别:</strong>
                                    <span class="badge bg-primary fs-6">${categoryNames[classification.category] || classification.category}</span>
                                </div>
                                <div class="col-6">
                                    <strong>置信度:</strong>
                                    <span class="badge bg-success fs-6">${(classification.confidence * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                            <div class="mt-2">
                                <strong>分析理由:</strong><br>
                                <small class="text-muted">${classification.reasoning}</small>
                            </div>
                            <div class="mt-2">
                                <strong>分类方法:</strong>
                                <span class="badge bg-info">${classification.method}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mb-3">
                    <h6>📄 翻译结果</h6>
                    <div class="card">
                        <div class="card-body">
                            <div class="mb-2">
                                <strong>翻译标题:</strong><br>
                                <div class="bg-light p-2 rounded">${result.translated_title}</div>
                            </div>
                            <div>
                                <strong>翻译内容:</strong><br>
                                <div class="bg-light p-2 rounded" style="max-height: 200px; overflow-y: auto;">
                                    ${result.translated_content.substring(0, 500)}${result.translated_content.length > 500 ? '...' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                ${result.usage ? `
                <div class="mb-3">
                    <h6>💰 Token使用情况</h6>
                    <div class="small text-muted">
                        输入: ${result.usage.prompt_tokens || 0} |
                        输出: ${result.usage.completion_tokens || 0} |
                        总计: ${result.usage.total_tokens || 0}
                    </div>
                </div>
                ` : ''}
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle"></i> 分析失败</h6>
                    <p>${result.error || '未知错误'}</p>
                </div>
            `;
        }
    }

    async compareWithTraditionalClassification() {
        // 对比传统分类方法的功能
        this.showToast('传统分类对比功能开发中...', 'info');
    }

    showClassificationResult(result) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">文章分类结果</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>分类信息</h6>
                                <p><strong>内容类别:</strong>
                                   <span class="badge bg-info">${result.content_category}</span>
                                </p>
                                <p><strong>置信度:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
                                <p><strong>处理规则ID:</strong> ${result.processing_rule_id || '无'}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>处理配置</h6>
                                <pre class="bg-light p-2 rounded">${JSON.stringify(result.configuration, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    showTestClassificationModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">测试文章分类</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="testClassificationForm">
                            <div class="mb-3">
                                <label for="articleId" class="form-label">文章ID</label>
                                <input type="number" class="form-control" id="articleId"
                                       placeholder="请输入要测试的文章ID" required>
                                <div class="form-text">输入现有文章的ID来测试智能分类功能</div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="app.executeTestClassification()">
                            <i class="fas fa-flask me-1"></i>开始测试
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    executeTestClassification() {
        const articleId = document.getElementById('articleId').value;
        if (!articleId) {
            this.showError('请输入文章ID');
            return;
        }

        // 关闭模态框
        const modal = document.querySelector('.modal.show');
        if (modal) {
            bootstrap.Modal.getInstance(modal).hide();
        }

        // 执行测试
        this.testArticleClassification(articleId);
    }

    async validateApiUrl() {
        const apiUrlInput = document.getElementById('editProviderApiUrl');
        if (!apiUrlInput) {
            this.showError('找不到API URL输入框');
            return;
        }

        const apiUrl = apiUrlInput.value.trim();
        if (!apiUrl) {
            this.showError('请输入API URL');
            return;
        }

        // 简单的URL格式验证
        try {
            const url = new URL(apiUrl);

            // 检查URL格式
            if (!url.protocol.startsWith('http')) {
                this.showError('❌ URL必须以http://或https://开头');
                apiUrlInput.classList.remove('is-valid');
                apiUrlInput.classList.add('is-invalid');
                return;
            }

            // 检查是否包含必要的路径
            if (!apiUrl.includes('/chat/completions') && !apiUrl.includes('/v1')) {
                this.showError('⚠️ URL可能不正确，建议包含/v1/chat/completions路径');
                apiUrlInput.classList.remove('is-valid');
                apiUrlInput.classList.add('is-invalid');
                return;
            }

            // 基本格式验证通过
            this.showSuccess('✅ URL格式验证通过！');
            apiUrlInput.classList.remove('is-invalid');
            apiUrlInput.classList.add('is-valid');

        } catch (error) {
            console.error('URL格式验证失败:', error);
            this.showError('❌ URL格式不正确，请检查格式');
            apiUrlInput.classList.remove('is-valid');
            apiUrlInput.classList.add('is-invalid');
        }
    }

    resetApiUrl() {
        const apiUrlInput = document.getElementById('editProviderApiUrl');
        if (!apiUrlInput) {
            this.showError('找不到API URL输入框');
            return;
        }

        // 重置为推荐的本地API地址
        const recommendedUrl = 'http://localhost:8000/v1/chat/completions';
        apiUrlInput.value = recommendedUrl;

        // 清除验证状态
        apiUrlInput.classList.remove('is-valid', 'is-invalid');

        this.showSuccess('✅ API URL已重置为推荐地址');
        console.log('🔄 API URL已重置为:', recommendedUrl);
    }

    showLoading(message = '加载中...') {
        console.log(`🔄 显示加载指示器: ${message}`);

        // 创建或显示全局加载指示器
        let loadingElement = document.getElementById('global-loading');
        if (!loadingElement) {
            loadingElement = document.createElement('div');
            loadingElement.id = 'global-loading';
            loadingElement.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            loadingElement.style.cssText = `
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 9999;
                backdrop-filter: blur(2px);
            `;
            loadingElement.innerHTML = `
                <div class="bg-white rounded-3 p-4 text-center shadow-lg">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="text-muted" id="loading-message">${message}</div>
                </div>
            `;
            document.body.appendChild(loadingElement);
        } else {
            const messageElement = loadingElement.querySelector('#loading-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
            loadingElement.style.display = 'flex';
        }
    }

    hideLoading() {
        console.log('🔄 隐藏加载指示器');

        const loadingElement = document.getElementById('global-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
            console.log('✅ 加载指示器已隐藏');

            // 确保加载指示器完全移除
            setTimeout(() => {
                if (loadingElement && loadingElement.style.display === 'none') {
                    loadingElement.remove();
                    console.log('🗑️ 加载指示器已移除');
                }
            }, 100);
        } else {
            console.warn('⚠️ 找不到加载指示器元素');
        }
    }

    showSuccess(message) {
        console.log(`✅ 成功消息: ${message}`);
        this.showToast(message, 'success');
    }

    showError(message) {
        console.error(`❌ 错误消息: ${message}`);
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        try {
            console.log(`🍞 显示Toast: ${type} - ${message}`);

            // 创建toast容器（如果不存在）
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'position-fixed top-0 end-0 p-3';
                toastContainer.style.zIndex = '10001'; // 比加载指示器更高
                document.body.appendChild(toastContainer);
                console.log('📦 创建了Toast容器');
            }

            // 创建toast元素
            const toastId = 'toast-' + Date.now();
            const toastClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
            const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle';

            const toastElement = document.createElement('div');
            toastElement.id = toastId;
            toastElement.className = `toast align-items-center text-white ${toastClass} border-0`;
            toastElement.setAttribute('role', 'alert');
            toastElement.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-${icon} me-2"></i>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            toastContainer.appendChild(toastElement);
            console.log(`📝 创建了Toast元素: ${toastId}`);

            // 检查Bootstrap是否可用
            if (typeof bootstrap === 'undefined') {
                console.error('❌ Bootstrap未加载，无法显示Toast');
                // 降级处理：使用alert
                alert(`${type.toUpperCase()}: ${message}`);
                return;
            }

            // 显示toast
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: type === 'error' ? 5000 : 3000
            });

            console.log('🎭 显示Toast...');
            toast.show();

            // 自动清理
            toastElement.addEventListener('hidden.bs.toast', () => {
                console.log(`🗑️ 清理Toast: ${toastId}`);
                toastElement.remove();
            });

        } catch (error) {
            console.error('❌ 显示Toast失败:', error);
            // 降级处理：使用alert
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }

    // 一键复制文章内容
    async copyArticleContent(articleId) {
        try {
            const response = await fetch(`/api/articles/${articleId}`);
            if (!response.ok) {
                throw new Error('获取文章内容失败');
            }

            const article = await response.json();

            // 构建要复制的内容
            let contentToCopy = '';

            // 添加标题
            if (article.title) {
                contentToCopy += `标题：${article.title}\n\n`;
            }

            // 添加优化后的内容（如果有）
            if (article.optimized_content) {
                contentToCopy += `优化后内容：\n${article.optimized_content}\n\n`;
            }

            // 添加原始内容（如果没有优化内容）
            if (!article.optimized_content && article.original_content) {
                contentToCopy += `原始内容：\n${article.original_content}\n\n`;
            }

            // 添加来源信息
            if (article.source_url) {
                contentToCopy += `来源：${article.source_url}\n`;
            }

            // 使用现代浏览器的Clipboard API
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(contentToCopy);
                this.showSuccess('文章内容已复制到剪贴板！');
            } else {
                // 降级方案：使用传统方法
                const textArea = document.createElement('textarea');
                textArea.value = contentToCopy;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();

                try {
                    document.execCommand('copy');
                    this.showSuccess('文章内容已复制到剪贴板！');
                } catch (err) {
                    this.showError('复制失败，请手动复制内容');
                }

                document.body.removeChild(textArea);
            }

        } catch (error) {
            console.error('❌ 复制文章内容失败:', error);
            this.showError('复制失败：' + error.message);
        }
    }

    // 切换发布状态
    async togglePublishStatus(articleId, action) {
        try {
            const response = await fetch(`/api/articles/${articleId}/publish`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: action })
            });

            if (!response.ok) {
                throw new Error('更新发布状态失败');
            }

            const result = await response.json();

            if (action === 'publish') {
                this.showSuccess('文章已标记为已发布！');
            } else {
                this.showSuccess('文章发布状态已取消！');
            }

            // 刷新文章列表
            this.loadArticlesData();

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('articleDetailModal'));
            if (modal) {
                modal.hide();
            }

        } catch (error) {
            console.error('❌ 切换发布状态失败:', error);
            this.showError('操作失败：' + error.message);
        }
    }

    // ==================== AI优化配置管理 ====================

    async loadAIOptimizationConfig() {
        try {
            const response = await fetch(`${this.apiBase}/config/ai-optimization`);
            if (!response.ok) {
                throw new Error('获取配置失败');
            }

            const result = await response.json();
            const config = result.config;

            // 填充表单
            document.getElementById('maxAttempts').value = config.max_attempts;
            document.getElementById('aiThreshold').value = config.threshold;
            document.getElementById('retryDelay').value = config.retry_delay_seconds;
            document.getElementById('enableProgressiveOptimization').checked = config.enable_progressive_optimization;

            this.showSuccess('AI优化配置已加载');

        } catch (error) {
            console.error('❌ 加载AI优化配置失败:', error);
            this.showError('加载配置失败：' + error.message);
        }
    }

    async saveAIOptimizationConfig() {
        try {
            const config = {
                max_attempts: parseInt(document.getElementById('maxAttempts').value),
                threshold: parseFloat(document.getElementById('aiThreshold').value),
                retry_delay_seconds: parseInt(document.getElementById('retryDelay').value),
                enable_progressive_optimization: document.getElementById('enableProgressiveOptimization').checked
            };

            // 验证配置
            if (config.max_attempts < 1 || config.max_attempts > 20) {
                throw new Error('最大尝试次数必须在1-20之间');
            }

            if (config.threshold < 0 || config.threshold > 100) {
                throw new Error('AI浓度阈值必须在0-100之间');
            }

            if (config.retry_delay_seconds < 0 || config.retry_delay_seconds > 60) {
                throw new Error('重试间隔必须在0-60秒之间');
            }

            const response = await fetch(`${this.apiBase}/config/ai-optimization`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '保存配置失败');
            }

            const result = await response.json();
            this.showSuccess('AI优化配置已保存');

        } catch (error) {
            console.error('❌ 保存AI优化配置失败:', error);
            this.showError('保存配置失败：' + error.message);
        }
    }

    resetAIOptimizationConfig() {
        // 恢复默认值
        document.getElementById('maxAttempts').value = 5;
        document.getElementById('aiThreshold').value = 25.0;
        document.getElementById('retryDelay').value = 2;
        document.getElementById('enableProgressiveOptimization').checked = true;

        this.showInfo('已恢复默认配置，请点击保存按钮应用更改');
    }
}



// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function truncateText(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('🚀 开始初始化应用...');
        window.app = new ArticleMigrationApp();
        console.log('✅ 应用初始化成功');
    } catch (error) {
        console.error('❌ 应用初始化失败:', error);
    }
});

// Global function for topic creation submit (backup method)
window.handleTopicCreationSubmit = function() {
    console.log('🌍 全局函数被调用: handleTopicCreationSubmit');
    if (window.app && typeof window.app.submitTopicCreation === 'function') {
        console.log('✅ 调用 app.submitTopicCreation()');
        window.app.submitTopicCreation();
    } else {
        console.error('❌ window.app 或 submitTopicCreation 方法不存在');
        console.log('🔍 window.app:', window.app);
    }
};
