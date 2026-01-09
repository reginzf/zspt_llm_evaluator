// 标注功能相关的JavaScript代码
let currentKnoId = null;
let currentEnvironment = null;
let expandedEnvironmentId = null;  // 记录当前展开的环境ID


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
    const environmentTableBody = document.getElementById('environmentTableBody');
    const createTaskBtn = document.getElementById('createTaskBtn');
    
    if (data && data.environments && data.environments.length > 0) {
        // 显示所有环境
        let rows = '';
        
        data.environments.forEach(env => {
            // 检查当前环境是否被绑定
            const isBound = data.bound_environments && data.bound_environments.some(bound => bound.label_studio_id === env.label_studio_id);
            
            // 获取该环境下的任务数量
            const taskCount = env.task_count || 0;  // 假设后端会返回每个环境的任务数量
            
            // 设置当前环境
            if (isBound) {
                currentEnvironment = env;
                createTaskBtn.disabled = false;
            }
            
            // 环境行
            rows += `
                <tr>
                    <td>${env.label_studio_id}</td>
                    <td><a href="${env.label_studio_url}" target="_blank">${env.label_studio_url}</a></td>
                    <td>${taskCount}</td>
                    <td>
                        <div class="environment-actions">
                            <button class="environment-action-btn expand-btn" onclick="toggleEnvironmentTasks('${env.label_studio_id}')">展开</button>
                            <button class="environment-action-btn create-task-env-btn" onclick="showCreateTaskModalWithEnv('${env.label_studio_id}')">创建任务</button>
                            ${isBound ? `<button class="environment-action-btn unbind-env-btn" onclick="showUnbindModal('${env.label_studio_id}')">解绑</button>` : 
                              `<button class="environment-action-btn" onclick="bindEnvironmentToId('${env.label_studio_id}')" ${currentEnvironment ? 'disabled' : ''}>绑定</button>`}
                        </div>
                    </td>
                </tr>
            `;
        });
        
        environmentTableBody.innerHTML = rows;
    } else {
        // 未绑定环境
        currentEnvironment = null;
        environmentTableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center;">暂无Label-Studio环境，请先添加环境</td>
            </tr>
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

// 绑定特定环境ID
function bindEnvironmentToId(envId) {
    fetch('/local_knowledge_detail/label_studio/bind_environment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId,
            ls_id: envId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('环境绑定成功');
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
function showUnbindModal(envId) {
    if (confirm('确定要解绑当前Label-Studio环境吗？')) {
        unbindEnvironment(envId);
    }
}

// 解绑环境
function unbindEnvironment(envId) {
    fetch('/local_knowledge_detail/label_studio/unbind_environment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: currentKnoId,
            ls_id: envId || (currentEnvironment ? currentEnvironment.label_studio_id : '')
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

// 展开/收起环境下的任务列表
function toggleEnvironmentTasks(envId) {
    // 如果点击的是当前展开的环境，则收起它
    if (expandedEnvironmentId === envId) {
        expandedEnvironmentId = null;
        // 这里可以隐藏任务列表（如果实现任务列表展示功能）
        return;
    }
    
    expandedEnvironmentId = envId;
    // 加载并显示该环境下的任务列表
    loadTasksForEnvironment(envId);
}

// 加载特定环境的任务列表
function loadTasksForEnvironment(envId) {
    fetch('/local_knowledge_detail/label_studio/get_tasks_by_environment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            env_id: envId,
            kno_id: currentKnoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 在这里展示环境下的任务列表
            // 可以在表格下方添加一个子表格来展示任务
            console.log('获取环境任务列表:', data.data);
        } else {
            console.error('获取环境任务列表失败:', data.message);
        }
    })
    .catch(error => {
        console.error('请求环境任务列表时出错:', error);
    });
}

// 显示创建任务模态框（带环境ID）
function showCreateTaskModalWithEnv(envId) {
    // 预先设置环境ID
    document.getElementById('taskEnvironment').value = envId;
    
    // 加载知识库列表
    loadBoundKnowledgeBases(envId);
    
    showCreateTaskModal();
}

// 加载已绑定的知识库列表
function loadBoundKnowledgeBases(envId) {
    fetch('/local_knowledge_detail/label_studio/knowledge/bound_list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            env_id: envId,
            local_knowledge_id: currentKnoId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('taskKnowledgeBaseSelect');
            select.innerHTML = '<option value="">请选择知识库</option>';
            
            data.data.forEach(kb => {
                const option = document.createElement('option');
                option.value = kb.knowledge_id;
                option.textContent = `${kb.knowledge_name}(${kb.knowledge_id})`;
                select.appendChild(option);
            });
        } else {
            console.error('获取知识库列表失败:', data.message);
        }
    })
    .catch(error => {
        console.error('请求知识库列表时出错:', error);
    });
}

// 当选择知识库时，加载问题集列表
function loadQuestionSetsForKnowledgeBase() {
    // 使用本地知识库ID而不是下拉框选中的值
    const localKnowledgeId = currentKnoId;
    if (!localKnowledgeId) {
        document.getElementById('taskQuestionSet').innerHTML = '<option value="">请选择知识库</option>';
        return;
    }
    
    fetch('/local_knowledge_detail/label_studio/questionset/available', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            knowledge_id: localKnowledgeId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('taskQuestionSet');
            select.innerHTML = '<option value="">请选择问题集</option>';
            
            data.data.forEach(qs => {
                const option = document.createElement('option');
                option.value = qs.question_id;
                option.textContent = `${qs.question_name}(${qs.question_id})`;
                select.appendChild(option);
            });
        } else {
            console.error('获取问题集列表失败:', data.message);
        }
    })
    .catch(error => {
        console.error('请求问题集列表时出错:', error);
    });
}

