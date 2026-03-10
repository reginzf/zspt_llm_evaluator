// 问答对组详情页面JavaScript

// 工具函数：HTML转义
function escapeHtml(text) {
    if (typeof text !== 'string') {
        return text;
    }
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// 工具函数：显示成功消息
function showSuccess(message) {
    showToast(message, 'success');
}

// 工具函数：显示错误消息
function showError(message) {
    showToast(message, 'error');
}

// 工具函数：显示信息消息
function showInfo(message) {
    showToast(message, 'info');
}

// 显示消息提示（自动消失）
function showToast(message, type = 'info') {
    // 移除已有的消息
    const existingToast = document.querySelector('.message-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 创建消息元素
    const toast = document.createElement('div');
    toast.className = `message-toast ${type}`;
    
    // 设置图标
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `${icon} ${escapeHtml(message)}`;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 3000);
}

// 全局变量
let currentQAPage = 1;
let qaPageSize = 20;
let qaTotalPages = 1;
let qaTotalItems = 0;
let currentQAFilters = {};
let isQAImporting = false;
let qaImportCanceled = false;

// 批量操作相关变量
let isBatchMode = false;
let selectedQAIds = new Set();
let currentQARows = [];

// API基础URL
const API_BASE = '/api/qa';

// 页面加载完成后初始化
// 注意：DOMContentLoaded 事件处理在 qa_group_detail.html 中定义
// 这里只导出需要在页面加载时调用的函数

// 初始化事件监听器
function initQAEventListeners() {
    // 搜索框回车事件
    document.getElementById('searchQuestion').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchQA();
        }
    });
    
    // 筛选器变化事件
    document.getElementById('filterQuestionType').addEventListener('change', function() {
        applyQAFilters();
    });
    
    document.getElementById('filterDifficulty').addEventListener('change', function() {
        applyQAFilters();
    });
    
    document.getElementById('filterCategory').addEventListener('change', function() {
        applyQAFilters();
    });
    
    // 分页输入框事件
    document.getElementById('qaPageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            goToQAPage(this.value);
        }
    });
}

// 初始化表格列宽调整
function initResizableColumns() {
    const table = document.getElementById('qaTable');
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

// ==================== 批量操作功能 ====================

// 切换批量操作模式
function toggleBatchMode() {
    isBatchMode = !isBatchMode;
    const btn = document.getElementById('batchModeBtn');
    const checkboxes = document.querySelectorAll('.batch-checkbox');
    const toolbar = document.getElementById('batchToolbar');
    
    if (isBatchMode) {
        btn.textContent = '退出批量';
        btn.classList.add('active');
        checkboxes.forEach(cb => cb.style.display = '');
        toolbar.style.display = 'flex';
    } else {
        btn.textContent = '批量操作';
        btn.classList.remove('active');
        checkboxes.forEach(cb => cb.style.display = 'none');
        toolbar.style.display = 'none';
        clearBatchSelection();
    }
    
    // 重新渲染表格以显示/隐藏复选框
    loadQAData();
}

// 全选/取消全选
function toggleSelectAll(checkbox) {
    const rowCheckboxes = document.querySelectorAll('.qa-row-checkbox');
    rowCheckboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const qaId = parseInt(cb.dataset.qaId);
        if (checkbox.checked) {
            selectedQAIds.add(qaId);
        } else {
            selectedQAIds.delete(qaId);
        }
    });
    updateBatchToolbar();
}

// 选择单个行
function toggleRowSelection(checkbox, qaId) {
    qaId = parseInt(qaId);
    if (checkbox.checked) {
        selectedQAIds.add(qaId);
    } else {
        selectedQAIds.delete(qaId);
    }
    updateBatchToolbar();
    updateSelectAllCheckbox();
}

// 更新批量工具栏显示
function updateBatchToolbar() {
    const count = selectedQAIds.size;
    document.getElementById('batchSelectedCount').textContent = count;
    
    // 更新行样式
    document.querySelectorAll('.qa-row-checkbox').forEach(cb => {
        const qaId = parseInt(cb.dataset.qaId);
        const row = cb.closest('tr');
        if (selectedQAIds.has(qaId)) {
            row.classList.add('selected');
        } else {
            row.classList.remove('selected');
        }
    });
}

