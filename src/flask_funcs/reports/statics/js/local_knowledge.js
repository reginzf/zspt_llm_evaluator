// 用于详细页面的上传文件功能
function showUploadDialogFromJS(knoId) {
    // 保存当前知识库 ID
    window.currentKnoId = knoId;
    // 显示上传对话框
    if (typeof uploadDialog !== 'undefined' && uploadDialog) {
        uploadDialog.show();
    } else {
        document.getElementById('uploadDialog').style.display = 'block';
    }
}

// 上传文件功能 - 用于详细页面（仅使用MinIO存储）
function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

    if (files.length === 0) {
        DialogManager.showWarning('请选择要上传的文件');
        return;
    }

    const formData = new FormData();

    // 添加所有选中的文件
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    formData.append('kno_id', window.currentKnoId);
    // 强制使用MinIO存储
    formData.append('storage_type', 'minio');

    fetch('/local_knowledge/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.status === 'partial_success') {
                DialogManager.showSuccess(data.message, () => {
                    closeUploadDialog();
                    // 重新加载文件列表
                    if (typeof loadFileList !== 'undefined') {
                        loadFileList();
                    } else {
                        location.reload();
                    }
                });
            } else {
                DialogManager.showError('上传失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('上传文件时出错:', error);
            DialogManager.showError('上传过程中发生错误：' + error.message);
        });
}

// 关闭上传对话框
function closeUploadDialog() {
    document.getElementById('uploadDialog').style.display = 'none';
    // 清空文件选择框
    document.getElementById('fileInput').value = '';
}


function editKnowledge(event, knoId, knoName, currentDescribe, knowledgeDomain, domainDescription, requiredBackgroundStr, requiredSkillsStr) {
    event.stopPropagation(); // 防止事件冒泡
    
    // 保存当前知识库信息到全局变量
    window.currentKnoId = knoId;
    window.currentKnoName = knoName;
    
    // 解析JSON数据
    let requiredBackground = [];
    let requiredSkills = [];
    
    try {
        requiredBackground = JSON.parse(decodeURIComponent(requiredBackgroundStr));
    } catch(e) {
        console.warn('Failed to parse requiredBackground:', e);
        requiredBackground = [];
    }
    
    try {
        requiredSkills = JSON.parse(decodeURIComponent(requiredSkillsStr));
    } catch(e) {
        console.warn('Failed to parse requiredSkills:', e);
        requiredSkills = [];
    }
    
    // 设置表单初始值 - 使用实际值或空字符串
    document.getElementById('editKnoDescribe').value = currentDescribe || '';
    document.getElementById('editKnowledgeDomain').value = knowledgeDomain || '';
    document.getElementById('editDomainDescription').value = domainDescription || '';
    document.getElementById('editRequiredBackground').value = requiredBackground && requiredBackground.length > 0 ? requiredBackground.join(', ') : '';
    document.getElementById('editRequiredSkills').value = requiredSkills && requiredSkills.length > 0 ? requiredSkills.join(', ') : '';
    
    // 显示编辑对话框
    document.getElementById('editKnowledgeDialog').style.display = 'block';
}

function submitEditKnowledge() {
    // 获取表单值
    const knoDescribe = document.getElementById('editKnoDescribe').value;
    const knowledgeDomain = document.getElementById('editKnowledgeDomain').value;
    const domainDescription = document.getElementById('editDomainDescription').value;
    const requiredBackgroundInput = document.getElementById('editRequiredBackground').value;
    const requiredSkillsInput = document.getElementById('editRequiredSkills').value;
    
    // 将输入的字符串转换为数组
    const requiredBackground = requiredBackgroundInput ? requiredBackgroundInput.split(',').map(item => item.trim()) : [];
    const requiredSkills = requiredSkillsInput ? requiredSkillsInput.split(',').map(item => item.trim()) : [];
    
    // 发送更新请求
    fetch('/local_knowledge/edit', {
        method: 'POST',  // 改为POST方法
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            kno_id: window.currentKnoId,
            kno_name: window.currentKnoName,
            kno_describe: knoDescribe,
            knowledge_domain: knowledgeDomain,
            domain_description: domainDescription,
            required_background: requiredBackground,
            required_skills: requiredSkills
        })
    })
        .then(response => response.json())
        .then(data => {
            // 隐藏对话框
            document.getElementById('editKnowledgeDialog').style.display = 'none';
            
            if (data.success) {
                DialogManager.showSuccess('知识库更新成功', () => {
                    closeEditKnowledgeDialog();
                    location.reload();
                });
            } else {
                DialogManager.showError('知识库更新失败：' + data.message);
            }
        })
        .catch(error => {
            // 隐藏对话框
            document.getElementById('editKnowledgeDialog').style.display = 'none';
                    
            console.error('更新知识库时出错:', error);
            DialogManager.showError('更新过程中发生错误：' + error.message);
        });
}

