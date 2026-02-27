// 优化后的问答对组管理页面JavaScript
// 使用通用组件重构

// 全局变量
let currentGroupId = null;
let pagination = null;
let searchComponent = null;
let filterComponent = null;

// API基础URL
const API_BASE = '/api/qa';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    loadGroups();
});

/**
 * 初始化所有组件
 */
function initializeComponents() {
    // 初始化分页组件
    pagination = new PaginationComponent('paginationArea', (page, size) => {
        currentPage = page;
        pageSize = size;
        loadGroups();
    });

    // 初始化搜索组件
    searchComponent = new SearchComponent('searchKeyword', null, (keyword) => {
        currentFilters.keyword = keyword;
        currentPage = 1;
        loadGroups();
    });

    // 初始化筛选组件
    filterComponent = new FilterComponent([
        'filterTestType',
        'filterLanguage', 
        'filterStatus'
    ], (filters) => {
        currentFilters = { ...currentFilters, ...filters };
        currentPage = 1;
        loadGroups();
    });

    // 初始化表格列宽调整
    initResizableColumns();
}

/**
 * 初始化表格列宽调整
 */
function initResizableColumns() {
    const table = document.getElementById('groupsTable');
    if (!table) return;
    
    const ths = table.querySelectorAll('th.resizable-col');
    let isResizing = false;
    let startX, startWidth, columnIndex;
    
    ths.forEach((th, index) => {
        const resizer = document.createElement('div');
        resizer.className = 'column-resizer';
        th.appendChild(resizer);
        
        resizer.addEventListener('mousedown', function(e) {
            isResizing = true;
            startX = e.clientX;
            startWidth = th.offsetWidth;
            columnIndex = index;
            document.body.style.cursor = 'col-resize';
            document.body.classList.add('resizing');
            
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const th = ths[columnIndex];
        const newWidth = startWidth + (e.clientX - startX);
        
        if (newWidth >= 50) {
            th.style.width = newWidth + 'px';
            
            // 更新同一列的所有单元格
            const tds = table.querySelectorAll(`tbody td:nth-child(${columnIndex + 1})`);
            tds.forEach(td => {
                td.style.width = newWidth + 'px';
            });
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.classList.remove('resizing');
        }
    });
}

/**
 * 加载分组数据
 */
async function loadGroups() {
    const tableBody = document.getElementById('groupsTableBody');
    if (!tableBody) return;
    
    // 显示加载状态
    tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载中...</td></tr>';
    
    try {
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize,
            ...currentFilters
        });
        
        const response = await fetch(`${API_BASE}/groups?${params}`);
        const data = await response.json();
        
        if (data.success) {
            renderGroupsTable(data.data.rows);
            pagination.update(data.data.total, data.data.page, data.data.limit);
        } else {
            CommonUtils.showError('加载分组数据失败: ' + data.message);
            tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载失败</td></tr>';
        }
    } catch (error) {
        console.error('加载分组数据失败:', error);
        CommonUtils.showError('加载分组数据失败: ' + error.message);
        tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载失败</td></tr>';
    }
}

/**
 * 渲染分组表格
 */
