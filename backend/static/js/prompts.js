/**
 * 提示词管理页面的JavaScript功能
 */

let currentPage = 1;
let pageSize = 12;
let selectedTemplates = new Set();
let searchTimeout;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    setupEventListeners();
    setupNavigation();
});

// 设置导航功能
function setupNavigation() {
    // 处理导航链接点击
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            // 如果是主页面的标签链接，进行特殊处理
            if (href && href.startsWith('/#')) {
                e.preventDefault();
                const tabName = href.substring(2); // 移除 '/#' 前缀

                // 跳转到主页面并激活对应标签
                window.location.href = `/?tab=${tabName}`;
            }
        });
    });
}

// 设置事件监听器
function setupEventListeners() {
    // 模态框关闭时重置表单
    document.getElementById('templateModal').addEventListener('hidden.bs.modal', function() {
        resetTemplateForm();
    });
    
    // 提示词内容变化时自动提取变量
    document.getElementById('templateContent').addEventListener('input', function() {
        extractVariables();
    });
}

// 加载提示词列表
async function loadTemplates() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            sort_by: document.getElementById('sortBy').value,
            sort_order: 'desc'
        });
        
        // 添加筛选条件
        const typeFilter = document.getElementById('typeFilter').value;
        if (typeFilter) params.append('type', typeFilter);
        
        const statusFilter = document.getElementById('statusFilter').value;
        if (statusFilter === 'active') params.append('active_only', 'true');
        
        const searchInput = document.getElementById('searchInput').value;
        if (searchInput) params.append('search', searchInput);
        
        const response = await fetch(`/api/v1/prompts?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            renderTemplates(data.templates);
            renderPagination(data.total, data.page, data.page_size);
            updateStatistics(data.templates);
        } else {
            showError('加载提示词失败: ' + data.detail);
        }
    } catch (error) {
        showError('加载提示词失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 渲染提示词列表
function renderTemplates(templates) {
    const container = document.getElementById('templatesContainer');
    
    if (templates.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="bi bi-chat-text-fill text-muted" style="font-size: 3rem;"></i>
                    <h5 class="text-muted mt-3">暂无提示词</h5>
                    <p class="text-muted">点击"新建提示词"开始创建您的第一个提示词模板</p>
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = templates.map(template => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card template-card ${!template.is_active ? 'inactive' : ''} ${template.is_default ? 'default' : ''}" 
                 data-template-id="${template.id}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <input type="checkbox" class="form-check-input me-2" 
                               onchange="toggleSelection(${template.id})" 
                               ${selectedTemplates.has(template.id) ? 'checked' : ''}>
                        <h6 class="mb-0">${escapeHtml(template.display_name)}</h6>
                    </div>
                    <div class="template-actions">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editTemplate(${template.id})" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-secondary" onclick="duplicateTemplate(${template.id})" title="复制">
                                <i class="bi bi-files"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteTemplate(${template.id})" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="mb-2">
                        <span class="badge bg-primary badge-type">${getTypeDisplayName(template.type)}</span>
                        ${template.is_default ? '<span class="badge bg-success ms-1">默认</span>' : ''}
                        ${!template.is_active ? '<span class="badge bg-secondary ms-1">禁用</span>' : ''}
                        <span class="badge bg-info ms-1">v${template.version}</span>
                    </div>
                    
                    ${template.description ? `<p class="text-muted small mb-2">${escapeHtml(template.description)}</p>` : ''}
                    
                    <div class="template-preview mb-2">
                        ${escapeHtml(template.template.substring(0, 200))}${template.template.length > 200 ? '...' : ''}
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted">
                                <i class="bi bi-eye"></i> ${template.usage_count}
                                <i class="bi bi-star ms-2"></i> ${template.success_rate.toFixed(1)}%
                            </small>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="previewTemplate(${template.id})">
                                预览
                            </button>
                            <button class="btn btn-sm ${template.is_active ? 'btn-warning' : 'btn-success'}" 
                                    onclick="toggleTemplateStatus(${template.id}, ${!template.is_active})">
                                ${template.is_active ? '禁用' : '启用'}
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-footer text-muted small">
                    <div class="d-flex justify-content-between">
                        <span>创建: ${formatDate(template.created_at)}</span>
                        <span>更新: ${formatDate(template.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// 渲染分页
function renderPagination(total, page, pageSize) {
    const totalPages = Math.ceil(total / pageSize);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一页
    paginationHTML += `
        <li class="page-item ${page <= 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page - 1})">上一页</a>
        </li>
    `;
    
    // 页码
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages})">${totalPages}</a></li>`;
    }
    
    // 下一页
    paginationHTML += `
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page + 1})">下一页</a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// 更新统计信息
function updateStatistics(templates) {
    const total = templates.length;
    const active = templates.filter(t => t.is_active).length;
    const defaultCount = templates.filter(t => t.is_default).length;
    const totalUsage = templates.reduce((sum, t) => sum + t.usage_count, 0);
    
    document.getElementById('totalCount').textContent = total;
    document.getElementById('activeCount').textContent = active;
    document.getElementById('defaultCount').textContent = defaultCount;
    document.getElementById('totalUsage').textContent = totalUsage;
}

// 切换页面
function changePage(page) {
    currentPage = page;
    loadTemplates();
}

// 防抖搜索
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        loadTemplates();
    }, 500);
}

// 显示创建模态框
function showCreateModal() {
    resetTemplateForm();
    document.getElementById('templateModalTitle').textContent = '新建提示词';
    new bootstrap.Modal(document.getElementById('templateModal')).show();
}

// 编辑提示词
async function editTemplate(templateId) {
    try {
        const response = await fetch(`/api/v1/prompts/${templateId}`);
        const template = await response.json();
        
        if (response.ok) {
            fillTemplateForm(template);
            document.getElementById('templateModalTitle').textContent = '编辑提示词';
            new bootstrap.Modal(document.getElementById('templateModal')).show();
        } else {
            showError('加载提示词失败: ' + template.detail);
        }
    } catch (error) {
        showError('加载提示词失败: ' + error.message);
    }
}

// 填充表单
function fillTemplateForm(template) {
    document.getElementById('templateId').value = template.id;
    document.getElementById('templateName').value = template.name;
    document.getElementById('templateDisplayName').value = template.display_name;
    document.getElementById('templateDescription').value = template.description || '';
    document.getElementById('templateType').value = template.type;
    document.getElementById('templateVersion').value = template.version;
    document.getElementById('templatePriority').value = template.priority;
    document.getElementById('templateContent').value = template.template;
    document.getElementById('templateVariables').value = template.variables.join(', ');
    document.getElementById('templateLanguage').value = template.language;
}

// 重置表单
function resetTemplateForm() {
    document.getElementById('templateForm').reset();
    document.getElementById('templateId').value = '';
    document.getElementById('templateVersion').value = '1.0';
    document.getElementById('templatePriority').value = '0';
    document.getElementById('templateLanguage').value = 'zh-CN';
}

// 从提示词内容中提取变量
function extractVariables() {
    const content = document.getElementById('templateContent').value;
    const variableRegex = /\{(\w+)\}/g;
    const variables = new Set();
    let match;
    
    while ((match = variableRegex.exec(content)) !== null) {
        variables.add(match[1]);
    }
    
    document.getElementById('templateVariables').value = Array.from(variables).join(', ');
}

// 保存提示词
async function saveTemplate() {
    try {
        const form = document.getElementById('templateForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const templateId = document.getElementById('templateId').value;
        const isEdit = !!templateId;
        
        const templateData = {
            name: document.getElementById('templateName').value,
            display_name: document.getElementById('templateDisplayName').value,
            description: document.getElementById('templateDescription').value,
            type: document.getElementById('templateType').value,
            template: document.getElementById('templateContent').value,
            variables: document.getElementById('templateVariables').value.split(',').map(v => v.trim()).filter(v => v),
            version: document.getElementById('templateVersion').value,
            language: document.getElementById('templateLanguage').value,
            priority: parseInt(document.getElementById('templatePriority').value)
        };
        
        const url = isEdit ? `/api/v1/prompts/${templateId}` : '/api/v1/prompts';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templateData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(isEdit ? '提示词更新成功' : '提示词创建成功');
            bootstrap.Modal.getInstance(document.getElementById('templateModal')).hide();
            loadTemplates();
        } else {
            showError('保存失败: ' + result.detail);
        }
    } catch (error) {
        showError('保存失败: ' + error.message);
    }
}

// 删除提示词
async function deleteTemplate(templateId) {
    if (!confirm('确定要删除这个提示词吗？此操作不可恢复。')) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/prompts/${templateId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess('提示词删除成功');
            loadTemplates();
        } else {
            showError('删除失败: ' + result.detail);
        }
    } catch (error) {
        showError('删除失败: ' + error.message);
    }
}

// 复制提示词
async function duplicateTemplate(templateId) {
    try {
        const response = await fetch(`/api/v1/prompts/${templateId}`);
        const template = await response.json();

        if (response.ok) {
            // 修改名称和显示名称
            template.name = template.name + '_copy';
            template.display_name = template.display_name + ' (副本)';
            delete template.id;
            delete template.created_at;
            delete template.updated_at;
            delete template.last_used_at;

            const createResponse = await fetch('/api/v1/prompts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(template)
            });

            if (createResponse.ok) {
                showSuccess('提示词复制成功');
                loadTemplates();
            } else {
                const error = await createResponse.json();
                showError('复制失败: ' + error.detail);
            }
        } else {
            showError('加载提示词失败: ' + template.detail);
        }
    } catch (error) {
        showError('复制失败: ' + error.message);
    }
}

// 切换提示词状态
async function toggleTemplateStatus(templateId, isActive) {
    try {
        const response = await fetch(`/api/v1/prompts/${templateId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: isActive })
        });

        if (response.ok) {
            showSuccess(`提示词已${isActive ? '启用' : '禁用'}`);
            loadTemplates();
        } else {
            const error = await response.json();
            showError('操作失败: ' + error.detail);
        }
    } catch (error) {
        showError('操作失败: ' + error.message);
    }
}

