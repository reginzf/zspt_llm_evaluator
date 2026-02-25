// 问答对组管理页面JavaScript

// 全局变量
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let totalItems = 0;
let currentFilters = {};
let isImporting = false;
let importCanceled = false;

// API基础URL
const API_BASE = '/api/qa';

// 页面加载完成后初始化
// 注意：DOMContentLoaded 事件处理在 qa_groups.html 中定义

// 初始化事件监听器
function initEventListeners() {
    // 搜索框回车事件
    document.getElementById('searchKeyword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchGroups();
        }
    });
    
    // 筛选器变化事件
    document.getElementById('filterTestType').addEventListener('change', function() {
        applyFilters();
    });
    
    document.getElementById('filterLanguage').addEventListener('change', function() {
        applyFilters();
    });
    
    document.getElementById('filterStatus').addEventListener('change', function() {
        applyFilters();
    });
    
    // 分页输入框事件
    document.getElementById('pageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            goToPage(this.value);
        }
    });
}

// 初始化表格列宽调整
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
        
        if (newWidth >= 50) { // 最小宽度限制
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

// 加载分组数据
function loadGroups() {
    const tableBody = document.getElementById('groupsTableBody');
    if (!tableBody) return;
    
    // 显示加载状态
    tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载中...</td></tr>';
    
    // 构建查询参数
    const params = new URLSearchParams({
        page: currentPage,
        limit: pageSize,
        ...currentFilters
    });
    
    // 发送请求
    fetch(`${API_BASE}/groups?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                renderGroupsTable(data.data);
                updatePagination(data.data);
            } else {
                showError('加载分组数据失败: ' + data.message);
                tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载失败</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载分组数据失败:', error);
            showError('加载分组数据失败: ' + error.message);
            tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">加载失败</td></tr>';
        });
}

// 渲染分组表格
function renderGroupsTable(data) {
    const tableBody = document.getElementById('groupsTableBody');
    if (!tableBody || !data.rows) return;
    
    if (data.rows.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="11" class="loading-cell">暂无数据</td></tr>';
        return;
    }
    
    let html = '';
    data.rows.forEach(group => {
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
        const createdAt = group.created_at ? new Date(group.created_at).toLocaleString() : '未知';
        
        html += `
        <tr>
            <td>${group.id}</td>
            <td>
                <a href="/qa/groups/${group.id}" class="group-link" title="点击查看详情">
                    ${escapeHtml(group.name || '')}
                </a>
            </td>
            <td class="text-truncate" title="${escapeHtml(group.purpose || '')}">
                ${escapeHtml(group.purpose || '暂无')}
            </td>
            <td>${testTypeMap[group.test_type] || group.test_type}</td>
            <td>${languageMap[group.language] || group.language}</td>
            <td>${group.difficulty_range || '未设置'}</td>
            <td class="text-truncate" title="${escapeHtml(tags)}">
                ${escapeHtml(tags) || '无'}
            </td>
            <td>${group.qa_count || 0}</td>
            <td><span class="${statusClass}">${statusText}</span></td>
            <td>${createdAt}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editGroup(${group.id}, '${escapeHtml(group.name)}')" title="编辑">
                    ✏
                </button>
                <button class="action-btn delete-btn" onclick="deleteGroup(${group.id}, '${escapeHtml(group.name)}')" title="删除">
                    🗑
                </button>
                <button class="action-btn ${group.is_active ? 'deactivate-btn' : 'activate-btn'}" 
                        onclick="toggleGroupStatus(${group.id}, ${group.is_active})" 
                        title="${group.is_active ? '停用' : '激活'}">
                    ${group.is_active ? '⚡' : '🔋'}
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// 更新分页信息
function updatePagination(data) {
    totalItems = data.total || 0;
    totalPages = data.pages || 1;
    currentPage = data.page || 1;
    
    // 更新分页信息显示
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('totalItems').textContent = totalItems;
    document.getElementById('maxPage').textContent = totalPages;
    document.getElementById('pageInput').value = currentPage;
    
    // 更新分页按钮状态
    const firstBtn = document.querySelector('.first-btn');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    const lastBtn = document.querySelector('.last-btn');
    
    if (firstBtn) firstBtn.disabled = currentPage <= 1;
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (lastBtn) lastBtn.disabled = currentPage >= totalPages;
}

// 搜索分组
function searchGroups() {
    const keyword = document.getElementById('searchKeyword').value.trim();
    currentFilters.keyword = keyword;
    currentPage = 1;
    loadGroups();
}

// 重置搜索
function resetSearch() {
    document.getElementById('searchKeyword').value = '';
    document.getElementById('filterTestType').value = '';
    document.getElementById('filterLanguage').value = '';
    document.getElementById('filterStatus').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadGroups();
}

// 应用筛选器
function applyFilters() {
    const testType = document.getElementById('filterTestType').value;
    const language = document.getElementById('filterLanguage').value;
    const status = document.getElementById('filterStatus').value;
    
    currentFilters = {};
    if (testType) currentFilters.test_type = testType;
    if (language) currentFilters.language = language;
    if (status) currentFilters.is_active = status;
    
    currentPage = 1;
    loadGroups();
}

// 分页导航
function goToPage(page) {
    page = parseInt(page);
    if (isNaN(page) || page < 1 || page > totalPages) {
        showError('请输入有效的页码');
        return;
    }
    currentPage = page;
    loadGroups();
}

function goToPrevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadGroups();
    }
}

function goToNextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadGroups();
    }
}

