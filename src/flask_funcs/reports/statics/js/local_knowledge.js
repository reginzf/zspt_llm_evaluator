function toggleKnowledgeDetails(element) {
    const details = element.nextElementSibling;
    const toggleIcon = element.querySelector('.toggle-icon');

    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
        // 更新图标为向下箭头
        toggleIcon.textContent = '▼';
        element.classList.add('active');

        // 获取知识库ID
        const knowledgeId = element.querySelector('.knowledge-id').textContent;

        // 加载文件列表
        loadKnowledgeFiles(element);

        // 加载绑定状态
        loadBindingStatus(knowledgeId);
    } else {
        details.style.display = 'none';
        // 更新图标为向右箭头
        toggleIcon.textContent = '▶';
        element.classList.remove('active');
    }
}

function loadKnowledgeFiles(headerElement) {
    // 获取知识库ID和名称
    const knowledgeId = headerElement.querySelector('.knowledge-id').textContent;
    const knowledgeName = headerElement.querySelector('.knowledge-name').getAttribute('title');
    const fileListContainer = headerElement.nextElementSibling.querySelector('.file-list');

    // 显示加载状态
    fileListContainer.innerHTML = '<li class="file-item-placeholder">正在加载文件列表...</li>';

    // 通过API获取知识库详细信息
    fetch(`/api/local_knowledge_detail/${knowledgeId}/${knowledgeName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            // 清空加载提示
            fileListContainer.innerHTML = '';

            if (data && data.length > 0) {
                // 渲染文件列表
                data.forEach(file => {
                    const fileItem = createFileItem(file);
                    fileListContainer.appendChild(fileItem);
                });
            } else {
                fileListContainer.innerHTML = '<li class="file-item-placeholder">暂无文件</li>';
            }
        })
        .catch(error => {
            console.error('加载文件列表时出错:', error);
            fileListContainer.innerHTML = '<li class="file-item-placeholder">加载文件列表失败</li>';
        });
}

// 创建文件项
function createFileItem(file) {
    const template = document.getElementById('file-item-template');
    const clone = template.content.cloneNode(true);
    
    const fileItem = clone.querySelector('.file-item');
    const fileName = clone.querySelector('.file-name');
    const fileDescription = clone.querySelector('.file-description');
    const fileStatus = clone.querySelector('.file-status');
    const deleteBtn = clone.querySelector('.delete-btn');
    const editBtn = clone.querySelector('.edit-btn');
    
    fileName.textContent = file.kno_name;
    fileDescription.textContent = file.kno_describe || '无描述';
    
    const statusClass = file.ls_status === 'sync_ok' ? 'sync-ok' : 'sync-wait';
    const statusText = file.ls_status === 'sync_ok' ? '已同步' : '待同步';
    fileStatus.textContent = statusText;
    fileStatus.className = `file-status ${statusClass}`;
    
    deleteBtn.textContent = '删除';
    deleteBtn.onclick = () => deleteFile(file.knol_id, file.kno_name);
    
    editBtn.textContent = '编辑';
    editBtn.onclick = () => editFile(file.knol_id, file.kno_name);
    
    return fileItem;
}

function uploadFile(knowledgeId) {
    // 上传文件功能
    // 显示文件选择对话框，支持多选
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;  // 支持多文件选择
    input.onchange = function (e) {
        const files = e.target.files;
        if (files.length > 0) {
            // 创建 FormData 对象来发送文件
            const formData = new FormData();

            // 添加所有选中的文件
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }

            formData.append('kno_id', knowledgeId);

            // 显示上传进度提示
            alert(`准备上传 ${files.length} 个文件到知识库: ${knowledgeId}`);

            // 发送文件到服务器
            fetch('/local_knowledge/upload', {
                method: 'POST',
                body: formData  // 注意：不设置 Content-Type，让浏览器自动设置
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('网络响应不正常');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success' || data.status === 'partial_success') {
                        alert(data.message);
                        // 重新加载页面或刷新知识库详情
                        location.reload(); // 或者可以只刷新对应的知识库详情
                    } else {
                        alert('上传失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('上传文件时出错:', error);
                    alert('上传过程中发生错误: ' + error.message);
                });
        }
    };
    input.click();
}

function deleteFile(knolId, knoName) {
    if (confirm(`确定要删除文件 "${knoName}" 吗？`)) {
        // 执行删除逻辑
        console.log('删除文件:', knolId);

        // 调用API删除文件
        fetch(`/local_knowledge/delete/${knolId}`, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    // 重新加载页面以更新文件列表
                    location.reload();
                } else {
                    alert('删除失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('删除文件时出错:', error);
                alert('删除过程中发生错误: ' + error.message);
            });
    }
}


function editFile(knolId, knolName) {
    const currentDescription = prompt(`请输入文件 "${knolName}" 的新描述:`, '');

    if (currentDescription !== null) {  // 用户没有取消
        // 创建 FormData 对象来发送描述信息
        const formData = new FormData();
        formData.append('knol_describe', currentDescription);

        // 发送请求到服务器
        fetch(`/local_knowledge/edit/${knolId}`, {
            method: 'PUT',
            body: formData
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络响应不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    alert(data.message);
                    // 重新加载页面以更新文件列表
                    location.reload();
                } else {
                    alert('编辑失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('编辑文件时出错:', error);
                alert('编辑过程中发生错误: ' + error.message);
            });
    }
}

// 显示绑定对话框
function showBindDialog(knoId, knoName) {
    // 保存当前知识库ID和名称
    window.currentKnoId = knoId;
    window.currentKnoName = knoName;

    // 显示对话框
    document.getElementById('bindDialog').style.display = 'block';

    // 加载环境列表
    loadEnvironments();
}

// 加载环境列表
function loadEnvironments() {
    const envSelect = document.getElementById('environmentSelect');
    envSelect.innerHTML = '<option value="">请选择环境</option>';

    // 通过API获取环境列表
    fetch('/environment/list/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                data.data.forEach(env => {
                    const option = document.createElement('option');
                    option.value = env.zlpt_base_id;
                    option.textContent = env.zlpt_name + ' / ' + env.zlpt_base_id;
                    envSelect.appendChild(option);
                });
            } else {
                console.error('获取环境列表失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载环境列表时出错:', error);
        });
}

// 根据选择的环境加载知识库列表
function loadKnowledgeBases() {
    const envSelect = document.getElementById('environmentSelect');
    const kbSelect = document.getElementById('knowledgeBaseSelect');
    const selectedEnvId = envSelect.value;

    // 清空知识库选择框
    kbSelect.innerHTML = '<option value="">请先选择环境</option>';

    if (!selectedEnvId) {
        return;
    }

    // 通过API获取指定环境下的知识库列表
    fetch('/environment_detail_list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            zlpt_id: selectedEnvId
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                kbSelect.innerHTML = '<option value="">请选择知识库</option>';
                data.data.forEach(kb => {
                    const option = document.createElement('option');
                    option.value = kb.knowledge_id;
                    option.textContent = kb.knowledge_name + ' / ' + kb.knowledge_id;
                    kbSelect.appendChild(option);
                });
            } else {
                console.error('获取知识库列表失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载知识库列表时出错:', error);
        });
}

// 执行绑定操作
function bindKnowledge() {
    const envSelect = document.getElementById('environmentSelect');
    const kbSelect = document.getElementById('knowledgeBaseSelect');

    const selectedEnvId = envSelect.value;
    const selectedEnvName = envSelect.options[envSelect.selectedIndex].text;
    const selectedKbId = kbSelect.value;
    const selectedKbName = kbSelect.options[kbSelect.selectedIndex].text;

    if (!selectedEnvId || !selectedKbId) {
        alert('请先选择环境和知识库');
        return;
    }

    // 调用绑定API
    fetch('/local_knowledge/bind', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            local_kno_id: window.currentKnoId,
            kb_id: selectedKbId,
            action: 'bind'
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('绑定成功');
                closeBindDialog();
                location.reload();
            } else {
                alert('绑定失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('绑定知识库时出错:', error);
            alert('绑定过程中发生错误: ' + error.message);
        });
}

// 关闭绑定对话框
function closeBindDialog() {
    document.getElementById('bindDialog').style.display = 'none';
    // 清空选择框
    document.getElementById('environmentSelect').value = '';
    document.getElementById('knowledgeBaseSelect').innerHTML = '<option value="">请先选择环境</option>';
}

// 加载绑定状态
function loadBindingStatus(knoId) {
    const bindingListContainer = document.getElementById('binding-list-' + knoId);

    if (!bindingListContainer) {
        console.error('找不到绑定状态容器:', 'binding-list-' + knoId);
        return;
    }

    // 通过API获取绑定状态
    fetch(`/local_knowledge/bindings/${knoId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            // 清空加载提示
            bindingListContainer.innerHTML = '';
            
            if (data && typeof data === 'object' && !Array.isArray(data)) {
                // 后端返回单个对象
                const bindingItem = createBindingItem(data, knoId);
                bindingListContainer.appendChild(bindingItem);
            } else {
                bindingListContainer.innerHTML = '<li class="binding-item-placeholder">暂无绑定</li>';
            }
        })
        .catch(error => {
            console.error('加载绑定状态时出错:', error);
            bindingListContainer.innerHTML = '<li class="binding-item-placeholder">加载绑定状态失败</li>';
        });
}