// 预览提示词
function previewTemplate(templateId) {
    // 这里可以实现预览功能，比如在模态框中显示完整的提示词内容
    console.log('Preview template:', templateId);
}

// 选择/取消选择提示词
function toggleSelection(templateId) {
    if (selectedTemplates.has(templateId)) {
        selectedTemplates.delete(templateId);
    } else {
        selectedTemplates.add(templateId);
    }

    updateBulkActions();
}

// 更新批量操作界面
function updateBulkActions() {
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');

    if (selectedTemplates.size > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = selectedTemplates.size;
    } else {
        bulkActions.style.display = 'none';
    }
}

// 清除选择
function clearSelection() {
    selectedTemplates.clear();
    document.querySelectorAll('.template-card input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    updateBulkActions();
}

// 批量操作
async function bulkOperation(operation) {
    if (selectedTemplates.size === 0) {
        showError('请先选择要操作的提示词');
        return;
    }

    const operationNames = {
        'activate': '启用',
        'deactivate': '禁用',
        'delete': '删除'
    };

    if (!confirm(`确定要${operationNames[operation]}选中的 ${selectedTemplates.size} 个提示词吗？`)) {
        return;
    }

    try {
        const response = await fetch('/api/v1/prompts/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template_ids: Array.from(selectedTemplates),
                operation: operation
            })
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess(`批量${operationNames[operation]}成功`);
            clearSelection();
            loadTemplates();
        } else {
            showError(`批量操作失败: ${result.detail}`);
        }
    } catch (error) {
        showError(`批量操作失败: ${error.message}`);
    }
}