function goToLastPage() {
    if (currentPage < totalPages) {
        currentPage = totalPages;
        loadGroups();
    }
}

function changePageSize(size) {
    pageSize = parseInt(size);
    currentPage = 1;
    loadGroups();
}

// 显示创建分组对话框
function showCreateGroupDialog() {
    // 重置表单
    document.getElementById('createGroupForm').reset();
    document.getElementById('groupNameError').textContent = '';
    
    // 显示对话框
    document.getElementById('createGroupDialog').style.display = 'block';
}

// 关闭创建分组对话框
function closeCreateGroupDialog() {
    document.getElementById('createGroupDialog').style.display = 'none';
}

// 提交创建分组
function submitCreateGroup() {
    const name = document.getElementById('groupName').value.trim();
    const purpose = document.getElementById('groupPurpose').value.trim();
    const testType = document.getElementById('groupTestType').value;
    const language = document.getElementById('groupLanguage').value;
    const difficultyRange = document.getElementById('groupDifficultyRange').value.trim();
    const tagsInput = document.getElementById('groupTags').value.trim();
    const metadataInput = document.getElementById('groupMetadata').value.trim();
    
    // 验证必填字段
    if (!name) {
        document.getElementById('groupNameError').textContent = '分组名称不能为空';
        return;
    }
    
    // 处理标签
    let tags = [];
    if (tagsInput) {
        tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
    }
    
    // 处理元数据
    let metadata = {};
    if (metadataInput) {
        try {
            metadata = JSON.parse(metadataInput);
        } catch (e) {
            showError('元数据必须是有效的JSON格式');
            return;
        }
    }
    
    // 准备请求数据
    const data = {
        name: name,
        purpose: purpose || null,
        test_type: testType,
        language: language,
        difficulty_range: difficultyRange || null,
        tags: tags,
        metadata: metadata
    };
    
    // 发送创建请求
    fetch(`${API_BASE}/groups`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('分组创建成功');
            closeCreateGroupDialog();
            loadGroups(); // 刷新列表
        } else {
            showError('分组创建失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('创建分组失败:', error);
        showError('创建分组失败: ' + error.message);
    });
}

