function toggleKnowledgeDetails(element) {
    const details = element.nextElementSibling;
    const toggleIcon = element.querySelector('.toggle-icon');
    
    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
        // 更新图标为向下箭头
        toggleIcon.textContent = '▼';
        element.classList.add('active');
        
        // 加载文件列表
        loadKnowledgeFiles(element);
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
                    const fileItem = document.createElement('li');
                    fileItem.className = 'file-item';
                    
                    const statusClass = file.ls_status === 'sync_ok' ? 'sync-ok' : 'sync-wait';
                    const statusText = file.ls_status === 'sync_ok' ? '已同步' : '待同步';
                    
                    fileItem.innerHTML = `
                        <div class="file-info">
                            <span class="file-name">${file.kno_name}</span>
                            <span class="file-description">${file.kno_describe || '无描述'}</span>
                            <span class="file-status ${statusClass}">${statusText}</span>
                        </div>
                        <div class="file-actions">
                            <button class="action-btn delete-btn" onclick="deleteFile('${file.knol_id}','${file.kno_name}')">删除</button>
                            <button class="action-btn upload-online-btn" onclick="uploadToOnlineKnowledge('${file.knol_id}')">上传到线上知识库</button>
                            <button class="action-btn edit-btn" onclick="editFile('${file.knol_id}','${file.kno_name}')">编辑</button>
                        </div>
                    `;
                    
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

function uploadFile(knowledgeId) {
    // 上传文件功能
    // 显示文件选择对话框，支持多选
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;  // 支持多文件选择
    input.onchange = function(e) {
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

function uploadToOnlineKnowledge(fileName) {
    if (confirm(`确定要将文件 "${fileName}" 上传到线上知识库吗？`)) {
        // 执行上传到线上知识库的逻辑
        console.log('上传文件到线上知识库:', fileName);
        // 这里应该调用API上传文件到线上知识库
    }
}

function editFile(knolId, knolName) {
    // 编辑文件功能
    // 获取当前描述
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
                    option.textContent = env.zlpt_name;
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
            zlpt_base_id: selectedEnvId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data) {
            kbSelect.innerHTML = '<option value="">请选择知识库</option>';
            data.data.forEach(kb => {
                const option = document.createElement('option');
                option.value = kb.knowledge_id;
                option.textContent = kb.knowledge_name;
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
            local_kno_name: window.currentKnoName,
            env_id: selectedEnvId,
            env_name: selectedEnvName,
            kb_id: selectedKbId,
            kb_name: selectedKbName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('绑定成功');
            closeBindDialog();
            // 可以选择刷新页面以显示更新后的状态
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

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    console.log('本地知识库页面已加载');
});