// 标签页切换功能
function switchTab(tabName) {
    // 隐藏所有标签内容
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // 移除所有标签按钮的active类
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });

    // 显示选中的标签内容
    document.getElementById(tabName).classList.add('active');

    // 为选中的标签按钮添加active类
    event.target.classList.add('active');

    // 根据标签加载相应内容
    if (tabName === 'files') {
        loadFileList();
    } else if (tabName === 'bindings') {
        loadBindingStatus();
    } else if (tabName === 'annotations') {
        // 初始化标注页签
        const knoId = document.getElementById('knowledge-id').textContent.trim();
        if (typeof initAnnotationTab !== 'undefined') {
            initAnnotationTab(knoId);
        }
    } else if (tabName === 'questions') {
        // 初始化问题集页签
        const knoId = document.getElementById('knowledge-id').textContent.trim();
        if (typeof initQuestionTab !== 'undefined') {
            initQuestionTab(knoId);
        }
    } else if (tabName === 'tasks') {
        // 初始化任务页签
        const knoId = document.getElementById('knowledge-id').textContent.trim();
        if (typeof initTaskTab !== 'undefined') {
            initTaskTab(knoId);
        }
    }
}

// 添加展开/折叠标注任务管理功能
function toggleTaskManagement() {
    const taskManagementContent = document.getElementById('taskManagementContent');
    const toggleButton = document.getElementById('taskManagementToggle');
    
    if (taskManagementContent.style.display === 'none' || taskManagementContent.style.display === '') {
        // 展开
        taskManagementContent.style.display = 'block';
        toggleButton.textContent = '折叠';
    } else {
        // 折叠
        taskManagementContent.style.display = 'none';
        toggleButton.textContent = '展开';
    }
}

// 加载文件列表
function loadFileList() {
    const fileListContainer = document.getElementById('file-list');
    const knoId = document.getElementById('knowledge-id').textContent.trim();
    const knoName = document.getElementById('knowledge-name').textContent.trim();

    fetch(`/api/local_knowledge_detail`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            kno_id: knoId,
            kno_name: knoName
        })
    })
    .then(response => response.json())
    .then(data => {
        fileListContainer.innerHTML = '';
        if (data && data.length > 0) {
            data.forEach(file => {
                const fileCard = document.createElement('div');
                fileCard.className = 'file-card';
                fileCard.innerHTML = `
                    <div class="file-info">
                        <div class="file-field">
                            <div class="field-label">文件名称</div>
                            <div class="field-value">${file.kno_name || file.knol_name || 'N/A'}</div>
                        </div>
                        <div class="file-field">
                            <div class="field-label">描述</div>
                            <div class="field-value">${file.kno_describe || file.knol_describe || '暂无描述'}</div>
                        </div>
                        <div class="file-field">
                            <div class="field-label">状态</div>
                            <div class="field-value">
                                <span class="file-status ${file.ls_status === 0 ? 'completed' : file.ls_status === 1 ? 'pending' : file.ls_status === 2 ? 'in-progress' : 'unknown'}">
                                    ${file.ls_status === 0 ? '已完成' : file.ls_status === 1 ? '未开始' : file.ls_status === 2 ? '进行中' : '未知'}
                                </span>
                            </div>
                        </div>
                        <div class="file-field">
                            <div class="field-label">路径</div>
                            <div class="field-value">${file.knol_path || file.kno_path || 'N/A'}</div>
                        </div>
                        <div class="file-field">
                            <div class="field-label">创建时间</div>
                            <div class="field-value">${file.created_at || 'N/A'}</div>
                        </div>
                        <div class="file-field">
                            <div class="field-label">操作</div>
                            <div class="field-value">
                                <div class="file-actions">
                                    <button class="action-btn delete-btn" onclick="deleteFile('${file.knol_id || file.kno_id}', '${file.kno_name || file.knol_name}')">删除</button>
                                    <button class="action-btn edit-btn" onclick="editFile('${file.knol_id || file.kno_id}', '${file.kno_name || file.knol_name}', '${file.kno_describe || file.knol_describe || ""}')">编辑</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                fileListContainer.appendChild(fileCard);
            });
        } else {
            const noDataDiv = document.createElement('div');
            noDataDiv.className = 'no-data';
            noDataDiv.innerHTML = '<div style="text-align: center; padding: 20px;">暂无文件</div>';
            fileListContainer.appendChild(noDataDiv);
        }
    })
    .catch(error => {
        console.error('加载文件列表时出错:', error);
        fileListContainer.innerHTML = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.innerHTML = '<div style="text-align: center; padding: 20px;">加载文件列表失败</div>';
        fileListContainer.appendChild(errorDiv);
    });
}

// 加载绑定状态
function loadBindingStatus() {
    const bindingListContainer = document.getElementById('binding-list');
    const knoId = document.getElementById('knowledge-id').textContent.trim();

    fetch(`/local_knowledge/bindings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            kno_id: knoId
        })
    })
    .then(response => response.json())
    .then(data => {
        bindingListContainer.innerHTML = '';

        if (Array.isArray(data) && data.length > 0) {
            // 多个绑定对象
            data.forEach(binding => {
                const bindingItem = createBindingItem(binding, knoId);
                bindingListContainer.appendChild(bindingItem);
            });
        } else {
            bindingListContainer.innerHTML = '<li class="no-data">暂无绑定</li>';
        }
    })
    .catch(error => {
        console.error('加载绑定状态时出错:', error);
        bindingListContainer.innerHTML = '<li class="error">加载绑定状态失败</li>';
    });
}

