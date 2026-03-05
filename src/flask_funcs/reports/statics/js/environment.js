// 环境管理页面 JavaScript
// 使用公共组件重构版本

// 全局变量
let currentAction = '';
let deleteEnvId = '';
let environmentModal, deleteModal; // 模态框控制器
let searchComponent; // 搜索组件
let pagination; // 分页组件
let currentPage = 1;
let pageSize = 20;
let currentKeyword = '';

// 显示创建模态框
function showCreateModal() {
    currentAction = 'create';
    document.getElementById('modalTitle').textContent = '创建环境';
    document.getElementById('environmentForm').reset();
    document.getElementById('zlpt_base_id').value = '';
    document.getElementById('zlpt_base_id').readOnly = true; // 在创建时 ID 字段只读
    document.getElementById('zlpt_base_id_group').style.display = 'none'; // 隐藏 ID 字段组
    document.getElementById('zlpt_name').disabled = false;
    document.getElementById('saveBtn').textContent = '创建';
    
    if (environmentModal) {
        environmentModal.show();
    } else {
        document.getElementById('environmentModal').style.display = 'block';
    }
}

// 显示编辑模态框
function showEditModal(id, name, projectName, url, domain, username, password) {
    currentAction = 'edit';
    document.getElementById('modalTitle').textContent = '编辑环境';
    document.getElementById('zlpt_base_id').value = id;
    document.getElementById('zlpt_base_id').readOnly = true; // ID 字段只读（但会包含在提交中）
    document.getElementById('zlpt_base_id_group').style.display = ''; // 显示 ID 字段组
    document.getElementById('zlpt_name').value = name;
    document.getElementById('project_name').value = projectName || '';
    document.getElementById('zlpt_base_url').value = url;
    document.getElementById('domain').value = domain;
    document.getElementById('username').value = username;
    document.getElementById('password').value = password;
    document.getElementById('saveBtn').textContent = '更新';
    
    if (environmentModal) {
        environmentModal.show();
    } else {
        document.getElementById('environmentModal').style.display = 'block';
    }
}

// 显示删除模态框
function showDeleteModal(id, name) {
    deleteEnvId = id;
    document.getElementById('deleteEnvName').textContent = name;
    
    if (deleteModal) {
        deleteModal.show();
    } else {
        document.getElementById('deleteModal').style.display = 'block';
    }
}

// 关闭模态框
function closeModal() {
    if (environmentModal) {
        environmentModal.hide();
    } else {
        document.getElementById('environmentModal').style.display = 'none';
    }
}

function closeDeleteModal() {
    if (deleteModal) {
        deleteModal.hide();
    } else {
        document.getElementById('deleteModal').style.display = 'none';
    }
    deleteEnvId = '';
}

// 加载环境列表（支持分页和搜索）
function loadEnvironments(page = 1, pageSize = 20, keyword = '') {
    console.log(`加载环境列表：第${page}页，每页${pageSize}条，关键词：${keyword}`);
    
    // TODO: 调用后端 API 获取数据
    // 目前先使用前端过滤，后续改为服务端分页
    const table = document.getElementById('environmentTableBody');
    const rows = table.getElementsByTagName('tr');
    let visibleCount = 0;
    let totalRows = 0;
    
    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = true;
        
        // 搜索过滤
        if (keyword) {
            found = false;
            for (let j = 0; j < cells.length - 1; j++) { // 不搜索操作列
                if (cells[j].textContent.toUpperCase().indexOf(keyword.toUpperCase()) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        if (found) {
            totalRows++;
            // 分页逻辑
            const startIndex = (page - 1) * pageSize;
            const endIndex = startIndex + pageSize;
            
            if (visibleCount >= startIndex && visibleCount < endIndex) {
                rows[i].style.display = '';
                visibleCount++;
            } else {
                rows[i].style.display = 'none';
            }
        } else {
            rows[i].style.display = 'none';
        }
    }
    
    // 更新分页组件
    if (pagination) {
        pagination.update(totalRows, page, pageSize);
    }
}

// 搜索回调函数
function handleSearch(keyword) {
    currentKeyword = keyword;
    currentPage = 1; // 重置到第一页
    loadEnvironments(currentPage, pageSize, currentKeyword);
}

// 表单提交事件
document.addEventListener('DOMContentLoaded', function() {
    const environmentForm = document.getElementById('environmentForm');
    if (environmentForm) {
        environmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            if (currentAction === 'create') {
                createEnvironment(data);
            } else if (currentAction === 'edit') {
                updateEnvironment(data);
            }
        });
    }
});

// 创建环境
function createEnvironment(data) {
    fetch('/environment/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            DialogManager.showSuccess('环境创建成功', () => {
                closeModal();
                location.reload(); // 刷新页面以显示新环境
            });
        } else {
            DialogManager.showError('创建失败：' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        DialogManager.showError('创建失败', error);
    });
}

// 更新环境
function updateEnvironment(data) {
    fetch(`/environment/update/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            DialogManager.showSuccess('环境更新成功', () => {
                closeModal();
                location.reload(); // 刷新页面以显示更新后的环境
            });
        } else {
            DialogManager.showError('更新失败：' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        DialogManager.showError('更新失败', error);
    });
}

// 确认删除
function confirmDelete() {
    const envName = document.getElementById('deleteEnvName').textContent;
    
    DialogManager.confirm(
        `确定要删除环境 "${envName}" 吗？此操作不可撤销。`,
        async () => {
            // 用户确认，执行删除
            try {
                const response = await fetch(`/environment/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        zlpt_base_id: deleteEnvId
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    DialogManager.showSuccess('环境删除成功', () => {
                        closeDeleteModal();
                        location.reload();
                    });
                } else {
                    DialogManager.showError('删除失败：' + result.message);
                }
            } catch (error) {
                console.error('Delete error:', error);
                DialogManager.showError('删除失败', error);
            }
        },
        () => {
            // 用户取消
            console.log('用户取消删除');
        }
    );
}

// 切换密码可见性
function togglePasswordVisibility(element, password) {
    const passwordSpan = element.previousElementSibling;
    if (passwordSpan.textContent === '********') {
        passwordSpan.textContent = password;
        element.textContent = '🙈'; // 改为隐藏图标
    } else {
        passwordSpan.textContent = '********';
        element.textContent = '👁️'; // 显示图标
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 1. 创建搜索组件
    searchComponent = new SearchComponent('searchInput', 'searchBtn', handleSearch);
    
    // 2. 绑定刷新按钮事件
    document.getElementById('refreshBtn').addEventListener('click', function() {
        // 清空搜索框
        document.getElementById('searchInput').value = '';
        currentKeyword = '';
        currentPage = 1;
        // 刷新列表
        loadEnvironments(1, pageSize, '');
    });
    
    // 3. 创建分页组件
    pagination = new PaginationComponent('paginationArea', (page, size) => {
        currentPage = page;
        pageSize = size;
        loadEnvironments(page, size, currentKeyword);
    });
    
    // 4. 初始化模态框控制器
    environmentModal = new ModalController('environmentModal', {
        closeOnOutsideClick: true,
        closeOnEsc: true
    });
    
    deleteModal = new ModalController('deleteModal', {
        closeOnOutsideClick: true,
        closeOnEsc: true
    });
    
    // 5. 设置关闭回调（清理）
    environmentModal.setOnClose(() => {
        document.getElementById('environmentForm').reset();
        currentAction = '';
    });
    
    deleteModal.setOnClose(() => {
        deleteEnvId = '';
    });
    
    // 6. 加载初始数据
    loadEnvironments(1, 20);
    
    console.log('环境管理页面已加载，组件初始化完成');
});