// 显示创建任务模态框
function showCreateTaskModal() {
    document.getElementById('taskModalTitle').textContent = '创建标注任务';
    document.getElementById('taskIdInput').style.display = 'none';
    document.getElementById('taskId').value = '';
    document.getElementById('taskName').value = '';
    // 注释掉不存在的元素，使用taskKnowledgeBaseSelect代替
    // document.getElementById('taskKnowledgeBase').value = currentKnoId;
    document.getElementById('taskEnvironment').value = currentEnvironment ? currentEnvironment.label_studio_id : '';
    
    // 重置选择框
    document.getElementById('taskKnowledgeBaseSelect').innerHTML = '<option value="">加载中...</option>';
    document.getElementById('taskQuestionSet').innerHTML = '<option value="">请选择知识库</option>';
    
    document.getElementById('taskModal').style.display = 'block';
}

// 显示编辑任务模态框
function showEditTaskModal(task) {
    document.getElementById('taskModalTitle').textContent = '编辑标注任务';
    document.getElementById('taskIdInput').style.display = 'block';
    document.getElementById('taskId').value = task.id;
    document.getElementById('taskName').value = task.name;
    // 注释掉不存在的元素，使用taskKnowledgeBaseSelect代替
    // document.getElementById('taskKnowledgeBase').value = task.knowledge_base_id;
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
    const knowledgeBaseId = document.getElementById('taskKnowledgeBaseSelect').value;
    const environmentId = document.getElementById('taskEnvironment').value;
    const questionSetId = document.getElementById('taskQuestionSet').value; // 新增问题集ID
    
    if (!taskName) {
        alert('请输入任务名称');
        return;
    }
    
    if (!questionSetId) {
        alert('请选择问题集');
        return;
    }
    
    const isEdit = !!taskId;
    const method = isEdit ? 'PUT' : 'POST';
    const url = isEdit ? '/local_knowledge_detail/label_studio/update_project' : '/local_knowledge_detail/label_studio/create_annotation_project';
    
    const requestData = {
        name: taskName
    };
    
    if (isEdit) {
        // 更新模式：只需要任务ID和基本信息
        requestData.id = taskId;
    } else {
        // 创建模式：需要所有参数
        requestData.knowledge_base_id = currentKnoId;  // 使用本地知识库ID
        requestData.label_studio_id = environmentId;  // 改名为label_studio_id
        requestData.question_set_id = questionSetId;  // 添加问题集ID
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
            loadEnvironmentStatus();  // 重新加载环境状态以更新任务计数
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
                loadEnvironmentStatus();  // 重新加载环境状态以更新任务计数
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
            const progressText = task.annotated_chunks ? `${task.annotated_chunks}/${task.total_chunks}` : '0/0';
            const progressPercent = task.total_chunks ? (task.annotated_chunks / task.total_chunks * 100) : 0;
            
            let statusClass = '';
            let statusText = '';
            switch(task.task_status || task.status) {
                case '未开始':
                    statusClass = 'status-not-started';
                    statusText = '未开始';
                    break;
                case '进行中':
                    statusClass = 'status-in-progress';
                    statusText = '进行中';
                    break;
                case '已完成':
                    statusClass = 'status-completed';
                    statusText = '已完成';
                    break;
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
                    statusText = task.task_status || task.status;
            }
            
            // 创建一个安全的onclick事件处理器
            const taskJson = encodeURIComponent(JSON.stringify(task));
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task.name}</td>
                <td>${task.knowledge_base_name || task.knowledge_base_id}(${task.knowledge_base_id})</td>
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
                        <button class="task-action-btn sync-btn" onclick="syncTask('${task.task_id || task.id}')">同步</button>
                        <button class="task-action-btn delete-btn" onclick="deleteTask('${task.task_id || task.id}')">删除</button>
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

// 同步任务（预留功能）
function syncTask(taskId) {
    alert('同步功能正在开发中...');
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



// 添加初始化函数，供页面调用
function initAnnotationTab(knoId) {
    currentKnoId = knoId;
    loadEnvironmentStatus();
    loadAnnotationProjects();
}