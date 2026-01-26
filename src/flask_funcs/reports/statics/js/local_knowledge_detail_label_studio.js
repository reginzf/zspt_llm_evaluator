// 本地知识库详情页的标注功能相关的JavaScript代码
// 与 local_knowledge_detail_label_studio.py 路由文件对应

let currentKnoId = null;
let currentEnvironment = null;

// 初始化表格列宽调整功能
function initTableColumnResizing() {
    // 为所有任务表格的表头添加列宽调整器
    const tables = document.querySelectorAll('.task-table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            // 检查是否已经添加了调整器
            if (!header.querySelector('.column-resizer')) {
                const resizer = document.createElement('div');
                resizer.className = 'column-resizer';
                
                // 为最后一个列不添加调整器
                if (index < headers.length - 1) {
                    header.appendChild(resizer);
                    
                    let startX, startWidth;
                    
                    resizer.addEventListener('mousedown', function(e) {
                        startX = e.pageX;
                        startWidth = header.offsetWidth;
                        
                        document.documentElement.classList.add('resizing');
                        
                        e.preventDefault();
                        
                        const mouseMoveHandler = function(e) {
                            const diff = e.pageX - startX;
                            const newWidth = startWidth + diff;
                            
                            if (newWidth > 50) { // 最小宽度50px
                                header.style.width = newWidth + 'px';
                                header.style.minWidth = newWidth + 'px';
                                header.style.maxWidth = newWidth + 'px';
                            }
                        };
                        
                        const mouseUpHandler = function() {
                            document.documentElement.classList.remove('resizing');
                            document.removeEventListener('mousemove', mouseMoveHandler);
                            document.removeEventListener('mouseup', mouseUpHandler);
                        };
                        
                        document.addEventListener('mousemove', mouseMoveHandler);
                        document.addEventListener('mouseup', mouseUpHandler);
                    });
                }
            }
        });
    });
}

// 通用的任务状态处理函数
function getTaskStatusInfo(task) {
    let statusClass = '';
    let statusText = '';
    switch(task.task_status || task.status) {
        case '未开始':
        case 'not_started':
            statusClass = 'status-not-started';
            statusText = '未开始';
            break;
        case '标注中':
        case 'in_progress':
            statusClass = 'status-in-progress';
            statusText = '标注中';
            break;
        case '已完成':
        case 'completed':
            statusClass = 'status-completed';
            statusText = '已完成';
            break;
        default:
            statusClass = 'status-not-started';
            statusText = task.task_status || task.status || '未知';
    }
    return { statusClass, statusText };
}

// 标注标签页专用的创建任务行函数
function createAnnotationTaskRow(task, envId = null) {
    console.log('Creating annotation task row with data:', task); // 添加调试日志
    // 确保数据存在
    const annotatedChunks = task.annotated_chunks !== undefined ? task.annotated_chunks : 0;
    const totalChunks = task.total_chunks !== undefined ? task.total_chunks : 0;
    const progressText = `${annotatedChunks}/${totalChunks}`;
    const progressPercent = totalChunks ? (annotatedChunks / totalChunks * 100) : 0;
    
    const { statusClass, statusText } = getTaskStatusInfo(task);
    
    // 创建一个安全的onclick事件处理器
    const taskJson = encodeURIComponent(JSON.stringify(task));
    const row = document.createElement('tr');
    
    // 根据是否有envId决定使用哪个编辑点击处理器
    const editClickHandler = envId ? 
        `handleEditTaskClickForEnv(decodeURIComponent('${taskJson}'), '${envId}')` : 
        `handleEditTaskClick(decodeURIComponent('${taskJson}'))`;
    
    // 根据是否有envId决定删除按钮的参数
    const deleteBtnParams = envId ? `'${task.task_id}', '${envId}'` : `'${task.task_id}'`;
    
    // 确保所有字段都有默认值，防止显示N/A或未设置
    const taskName = task.task_name || '未知任务';
    const knowledgeBaseName = task.knowledge_base_name || '未知知识库';
    const knowledgeBaseId = task.knowledge_base_id || 'N/A';
    const questionSetName = task.question_set_name || '未知问题集';
    const questionSetId = task.question_set_id || 'N/A';
    const taskId = task.task_id  || 'N/A';
    const annotationType = task.annotation_type || '未设置';
    
    row.innerHTML = `
        <td><div>${taskName}</div><div style="font-size: 0.8em; color: #666;">(ID: ${taskId})</div></td>
        <td><div>${knowledgeBaseName}</div><div style="font-size: 0.8em; color: #666;">(${knowledgeBaseId})</div></td>
        <td><div>${questionSetName}</div><div style="font-size: 0.8em; color: #666;">(${questionSetId})</div></td>
        <td>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressPercent}%"></div>
                </div>
                <span class="progress-text">${progressText}</span>
            </div>
            <div style="font-size: 0.8em; color: #666; margin-top: 4px;">${annotationType}</div>
        </td>
        <td><span class="status-label ${statusClass}">${statusText}</span></td>
        <td>
            <div class="task-actions">
                <button class="task-action-btn annotate-btn" onclick="showAnnotationDialog('${task.task_id}')">标注</button>
                <button class="task-action-btn edit-btn" onclick="${editClickHandler}">编辑</button>
                <button class="task-action-btn sync-btn" onclick="syncTask('${task.task_id}')">同步</button>
                <button class="task-action-btn delete-btn" onclick="deleteTask(${deleteBtnParams})">删除</button>
            </div>
        </td>
    `;
    
    return row;
}