function renderGroupsTable(groups) {
    const tableBody = document.getElementById('groupsTableBody');
    if (!tableBody) return;
    
    if (!groups || groups.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">暂无数据</td></tr>';
        return;
    }
    
    let html = '';
    groups.forEach(group => {
        // 格式化标签
        const tags = Array.isArray(group.tags) ? group.tags.join(', ') : group.tags || '';
        
        // 格式化测试类型
        const testTypeMap = {
            'accuracy': '准确率测试',
            'performance': '性能测试',
            'robustness': '鲁棒性测试',
            'comprehensive': '综合测试',
            'custom': '自定义测试'
        };
        
        // 格式化语言
        const languageMap = {
            'zh': '中文',
            'en': '英文',
            'multi': '多语言'
        };
        
        // 格式化状态
        const statusText = group.is_active ? '已激活' : '已停用';
        const statusClass = group.is_active ? 'text-success' : 'text-danger';
        
        // 格式化创建时间
        const createdAt = group.created_at ? CommonUtils.formatDateTime(group.created_at) : '未知';
        
        html += `
        <tr>
            <td>${group.id}</td>
            <td>
                <a href="/qa/groups/${group.id}" class="group-link" title="点击查看详情">
                    ${CommonUtils.escapeHtml(group.name || '')}
                </a>
            </td>
            <td class="text-truncate" title="${CommonUtils.escapeHtml(group.purpose || '')}">
                ${CommonUtils.escapeHtml(group.purpose || '暂无')}
            </td>
            <td>${testTypeMap[group.test_type] || group.test_type}</td>
            <td>${languageMap[group.language] || group.language}</td>
            <td>${group.difficulty_range || '未设置'}</td>
            <td class="text-truncate" title="${CommonUtils.escapeHtml(tags)}">
                ${CommonUtils.escapeHtml(tags) || '无'}
            </td>
            <td>${group.qa_count || 0}</td>
            <td><span class="${statusClass}">${statusText}</span></td>
            <td>${createdAt}</td>
            <td>
                <button class="action-btn edit-btn" onclick="showEditGroupDialog(${group.id})" title="编辑">
                    ✏️
                </button>
                <button class="action-btn delete-btn" onclick="showDeleteConfirmDialog(${group.id})" title="删除">
                    🗑️
                </button>
                <button class="action-btn detail-btn" onclick="viewGroupDetail(${group.id})" title="查看详情">
                    👁️
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

/**
 * 搜索分组
 */
function searchGroups() {
    if (searchComponent) {
        searchComponent.performSearch();
    }
}

/**
 * 重置搜索
 */
function resetSearch() {
    if (searchComponent) {
        searchComponent.clear();
    }
    if (filterComponent) {
        filterComponent.reset();
    }
    currentFilters = {};
    currentPage = 1;
    loadGroups();
}

/**
 * 应用筛选
 */
function applyFilters() {
    if (filterComponent) {
        filterComponent.applyFilters();
    }
}

/**
 * 显示创建分组对话框
 */
function showCreateGroupDialog() {
    const dialog = new ModalComponent('createGroupDialog');
    dialog.show();
}

/**
 * 关闭创建分组对话框
 */
function closeCreateGroupDialog() {
    const dialog = new ModalComponent('createGroupDialog');
    dialog.hide();
}

/**
 * 提交创建分组
 */
async function submitCreateGroup() {
    const form = document.getElementById('createGroupForm');
    const formData = new FormData(form);
    
    const data = {
        name: document.getElementById('groupName').value,
        purpose: document.getElementById('groupPurpose').value,
        test_type: document.getElementById('groupTestType').value,
        language: document.getElementById('groupLanguage').value,
        difficulty_range: document.getElementById('groupDifficultyRange').value,
        tags: document.getElementById('groupTags').value.split(',').map(tag => tag.trim()).filter(tag => tag),
        metadata: {}
    };
    
    try {
        const metadataStr = document.getElementById('groupMetadata').value;
        if (metadataStr) {
            data.metadata = JSON.parse(metadataStr);
        }
    } catch (e) {
        CommonUtils.showError('元数据格式错误，请输入有效的JSON');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/groups`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            CommonUtils.showSuccess('分组创建成功');
            closeCreateGroupDialog();
            loadGroups();
        } else {
            CommonUtils.showError('创建分组失败: ' + result.message);
        }
    } catch (error) {
        console.error('创建分组失败:', error);
        CommonUtils.showError('创建分组失败: ' + error.message);
    }
}

/**
 * 显示编辑分组对话框
 */
async function showEditGroupDialog(groupId) {
    try {
        const response = await fetch(`${API_BASE}/groups/${groupId}`);
        const result = await response.json();
        
        if (result.success) {
            const group = result.data;
            populateEditForm(group);
            const dialog = new ModalComponent('editGroupDialog');
            dialog.show();
        } else {
            CommonUtils.showError('获取分组信息失败: ' + result.message);
        }
    } catch (error) {
        console.error('获取分组信息失败:', error);
        CommonUtils.showError('获取分组信息失败: ' + error.message);
    }
}

/**
 * 填充分组编辑表单
 */
function populateEditForm(group) {
    document.getElementById('editGroupId').value = group.id;
    document.getElementById('editGroupName').value = group.name || '';
    document.getElementById('editGroupPurpose').value = group.purpose || '';
    document.getElementById('editGroupTestType').value = group.test_type || 'custom';
    document.getElementById('editGroupLanguage').value = group.language || 'zh';
    document.getElementById('editGroupDifficultyRange').value = group.difficulty_range || '';
    document.getElementById('editGroupTags').value = Array.isArray(group.tags) ? group.tags.join(', ') : group.tags || '';
    document.getElementById('editGroupMetadata').value = group.metadata ? JSON.stringify(group.metadata, null, 2) : '';
}