// 更新全选复选框状态
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const rowCheckboxes = document.querySelectorAll('.qa-row-checkbox');
    const checkedCount = document.querySelectorAll('.qa-row-checkbox:checked').length;
    
    if (checkedCount === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCount === rowCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// 清空选择
function clearBatchSelection() {
    selectedQAIds.clear();
    document.getElementById('selectAllCheckbox').checked = false;
    document.getElementById('selectAllCheckbox').indeterminate = false;
    document.querySelectorAll('.qa-row-checkbox').forEach(cb => {
        cb.checked = false;
        const row = cb.closest('tr');
        row.classList.remove('selected');
    });
    updateBatchToolbar();
}

// 批量删除
function batchDeleteQA() {
    const count = selectedQAIds.size;
    if (count === 0) {
        showError('请先选择要删除的问答对');
        return;
    }
    
    DialogManager.confirm(
        `确定要删除选中的 ${count} 个问答对吗？此操作不可恢复。`,
        async () => {
            // 用户确认，执行删除
            const groupId = window.currentGroupId;
            const ids = Array.from(selectedQAIds);
            
            // 显示加载状态
            const deleteBtn = document.querySelector('.batch-delete-btn');
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<span class="btn-icon">⏳</span> 删除中...';
            deleteBtn.disabled = true;
            
            try {
                const response = await fetch(`${API_BASE}/groups/${groupId}/items/batch-delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ids: ids })
                });
                
                const data = await response.json();
                
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                
                if (data.success) {
                    showSuccess(`成功删除 ${data.data.deleted_count} 个问答对`);
                    clearBatchSelection();
                    loadQAData();
                    loadGroupTags();
                } else {
                    showError('批量删除失败：' + data.message);
                }
            } catch (error) {
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                console.error('批量删除失败:', error);
                showError('批量删除失败：' + error.message);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 加载分组标签
function loadGroupTags() {
    const container = document.getElementById('groupTagsContainer');
    if (!container) return;
    
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    fetch(`${API_BASE}/groups/${groupId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success && result.data.tags) {
                const tags = result.data.tags;
                if (Array.isArray(tags) && tags.length > 0) {
                    container.innerHTML = tags.map(tag => 
                        `<span class="tag">${escapeHtml(tag)}</span>`
                    ).join('');
                } else {
                    container.innerHTML = '<span class="text-muted">无标签</span>';
                }
            } else {
                container.innerHTML = '<span class="text-muted">加载失败</span>';
            }
        })
        .catch(error => {
            console.error('加载分组标签失败:', error);
            container.innerHTML = '<span class="text-muted">加载失败</span>';
        });
}

// 加载问答对数据
function loadQAData() {
    const tableBody = document.getElementById('qaTableBody');
    if (!tableBody) return;
    
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    // 显示加载状态
    tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">加载中...</td></tr>';
    
    // 构建查询参数
    const params = new URLSearchParams({
        page: currentQAPage,
        limit: qaPageSize,
        ...currentQAFilters
    });
    
    // 发送请求
    fetch(`${API_BASE}/groups/${groupId}/items?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                renderQATable(data.data);
                updateQAPagination(data.data);
                // 使用已加载的数据更新分类选项，避免额外请求
                loadCategoryOptions(data.data.rows);
            } else {
                showError('加载问答对数据失败: ' + data.message);
                tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">加载失败</td></tr>';
            }
        })
        .catch(error => {
            console.error('加载问答对数据失败:', error);
            showError('加载问答对数据失败: ' + error.message);
            tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">加载失败</td></tr>';
        });
}

// 渲染问答对表格
function renderQATable(data) {
    const tableBody = document.getElementById('qaTableBody');
    if (!tableBody || !data.rows) return;
    
    if (data.rows.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">暂无数据</td></tr>';
        return;
    }
    
    // 保存当前行数据用于批量操作
    currentQARows = data.rows;
    
    let html = '';
    data.rows.forEach(qa => {
        // 格式化问题（截断）
        const question = qa.question || '';
        const questionShort = question.length > 100 ? question.substring(0, 100) + '...' : question;
        
        // 格式化答案
        let answerText = '';
        if (qa.answers) {
            if (typeof qa.answers === 'string') {
                answerText = qa.answers;
            } else if (qa.answers.text && Array.isArray(qa.answers.text)) {
                answerText = qa.answers.text.join(', ');
            } else if (typeof qa.answers === 'object') {
                answerText = JSON.stringify(qa.answers);
            }
        }
        const answerShort = answerText.length > 100 ? answerText.substring(0, 100) + '...' : answerText;
        
        // 格式化上下文
        const context = qa.context || '';
        const contextShort = context.length > 100 ? context.substring(0, 100) + '...' : context;
        
        // 格式化问题类型
        const questionTypeMap = {
            'factual': '事实性问题',
            'contextual': '上下文问题',
            'conceptual': '概念性问题',
            'reasoning': '推理问题',
            'application': '应用问题',
            'multi_choice': '多选题'
        };
        
        // 格式化标签
        const tags = Array.isArray(qa.tags) ? qa.tags.join(', ') : qa.tags || '';
        
        // 格式化创建时间
        const createdAt = qa.created_at ? new Date(qa.created_at).toLocaleString() : '未知';
        
        // 检查是否已选中
        const isChecked = selectedQAIds.has(qa.id) ? 'checked' : '';
        const isSelected = selectedQAIds.has(qa.id) ? 'selected' : '';
        
        // 复选框列（批量操作模式下显示）
        const checkboxCol = isBatchMode ? 
            `<td class="checkbox-col">
                <input type="checkbox" class="qa-row-checkbox" data-qa-id="${qa.id}" 
                       ${isChecked} onchange="toggleRowSelection(this, ${qa.id})">
            </td>` : 
            '<td class="checkbox-col batch-checkbox" style="display: none;"></td>';
        
        html += `
        <tr class="${isSelected}">
            ${checkboxCol}
            <td>${qa.id}</td>
            <td class="text-truncate" title="${escapeHtml(question)}">
                ${escapeHtml(questionShort)}
            </td>
            <td class="text-truncate" title="${escapeHtml(answerText)}">
                ${escapeHtml(answerShort)}
            </td>
            <td class="text-truncate" title="${escapeHtml(context)}">
                ${escapeHtml(contextShort) || '无'}
            </td>
            <td>${questionTypeMap[qa.question_type] || qa.question_type || '未知'}</td>
            <td>${qa.difficulty_level || '未设置'}</td>
            <td>${escapeHtml(qa.category || '')}</td>
            <td class="text-truncate" title="${escapeHtml(tags)}">
                ${escapeHtml(tags) || '无'}
            </td>
            <td>${createdAt}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editQA(${qa.id})" title="编辑">
                    ✏
                </button>
                <button class="action-btn delete-btn" onclick="deleteQA(${qa.id})" title="删除">
                    🗑
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // 更新全选复选框状态
    if (isBatchMode) {
        updateSelectAllCheckbox();
        updateBatchToolbar();
    }
}

// 更新问答对分页信息
function updateQAPagination(data) {
    qaTotalItems = data.total || 0;
    qaTotalPages = data.pages || 1;
    currentQAPage = data.page || 1;
    
    const paginationArea = document.getElementById('qaPaginationArea');
    if (!paginationArea) return;
    
    // 如果分页区域为空，先生成 HTML 结构
    if (!paginationArea.innerHTML.trim()) {
        paginationArea.innerHTML = `
            <div class="pagination-left">
                <button class="pagination-btn first-btn" onclick="goToQAPage(1)" title="首页">首页</button>
                <button class="pagination-btn prev-btn" onclick="goToQAPage(${currentQAPage - 1})" title="上一页">上一页</button>
                <span class="pagination-info">
                    第 <span id="qaCurrentPage">${currentQAPage}</span> 页 / 共 <span id="qaTotalPages">${qaTotalPages}</span> 页
                    (共 <span id="qaTotalItems">${qaTotalItems}</span> 条)
                </span>
                <button class="pagination-btn next-btn" onclick="goToQAPage(${currentQAPage + 1})" title="下一页">下一页</button>
                <button class="pagination-btn last-btn" onclick="goToQAPage(${qaTotalPages})" title="末页">末页</button>
            </div>
            <div class="pagination-right">
                <span>跳转到</span>
                <input type="number" id="qaPageInput" class="page-input" value="${currentQAPage}" min="1" max="${qaTotalPages}" onkeypress="if(event.key==='Enter') goToQAPage(this.value)">
                <span>页</span>
                <span class="max-page">(共 <span id="qaMaxPage">${qaTotalPages}</span> 页)</span>
            </div>
            <div class="pagination-size">
                <span>每页显示：</span>
                <select id="qaPageSize" class="form-control" onchange="changeQAPageSize(this.value)">
                    <option value="10" ${qaPageSize === 10 ? 'selected' : ''}>10</option>
                    <option value="20" ${qaPageSize === 20 ? 'selected' : ''}>20</option>
                    <option value="50" ${qaPageSize === 50 ? 'selected' : ''}>50</option>
                    <option value="100" ${qaPageSize === 100 ? 'selected' : ''}>100</option>
                </select>
            </div>
        `;
    } else {
        // 更新分页信息显示
        const currentPageEl = document.getElementById('qaCurrentPage');
        const totalPagesEl = document.getElementById('qaTotalPages');
        const totalItemsEl = document.getElementById('qaTotalItems');
        const maxPageEl = document.getElementById('qaMaxPage');
        const pageInputEl = document.getElementById('qaPageInput');
        
        if (currentPageEl) currentPageEl.textContent = currentQAPage;
        if (totalPagesEl) totalPagesEl.textContent = qaTotalPages;
        if (totalItemsEl) totalItemsEl.textContent = qaTotalItems;
        if (maxPageEl) maxPageEl.textContent = qaTotalPages;
        if (pageInputEl) {
            pageInputEl.value = currentQAPage;
            pageInputEl.max = qaTotalPages;
        }
    }
    
    // 更新分页按钮状态
    const firstBtn = document.querySelector('#qaPaginationArea .first-btn');
    const prevBtn = document.querySelector('#qaPaginationArea .prev-btn');
    const nextBtn = document.querySelector('#qaPaginationArea .next-btn');
    const lastBtn = document.querySelector('#qaPaginationArea .last-btn');
    
    if (firstBtn) firstBtn.disabled = currentQAPage <= 1;
    if (prevBtn) prevBtn.disabled = currentQAPage <= 1;
    if (nextBtn) nextBtn.disabled = currentQAPage >= qaTotalPages;
    if (lastBtn) lastBtn.disabled = currentQAPage >= qaTotalPages;
    
    // 更新按钮的 onclick 事件
    if (firstBtn) firstBtn.onclick = () => goToQAPage(1);
    if (prevBtn) prevBtn.onclick = () => goToQAPage(currentQAPage - 1);
    if (nextBtn) nextBtn.onclick = () => goToQAPage(currentQAPage + 1);
    if (lastBtn) lastBtn.onclick = () => goToQAPage(qaTotalPages);
}

// 搜索问答对
function searchQA() {
    const keyword = document.getElementById('searchQuestion').value.trim();
    currentQAFilters.question_keyword = keyword;
    currentQAPage = 1;
    loadQAData();
}

// 重置搜索
function resetQASearch() {
    document.getElementById('searchQuestion').value = '';
    document.getElementById('filterQuestionType').value = '';
    document.getElementById('filterDifficulty').value = '';
    document.getElementById('filterCategory').value = '';
    
    currentQAFilters = {};
    currentQAPage = 1;
    loadQAData();
}

// 应用筛选器
function applyQAFilters() {
    const questionType = document.getElementById('filterQuestionType').value;
    const difficulty = document.getElementById('filterDifficulty').value;
    const category = document.getElementById('filterCategory').value;
    
    currentQAFilters = {};
    if (questionType) currentQAFilters.question_type = questionType;
    if (difficulty) currentQAFilters.difficulty_level = difficulty;
    if (category) currentQAFilters.category = category;
    
    currentQAPage = 1;
    loadQAData();
}

// 分页导航
function goToQAPage(page) {
    page = parseInt(page);
    if (isNaN(page) || page < 1 || page > qaTotalPages) {
        showError('请输入有效的页码');
        return;
    }
    currentQAPage = page;
    loadQAData();
}

function goToQAPrevPage() {
    if (currentQAPage > 1) {
        currentQAPage--;
        loadQAData();
    }
}

function goToQANextPage() {
    if (currentQAPage < qaTotalPages) {
        currentQAPage++;
        loadQAData();
    }
}

function goToQALastPage() {
    if (currentQAPage < qaTotalPages) {
        currentQAPage = qaTotalPages;
        loadQAData();
    }
}

function changeQAPageSize(size) {
    qaPageSize = parseInt(size);
    currentQAPage = 1;
    loadQAData();
}

// 加载分类选项
// 如果传入qaDataRows参数，则直接从该数据中提取分类；否则发送请求获取
function loadCategoryOptions(qaDataRows) {
    const select = document.getElementById('filterCategory');
    if (!select) return;
    
    // 如果提供了数据行，直接使用
    if (qaDataRows && Array.isArray(qaDataRows)) {
        updateCategorySelect(qaDataRows);
        return;
    }
    
    // 否则从已加载的表格数据中提取分类（如果表格已有数据）
    const tableBody = document.getElementById('qaTableBody');
    if (tableBody && tableBody.children.length > 0 && !tableBody.querySelector('.loading-cell')) {
        // 表格已有数据，尝试从当前页数据中提取分类
        const rows = [];
        tableBody.querySelectorAll('tr').forEach(tr => {
            // 从行数据属性中获取分类（如果存储了的话）
            const category = tr.dataset.category;
            if (category) {
                rows.push({ category });
            }
        });
        if (rows.length > 0) {
            updateCategorySelect(rows);
            return;
        }
    }
    
    // 如果表格没有数据，则发送请求获取（备用方案）
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    fetch(`${API_BASE}/groups/${groupId}/items?limit=1000`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.rows.length > 0) {
                updateCategorySelect(data.data.rows);
            }
        })
        .catch(error => {
            console.error('加载分类选项失败:', error);
        });
}

// 更新分类下拉框选项
function updateCategorySelect(rows) {
    const select = document.getElementById('filterCategory');
    if (!select || !rows) return;
    
    // 提取所有唯一的分类
    const categories = new Set();
    rows.forEach(qa => {
        if (qa.category) {
            categories.add(qa.category);
        }
    });
    
    // 添加选项
    let options = '<option value="">所有分类</option>';
    Array.from(categories).sort().forEach(category => {
        options += `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`;
    });
    select.innerHTML = options;
}

// 切换分组状态
function toggleGroupStatus() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    fetch(`${API_BASE}/groups/${groupId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})  // 发送空的JSON对象
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess(`分组已${result.status ? '激活' : '停用'}`);
            // 刷新页面
            location.reload();
        } else {
            showError('状态更新失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('切换分组状态失败:', error);
        showError('切换分组状态失败: ' + error.message);
    });
}

// 编辑分组
function editGroup() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    // 获取分组详情并显示编辑对话框
    fetch(`${API_BASE}/groups/${groupId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const group = result.data;
                // 填充编辑表单
                document.getElementById('editGroupId').value = groupId;
                document.getElementById('editGroupName').value = group.name || '';
                document.getElementById('editGroupPurpose').value = group.purpose || '';
                document.getElementById('editGroupTestType').value = group.test_type || 'custom';
                document.getElementById('editGroupLanguage').value = group.language || 'zh';
                document.getElementById('editGroupDifficultyRange').value = group.difficulty_range || '';
                document.getElementById('editGroupTags').value = Array.isArray(group.tags) ? group.tags.join(', ') : group.tags || '';
                document.getElementById('editGroupMetadata').value = group.metadata ? JSON.stringify(group.metadata, null, 2) : '{}';
                
                // 显示编辑对话框
                document.getElementById('editGroupDialog').classList.add('active');
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
    document.getElementById('editGroupDialog').classList.remove('active');
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
            document.getElementById('editGroupMetadataError').textContent = '元数据必须是有效的JSON格式';
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
            // 刷新页面
            location.reload();
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
function deleteGroup() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    DialogManager.confirm(
        '确定要删除这个分组吗？删除后无法恢复。',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/groups/${groupId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('分组删除成功');
                    // 返回列表页面
                    window.location.href = '/qa/groups';
                } else {
                    showError('分组删除失败：' + result.message);
                }
            } catch (error) {
                console.error('删除分组失败:', error);
                showError('删除分组失败：' + error.message);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 导出分组数据
function exportGroupData() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    // 这里可以实现导出功能
    showInfo('导出功能开发中...');
}

// 显示创建问答对对话框
function showCreateQADialog() {
    // 重置表单
    document.getElementById('createQAForm').reset();
    document.getElementById('qaQuestionError').textContent = '';
    document.getElementById('qaAnswersError').textContent = '';
    
    // 显示对话框
    document.getElementById('createQADialog').classList.add('active');
}

// 关闭创建问答对对话框
function closeCreateQADialog() {
    document.getElementById('createQADialog').classList.remove('active');
}

// 提交创建问答对
function submitCreateQA() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    const question = document.getElementById('qaQuestion').value.trim();
    const answersInput = document.getElementById('qaAnswers').value.trim();
    const context = document.getElementById('qaContext').value.trim();
    const questionType = document.getElementById('qaQuestionType').value;
    const language = document.getElementById('qaLanguage').value;
    const difficulty = document.getElementById('qaDifficulty').value;
    const category = document.getElementById('qaCategory').value.trim();
    const subCategory = document.getElementById('qaSubCategory').value.trim();
    const tagsInput = document.getElementById('qaTags').value.trim();
    const sourceDataset = document.getElementById('qaSourceDataset').value.trim();
    const hfDatasetId = document.getElementById('qaHFDatasetId').value.trim();
    
    // 验证必填字段
    if (!question) {
        document.getElementById('qaQuestionError').textContent = '问题不能为空';
        return;
    }
    
    if (!answersInput) {
        document.getElementById('qaAnswersError').textContent = '答案不能为空';
        return;
    }
    
    // 处理答案（支持多种格式）
    let answers;
    try {
        // 尝试解析为JSON
        answers = JSON.parse(answersInput);
    } catch (e) {
        // 如果不是JSON，作为普通文本处理
        answers = answersInput;
    }
    
    // 处理标签
    let tags = [];
    if (tagsInput) {
        tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
    }
    
    // 准备请求数据
    const data = {
        question: question,
        answers: answers,
        context: context || null,
        question_type: questionType || null,
        language: language,
        difficulty_level: difficulty ? parseInt(difficulty) : null,
        category: category || null,
        sub_category: subCategory || null,
        tags: tags,
        source_dataset: sourceDataset || null,
        hf_dataset_id: hfDatasetId || null
    };
    
    // 发送创建请求
    fetch(`${API_BASE}/groups/${groupId}/items`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('问答对创建成功');
            closeCreateQADialog();
            loadQAData(); // 刷新列表
            loadGroupTags(); // 刷新标签（如果有新标签）
        } else {
            showError('问答对创建失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('创建问答对失败:', error);
        showError('创建问答对失败: ' + error.message);
    });
}

// 编辑问答对
function editQA(qaId) {
    // 获取问答对详情
    fetch(`${API_BASE}/items/${qaId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const qa = result.data;
                
                // 填充表单
                document.getElementById('editQAId').value = qaId;
                document.getElementById('editQAQuestion').value = qa.question || '';
                document.getElementById('editQAContext').value = qa.context || '';
                document.getElementById('editQAQuestionType').value = qa.question_type || '';
                document.getElementById('editQALanguage').value = qa.language || 'zh';
                document.getElementById('editQADifficulty').value = qa.difficulty_level || '';
                document.getElementById('editQACategory').value = qa.category || '';
                document.getElementById('editQASubCategory').value = qa.sub_category || '';
                document.getElementById('editQASourceDataset').value = qa.source_dataset || '';
                document.getElementById('editQAHFDatasetId').value = qa.hf_dataset_id || '';
                
                // 处理答案
                let answersText = '';
                if (qa.answers) {
                    if (typeof qa.answers === 'string') {
                        answersText = qa.answers;
                    } else {
                        answersText = JSON.stringify(qa.answers, null, 2);
                    }
                }
                document.getElementById('editQAAnswers').value = answersText;
                
                // 处理标签
                const tags = Array.isArray(qa.tags) ? qa.tags.join(', ') : qa.tags || '';
                document.getElementById('editQATags').value = tags;
                
                // 显示对话框
                document.getElementById('editQADialog').classList.add('active');
            } else {
                showError('获取问答对详情失败: ' + result.message);
            }
        })
        .catch(error => {
            console.error('获取问答对详情失败:', error);
            showError('获取问答对详情失败: ' + error.message);
        });
}

// 关闭编辑问答对对话框
function closeEditQADialog() {
    document.getElementById('editQADialog').classList.remove('active');
}

// 提交编辑问答对
function submitEditQA() {
    const qaId = document.getElementById('editQAId').value;
    const question = document.getElementById('editQAQuestion').value.trim();
    const answersInput = document.getElementById('editQAAnswers').value.trim();
    const context = document.getElementById('editQAContext').value.trim();
    const questionType = document.getElementById('editQAQuestionType').value;
    const language = document.getElementById('editQALanguage').value;
    const difficulty = document.getElementById('editQADifficulty').value;
    const category = document.getElementById('editQACategory').value.trim();
    const subCategory = document.getElementById('editQASubCategory').value.trim();
    const tagsInput = document.getElementById('editQATags').value.trim();
    const sourceDataset = document.getElementById('editQASourceDataset').value.trim();
    const hfDatasetId = document.getElementById('editQAHFDatasetId').value.trim();
    
    // 验证必填字段
    if (!question) {
        document.getElementById('editQAQuestionError').textContent = '问题不能为空';
        return;
    }
    
    if (!answersInput) {
        document.getElementById('editQAAnswersError').textContent = '答案不能为空';
        return;
    }
    
    // 处理答案（支持多种格式）
    let answers;
    try {
        // 尝试解析为JSON
        answers = JSON.parse(answersInput);
    } catch (e) {
        // 如果不是JSON，作为普通文本处理
        answers = answersInput;
    }
    
    // 处理标签
    let tags = [];
    if (tagsInput) {
        tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
    }
    
    // 准备请求数据
    const data = {
        question: question,
        answers: answers,
        context: context || null,
        question_type: questionType || null,
        language: language,
        difficulty_level: difficulty ? parseInt(difficulty) : null,
        category: category || null,
        sub_category: subCategory || null,
        tags: tags,
        source_dataset: sourceDataset || null,
        hf_dataset_id: hfDatasetId || null
    };
    
    // 发送更新请求
    fetch(`${API_BASE}/items/${qaId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('问答对更新成功');
            closeEditQADialog();
            loadQAData(); // 刷新列表
        } else {
            showError('问答对更新失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('更新问答对失败:', error);
        showError('更新问答对失败: ' + error.message);
    });
}

// 删除问答对
function deleteQA(qaId) {
    DialogManager.confirm(
        '确定要删除这个问答对吗？删除后无法恢复。',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/items/${qaId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess('问答对删除成功');
                    loadQAData(); // 刷新列表
                } else {
                    showError('问答对删除失败：' + result.message);
                }
            } catch (error) {
                console.error('删除问答对失败:', error);
                showError('删除问答对失败：' + error.message);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 显示批量创建对话框
function showBatchCreateDialog() {
    // 重置表单
    document.getElementById('batchQAData').value = '';
    document.getElementById('batchQADataError').textContent = '';
    
    // 显示对话框
    document.getElementById('batchCreateDialog').classList.add('active');
}

// 关闭批量创建对话框
function closeBatchCreateDialog() {
    document.getElementById('batchCreateDialog').classList.remove('active');
}

// 提交批量创建
function submitBatchCreate() {
    const groupId = window.currentGroupId;
    if (!groupId) return;
    
    const qaDataInput = document.getElementById('batchQAData').value.trim();
    
    if (!qaDataInput) {
        document.getElementById('batchQADataError').textContent = '问答对数据不能为空';
        return;
    }
    
    let qaData;
    try {
        qaData = JSON.parse(qaDataInput);
        if (!Array.isArray(qaData)) {
            throw new Error('数据必须是数组格式');
        }
    } catch (error) {
        document.getElementById('batchQADataError').textContent = '数据必须是有效的JSON数组格式';
        return;
    }
    
    // 为每个项目添加group_id
    qaData.forEach(item => {
        item.group_id = parseInt(groupId);
    });
    
    // 发送批量创建请求
    fetch(`${API_BASE}/groups/${groupId}/items/batch`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ items: qaData })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess(`批量创建完成，成功${result.stats.success}条，失败${result.stats.failed}条`);
            closeBatchCreateDialog();
            loadQAData(); // 刷新列表
        } else {
            showError('批量创建失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('批量创建失败:', error);
        showError('批量创建失败: ' + error.message);
    });
}

// 显示导入问答对对话框
function showImportQADialog() {
    // 跳转到新的导入页面
    const groupId = window.currentGroupId;
    if (groupId) {
        window.location.href = `/qa/groups/${groupId}/import`;
    } else {
        showError('无法获取分组ID');
    }
}

// 关闭导入问答对对话框
function closeImportQADialog() {
    document.getElementById('importQADialog').classList.remove('active');
}

// 切换导入选项
function toggleQAImportOptions() {
    const importType = document.getElementById('importQAType').value;
    const fileUploadSection = document.getElementById('qaFileUploadSection');
    const huggingfaceSection = document.getElementById('qaHuggingfaceSection');
    
    if (importType === 'huggingface') {
        fileUploadSection.style.display = 'none';
        huggingfaceSection.style.display = 'block';
    } else {
        fileUploadSection.style.display = 'block';
        huggingfaceSection.style.display = 'none';
    }
}

// 开始导入问答对
function startQAImport() {
    const groupId = window.currentGroupId;
    const importType = document.getElementById('importQAType').value;
    const batchSize = parseInt(document.getElementById('importQABatchSize').value) || 1000;
    
    if (!groupId) {
        showError('分组ID不存在');
        return;
    }
    
    if (importType === 'huggingface') {
        const datasetPath = document.getElementById('qaHFDatasetPath').value.trim();
        if (!datasetPath) {
            showError('请输入数据集路径');
            return;
        }
        
        // 发送HuggingFace导入请求
        fetch(`${API_BASE}/groups/${groupId}/items/import/huggingface`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dataset_path: datasetPath,
                batch_size: batchSize
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showQAImportProgress(result.stats);
            } else {
                showError('导入失败: ' + result.message);
            }
        })
        .catch(error => {
            console.error('导入失败:', error);
            showError('导入失败: ' + error.message);
        });
        
    } else {
        const fileInput = document.getElementById('importQAFile');
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
                    data = parseCSV(e.target.result);
                }
                
                if (!Array.isArray(data)) {
                    showError('文件内容必须是数组格式');
                    return;
                }
                
                // 开始批量导入
                startQABatchImport(groupId, data, batchSize);
                
            } catch (error) {
                showError('文件解析失败: ' + error.message);
            }
        };
        
        reader.onerror = function() {
            showError('文件读取失败');
        };
        
        reader.readAsText(file);
    }
}

