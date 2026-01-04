// 生成知识库列表的HTML结构
function generateKnowledgeBaseTable(knowledgeBases) {
    let html = '';
    
    if (knowledgeBases && knowledgeBases.length > 0) {
        // 添加表格头部
        html += `
            <div class="knowledge-base-table-header">
                <div class="table-header-cell">名称/ID</div>
                <div class="table-header-cell">根ID</div>
                <div class="table-header-cell">分块大小</div>
                <div class="table-header-cell">分块重叠</div>
                <div class="table-header-cell">可见范围</div>
                <div class="table-header-cell">创建时间</div>
                <div class="table-header-cell">编辑时间</div>
                <div class="table-header-cell">操作</div>
            </div>
        `;
        
        // 添加每个知识库行
        knowledgeBases.forEach(kb => {
            html += `
                <div class="knowledge-base-table-row">
                    <div class="table-cell" data-label="名称/ID">
                        <div class="knowledge-name">${kb.knowledge_name || ''}</div>
                        <div class="knowledge-id">${kb.knowledge_id || ''}</div>
                    </div>
                    <div class="table-cell" data-label="根ID">${kb.kno_root_id || 'N/A'}</div>
                    <div class="table-cell" data-label="分块大小">${kb.chunk_size || 'N/A'}</div>
                    <div class="table-cell" data-label="分块重叠">${kb.chunk_overlap || 'N/A'}</div>
                    <div class="table-cell" data-label="可见范围">${kb.visiblerange || 'N/A'}</div>
                    <div class="table-cell" data-label="创建时间">${kb.created_at || 'N/A'}</div>
                    <div class="table-cell" data-label="编辑时间">${kb.updated_at || 'N/A'}</div>
                    <div class="table-cell actions-cell" data-label="操作">
                        <button class="action-btn edit-btn" onclick="editKnowledgeBase('${kb.knowledge_id}')">编辑</button>
                        <button class="action-btn delete-btn" onclick="deleteKnowledgeBase('${kb.knowledge_id}')">删除</button>
                    </div>
                </div>
            `;
        });
    } else {
        html += '<div class="empty-state"><p>暂无知识库</p></div>';
    }
    
    return html;
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