// 创建绑定项
function createBindingItem(data, knoId) {
    const template = document.getElementById('binding-item-template');
    const clone = template.content.cloneNode(true);
    
    const bindingItem = clone.querySelector('.binding-item');
    const bindingKbName = clone.querySelector('.binding-kb-name');
    const bindingStatus = clone.querySelector('.binding-status');
    const syncBtn = clone.querySelector('.sync-btn');
    const unbindBtn = clone.querySelector('.unbind-btn');
    
    bindingKbName.textContent = `知识库: ${data.knowledge_name || data.knowledge_id}`;
    
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
    
    bindingStatus.textContent = statusText;
    bindingStatus.className = `binding-status ${statusClass}`;
    
    // 根据绑定状态显示或隐藏同步按钮
    if (data.bind_status === 2) { // 已绑定状态
        syncBtn.style.display = 'inline-block';
        syncBtn.onclick = () => syncKnowledge(knoId, data.knowledge_id);
    } else {
        syncBtn.style.display = 'none';
    }
    
    unbindBtn.textContent = '解绑';
    unbindBtn.onclick = () => unbindKnowledge(knoId, data.knowledge_id);
    
    return bindingItem;
}

// 同步知识库
function syncKnowledge(knoId, knowledgeId) {
    if (confirm(`确定要同步知识库 ${knowledgeId} 吗？`)) {
        fetch('/local_knowledge/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                local_kno_id: knoId,
                knowledge_id: knowledgeId
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('知识库同步成功');
                } else {
                    alert('知识库同步失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('同步知识库时出错:', error);
                alert('同步过程中发生错误: ' + error.message);
            });
    }
}

// 解绑知识库
function unbindKnowledge(knoId, knowledgeId) {
    if (confirm(`确定要解绑知识库 ${knowledgeId} 吗？`)) {
        // 调用解绑API
        fetch('/local_knowledge/bind', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                local_kno_id: knoId,
                kb_id: knowledgeId,
                action: 'unbind'
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('解绑成功');
                    location.reload();
                } else {
                    alert('解绑失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('解绑知识库时出错:', error);
                alert('解绑过程中发生错误: ' + error.message);
            });
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', function () {
    console.log('本地知识库页面已加载');
});