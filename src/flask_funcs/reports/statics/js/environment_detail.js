// 环境详情页面JavaScript代码

// 搜索功能
function searchKnowledgeBases() {
    const searchInput = document.querySelector('.search-box');
    const searchField = document.querySelector('.search-field');
    const searchTerm = searchInput.value;
    const selectedField = searchField.value;
    
    // 从URL参数中获取zlpt_base_id
    const urlParams = new URLSearchParams(window.location.search);
    const zlpt_base_id = urlParams.get('zlpt_base_id');
    
    if (!zlpt_base_id) {
        console.error('无法获取zlpt_base_id参数');
        return;
    }
    
    // 构建搜索参数
    let searchParams = {
        zlpt_id: zlpt_base_id  // 后端方法使用zlpt_id参数
    };
    
    // 如果搜索词不为空，添加搜索字段和值
    if (searchTerm.trim() !== '') {
        searchParams.search_field = selectedField;
        searchParams.search_value = searchTerm;
    }
    
    // 向后端发送请求
    fetch('/environment_detail_list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchParams)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 渲染知识库列表
            renderKnowledgeBaseList(data.data);
        } else {
            console.error('获取知识库列表失败:', data.message);
        }
    })
    .catch(error => {
        console.error('搜索知识库时出错:', error);
    });
}

// 渲染知识库列表
function renderKnowledgeBaseList(knowledgeBases) {
    const container = document.querySelector('.knowledge-base-items');
    
    // 清空当前内容
    container.innerHTML = '';

    if (knowledgeBases && knowledgeBases.length > 0) {
        // 添加表格头部
        const tableHeader = document.createElement('div');
        tableHeader.className = 'knowledge-base-table-header';
        tableHeader.innerHTML = `
            <div class="table-header-cell">名称/ID</div>
            <div class="table-header-cell">根ID</div>
            <div class="table-header-cell">分块大小</div>
            <div class="table-header-cell">分块重叠</div>
            <div class="table-header-cell">可见范围</div>
            <div class="table-header-cell">创建时间</div>
            <div class="table-header-cell">编辑时间</div>
            <div class="table-header-cell">操作</div>
        `;
        container.appendChild(tableHeader);
        
        // 添加每个知识库行
        knowledgeBases.forEach(kb => {
            console.log('Processing knowledge base:', kb); // 调试信息
            const row = document.createElement('div');
            row.className = 'knowledge-base-table-row';
            // 在模板字符串中，使用 ${} 语法来引用变量
            let innerHTML = '<div class="table-cell" data-label="名称/ID">' +
                '<div class="knowledge-name">' + (kb.knowledge_name || '') + '</div>' +
                '<div class="knowledge-id">/' + (kb.knowledge_id || '') + '</div>' +
                '</div>' +
                '<div class="table-cell" data-label="根ID">' + (kb.kno_root_id || 'N/A') + '</div>' +
                '<div class="table-cell" data-label="分块大小">' + (kb.chunk_size || 'N/A') + '</div>' +
                '<div class="table-cell" data-label="分块重叠">' + (kb.chunk_overlap || 'N/A') + '</div>' +
                '<div class="table-cell" data-label="可见范围">' + (kb.visiblerange || 'N/A') + '</div>' +
                '<div class="table-cell" data-label="创建时间">' + (kb.created_at || 'N/A') + '</div>' +
                '<div class="table-cell" data-label="编辑时间">' + (kb.updated_at || 'N/A') + '</div>' +
                '<div class="table-cell actions-cell" data-label="操作">' +
                '<button class="action-btn edit-btn" onclick="editKnowledgeBase(\'' + kb.knowledge_id + '\')">编辑</button>' +
                '<button class="action-btn delete-btn" onclick="deleteKnowledgeBase(\'' + kb.knowledge_id + '\')">删除</button>' +
                '</div>';
            row.innerHTML = innerHTML;
            container.appendChild(row);
        });
    } else {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = '<p>暂无知识库</p>';
        container.appendChild(emptyState);
    }
}

// 页面加载完成后获取初始数据
document.addEventListener('DOMContentLoaded', function() {
    // 页面加载时获取初始数据
    searchKnowledgeBases();
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