// 通用的创建任务行函数（保持原名用于兼容性，但内部调用标注专用函数）
function createTaskRow(task, envId = null) {
    return createAnnotationTaskRow(task, envId);
}

// 显示标注方式选择对话框
function showAnnotationDialog(taskId) {
    // 存储当前任务ID
    document.getElementById('currentTaskId').value = taskId;

    // 显示模态框
    document.getElementById('annotationModal').style.display = 'block';
}

// 隐藏标注方式选择对话框
function hideAnnotationModal() {
    document.getElementById('annotationModal').style.display = 'none';
}

// 确认标注类型
function confirmAnnotationType() {
    const selectedType = document.getElementById('annotationTypeSelect').value;
    const taskId = document.getElementById('currentTaskId').value;

    // 使用Label Studio的更新接口更新标注类型
    fetch('/local_knowledge_detail/label_studio/update_annotation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_id: taskId,
            annotation_type: selectedType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('标注方式更新成功');
            hideAnnotationModal();
            // 重新加载任务列表 - 需要重新加载相关的任务列表
            if(currentEnvironment) {
                // 如果当前有展开的环境，重新加载该环境的任务列表
                const envId = currentEnvironment.label_studio_id;
                const taskRow = document.getElementById(`taskManagementRow-${envId}`);
                if (taskRow && taskRow.style.display !== 'none') {
                    loadTasksForEnvironment(envId);
                }
            }
            // 同时重新加载主任务列表
            loadAnnotationProjects();
        } else {
            alert('更新失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('更新标注方式时出错:', error);
        alert('更新标注方式时发生错误');
    });
}

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
            // 只显示绑定的环境
            if (data.data.bound_environments && Array.isArray(data.data.bound_environments) && data.data.bound_environments.length > 0) {
                // 创建一个新的数据结构，只包含绑定的环境
                const boundData = {
                    environments: data.data.bound_environments.map(boundEnv => {
                        // 找到对应环境的完整信息
                        const fullEnv = data.data.environments.find(env => env.label_studio_id === boundEnv.label_studio_id);
                        return fullEnv || boundEnv;
                    }),
                    bound_environments: data.data.bound_environments
                };
                updateEnvironmentDisplay(boundData);
            } else {
                // 如果没有绑定的环境，只传递空的environments数组
                updateEnvironmentDisplay({
                    environments: [],
                    bound_environments: null
                });
            }
            // 在更新完环境显示后初始化列宽调整功能
            setTimeout(initTableColumnResizing, 100);
        } else {
            console.error('获取环境状态失败:', data.message);
            // 即使失败也更新UI显示错误信息
            const environmentTableBody = document.getElementById('environmentTableBody');
            environmentTableBody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; color: red;">获取环境信息失败: ${data.message}</td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('请求环境状态时出错:', error);
        // 错误时也更新UI显示错误信息
        const environmentTableBody = document.getElementById('environmentTableBody');
        environmentTableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: red;">网络请求错误: ${error.message}</td>
            </tr>
        `;
    });
}

// 更新环境显示
function updateEnvironmentDisplay(data) {
    const environmentTableBody = document.getElementById('environmentTableBody');
    
    if (data && data.environments && data.environments.length > 0) {
        // 显示所有环境
        let rows = '';
        
        data.environments.forEach(env => {
            // 检查当前环境是否被绑定
            const isBound = data.bound_environments && 
                           Array.isArray(data.bound_environments) && 
                           data.bound_environments.some(bound => bound.label_studio_id === env.label_studio_id && bound.bind_status === 2);
            
            // 获取该环境下的任务数量
            const taskCount = env.task_count || 0;  // 假设后端会返回每个环境的任务数量
            
            // 设置当前环境
            if (isBound) {
                currentEnvironment = env;
            }
            
            // 环境行
            rows += `
                <tr class="environment-row" data-env-id="${env.label_studio_id}">
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
            
            // 为每个环境添加一个隐藏的任务管理区域行
            rows += `
                <tr id="taskManagementRow-${env.label_studio_id}" class="task-management-row" style="display: none;">
                    <td colspan="4">
                        <table class="task-table" style="margin-top: 15px;">
                            <thead>
                                <tr>
                                    <th>任务名称</th>
                                    <th>知识库</th>
                                    <th>问题集</th>
                                    <th>标注进度</th>
                                    <th>状态</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="taskTableBody-${env.label_studio_id}">
                                <tr>
                                    <td colspan="6" style="text-align: center;">加载中...</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            `;
        });
        
        environmentTableBody.innerHTML = rows;
    } else {
        // 未找到任何环境
        currentEnvironment = null;
        environmentTableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center;">暂无Label-Studio环境，请先添加环境</td>
            </tr>
        `;
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
    const taskRow = document.getElementById(`taskManagementRow-${envId}`);
    const expandButton = document.querySelector(`.environment-row[data-env-id="${envId}"] .expand-btn`);
    
    if (!taskRow || !expandButton) {
        console.error('找不到对应的行或按钮:', envId);
        return;
    }
    
    // 检查元素是否当前是隐藏的（通过检查offsetParent是否存在）
    // offsetParent为null表示元素不可见
    if (!taskRow.offsetParent) {
        // 展开：显示对应环境的任务管理区域
        taskRow.style.display = '';
        expandButton.textContent = '折叠';
        
        // 只有在展开时才加载任务数据
        loadTasksForEnvironment(envId);
    } else {
        // 折叠：隐藏对应环境的任务管理区域，不重新加载数据
        taskRow.style.display = 'none';
        expandButton.textContent = '展开';
    }
}

// 加载特定环境的任务列表
function loadTasksForEnvironment(envId) {
    console.log('Loading tasks for environment:', envId, 'and knowledge base:', currentKnoId);
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
    .then(response => {
        console.log('Raw response:', response);
        return response.json();
    })
    .then(data => {
        console.log('Parsed response data:', data);
        if (data.success) {
            renderTaskTableForEnvironment(envId, data.data);
        } else {
            console.error('获取环境任务列表失败:', data.message);
            const tableBody = document.getElementById(`taskTableBody-${envId}`);
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center;">获取任务列表失败: ${data.message}</td></tr>`;
            }
        }
    })
    .catch(error => {
        console.error('请求环境任务列表时出错:', error);
        const tableBody = document.getElementById(`taskTableBody-${envId}`);
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center;">网络请求错误: ${error.message}</td></tr>`;
        }
    });
}