// 编辑分组
function editGroup(groupId, groupName) {
    // 先获取分组详情
    fetch(`${API_BASE}/groups/${groupId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const group = result.data;
                
                // 填充表单
                document.getElementById('editGroupId').value = groupId;
                document.getElementById('editGroupName').value = group.name || '';
                document.getElementById('editGroupPurpose').value = group.purpose || '';
                document.getElementById('editGroupTestType').value = group.test_type || 'custom';
                document.getElementById('editGroupLanguage').value = group.language || 'zh';
                document.getElementById('editGroupDifficultyRange').value = group.difficulty_range || '';
                
                // 处理标签
                const tags = Array.isArray(group.tags) ? group.tags.join(', ') : group.tags || '';
                document.getElementById('editGroupTags').value = tags;
                
                // 处理元数据
                if (group.metadata && typeof group.metadata === 'object') {
                    document.getElementById('editGroupMetadata').value = JSON.stringify(group.metadata, null, 2);
                } else {
                    document.getElementById('editGroupMetadata').value = '';
                }
                
                // 显示对话框
                document.getElementById('editGroupDialog').style.display = 'block';
            } else {
                showError('获取分组详情失败: ' + result.message);
            }
        })
        .catch(error => {
            console.error('获取分组详情失败:', error);
            showError('获取分组详情失败: ' + error.message);
        });
}

// 关闭编辑分组对话框
function closeEditGroupDialog() {
    document.getElementById('editGroupDialog').style.display = 'none';
}

// 提交编辑分组
function submitEditGroup() {
    const groupId = document.getElementById('editGroupId').value;
    const name = document.getElementById('editGroupName').value.trim();
    const purpose = document.getElementById('editGroupPurpose').value.trim();
    const testType = document.getElementById('editGroupTestType').value;
    const language = document.getElementById('editGroupLanguage').value;
    const difficultyRange = document.getElementById('editGroupDifficultyRange').value.trim();
    const tagsInput = document.getElementById('editGroupTags').value.trim();
    const metadataInput = document.getElementById('editGroupMetadata').value.trim();
    
    // 验证必填字段
    if (!name) {
        document.getElementById('editGroupNameError').textContent = '分组名称不能为空';
        return;
    }
    
    // 处理标签
    let tags = [];
    if (tagsInput) {
        tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
    }
    
    // 处理元数据
    let metadata = {};
    if (metadataInput) {
        try {
            metadata = JSON.parse(metadataInput);
        } catch (e) {
            showError('元数据必须是有效的JSON格式');
            return;
        }
    }
    
    // 准备请求数据
    const data = {
        name: name,
        purpose: purpose || null,
        test_type: testType,
        language: language,
        difficulty_range: difficultyRange || null,
        tags: tags,
        metadata: metadata
    };
    
    // 发送更新请求
    fetch(`${API_BASE}/groups/${groupId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('分组更新成功');
            closeEditGroupDialog();
            loadGroups(); // 刷新列表
        } else {
            showError('分组更新失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('更新分组失败:', error);
        showError('更新分组失败: ' + error.message);
    });
}

// 删除分组
function deleteGroup(groupId, groupName) {
    // 保存当前分组信息
    window.deleteGroupId = groupId;
    window.deleteGroupName = groupName;
    
    // 更新确认消息
    document.getElementById('deleteConfirmMessage').textContent = 
        `确定要删除分组 "${groupName}" 吗？`;
    
    // 重置强制删除复选框
    document.getElementById('forceDeleteCheckbox').checked = false;
    
    // 显示确认对话框
    document.getElementById('deleteConfirmDialog').style.display = 'block';
}

// 关闭删除确认对话框
function closeDeleteConfirmDialog() {
    document.getElementById('deleteConfirmDialog').style.display = 'none';
}

// 确认删除分组
function confirmDeleteGroup() {
    const groupId = window.deleteGroupId;
    const forceDelete = document.getElementById('forceDeleteCheckbox').checked;
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (forceDelete) {
        params.append('force', 'true');
    }
    
    // 发送删除请求
    fetch(`${API_BASE}/groups/${groupId}?${params}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('分组删除成功');
            closeDeleteConfirmDialog();
            loadGroups(); // 刷新列表
        } else {
            showError('分组删除失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('删除分组失败:', error);
        showError('删除分组失败: ' + error.message);
    });
}

// 切换分组状态
function toggleGroupStatus(groupId, currentStatus) {
    const newStatus = !currentStatus;
    
    fetch(`${API_BASE}/groups/${groupId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess(`分组已${newStatus ? '激活' : '停用'}`);
            loadGroups(); // 刷新列表
        } else {
            showError('状态更新失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('切换分组状态失败:', error);
        showError('切换分组状态失败: ' + error.message);
    });
}

// 显示导入对话框
function showImportDialog() {
    // 显示对话框
    document.getElementById('importDialog').style.display = 'block';
}

// 关闭导入对话框
function closeImportDialog() {
    document.getElementById('importDialog').style.display = 'none';
}

// 切换导入选项
function toggleImportOptions() {
    const importType = document.getElementById('importType').value;
    const fileUploadSection = document.getElementById('fileUploadSection');
    const huggingfaceSection = document.getElementById('huggingfaceSection');
    
    if (importType === 'huggingface') {
        fileUploadSection.style.display = 'none';
        huggingfaceSection.style.display = 'block';
    } else {
        fileUploadSection.style.display = 'block';
        huggingfaceSection.style.display = 'none';
    }
}

// 开始导入
function startImport() {
    const groupId = document.getElementById('importGroupSelect').value;
    const importType = document.getElementById('importType').value;
    const batchSize = parseInt(document.getElementById('importBatchSize').value) || 1000;
    
    if (!groupId) {
        showError('请选择目标分组');
        return;
    }
    
    // 准备导入数据
    let importData = {
        batch_size: batchSize
    };
    
    if (importType === 'huggingface') {
        const datasetPath = document.getElementById('hfDatasetPath').value.trim();
        if (!datasetPath) {
            showError('请输入数据集路径');
            return;
        }
        importData.dataset_path = datasetPath;
    } else {
        const fileInput = document.getElementById('importFile');
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('请选择要导入的文件');
            return;
        }
        
        // 读取文件内容
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                let data;
                if (importType === 'json') {
                    data = JSON.parse(e.target.result);
                } else if (importType === 'csv') {
                    // CSV解析逻辑（简化版）
                    data = parseCSV(e.target.result);
                }
                
                if (!Array.isArray(data)) {
                    showError('文件内容必须是数组格式');
                    return;
                }
                
                // 开始批量导入
                startBatchImport(groupId, data, batchSize);
                
            } catch (error) {
                showError('文件解析失败: ' + error.message);
            }
        };
        
        reader.onerror = function() {
            showError('文件读取失败');
        };
        
        if (importType === 'json') {
            reader.readAsText(file);
        } else if (importType === 'csv') {
            reader.readAsText(file);
        }
        
        return; // 文件读取是异步的，直接返回
    }
    
    // 对于HuggingFace导入，直接发送请求
    fetch(`${API_BASE}/groups/${groupId}/items/import/huggingface`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(importData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showImportProgress(result.stats);
        } else {
            showError('导入失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('导入失败:', error);
        showError('导入失败: ' + error.message);
    });
}