function cancelEditKnowledge() {
    // 隐藏对话框
    document.getElementById('editKnowledgeDialog').style.display = 'none';
}

// 关闭编辑知识库对话框
function closeEditKnowledgeDialog() {
    document.getElementById('editKnowledgeDialog').style.display = 'none';
}

// 删除知识库功能
function deleteKnowledge(event, knoId) {
    event.stopPropagation(); // 防止事件冒泡
    
    DialogManager.confirm(
        '确定要删除此知识库吗？',
        async () => {
            try {
                const response = await fetch(`/local_knowledge/delete/${knoId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    DialogManager.showSuccess('知识库删除成功', () => {
                        location.reload();
                    });
                } else {
                    DialogManager.showError('知识库删除失败：' + data.message);
                }
            } catch (error) {
                console.error('删除知识库时出错:', error);
                DialogManager.showError('删除过程中发生错误：' + error.message);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 创建知识库功能
function createKnowledge() {
    // 显示创建知识库对话框
    document.getElementById('createKnowledgeDialog').style.display = 'block';
}

// 关闭创建知识库对话框
function closeCreateKnowledgeDialog() {
    document.getElementById('createKnowledgeDialog').style.display = 'none';
    // 清空输入框
    document.getElementById('knowledgeName').value = '';
    document.getElementById('knowledgeDescription').value = '';
}

// 提交创建知识库
function submitCreateKnowledge() {
    const name = document.getElementById('knowledgeName').value;
    const description = document.getElementById('knowledgeDescription').value;
    
    if (!name || name.trim() === '') {
        DialogManager.showWarning('知识库名称不能为空');
        return;
    }

    // 发送创建请求
    fetch('/local_knowledge/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            kno_name: name.trim(),
            kno_describe: description ? description.trim() : null
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                DialogManager.showSuccess('知识库创建成功', () => {
                    closeCreateKnowledgeDialog();
                    location.reload();
                });
            } else {
                DialogManager.showError('知识库创建失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('创建知识库时出错:', error);
            DialogManager.showError('创建过程中发生错误：' + error.message);
        });
}

// 显示绑定对话框 - 用于详细页面
function showBindDialogFromJS() {
    // 显示对话框
    document.getElementById('bindDialog').style.display = 'block';

    // 从页面元素获取当前知识库ID
    const knowledgeIdElement = document.getElementById('knowledge-id');
    if (knowledgeIdElement) {
        window.currentKnoId = knowledgeIdElement.textContent.trim();
    }

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
    const selectedKbId = kbSelect.value;

    if (!selectedEnvId || !selectedKbId) {
        DialogManager.showWarning('请先选择环境和知识库');
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
                DialogManager.showSuccess('绑定成功', () => {
                    closeBindDialog();
                    // 如果在详细页面，重新加载绑定状态
                    if (typeof loadBindingStatus !== 'undefined') {
                        loadBindingStatus();
                    } else {
                        location.reload();
                    }
                });
            } else {
                DialogManager.showError('绑定失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('绑定知识库时出错:', error);
            DialogManager.showError('绑定过程中发生错误：' + error.message);
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
document.addEventListener('DOMContentLoaded', function () {
    console.log('本地知识库页面已加载');
    initColumnResizing();
});

// 初始化表格列宽调整功能
function initColumnResizing() {
    // 为所有带可调整列宽的表格的表头添加列宽调整器
    const tables = document.querySelectorAll('.table-with-resizable-cols');
    
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

// 显示知识域详细信息
function showDomainDetails(event, knowledgeDomain, domainDescription, requiredBackground, requiredSkills) {
    event.stopPropagation(); // 防止事件冒泡
    
    // 确保数组类型的参数正确处理
    let backgroundArray = requiredBackground;
    let skillsArray = requiredSkills;
    
    // 如果是字符串，则尝试解析为数组
    if(typeof requiredBackground === 'string') {
        try {
            backgroundArray = JSON.parse(requiredBackground);
        } catch(e) {
            // 如果不是有效的JSON，将其作为单个项目处理
            backgroundArray = [requiredBackground];
        }
    }
    
    if(typeof requiredSkills === 'string') {
        try {
            skillsArray = JSON.parse(requiredSkills);
        } catch(e) {
            // 如果不是有效的JSON，将其作为单个项目处理
            skillsArray = [requiredSkills];
        }
    }
    
    // 确保是数组类型
    backgroundArray = Array.isArray(backgroundArray) ? backgroundArray : [];
    skillsArray = Array.isArray(skillsArray) ? skillsArray : [];
    
    // 使用字符串拼接构建HTML
    var detailsHTML = '<div id="domainDetailsDialog" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 1px solid #ccc; z-index: 1001; box-shadow: 0 4px 8px rgba(0,0,0,0.2); max-width: 600px; max-height: 80vh; overflow-y: auto;">' +
        '<div style="margin-bottom: 15px;">' +
            '<h3 style="color: #667eea; margin: 0 0 10px 0;">知识域详细信息</h3>' +
            '<div style="margin-bottom: 10px;"><strong>知识域名:</strong> ' + (knowledgeDomain || '暂无') + '</div>' +
            '<div style="margin-bottom: 10px;"><strong>知识域描述:</strong> ' + (domainDescription || '暂无') + '</div>' +
            '<div style="margin-bottom: 10px;"><strong>背景知识:</strong> ' + (backgroundArray.length > 0 ? backgroundArray.join(', ') : '暂无') + '</div>' +
            '<div style="margin-bottom: 15px;"><strong>标注LLM能力:</strong> ' + (skillsArray.length > 0 ? skillsArray.join(', ') : '暂无') + '</div>' +
        '</div>' +
        '<div style="text-align: right;">' +
            '<button onclick="closeDomainDetailsDialog()" style="padding: 5px 15px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">关闭</button>' +
        '</div>' +
    '</div>' +
    '<div id="detailsOverlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;" onclick="closeDomainDetailsDialog()"></div>';
    
    // 添加对话框到页面
    document.body.insertAdjacentHTML('beforeend', detailsHTML);
}

// 关闭知识域详细信息对话框
function closeDomainDetailsDialog() {
    const dialog = document.getElementById('domainDetailsDialog');
    const overlay = document.getElementById('detailsOverlay');
    
    if (dialog) dialog.remove();
    if (overlay) overlay.remove();
}

// 加载所有知识库的绑定数量
function loadBindingCounts() {
    const bindingCountElements = document.querySelectorAll('.binding-count');
    bindingCountElements.forEach(element => {
        const knoId = element.getAttribute('data-kno-id');
        fetch(`/local_knowledge/bindings/${knoId}`, {
            method: 'GET'
        })
            .then(response => response.json())
            .then(data => {
                let count = 0;
                if (data && data.count !== undefined) {
                    // 如果返回包含count的对象
                    count = data.count;
                } else if (data && !Array.isArray(data)) {
                    // 如果返回单个对象，计为1
                    count = 1;
                } else if (Array.isArray(data)) {
                    // 如果返回数组，计算长度
                    count = data.length;
                }
                element.textContent = count;
            })
            .catch(error => {
                console.error('加载绑定数量时出错:', error);
                element.textContent = '获取失败';
            });
    });
}