// 显示导入模态框
function showImportModal() {
    new bootstrap.Modal(document.getElementById('importModal')).show();
}

// 导入提示词
async function importTemplates() {
    const fileInput = document.getElementById('importFile');
    const overwriteExisting = document.getElementById('overwriteExisting').checked;

    if (!fileInput.files.length) {
        showError('请选择要导入的文件');
        return;
    }

    const file = fileInput.files[0];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    try {
        let templates;

        if (fileExtension === 'json') {
            const text = await file.text();
            templates = JSON.parse(text);
        } else if (fileExtension === 'csv') {
            // CSV导入功能可以后续实现
            showError('CSV导入功能暂未实现');
            return;
        } else {
            showError('不支持的文件格式');
            return;
        }

        const response = await fetch('/api/v1/prompts/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                templates: templates,
                overwrite_existing: overwriteExisting
            })
        });

        const result = await response.json();

        if (response.ok) {
            showSuccess(`导入完成: 新增 ${result.imported_count} 个，更新 ${result.updated_count} 个`);
            if (result.errors.length > 0) {
                console.warn('导入错误:', result.errors);
            }
            bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
            loadTemplates();
        } else {
            showError('导入失败: ' + result.detail);
        }
    } catch (error) {
        showError('导入失败: ' + error.message);
    }
}

// 导出提示词
function exportTemplates() {
    const params = new URLSearchParams();

    // 如果有选中的提示词，只导出选中的
    if (selectedTemplates.size > 0) {
        selectedTemplates.forEach(id => params.append('template_ids', id));
    }

    // 添加当前筛选条件
    const typeFilter = document.getElementById('typeFilter').value;
    if (typeFilter) params.append('type', typeFilter);

    params.append('format', 'json');

    window.open(`/api/v1/prompts/export?${params}`, '_blank');
}

// 工具函数
function getTypeDisplayName(type) {
    const typeNames = {
        'translation': '翻译',
        'optimization': '优化',
        'title_generation': '标题生成',
        'summary': '摘要',
        'keyword_extraction': '关键词提取',
        'custom': '自定义'
    };
    return typeNames[type] || type;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    // 可以添加加载动画
}

function hideLoading() {
    // 隐藏加载动画
}

function showSuccess(message) {
    // 可以使用 toast 或其他方式显示成功消息
    alert(message);
}

function showError(message) {
    // 可以使用 toast 或其他方式显示错误消息
    alert(message);
}