// 为特定环境渲染任务表格
function renderTaskTableForEnvironment(envId, tasks) {
    console.log('Rendering tasks for environment:', envId, 'tasks:', tasks);
    const tableBody = document.getElementById(`taskTableBody-${envId}`);
    if (!tableBody) {
        console.error('找不到任务表格:', envId);
        return;
    }
    
    tableBody.innerHTML = '';
    
    if (tasks && tasks.length > 0) {
        console.log(`Rendering ${tasks.length} tasks`);
        tasks.forEach(task => {

            const row = createAnnotationTaskRow(task, envId); // 使用专用的标注任务创建函数
            if (row) {
                tableBody.appendChild(row);
            }
        });
         // 初始化列宽调整功能
        setTimeout(() => initTableColumnResizing(), 0);
    } else {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" style="text-align: center;">暂无标注任务</td>`;
        tableBody.appendChild(row);
        // 初始化列宽调整功能
        setTimeout(() => initTableColumnResizing(), 0);
    }
}

// 显示创建任务模态框（带环境ID）
function showCreateTaskModalWithEnv(envId) {
    // 预先设置环境ID
    document.getElementById('taskEnvironment').value = envId;
    
    // 加载知识库列表
    loadBoundKnowledgeBases(envId);
    
    // 重置选择框
    document.getElementById('taskQuestionSet').innerHTML = '<option value="">请选择知识库</option>';
    
    document.getElementById('taskModalTitle').textContent = '创建标注任务';
    document.getElementById('taskIdInput').style.display = 'none';
    document.getElementById('taskId').value = '';
    document.getElementById('taskName').value = '';
    
    // 隐藏任务状态组，仅在编辑时显示
    document.getElementById('taskStatusGroup').style.display = 'none';
    
    // 确保选择框处于启用状态
    const knowledgeBaseSelect = document.getElementById('taskKnowledgeBaseSelect');
    const questionSetSelect = document.getElementById('taskQuestionSet');
    knowledgeBaseSelect.disabled = false;
    questionSetSelect.disabled = false;
    
    document.getElementById('taskModal').style.display = 'block';
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
    // 根据规范，使用当前本地知识库ID，而不是绑定知识库的ID
    const knowledgeBaseId = currentKnoId;
    
    if (!knowledgeBaseId) {
        document.getElementById('taskQuestionSet').innerHTML = '<option value="">请先选择知识库</option>';
        return;
    }
    
    fetch('/local_knowledge_detail/label_studio/questionset/available', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            knowledge_id: knowledgeBaseId
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
    
    // 隐藏任务状态组，仅在编辑时显示
    document.getElementById('taskStatusGroup').style.display = 'none';
    
    // 确保选择框处于启用状态
    const knowledgeBaseSelect = document.getElementById('taskKnowledgeBaseSelect');
    const questionSetSelect = document.getElementById('taskQuestionSet');
    knowledgeBaseSelect.disabled = false;
    questionSetSelect.disabled = false;
    
    document.getElementById('taskModal').style.display = 'block';
}

// 显示编辑任务模态框
function showEditTaskModal(task) {
    document.getElementById('taskModalTitle').textContent = '编辑标注任务';
    document.getElementById('taskIdInput').style.display = 'block';
    document.getElementById('taskId').value = task.task_id;
    document.getElementById('taskName').value = task.name || task.task_name;  // 兼容新的数据结构
    // 注释掉不存在的元素，使用taskKnowledgeBaseSelect代替
    // document.getElementById('taskKnowledgeBase').value = task.knowledge_base_id;
    document.getElementById('taskEnvironment').value = task.environment_id || task.label_studio_env_id || task.label_studio_id || '';  // 兼容多种环境ID字段
    
    // 将知识库和问题集设置为只读或禁用，以防止在编辑模式下修改这些关联项
    const knowledgeBaseSelect = document.getElementById('taskKnowledgeBaseSelect');
    const questionSetSelect = document.getElementById('taskQuestionSet');
    
    // 显示当前关联的知识库和问题集信息，但不允许编辑
    if(task.knowledge_base_name) {
        knowledgeBaseSelect.innerHTML = `<option value="${task.knowledge_base_id || ''}">${task.knowledge_base_name}(${task.knowledge_base_id || ''})</option>`;
        knowledgeBaseSelect.disabled = true; // 禁用选择
    } else if(task.knowledge_base_id) {
        knowledgeBaseSelect.innerHTML = `<option value="${task.knowledge_base_id}">${task.knowledge_base_id}</option>`;
        knowledgeBaseSelect.disabled = true; // 禁用选择
    }
    
    if(task.question_set_name) {
        questionSetSelect.innerHTML = `<option value="${task.question_set_id || ''}">${task.question_set_name}(${task.question_set_id || ''})</option>`;
        questionSetSelect.disabled = true; // 禁用选择
    } else if(task.question_set_id) {
        questionSetSelect.innerHTML = `<option value="${task.question_set_id}">${task.question_set_id}</option>`;
        questionSetSelect.disabled = true; // 禁用选择
    }
    
    // 显示任务状态组，并设置当前状态
    const taskStatusGroup = document.getElementById('taskStatusGroup');
    taskStatusGroup.style.display = 'block';
    const taskStatusSelect = document.getElementById('taskStatus');
    // 设置选中的状态值，优先使用task_status，如果没有则尝试status
    const currentStatus = task.task_status || task.status || '未开始';
    taskStatusSelect.value = currentStatus;
    
    document.getElementById('taskModal').style.display = 'block';
}

// 隐藏任务模态框
function hideTaskModal() {
    // 重置选择框状态，确保下次打开时是启用的
    const knowledgeBaseSelect = document.getElementById('taskKnowledgeBaseSelect');
    const questionSetSelect = document.getElementById('taskQuestionSet');
    knowledgeBaseSelect.disabled = false;
    questionSetSelect.disabled = false;
    
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
        // 只在编辑模式下添加任务状态
        const taskStatus = document.getElementById('taskStatus').value;
        requestData.task_status = taskStatus; // 添加任务状态
    } else {
        // 创建模式：需要所有参数
        requestData.knowledge_base_id = knowledgeBaseId;  // 使用本地知识库ID
        requestData.local_knowledge_id = currentKnoId; // 同时传递local_knowledge_id
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
function deleteTask(taskId, envId) {
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
                hideTaskModal();
                // 如果任务管理区域是展开的，则重新加载该环境的任务列表
                if (document.getElementById(`taskManagementRow-${envId}`).style.display !== 'none') {
                    loadTasksForEnvironment(envId);
                }
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
    const tableBody = document.getElementById('annotationTaskTableBody');
    if (tableBody) {
        tableBody.innerHTML = '';
        
        if (tasks && tasks.length > 0) {
            tasks.forEach(task => {
                const row = createAnnotationTaskRow(task); // 使用专用的标注任务创建函数
                tableBody.appendChild(row);
            });
            // 初始化列宽调整功能
            setTimeout(() => initTableColumnResizing(), 0);
        } else {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="6" style="text-align: center;">暂无标注任务</td>`;
            tableBody.appendChild(row);
            // 初始化列宽调整功能
            setTimeout(() => initTableColumnResizing(), 0);
        }
    }
}

// 同步任务（实现同步功能）
function syncTask(taskId, envId) {
    if (!taskId) {
        alert('任务ID不能为空');
        return;
    }

    fetch('/local_knowledge_detail/label_studio/sync_project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_id: taskId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('任务同步成功');
            // 成功后刷新任务列表
            if (envId && document.getElementById(`taskManagementRow-${envId}`).style.display !== 'none') {
                loadTasksForEnvironment(envId);
            } else {
                loadAnnotationProjects();
            }
        } else {
            alert('任务同步失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('同步任务时出错:', error);
        alert('同步任务时发生错误');
    });
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

// 处理编辑任务点击事件（针对特定环境）
function handleEditTaskClickForEnv(taskJsonString) {
    try {
        const task = JSON.parse(decodeURIComponent(taskJsonString));
        showEditTaskModal(task);
    } catch (error) {
        console.error('解析任务数据时出错:', error);
        alert('编辑任务时发生错误');
    }
}

// 显示创建指标任务对话框
function showCreateMetricTaskDialog() {
    // 先加载已完成的标注任务列表
    loadCompletedAnnotationTasks();
    
    // 显示模态框
    document.getElementById('createMetricTaskModal').style.display = 'block';
}

// 隐藏创建指标任务对话框
function hideCreateMetricTaskModal() {
    document.getElementById('createMetricTaskModal').style.display = 'none';
}

// 添加初始化函数，供页面调用
function initAnnotationTab(knoId) {
    currentKnoId = knoId;
    loadEnvironmentStatus();
    loadAnnotationProjects();
}