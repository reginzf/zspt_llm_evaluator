// 环境详情页面 JavaScript 代码
// 使用公共组件重构版本

// 全局变量
let createModal; // 模态框控制器

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
            renderKnowledgeBaseList(data.data);
        } else {
            DialogManager.showError('获取知识库列表失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('搜索知识库时出错:', error);
        DialogManager.showError('搜索知识库时出错', error);
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
    
    console.log('环境详情页面已加载');
});

// 编辑知识库
function editKnowledgeBase(knowledgeId) {
    const newName = prompt('请输入新的知识库名称:', '');
    if (newName !== null && newName.trim() !== '') {
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
                DialogManager.showSuccess('知识库更新成功', () => {
                    location.reload();
                });
            } else {
                DialogManager.showError('更新失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('更新知识库时出错:', error);
            DialogManager.showError('更新知识库时发生错误', error);
        });
    }
}

// 删除知识库
function deleteKnowledgeBase(knowledgeId) {
    DialogManager.confirm(
        `确定要删除知识库 ${knowledgeId} 吗？此操作不可撤销。`,
        async () => {
            try {
                const response = await fetch(`/knowledge_base/delete/${knowledgeId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    DialogManager.showSuccess('知识库删除成功', () => {
                        location.reload();
                    });
                } else {
                    DialogManager.showError('删除失败：' + data.message);
                }
            } catch (error) {
                console.error('删除知识库时出错:', error);
                DialogManager.showError('删除知识库时发生错误', error);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 创建知识库 - 显示模态框
function createKnowledgeBase() {
    const modal = document.createElement('div');
    modal.id = 'createKnowledgeBaseModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>创建知识库</h3>
                <span class="close" onclick="closeCreateModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label for="knowledgeName">知识库名称:</label>
                    <input type="text" id="knowledgeName" class="form-control" placeholder="请输入知识库名称" required>
                </div>
                <div class="form-group">
                    <label for="chunkSize">分块大小:</label>
                    <input type="number" id="chunkSize" class="form-control" placeholder="请输入分块大小" value="400" required>
                </div>
                <div class="form-group">
                    <label for="chunkOverlap">分块重叠:</label>
                    <input type="number" id="chunkOverlap" class="form-control" placeholder="请输入分块重叠" value="50" required>
                </div>
                <div class="form-group">
                    <label for="sliceIdentifier">分隔符:</label>
                    <input type="text" id="sliceIdentifier" class="form-control" placeholder="请输入分隔符，用逗号分隔" value="。,！,!,？,?,，,:,：,." required>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="submitCreateKnowledgeBase()">创建</button>
                <button class="btn btn-secondary" onclick="closeCreateModal()">取消</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 使用 ModalController 或直接显示
    if (typeof ModalController !== 'undefined') {
        createModal = new ModalController('createKnowledgeBaseModal', {
            closeOnOutsideClick: true,
            closeOnEsc: true
        });
        createModal.show();
    } else {
        modal.style.display = 'block';
    }
}

// 关闭创建模态框
function closeCreateModal() {
    const modal = document.getElementById('createKnowledgeBaseModal');
    if (modal) {
        if (createModal) {
            createModal.hide();
            setTimeout(() => modal.remove(), 100); // 等待动画后移除
        } else {
            modal.remove();
        }
    }
}

// 提交创建知识库
function submitCreateKnowledgeBase() {
    const knowledgeName = document.getElementById('knowledgeName').value;
    const chunkSize = document.getElementById('chunkSize').value;
    const chunkOverlap = document.getElementById('chunkOverlap').value;
    const sliceIdentifierInput = document.getElementById('sliceIdentifier').value;
    
    // 将分隔符字符串转换为数组
    const sliceIdentifier = sliceIdentifierInput.split(',').map(item => item.trim()).filter(item => item !== '');
    
    // 从URL参数中获取zlpt_base_id
    const urlParams = new URLSearchParams(window.location.search);
    const zlpt_base_id = urlParams.get('zlpt_base_id');

    if (!zlpt_base_id) {
        DialogManager.showError('无法获取环境 ID，请返回环境列表页面重新进入');
        closeCreateModal();
        return;
    }
    
    if (!knowledgeName || !chunkSize || !chunkOverlap || !sliceIdentifier) {
        DialogManager.showWarning('请填写所有必填字段');
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
            zlpt_base_id: zlpt_base_id,
            chunk_size: parseInt(chunkSize),
            chunk_overlap: parseInt(chunkOverlap),
            sliceidentifier: sliceIdentifier
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            DialogManager.showSuccess('知识库创建成功', () => {
                closeCreateModal();
                location.reload();
            });
        } else {
            DialogManager.showError('创建失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('创建知识库时出错:', error);
        DialogManager.showError('创建知识库时发生错误', error);
    });
}

// 为创建按钮添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const createBtn = document.querySelector('.create-btn');
    if (createBtn) {
        createBtn.addEventListener('click', createKnowledgeBase);
    }
});