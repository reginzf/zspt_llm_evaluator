// 用于详细页面的上传文件功能
function showUploadDialogFromJS(knoId) {
    // 保存当前知识库ID
    window.currentKnoId = knoId;
    // 显示上传对话框
    document.getElementById('uploadDialog').style.display = 'block';
}

// 上传文件功能 - 用于详细页面
function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

    if (files.length === 0) {
        alert('请选择要上传的文件');
        return;
    }

    const formData = new FormData();

    // 添加所有选中的文件
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    formData.append('kno_id', window.currentKnoId);

    fetch('/local_knowledge/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.status === 'partial_success') {
                alert(data.message);
                closeUploadDialog();
                // 重新加载文件列表
                if (typeof loadFileList !== 'undefined') {
                    loadFileList();
                } else {
                    location.reload();
                }
            } else {
                alert('上传失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('上传文件时出错:', error);
            alert('上传过程中发生错误: ' + error.message);
        });
}

// 关闭上传对话框
function closeUploadDialog() {
    document.getElementById('uploadDialog').style.display = 'none';
    // 清空文件选择框
    document.getElementById('fileInput').value = '';
}


function editKnowledge(event, knoId, knoName, currentDescribe) {
    event.stopPropagation(); // 防止事件冒泡
    
    // 创建一个包含所有字段的表单对话框
    const formHTML = `
        <div id="editKnowledgeForm" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 1px solid #ccc; z-index: 1000; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <h3>编辑知识库</h3>
            <div style="margin-bottom: 10px;">
                <label>描述:</label>
                <input type="text" id="editKnoDescribe" value="${currentDescribe}" style="width: 100%; padding: 5px; margin-top: 5px;" />
            </div>
            <div style="margin-bottom: 10px;">
                <label>知识域名:</label>
                <input type="text" id="editKnowledgeDomain" placeholder="请输入知识域名" style="width: 100%; padding: 5px; margin-top: 5px;" />
            </div>
            <div style="margin-bottom: 10px;">
                <label>知识域描述:</label>
                <input type="text" id="editDomainDescription" placeholder="请输入知识域描述" style="width: 100%; padding: 5px; margin-top: 5px;" />
            </div>
            <div style="margin-bottom: 10px;">
                <label>背景知识 (用逗号分隔):</label>
                <input type="text" id="editRequiredBackground" placeholder="如: 网络基础知识,TCP/IP协议栈" style="width: 100%; padding: 5px; margin-top: 5px;" />
            </div>
            <div style="margin-bottom: 10px;">
                <label>标注LLM能力 (用逗号分隔):</label>
                <input type="text" id="editRequiredSkills" placeholder="如: 网络协议分析能力,技术文档理解能力" style="width: 100%; padding: 5px; margin-top: 5px;" />
            </div>
            <div style="text-align: right; margin-top: 15px;">
                <button onclick="cancelEditKnowledge()" style="padding: 5px 15px; margin-right: 10px;">取消</button>
                <button onclick="submitEditKnowledge('${knoId}', '${knoName}')" style="padding: 5px 15px; background-color: #007bff; color: white;">确定</button>
            </div>
        </div>
        <div id="overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999;"></div>
    `;
    
    // 添加表单到页面
    document.body.insertAdjacentHTML('beforeend', formHTML);
}

function submitEditKnowledge(knoId, knoName) {
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
            kno_id: knoId,
            kno_name: knoName,
            kno_describe: knoDescribe,
            knowledge_domain: knowledgeDomain,
            domain_description: domainDescription,
            required_background: requiredBackground,
            required_skills: requiredSkills
        })
    })
        .then(response => response.json())
        .then(data => {
            // 移除表单
            document.getElementById('editKnowledgeForm').remove();
            document.getElementById('overlay').remove();
            
            if (data.success) {
                alert('知识库更新成功');
                location.reload();
            } else {
                alert('知识库更新失败: ' + data.message);
            }
        })
        .catch(error => {
            // 移除表单
            document.getElementById('editKnowledgeForm').remove();
            document.getElementById('overlay').remove();
            
            console.error('更新知识库时出错:', error);
            alert('更新过程中发生错误: ' + error.message);
        });
}

function cancelEditKnowledge() {
    // 移除表单
    document.getElementById('editKnowledgeForm').remove();
    document.getElementById('overlay').remove();
}

// 删除知识库功能
function deleteKnowledge(event, knoId) {
    event.stopPropagation(); // 防止事件冒泡
    if (confirm('确定要删除此知识库吗？')) {
        fetch(`/local_knowledge/delete/${knoId}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('知识库删除成功');
                    location.reload();
                } else {
                    alert('知识库删除失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('删除知识库时出错:', error);
                alert('删除过程中发生错误: ' + error.message);
            });
    }
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
        alert('知识库名称不能为空');
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
                alert('知识库创建成功');
                closeCreateKnowledgeDialog();
                location.reload();
            } else {
                alert('知识库创建失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('创建知识库时出错:', error);
            alert('创建过程中发生错误: ' + error.message);
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
                // 如果在详细页面，重新加载绑定状态
                if (typeof loadBindingStatus !== 'undefined') {
                    loadBindingStatus();
                } else {
                    location.reload();
                }
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