/**
 * 关闭编辑分组对话框
 */
function closeEditGroupDialog() {
    const dialog = new ModalComponent('editGroupDialog');
    dialog.hide();
}

/**
 * 提交编辑分组
 */
async function submitEditGroup() {
    const groupId = document.getElementById('editGroupId').value;
    const form = document.getElementById('editGroupForm');
    
    const data = {
        name: document.getElementById('editGroupName').value,
        purpose: document.getElementById('editGroupPurpose').value,
        test_type: document.getElementById('editGroupTestType').value,
        language: document.getElementById('editGroupLanguage').value,
        difficulty_range: document.getElementById('editGroupDifficultyRange').value,
        tags: document.getElementById('editGroupTags').value.split(',').map(tag => tag.trim()).filter(tag => tag),
        metadata: {}
    };
    
    try {
        const metadataStr = document.getElementById('editGroupMetadata').value;
        if (metadataStr) {
            data.metadata = JSON.parse(metadataStr);
        }
    } catch (e) {
        CommonUtils.showError('元数据格式错误，请输入有效的JSON');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/groups/${groupId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            CommonUtils.showSuccess('分组更新成功');
            closeEditGroupDialog();
            loadGroups();
        } else {
            CommonUtils.showError('更新分组失败: ' + result.message);
        }
    } catch (error) {
        console.error('更新分组失败:', error);
        CommonUtils.showError('更新分组失败: ' + error.message);
    }
}

/**
 * 显示删除确认对话框
 */
function showDeleteConfirmDialog(groupId) {
    window.pendingDeleteGroupId = groupId;
    const dialog = new ModalComponent('deleteConfirmDialog');
    dialog.show();
}

/**
 * 关闭删除确认对话框
 */
function closeDeleteConfirmDialog() {
    const dialog = new ModalComponent('deleteConfirmDialog');
    dialog.hide();
    delete window.pendingDeleteGroupId;
}

/**
 * 确认删除分组
 */
async function confirmDeleteGroup() {
    const groupId = window.pendingDeleteGroupId;
    if (!groupId) return;
    
    const forceDelete = document.getElementById('forceDeleteCheckbox').checked;
    
    try {
        const url = `${API_BASE}/groups/${groupId}${forceDelete ? '?force=true' : ''}`;
        const response = await fetch(url, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            CommonUtils.showSuccess('分组删除成功');
            closeDeleteConfirmDialog();
            loadGroups();
        } else {
            CommonUtils.showError('删除分组失败: ' + result.message);
        }
    } catch (error) {
        console.error('删除分组失败:', error);
        CommonUtils.showError('删除分组失败: ' + error.message);
    }
}

/**
 * 查看分组详情
 */
function viewGroupDetail(groupId) {
    window.location.href = `/qa/groups/${groupId}`;
}

/**
 * 显示导入对话框
 */
function showImportDialog() {
    loadGroupOptions();
    const dialog = new ModalComponent('importDialog');
    dialog.show();
}

/**
 * 关闭导入对话框
 */
function closeImportDialog() {
    const dialog = new ModalComponent('importDialog');
    dialog.hide();
}

/**
 * 加载分组选项
 */
async function loadGroupOptions() {
    try {
        const response = await fetch(`${API_BASE}/groups?is_active=true&order_by=name ASC`);
        const result = await response.json();
        
        if (result.success) {
            const select = document.getElementById('importGroupSelect');
            select.innerHTML = '<option value="">请选择分组...</option>';
            
            result.data.rows.forEach(group => {
                const option = document.createElement('option');
                option.value = group.id;
                option.textContent = group.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载分组选项失败:', error);
    }
}

// 工具函数
function CommonUtils() {}

CommonUtils.escapeHtml = function(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

CommonUtils.showError = function(message) {
    alert('错误: ' + message);
    console.error(message);
};

CommonUtils.showSuccess = function(message) {
    alert('成功: ' + message);
    console.log(message);
};

CommonUtils.formatDateTime = function(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
};