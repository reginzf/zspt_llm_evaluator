// 本地知识库页面交互功能

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
    // 获取知识库ID
    const knowledgeId = headerElement.querySelector('.knowledge-id').textContent;
    const fileListContainer = headerElement.nextElementSibling.querySelector('.file-list');
    
    // 模拟加载文件列表，实际应用中应该通过API获取
    // 这里只是示例，实际应该从服务器获取数据
    fileListContainer.innerHTML = '<li class="file-item-placeholder">正在加载文件列表...</li>';
    
    // 模拟API调用
    setTimeout(() => {
        // 这里应该替换为实际的API调用
        fileListContainer.innerHTML = `
            <li class="file-item">
                <span class="file-name">sample_file.txt</span>
                <span class="file-description">示例文件描述</span>
                <div class="file-actions">
                    <button class="action-btn delete-btn" onclick="deleteFile('sample_file.txt')">删除</button>
                    <button class="action-btn upload-online-btn" onclick="uploadToOnlineKnowledge('sample_file.txt')">上传到线上知识库</button>
                    <button class="action-btn edit-btn" onclick="editFile('sample_file.txt')">编辑</button>
                </div>
            </li>
            <li class="file-item">
                <span class="file-name">another_file.pdf</span>
                <span class="file-description">另一个文件描述</span>
                <div class="file-actions">
                    <button class="action-btn delete-btn" onclick="deleteFile('another_file.pdf')">删除</button>
                    <button class="action-btn upload-online-btn" onclick="uploadToOnlineKnowledge('another_file.pdf')">上传到线上知识库</button>
                    <button class="action-btn edit-btn" onclick="editFile('another_file.pdf')">编辑</button>
                </div>
            </li>
        `;
    }, 500);
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