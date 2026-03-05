// 标注任务管理页面 JavaScript
// 与 annotation_tasks.html 路由文件对应

let pagination = null;
let searchComponent = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化分页组件
    pagination = new PaginationComponent('paginationArea', (page, pageSize) => {
        loadTaskList(page, pageSize);
    });
    
    // 初始化搜索组件
    searchComponent = new SearchComponent('searchInput', 'searchBtn', (keyword) => {
        loadTaskList(1, pagination.pageSize, keyword);
    });
    
    // 绑定刷新按钮事件
    document.getElementById('refreshBtn').addEventListener('click', function() {
        // 清空搜索框
        document.getElementById('searchInput').value = '';
        // 刷新列表
        refreshTaskList();
    });
    
    // 加载初始数据
    loadTaskList(1, 20);
    
    // 加载知识库和环境列表用于创建任务
    loadKnowledgeBases();
    loadEnvironments();
});

// 加载标注任务列表
async function loadTaskList(page = 1, pageSize = 20, keyword = null) {
    try {
        const tableBody = document.getElementById('taskTableBody');
        tableBody.innerHTML = '<tr><td colspan="12" style="text-align: center;">加载中...</td></tr>';
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: page,
            limit: pageSize
        });
        
        if (keyword) {
            params.append('keyword', keyword);
        }
        
        const response = await fetch(`/api/annotation/tasks/list?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            renderTaskTable(data.data.rows);
            pagination.update(data.data.total, page, pageSize);
        } else {
            DialogManager.showError(data.message || '加载任务列表失败');
            tableBody.innerHTML = '<tr><td colspan="12" style="text-align: center; color: red;">加载失败</td></tr>';
        }
    } catch (error) {
        console.error('加载任务列表时出错:', error);
        DialogManager.showError('网络请求错误', error);
        const tableBody = document.getElementById('taskTableBody');
        tableBody.innerHTML = '<tr><td colspan="12" style="text-align: center; color: red;">网络错误</td></tr>';
    }
}

// 渲染任务表格
function renderTaskTable(tasks) {
    const tableBody = document.getElementById('taskTableBody');
    tableBody.innerHTML = '';
    
    if (tasks && tasks.length > 0) {
        tasks.forEach(task => {
            const row = createTaskRow(task);
            tableBody.appendChild(row);
        });
    } else {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="12" style="text-align: center;">暂无标注任务</td>';
        tableBody.appendChild(row);
    }
}

// 创建任务行 - 参考 local_knowledge_detail_label_studio.js 的格式
function createTaskRow(task) {
    const annotatedChunks = task.annotated_chunks !== undefined ? task.annotated_chunks : 0;
    const totalChunks = task.total_chunks !== undefined ? task.total_chunks : 0;
    const progressText = `${annotatedChunks}/${totalChunks}`;
    const progressPercent = totalChunks ? (annotatedChunks / totalChunks * 100) : 0;
    
    // 获取状态信息
    const statusInfo = getTaskStatusInfo(task);
    
    // 格式化时间
    const createdAt = task.created_at ? formatDateTime(task.created_at) : '-';
    
    const row = document.createElement('tr');
    
    // 将任务数据编码为 JSON 字符串，用于编辑
    const taskJson = encodeURIComponent(JSON.stringify(task));
    
    row.innerHTML = `
        <td><div>${task.task_id || 'N/A'}</div></td>
        <td><div>${task.task_name || '未知任务'}</div></td>
        <td><div>${task.local_knowledge_id || 'N/A'}</div></td>
        <td><div>${task.knowledge_base_name || '未知知识库'}</div></td>
        <td><div>${task.question_set_id || 'N/A'}</div></td>
        <td><div>${task.question_set_name || '未知问题集'}</div></td>
        <td><div>${task.label_studio_env_id || 'N/A'}</div></td>
        <td>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressPercent}%"></div>
                </div>
                <span class="progress-text">${progressText}</span>
            </div>
        </td>
        <td><span class="status-label ${statusInfo.statusClass}">${statusInfo.statusText}</span></td>
        <td><div>${task.annotation_type || '-'}</div></td>
        <td><div>${createdAt}</div></td>
        <td>
            <div class="task-actions">
                <button class="task-action-btn edit-btn" onclick="handleEditTaskClick('${taskJson}')">编辑</button>
                <button class="task-action-btn delete-btn" onclick="deleteTask('${task.task_id}')">删除</button>
            </div>
        </td>
    `;
    
    return row;
}

// 获取任务状态信息
function getTaskStatusInfo(task) {
    let statusClass = '';
    let statusText = '';
    
    switch(task.task_status) {
        case '未开始':
            statusClass = 'status-not-started';
            statusText = '未开始';
            break;
        case '标注中':
            statusClass = 'status-in-progress';
            statusText = '标注中';
            break;
        case '已完成':
            statusClass = 'status-completed';
            statusText = '已完成';
            break;
        default:
            statusClass = 'status-not-started';
            statusText = task.task_status || '未知';
    }
    
    return { statusClass, statusText };
}

// 格式化日期时间
function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateStr;
    }
}

// 显示创建任务模态框
function showCreateTaskModal() {
    document.getElementById('taskModalTitle').textContent = '创建标注任务';
    document.getElementById('taskId').value = '';
    document.getElementById('taskName').value = '';
    document.getElementById('taskKnowledgeBaseSelect').value = '';
    document.getElementById('taskQuestionSet').innerHTML = '<option value="">请先选择知识库</option>';
    document.getElementById('taskEnvironmentDisplay').value = '';
    document.getElementById('taskEnvironment').value = '';
    document.getElementById('taskAnnotationType').value = '';
    
    // 隐藏任务状态组（仅编辑时显示）
    document.getElementById('taskStatusGroup').style.display = 'none';
    
    // 启用选择框
    document.getElementById('taskKnowledgeBaseSelect').disabled = false;
    document.getElementById('taskQuestionSet').disabled = false;
    document.getElementById('taskEnvironmentDisplay').style.display = 'none';
    document.getElementById('taskEnvironment').style.display = 'block';
    
    document.getElementById('taskModal').style.display = 'block';
}

// 显示编辑任务模态框
function handleEditTaskClick(taskJsonString) {
    try {
        const task = JSON.parse(decodeURIComponent(taskJsonString));
        
        document.getElementById('taskModalTitle').textContent = '编辑标注任务';
        document.getElementById('taskId').value = task.task_id || '';
        document.getElementById('taskName').value = task.task_name || '';
        
        // 设置知识库（只读）
        const kbSelect = document.getElementById('taskKnowledgeBaseSelect');
        if (task.knowledge_base_name) {
            kbSelect.innerHTML = `<option value="${task.local_knowledge_id}">${task.knowledge_base_name}(${task.local_knowledge_id})</option>`;
        } else {
            kbSelect.innerHTML = `<option value="${task.local_knowledge_id}">${task.local_knowledge_id}</option>`;
        }
        kbSelect.disabled = true;
        
        // 设置问题集（只读）
        const qsSelect = document.getElementById('taskQuestionSet');
        if (task.question_set_name) {
            qsSelect.innerHTML = `<option value="${task.question_set_id}">${task.question_set_name}(${task.question_set_id})</option>`;
        } else {
            qsSelect.innerHTML = `<option value="${task.question_set_id}">${task.question_set_id}</option>`;
        }
        qsSelect.disabled = true;
        
        // 设置环境（只读，直接显示在输入框中）
        document.getElementById('taskEnvironmentDisplay').value = task.label_studio_env_id || '';
        document.getElementById('taskEnvironment').value = task.label_studio_env_id || '';
        document.getElementById('taskEnvironmentDisplay').style.display = 'block';
        document.getElementById('taskEnvironment').style.display = 'none';
        
        // 显示并设置任务状态
        document.getElementById('taskStatusGroup').style.display = 'block';
        document.getElementById('taskStatus').value = task.task_status || '未开始';
        
        // 设置标注类型（只读）
        document.getElementById('taskAnnotationType').value = task.annotation_type || '';
        document.getElementById('taskAnnotationType').disabled = true;
        
        document.getElementById('taskModal').style.display = 'block';
    } catch (error) {
        console.error('解析任务数据时出错:', error);
        DialogManager.showError('编辑任务时发生错误');
    }
}

// 隐藏任务模态框
function hideTaskModal() {
    document.getElementById('taskModal').style.display = 'none';
}

// 保存任务（创建或更新）
async function saveTask() {
    const taskId = document.getElementById('taskId').value;
    const taskName = document.getElementById('taskName').value;
    const knowledgeBaseId = document.getElementById('taskKnowledgeBaseSelect').value;
    const environmentId = document.getElementById('taskEnvironment').value;
    const questionSetId = document.getElementById('taskQuestionSet').value;
    const annotationType = document.getElementById('taskAnnotationType').value;
    
    // 验证必填字段
    if (!taskName) {
        DialogManager.showError('请输入任务名称');
        return;
    }
    
    if (!knowledgeBaseId) {
        DialogManager.showError('请选择本地知识库');
        return;
    }
    
    if (!questionSetId) {
        DialogManager.showError('请选择问题集');
        return;
    }
    
    if (!environmentId) {
        DialogManager.showError('请选择 Label Studio 环境');
        return;
    }
    
    const isEdit = !!taskId;
    const method = isEdit ? 'PUT' : 'POST';
    const url = isEdit ? '/api/annotation/tasks/update' : '/api/annotation/tasks/create';
    
    const requestData = {
        task_name: taskName,
        local_knowledge_id: knowledgeBaseId,
        label_studio_env_id: environmentId,
        question_set_id: questionSetId,
        annotation_type: annotationType
    };
    
    if (isEdit) {
        requestData.task_id = taskId;
        // 只在编辑模式下添加任务状态
        const taskStatus = document.getElementById('taskStatus').value;
        requestData.task_status = taskStatus;
    }
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            DialogManager.showSuccess(isEdit ? '任务更新成功' : '任务创建成功', () => {
                hideTaskModal();
                loadTaskList(pagination.currentPage, pagination.pageSize);
            });
        } else {
            DialogManager.showError(isEdit ? '更新失败：' + data.message : '创建失败：' + data.message);
        }
    } catch (error) {
        console.error('保存任务时出错:', error);
        DialogManager.showError('保存任务时发生错误', error);
    }
}

// 删除任务
async function deleteTask(taskId) {
    if (!DialogManager.confirm('确定要删除这个标注任务吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/annotation/tasks/delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_id: taskId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            DialogManager.showSuccess('任务删除成功', () => {
                loadTaskList(pagination.currentPage, pagination.pageSize);
            });
        } else {
            DialogManager.showError('删除失败：' + data.message);
        }
    } catch (error) {
        console.error('删除任务时出错:', error);
        DialogManager.showError('删除任务时发生错误', error);
    }
}

// 刷新任务列表
function refreshTaskList() {
    loadTaskList(pagination.currentPage, pagination.pageSize);
}

// 加载知识库列表
async function loadKnowledgeBases() {
    try {
        const response = await fetch('/api/local_knowledge/list');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('taskKnowledgeBaseSelect');
            select.innerHTML = '<option value="">请选择知识库</option>';
            
            if (data.data && data.data.length > 0) {
                data.data.forEach(kb => {
                    const option = document.createElement('option');
                    option.value = kb.knowledge_id || kb.id;
                    option.textContent = `${kb.knowledge_name || kb.name}(${kb.knowledge_id || kb.id})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载知识库列表时出错:', error);
    }
}

