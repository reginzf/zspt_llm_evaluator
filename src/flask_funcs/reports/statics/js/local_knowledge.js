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
                            <button class="action-btn delete-btn" onclick="deleteFile('${file.kno_name}')">删除</button>
                            <button class="action-btn upload-online-btn" onclick="uploadToOnlineKnowledge('${file.kno_name}')">上传到线上知识库</button>
                            <button class="action-btn edit-btn" onclick="editFile('${file.kno_name}')">编辑</button>
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
    alert(`准备上传文件到知识库: ${knowledgeId}`);
    
    // 这里应该实现实际的上传逻辑
    // 例如显示文件选择对话框并上传到服务器
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // 执行上传逻辑
            console.log('准备上传文件:', file.name, '到知识库:', knowledgeId);
            // 实际上传代码...
        }
    };
    input.click();
}

function deleteFile(fileName) {
    if (confirm(`确定要删除文件 "${fileName}" 吗？`)) {
        // 执行删除逻辑
        console.log('删除文件:', fileName);
        // 这里应该调用API删除文件
    }
}

function uploadToOnlineKnowledge(fileName) {
    if (confirm(`确定要将文件 "${fileName}" 上传到线上知识库吗？`)) {
        // 执行上传到线上知识库的逻辑
        console.log('上传文件到线上知识库:', fileName);
        // 这里应该调用API上传文件到线上知识库
    }
}

function editFile(fileName) {
    // 编辑文件功能
    alert(`编辑文件: ${fileName}`);
    // 这里应该打开编辑界面
}

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    console.log('本地知识库页面已加载');
});