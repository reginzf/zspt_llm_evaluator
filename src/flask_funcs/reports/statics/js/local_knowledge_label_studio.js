// 标注功能相关的JavaScript代码
let currentKnoId = null;
let currentEnvironment = null;


// 加载环境绑定状态
function loadEnvironmentStatus() {
    fetch('/local_knowledge_detail/label_studio/get_environments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateEnvironmentDisplay(data.data);  // data.data 现在包含 environments 和 bound_environment
        } else {
            console.error('获取环境状态失败:', data.message);
        }
    })
    .catch(error => {
        console.error('请求环境状态时出错:', error);
    });
}

// 更新环境显示
function updateEnvironmentDisplay(data) {
    const environmentStatusDiv = document.getElementById('environmentStatus');
    const createTaskBtn = document.getElementById('createTaskBtn');
    
    if (data && data.bound_environment) {
        // 已绑定环境
        currentEnvironment = data.bound_environment;
        environmentStatusDiv.innerHTML = `
            <div class="environment-status bound">
                <div class="environment-info">
                    <strong>已绑定环境:</strong> ${data.bound_environment.label_studio_url}
                    <br>
                    <small>ID: ${data.bound_environment.label_studio_id}</small>
                </div>
                <div class="environment-actions">
                    <button class="unbind-btn" onclick="showUnbindModal()">解绑</button>
                </div>
            </div>
        `;
        createTaskBtn.disabled = false;
    } else {
        // 未绑定环境
        currentEnvironment = null;
        environmentStatusDiv.innerHTML = `
            <div class="environment-status unbound">
                <div class="environment-info">
                    <strong>未绑定Label-Studio环境</strong>
                    <br>
                    <small>请先绑定环境以启用标注功能</small>
                </div>
            </div>
        `;
        createTaskBtn.disabled = true;
    }
}

// 显示绑定环境模态框
function showBindModal() {
    fetch('/local_knowledge_detail/label_studio/get_environments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const environments = data.data.environments || [];  // 从 data.data.environments 获取环境列表
            let options = '<option value="">请选择Label-Studio环境</option>';
            
            environments.forEach(env => {
                options += `<option value="${env.label_studio_id}">${env.label_studio_id} - ${env.label_studio_url}</option>`;
            });
            
            document.getElementById('lsEnvironmentSelect').innerHTML = options;
            document.getElementById('bindModal').style.display = 'block';
        } else {
            alert('获取环境列表失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('获取环境列表时出错:', error);
        alert('获取环境列表失败');
    });
}

// 隐藏绑定环境模态框
function hideBindModal() {
    document.getElementById('bindModal').style.display = 'none';
}

// 绑定环境
function bindEnvironment() {
    const environmentId = document.getElementById('lsEnvironmentSelect').value;  // 修复：使用正确的元素ID
    if (!environmentId) {
        alert('请选择要绑定的环境');
        return;
    }
    
    fetch('/local_knowledge_detail/label_studio/bind_environment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId,
            ls_id: environmentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('环境绑定成功');
            hideBindModal();
            loadEnvironmentStatus();
        } else {
            alert('绑定失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('绑定环境时出错:', error);
        alert('绑定环境时发生错误');
    });
}

// 显示解绑环境模态框
function showUnbindModal() {
    if (confirm('确定要解绑当前Label-Studio环境吗？')) {
        unbindEnvironment();
    }
}

// 解绑环境
function unbindEnvironment() {
    fetch('/local_knowledge_detail/label_studio/unbind_environment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId,
            ls_id: currentEnvironment.label_studio_id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('环境解绑成功');
            loadEnvironmentStatus();
        } else {
            alert('解绑失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('解绑环境时出错:', error);
        alert('解绑环境时发生错误');
    });
}

// 显示创建任务模态框
function showCreateTaskModal() {
    document.getElementById('taskModalTitle').textContent = '创建标注任务';
    document.getElementById('taskIdInput').style.display = 'none';
    document.getElementById('taskId').value = '';
    document.getElementById('taskName').value = '';
    document.getElementById('taskKnowledgeBase').value = currentKnoId;
    document.getElementById('taskEnvironment').value = currentEnvironment ? currentEnvironment.label_studio_id : '';
    
    document.getElementById('taskModal').style.display = 'block';
}

// 显示编辑任务模态框
function showEditTaskModal(task) {
    document.getElementById('taskModalTitle').textContent = '编辑标注任务';
    document.getElementById('taskIdInput').style.display = 'block';
    document.getElementById('taskId').value = task.id;
    document.getElementById('taskName').value = task.name;
    document.getElementById('taskKnowledgeBase').value = task.knowledge_base_id;
    document.getElementById('taskEnvironment').value = task.environment_id;
    
    document.getElementById('taskModal').style.display = 'block';
}