// 开始批量导入
function startBatchImport(groupId, data, batchSize) {
    isImporting = true;
    importCanceled = false;
    
    // 显示进度对话框
    showImportProgressDialog();
    
    // 分批处理数据
    const total = data.length;
    let processed = 0;
    let success = 0;
    let failed = 0;
    let errors = [];
    
    function processBatch(startIndex) {
        if (importCanceled || startIndex >= total) {
            // 导入完成或取消
            isImporting = false;
            updateImportProgress(total, processed, success, failed, errors);
            
            if (!importCanceled) {
                // 显示完成按钮
                document.querySelector('#importProgressDialog .close-btn').style.display = 'block';
                document.querySelector('#importProgressDialog .cancel-btn').style.display = 'none';
            }
            
            return;
        }
        
        const endIndex = Math.min(startIndex + batchSize, total);
        const batch = data.slice(startIndex, endIndex);
        
        // 为每个项目添加group_id
        batch.forEach(item => {
            item.group_id = parseInt(groupId);
        });
        
        // 发送批量创建请求
        fetch(`${API_BASE}/groups/${groupId}/items/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: batch })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                success += result.stats.success;
                failed += result.stats.failed;
                processed += batch.length;
                
                // 更新进度
                updateImportProgress(total, processed, success, failed, errors);
                
                // 处理下一个批次
                setTimeout(() => processBatch(endIndex), 100);
            } else {
                errors.push(`批次 ${startIndex/batchSize + 1} 失败: ${result.message}`);
                failed += batch.length;
                processed += batch.length;
                
                // 更新进度
                updateImportProgress(total, processed, success, failed, errors);
                
                // 继续处理下一个批次
                setTimeout(() => processBatch(endIndex), 100);
            }
        })
        .catch(error => {
            errors.push(`批次 ${startIndex/batchSize + 1} 错误: ${error.message}`);
            failed += batch.length;
            processed += batch.length;
            
            // 更新进度
            updateImportProgress(total, processed, success, failed, errors);
            
            // 继续处理下一个批次
            setTimeout(() => processBatch(endIndex), 100);
        });
    }
    
    // 开始处理第一个批次
    processBatch(0);
}

// 显示导入进度对话框
function showImportProgressDialog() {
    // 重置进度
    document.getElementById('importProgressBar').style.width = '0%';
    document.getElementById('importProgressText').textContent = '0%';
    document.getElementById('importTotal').textContent = '0';
    document.getElementById('importSuccess').textContent = '0';
    document.getElementById('importFailed').textContent = '0';
    document.getElementById('importSkipped').textContent = '0';
    document.getElementById('importDuration').textContent = '0';
    document.getElementById('importErrorList').innerHTML = '';
    
    // 显示按钮
    document.querySelector('#importProgressDialog .close-btn').style.display = 'none';
    document.querySelector('#importProgressDialog .cancel-btn').style.display = 'block';
    
    // 显示对话框
    document.getElementById('importProgressDialog').style.display = 'block';
}

// 更新导入进度
function updateImportProgress(total, processed, success, failed, errors) {
    const progress = total > 0 ? Math.round((processed / total) * 100) : 0;
    
    document.getElementById('importProgressBar').style.width = progress + '%';
    document.getElementById('importProgressText').textContent = progress + '%';
    document.getElementById('importTotal').textContent = total;
    document.getElementById('importSuccess').textContent = success;
    document.getElementById('importFailed').textContent = failed;
    document.getElementById('importSkipped').textContent = total - processed;
    
    // 更新错误列表
    const errorList = document.getElementById('importErrorList');
    if (errors.length > 0) {
        errorList.innerHTML = errors.map(error => `<div>${escapeHtml(error)}</div>`).join('');
    }
}

// 关闭导入进度对话框
function closeImportProgressDialog() {
    document.getElementById('importProgressDialog').style.display = 'none';
}

// 取消导入
function cancelImport() {
    importCanceled = true;
    isImporting = false;
    closeImportProgressDialog();
    showInfo('导入已取消');
}

// 显示导入进度（用于HuggingFace导入）
function showImportProgress(stats) {
    showImportProgressDialog();
    updateImportProgress(stats.total, stats.total, stats.success, stats.failed, stats.errors);
    
    // 显示完成按钮
    document.querySelector('#importProgressDialog .close-btn').style.display = 'block';
    document.querySelector('#importProgressDialog .cancel-btn').style.display = 'none';
}

// 加载分组选项（用于导入）
function loadGroupOptions() {
    const select = document.getElementById('importGroupSelect');
    if (!select) return;
    
    // 获取激活的分组
    fetch(`${API_BASE}/groups?is_active=true&limit=100`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.rows.length > 0) {
                let options = '<option value="">请选择分组...</option>';
                data.data.rows.forEach(group => {
                    options += `<option value="${group.id}">${escapeHtml(group.name)}</option>`;
                });
                select.innerHTML = options;
            }
        })
        .catch(error => {
            console.error('加载分组选项失败:', error);
        });
}

// 解析CSV（简化版）
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const result = [];
    
    if (lines.length === 0) return result;
    
    // 假设第一行是标题行
    const headers = lines[0].split(',').map(header => header.trim());
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = line.split(',').map(value => value.trim());
        const item = {};
        
        headers.forEach((header, index) => {
            if (index < values.length) {
                item[header] = values[index];
            }
        });
        
        result.push(item);
    }
    
    return result;
}

// 工具函数：显示成功消息
function showSuccess(message) {
    alert('✅ ' + message);
}

// 工具函数：显示错误消息
function showError(message) {
    alert('❌ ' + message);
}

// 工具函数：显示信息消息
function showInfo(message) {
    alert('ℹ️ ' + message);
}

// 工具函数：HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}