// 加载 Label Studio 环境列表
async function loadEnvironments() {
    try {
        const response = await fetch('/api/label_studio/environments/list');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('taskEnvironment');
            select.innerHTML = '<option value="">请选择环境</option>';
            
            if (data.data && data.data.length > 0) {
                data.data.forEach(env => {
                    const option = document.createElement('option');
                    option.value = env.label_studio_id;
                    option.textContent = `${env.label_studio_id} - ${env.label_studio_url}`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载环境列表时出错:', error);
    }
}

// 当选择知识库时，加载问题集列表
async function loadQuestionSetsForKnowledgeBase() {
    const knowledgeBaseId = document.getElementById('taskKnowledgeBaseSelect').value;
    
    if (!knowledgeBaseId) {
        document.getElementById('taskQuestionSet').innerHTML = '<option value="">请先选择知识库</option>';
        return;
    }
    
    try {
        const response = await fetch(`/api/questions/list?knowledge_id=${knowledgeBaseId}`);
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('taskQuestionSet');
            select.innerHTML = '<option value="">请选择问题集</option>';
            
            if (data.data && data.data.length > 0) {
                data.data.forEach(qs => {
                    const option = document.createElement('option');
                    option.value = qs.question_id || qs.id;
                    option.textContent = `${qs.question_name || qs.name}(${qs.question_id || qs.id})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载问题集列表时出错:', error);
    }
}

// 关闭模态框（点击外部）
window.onclick = function(event) {
    const modal = document.getElementById('taskModal');
    if (event.target === modal) {
        hideTaskModal();
    }
}