// 隐藏任务模态框
function hideTaskModal() {
    document.getElementById('taskModal').style.display = 'none';
}

// 保存任务（创建或更新）
function saveTask() {
    const taskId = document.getElementById('taskId').value;
    const taskName = document.getElementById('taskName').value;
    const knowledgeBaseId = document.getElementById('taskKnowledgeBase').value;
    const environmentId = document.getElementById('taskEnvironment').value;
    
    if (!taskName) {
        alert('请输入任务名称');
        return;
    }
    
    const isEdit = !!taskId;
    const method = isEdit ? 'PUT' : 'POST';
    const url = isEdit ? '/local_knowledge_detail/label_studio/update_project' : '/local_knowledge_detail/label_studio/create_annotation_project';
    
    const requestData = {
        name: taskName,
        knowledge_base_id: knowledgeBaseId,
        environment_id: environmentId
    };
    
    if (isEdit) {
        requestData.id = taskId;
    }
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(isEdit ? '任务更新成功' : '任务创建成功');
            hideTaskModal();
            loadAnnotationProjects();
        } else {
            alert(isEdit ? '更新失败: ' : '创建失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error(isEdit ? '更新任务时出错:' : '创建任务时出错:', error);
        alert(isEdit ? '更新任务时发生错误' : '创建任务时发生错误');
    });
}

// 删除任务
function deleteTask(taskId) {
    if (confirm('确定要删除这个标注任务吗？')) {
        fetch('/local_knowledge_detail/label_studio/delete_project', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: taskId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('任务删除成功');
                loadAnnotationProjects();
            } else {
                alert('删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('删除任务时出错:', error);
            alert('删除任务时发生错误');
        });
    }
}

// 加载标注任务列表
function loadAnnotationProjects() {
    fetch('/local_knowledge_detail/label_studio/get_project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderTaskTable(data.data);
        } else {
            console.error('获取任务列表失败:', data.message);
        }
    })
    .catch(error => {
        console.error('请求任务列表时出错:', error);
    });
}

// 渲染任务表格
function renderTaskTable(tasks) {
    const tableBody = document.getElementById('taskTableBody');
    tableBody.innerHTML = '';
    
    if (tasks && tasks.length > 0) {
        tasks.forEach(task => {
            const progressText = task.annotated_count ? `${task.annotated_count}/${task.total_count}` : '0/0';
            const progressPercent = task.total_count ? (task.annotated_count / task.total_count * 100) : 0;
            
            let statusClass = '';
            let statusText = '';
            switch(task.status) {
                case 'not_started':
                    statusClass = 'status-not-started';
                    statusText = '未开始';
                    break;
                case 'in_progress':
                    statusClass = 'status-in-progress';
                    statusText = '进行中';
                    break;
                case 'completed':
                    statusClass = 'status-completed';
                    statusText = '已完成';
                    break;
                default:
                    statusClass = 'status-not-started';
                    statusText = task.status;
            }
            
            // 创建一个安全的onclick事件处理器
            const taskJson = encodeURIComponent(JSON.stringify(task));
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task.name}</td>
                <td>${task.knowledge_base_name}(${task.knowledge_base_id})</td>
                <td>${task.question_set_name || '待选择'}(${task.question_set_id || '-'})</td>
                <td>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progressPercent}%"></div>
                        </div>
                        <span class="progress-text">${progressText}</span>
                    </div>
                </td>
                <td><span class="status-label ${statusClass}">${statusText}</span></td>
                <td>
                    <div class="task-actions">
                        <button class="task-action-btn edit-btn" onclick="handleEditTaskClick(decodeURIComponent('${taskJson}'))">编辑</button>
                        <button class="task-action-btn delete-btn" onclick="deleteTask('${task.id}')">删除</button>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" style="text-align: center;">暂无标注任务</td>`;
        tableBody.appendChild(row);
    }
}

// 处理编辑任务点击事件
function handleEditTaskClick(taskJsonString) {
    try {
        const task = JSON.parse(decodeURIComponent(taskJsonString));
        showEditTaskModal(task);
    } catch (error) {
        console.error('解析任务数据时出错:', error);
        alert('编辑任务时发生错误');
    }
}

// 确保DOM加载完成后初始化
// document.addEventListener('DOMContentLoaded', function() {
//     // 这里需要从页面获取kno_id，通常在页面加载时通过模板变量传入
//     // initAnnotationTab(knoId); // 需要在页面中调用并传入实际的kno_id
// });

// 添加初始化函数，供页面调用
function initAnnotationTab(knoId) {
    currentKnoId = knoId;
    loadEnvironmentStatus();
    loadAnnotationProjects();
}