// 开始批量导入问答对
function startQABatchImport(groupId, data, batchSize) {
    isQAImporting = true;
    qaImportCanceled = false;
    
    // 显示进度对话框
    showQAImportProgressDialog();
    
    // 分批处理数据
    const total = data.length;
    let processed = 0;
    let success = 0;
    let failed = 0;
    let errors = [];
    
    function processBatch(startIndex) {
        if (qaImportCanceled || startIndex >= total) {
            // 导入完成或取消
            isQAImporting = false;
            updateQAImportProgress(total, processed, success, failed, errors);
            
            if (!qaImportCanceled) {
                // 显示完成按钮
                document.querySelector('#importQAProgressDialog .close-btn').style.display = 'block';
                document.querySelector('#importQAProgressDialog .cancel-btn').style.display = 'none';
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
                updateQAImportProgress(total, processed, success, failed, errors);
                
                // 处理下一个批次
                setTimeout(() => processBatch(endIndex), 100);
            } else {
                errors.push(`批次 ${startIndex/batchSize + 1} 失败: ${result.message}`);
                failed += batch.length;
                processed += batch.length;
                
                // 更新进度
                updateQAImportProgress(total, processed, success, failed, errors);
                
                // 继续处理下一个批次
                setTimeout(() => processBatch(endIndex), 100);
            }
        })
        .catch(error => {
            errors.push(`批次 ${startIndex/batchSize + 1} 错误: ${error.message}`);
            failed += batch.length;
            processed += batch.length;
            
            // 更新进度
            updateQAImportProgress(total, processed, success, failed, errors);
            
            // 继续处理下一个批次
            setTimeout(() => processBatch(endIndex), 100);
        });
    }
    
    // 开始处理第一个批次
    processBatch(0);
}

