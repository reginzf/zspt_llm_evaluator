// Label-Studio 环境管理页面 JavaScript
// 使用公共组件重构版本

// 全局变量
let currentAction = 'create'; // 'create' or 'edit'
let currentEnvironmentId = '';
let environmentModal, deleteModal; // 模态框控制器

function showCreateModal() {
    currentAction = 'create';
    document.getElementById('modalTitle').textContent = '创建 Label-Studio 环境';
    document.getElementById('environmentForm').reset();
    document.getElementById('label_studio_id_group').style.display = 'none';
    document.getElementById('saveBtn').textContent = '创建';
    
    if (environmentModal) {
        environmentModal.show();
    } else {
        document.getElementById('environmentModal').style.display = 'block';
    }
}

function showEditModal(id, url, apiKey) {
    currentAction = 'edit';
    currentEnvironmentId = id;
    document.getElementById('modalTitle').textContent = '编辑 Label-Studio 环境';
    document.getElementById('label_studio_id').value = id;
    document.getElementById('label_studio_url').value = url;
    document.getElementById('label_studio_api_key').value = apiKey;
    document.getElementById('label_studio_id_group').style.display = 'block';
    document.getElementById('saveBtn').textContent = '更新';
    
    if (environmentModal) {
        environmentModal.show();
    } else {
        document.getElementById('environmentModal').style.display = 'block';
    }
}

function closeModal() {
    if (environmentModal) {
        environmentModal.hide();
    } else {
        document.getElementById('environmentModal').style.display = 'none';
    }
}

function showDeleteModal(id, name) {
    currentEnvironmentId = id;
    document.getElementById('deleteEnvName').textContent = name;
    
    if (deleteModal) {
        deleteModal.show();
    } else {
        document.getElementById('deleteModal').style.display = 'block';
    }
}

function closeDeleteModal() {
    if (deleteModal) {
        deleteModal.hide();
    } else {
        document.getElementById('deleteModal').style.display = 'none';
    }
}

function confirmDelete() {
    const envName = document.getElementById('deleteEnvName').textContent;
    
    DialogManager.confirm(
        `确定要删除环境 "${envName}" 吗？此操作不可撤销。`,
        async () => {
            try {
                const response = await fetch('/label_studio_env/delete/', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        label_studio_id: currentEnvironmentId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    DialogManager.showSuccess('删除成功', () => {
                        location.reload();
                    });
                } else {
                    DialogManager.showError('删除失败：' + data.message);
                }
            } catch (error) {
                console.error('Delete error:', error);
                DialogManager.showError('删除过程中发生错误', error);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 确保 DOM 加载完成后再绑定事件监听器
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initModalControllers();
        bindFormSubmitHandler();
    });
} else {
    // DOM 已经加载完成
    initModalControllers();
    bindFormSubmitHandler();
}

// 初始化模态框控制器
function initModalControllers() {
    environmentModal = new ModalController('environmentModal', {
        closeOnOutsideClick: true,
        closeOnEsc: true
    });
    
    deleteModal = new ModalController('deleteModal', {
        closeOnOutsideClick: true,
        closeOnEsc: true
    });
    
    console.log('Label-Studio 环境管理页面已加载');
}

function bindFormSubmitHandler() {
    document.getElementById('environmentForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = {
            label_studio_url: document.getElementById('label_studio_url').value,
            label_studio_api_key: document.getElementById('label_studio_api_key').value
        };

        if (currentAction === 'edit') {
            formData.label_studio_id = currentEnvironmentId;
            // 发送PUT请求更新环境
            fetch('/label_studio_env/update/', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        DialogManager.showSuccess('更新成功', () => {
                            location.reload();
                        });
                    } else {
                        DialogManager.showError('更新失败：' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    DialogManager.showError('更新过程中发生错误', error);
                });
        } else {
            // 发送POST请求创建环境
            fetch('/label_studio_env/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        DialogManager.showSuccess('创建成功', () => {
                            location.reload();
                        });
                    } else {
                        DialogManager.showError('创建失败：' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    DialogManager.showError('创建过程中发生错误', error);
                });
        }
    });
}

function togglePasswordVisibility(element, fullText) {
    const passwordSpan = element.previousElementSibling;
    const isCurrentlyMasked = passwordSpan.textContent.startsWith('**');
    
    if (isCurrentlyMasked) {
        // 当前是星号掩码，显示真实API Key
        passwordSpan.textContent = fullText;
        element.textContent = '🔒';
    } else {
        // 当前是真实API Key，显示星号掩码
        passwordSpan.textContent = '*******';
        element.textContent = '👁️';
    }
}

function searchEnvironments() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const tableRows = document.querySelectorAll('#environmentTableBody tr');

    tableRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let found = false;

        cells.forEach(cell => {
            if (cell.textContent.toLowerCase().includes(searchTerm)) {
                found = true;
            }
        });

        row.style.display = found ? '' : 'none';
    });
}