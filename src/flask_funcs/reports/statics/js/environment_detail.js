// 环境详情页面JavaScript代码

// 搜索功能
function searchKnowledgeBases() {
    const searchInput = document.querySelector('.search-box');
    const searchTerm = searchInput.value.toLowerCase();
    const knowledgeItems = document.querySelectorAll('.knowledge-base-item');
    
    knowledgeItems.forEach(item => {
        const knowledgeName = item.querySelector('h3').textContent.toLowerCase();
        if (knowledgeName.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// 为搜索框添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        searchBox.addEventListener('input', searchKnowledgeBases);
    }
});

// 编辑知识库
function editKnowledgeBase(knowledgeId) {
    // 通过弹窗或模态框实现编辑功能
    const newName = prompt('请输入新的知识库名称:', '');
    if (newName !== null && newName.trim() !== '') {
        // 发送更新请求到后端
        fetch(`/knowledge_base/update/${knowledgeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                knowledge_name: newName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('知识库更新成功');
                location.reload(); // 刷新页面以显示更新后的数据
            } else {
                alert('更新失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('更新知识库时出错:', error);
            alert('更新知识库时发生错误');
        });
    }
}

// 删除知识库
function deleteKnowledgeBase(knowledgeId) {
    if (confirm(`确定要删除知识库 ${knowledgeId} 吗？此操作不可撤销。`)) {
        // 发送删除请求到后端
        fetch(`/knowledge_base/delete/${knowledgeId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('知识库删除成功');
                location.reload(); // 刷新页面以更新列表
            } else {
                alert('删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('删除知识库时出错:', error);
            alert('删除知识库时发生错误');
        });
    }
}

// 创建知识库
function createKnowledgeBase() {
    const knowledgeName = prompt('请输入知识库名称:', '');
    if (knowledgeName !== null && knowledgeName.trim() !== '') {
        // 从URL参数中获取zlpt_base_id
        const urlParams = new URLSearchParams(window.location.search);
        const zlpt_base_id = urlParams.get('zlpt_base_id');
        
        if (!zlpt_base_id) {
            alert('无法获取环境ID，请返回环境列表页面重新进入');
            return;
        }
        
        // 发送创建请求到后端
        fetch('/knowledge_base/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                knowledge_name: knowledgeName,
                zlpt_base_id: zlpt_base_id
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('知识库创建成功');
                location.reload(); // 刷新页面以显示新创建的知识库
            } else {
                alert('创建失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('创建知识库时出错:', error);
            alert('创建知识库时发生错误');
        });
    }
}

// 为创建按钮添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const createBtn = document.querySelector('.create-btn');
    if (createBtn) {
        createBtn.addEventListener('click', createKnowledgeBase);
    }
});