// 显示导入进度对话框
function showQAImportProgressDialog() {
    // 重置进度
    document.getElementById('importQAProgressBar').style.width = '0%';
    document.getElementById('importQAProgressText').textContent = '0%';
    document.getElementById('importQATotal').textContent = '0';
    document.getElementById('importQASuccess').textContent = '0';
    document.getElementById('importQAFailed').textContent = '0';
    document.getElementById('importQASkipped').textContent = '0';
    document.getElementById('importQADuration').textContent = '0';
    document.getElementById('importQAErrorList').innerHTML = '';
    
    // 显示按钮
    document.querySelector('#importQAProgressDialog .close-btn').style.display = 'none';
    document.querySelector('#importQAProgressDialog .cancel-btn').style.display = 'block';
    
    // 显示对话框
    document.getElementById('importQAProgressDialog').classList.add('active');
}

// 更新导入进度
function updateQAImportProgress(total, processed, success, failed, errors) {
    const progress = total > 0 ? Math.round((processed / total) * 100) : 0;
    
    document.getElementById('importQAProgressBar').style.width = progress + '%';
    document.getElementById('importQAProgressText').textContent = progress + '%';
    document.getElementById('importQATotal').textContent = total;
    document.getElementById('importQASuccess').textContent = success;
    document.getElementById('importQAFailed').textContent = failed;
    document.getElementById('importQASkipped').textContent = total - processed;
    
    // 更新错误列表
    const errorList = document.getElementById('importQAErrorList');
    if (errors.length > 0) {
        errorList.innerHTML = errors.map(error => `<div>${escapeHtml(error)}</div>`).join('');
    }
}

// 关闭导入进度对话框
function closeImportQAProgressDialog() {
    document.getElementById('importQAProgressDialog').classList.remove('active');
}

// 取消导入
function cancelQAImport() {
    qaImportCanceled = true;
    isQAImporting = false;
    closeImportQAProgressDialog();
    showInfo('导入已取消');
}