// 创建绑定项
function createBindingItem(data, knoId) {
    const bindingItem = document.createElement('li');
    bindingItem.className = 'binding-item';

    let statusText = '';
    let statusClass = '';
    switch (data.bind_status) {
        case 0:
            statusText = '未绑定';
            statusClass = 'bind-status-unbound';
            break;
        case 1:
            statusText = '绑定中';
            statusClass = 'bind-status-binding';
            break;
        case 2:
            statusText = '已绑定';
            statusClass = 'bind-status-bound';
            break;
        case 3:
            statusText = '解绑中';
            statusClass = 'bind-status-unbinding';
            break;
        case 4:
            statusText = '已解绑';
            statusClass = 'bind-status-unbounded';
            break;
        default:
            statusText = '未知';
            statusClass = 'bind-status-unknown';
    }

    bindingItem.innerHTML = `
        <div class="binding-info">
            <strong>知识库:</strong> ${data.knowledge_name || data.knowledge_id}<br>
            <strong>ID:</strong> ${data.knowledge_id}<br>
            <strong>状态:</strong> <span class="binding-status ${statusClass}">${statusText}</span>
        </div>
        <div class="binding-actions">
            ${data.bind_status === 2 ? `<button class="action-btn sync-btn" onclick="syncKnowledge('${knoId}', '${data.knowledge_id}')">同步知识库</button>` : ''}
            <button class="action-btn unbind-btn" onclick="unbindKnowledge('${knoId}', '${data.knowledge_id}')">解绑</button>
        </div>
    `;

    return bindingItem;
}

// 上传文件功能
function uploadFileForKnowledge(knoId) {
    // 使用已有的上传文件对话框
    showUploadDialog(knoId);
}

// 以下是现有的函数，需要在js文件中定义
function showUploadDialog(knoId) {
    // 这个函数应该在local_knowledge.js中定义
    if (typeof showUploadDialogFromJS !== 'undefined') {
        showUploadDialogFromJS(knoId);
    } else {
        alert('上传功能未定义，请检查JS文件');
    }
}

function deleteFile(knolId, knolName) {
    if (confirm(`确定要删除文件 "${knolName}" 吗？`)) {
        fetch(`/local_knowledge_doc/delete/${knolId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('文件删除成功');
                loadFileList(); // 重新加载文件列表
            } else {
                alert('文件删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('删除文件时出错:', error);
            alert('删除文件时发生错误');
        });
    }
}

function editFile(knolId, knolName, currentDescribe) {
    const newDescribe = prompt('请输入新的描述:', currentDescribe);
    if (newDescribe !== null) {
        const formData = new FormData();
        formData.append('knol_describe', newDescribe);

        fetch(`/local_knowledge_doc/edit/${knolId}`, {
            method: 'PUT',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('文件描述更新成功');
                loadFileList(); // 重新加载文件列表
            } else {
                alert('文件描述更新失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('更新文件描述时出错:', error);
            alert('更新文件描述时发生错误');
        });
    }
}

// 绑定相关函数
function showBindDialog() {
    // 这个函数应该在local_knowledge.js中定义
    if (typeof showBindDialogFromJS !== 'undefined') {
        showBindDialogFromJS();
    } else {
        alert('绑定功能未定义，请检查JS文件');
    }
}

function unbindKnowledge(localKnoId, knowledgeId) {
    if (confirm('确定要解绑此知识库吗？')) {
        fetch('/local_knowledge/bind', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                local_kno_id: localKnoId,
                kb_id: knowledgeId,
                action: 'unbind'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('解绑成功');
                loadBindingStatus(); // 重新加载绑定状态
            } else {
                alert('解绑失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('解绑时出错:', error);
            alert('解绑时发生错误');
        });
    }
}

function syncKnowledge(localKnoId, knowledgeId) {
    fetch('/local_knowledge_detail/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            local_kno_id: localKnoId,
            knowledge_id: knowledgeId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('同步成功');
        } else {
            alert('同步失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('同步时出错:', error);
        alert('同步时发生错误');
    });
}

// 页面加载完成后加载文件列表
document.addEventListener('DOMContentLoaded', function() {
    // 默认加载文件列表
    loadFileList();
});