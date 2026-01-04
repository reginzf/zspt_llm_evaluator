// 生成知识库列表的HTML结构
function generateKnowledgeBaseTable(knowledgeBases) {
    const container = document.querySelector('.knowledge-base-items');
    
    // 清空容器（除了模板）
    const templates = container.querySelectorAll('template');
    container.innerHTML = '';
    
    // 重新添加模板
    templates.forEach(template => {
        container.appendChild(template);
    });
    
    if (knowledgeBases && knowledgeBases.length > 0) {
        // 添加表格头部
        const headerTemplate = document.getElementById('knowledge-base-table-header-template');
        const headerClone = headerTemplate.content.cloneNode(true);
        container.appendChild(headerClone);
        
        // 添加每个知识库行
        knowledgeBases.forEach(kb => {
            const rowTemplate = document.getElementById('knowledge-base-table-row-template');
            const rowClone = rowTemplate.content.cloneNode(true);
            
            // 填充数据
            const knowledgeName = rowClone.querySelector('.knowledge-name');
            const knowledgeId = rowClone.querySelector('.knowledge-id');
            const rootId = rowClone.querySelector('.table-cell[data-label="根ID"]');
            const chunkSize = rowClone.querySelector('.table-cell[data-label="分块大小"]');
            const chunkOverlap = rowClone.querySelector('.table-cell[data-label="分块重叠"]');
            const visibleRange = rowClone.querySelector('.table-cell[data-label="可见范围"]');
            const createdAt = rowClone.querySelector('.table-cell[data-label="创建时间"]');
            const updatedAt = rowClone.querySelector('.table-cell[data-label="编辑时间"]');
            const editBtn = rowClone.querySelector('.edit-btn');
            const deleteBtn = rowClone.querySelector('.delete-btn');
            
            knowledgeName.textContent = kb.knowledge_name || '';
            knowledgeId.textContent = kb.knowledge_id || '';
            rootId.textContent = kb.kno_root_id || 'N/A';
            chunkSize.textContent = kb.chunk_size || 'N/A';
            chunkOverlap.textContent = kb.chunk_overlap || 'N/A';
            visibleRange.textContent = kb.visiblerange || 'N/A';
            createdAt.textContent = kb.created_at || 'N/A';
            updatedAt.textContent = kb.updated_at || 'N/A';
            
            // 添加事件监听器
            editBtn.textContent = '编辑';
            editBtn.onclick = () => editKnowledgeBase(kb.knowledge_id);
            deleteBtn.textContent = '删除';
            deleteBtn.onclick = () => deleteKnowledgeBase(kb.knowledge_id);
            
            container.appendChild(rowClone);
        });
    } else {
        const emptyTemplate = document.getElementById('empty-state-template');
        const emptyClone = emptyTemplate.content.cloneNode(true);
        container.appendChild(emptyClone);
    }
}

// 渲染知识库列表
function renderKnowledgeBaseList(knowledgeBases) {
    const container = document.querySelector('.knowledge-base-items');
    
    // 生成HTML并更新容器内容
    container.innerHTML = generateKnowledgeBaseTable(knowledgeBases);
}

// 页面加载完成后获取初始数据
document.addEventListener('DOMContentLoaded', function() {
    // 页面加载时获取初始数据
    searchKnowledgeBases();
});

// 搜索知识库
function searchKnowledgeBases() {
    // 获取搜索条件
    const searchField = document.querySelector('.search-field').value;
    const searchValue = document.querySelector('.search-box').value;
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (searchValue) {
        params.append('search_field', searchField);
        params.append('search_value', searchValue);
    }
    
    // 显示加载状态
    const container = document.querySelector('.knowledge-base-items');
    container.innerHTML = '<div class="loading-state"><p>正在搜索...</p></div>';
    
    // 发送请求到后端
    fetch(`/environment_detail_list?${params.toString()}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            // 如果有环境ID，也添加到请求中
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderKnowledgeBaseList(data.data);
        } else {
            container.innerHTML = '<div class="error-state"><p>获取数据失败: ' + data.message + '</p></div>';
        }
    })
    .catch(error => {
        console.error('搜索知识库时出错:', error);
        container.innerHTML = '<div class="error-state"><p>搜索知识库时发生错误</p></div>';
    });
}

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
                // 重新加载数据
                searchKnowledgeBases();
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
    if (confirm('确定要删除这个知识库吗？')) {
        fetch(`/knowledge_base/delete/${knowledgeId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('知识库删除成功');
                // 重新加载数据
                searchKnowledgeBases();
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
    const name = prompt('请输入知识库名称:', '');
    if (name !== null && name.trim() !== '') {
        fetch('/knowledge_base/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                knowledge_name: name
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('知识库创建成功');
                // 重新加载数据
                searchKnowledgeBases();
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