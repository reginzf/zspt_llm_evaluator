// 环境管理页面JavaScript
let currentAction = '';
let deleteEnvId = '';

// 显示创建模态框
function showCreateModal() {
    currentAction = 'create';
    document.getElementById('modalTitle').textContent = '创建环境';
    document.getElementById('environmentForm').reset();
    document.getElementById('zlpt_base_id').value = '';
    document.getElementById('zlpt_base_id').readOnly = true; // 在创建时ID字段只读
    document.getElementById('zlpt_base_id_group').style.display = 'none'; // 隐藏ID字段组
    document.getElementById('zlpt_name').disabled = false;
    document.getElementById('saveBtn').textContent = '创建';
    document.getElementById('environmentModal').style.display = 'block';
}

// 显示编辑模态框
function showEditModal(id, name, projectName, url, domain, username, password) {
    currentAction = 'edit';
    document.getElementById('modalTitle').textContent = '编辑环境';
    document.getElementById('zlpt_base_id').value = id;
    document.getElementById('zlpt_base_id').readOnly = true; // ID字段只读（但会包含在提交中）
    document.getElementById('zlpt_base_id_group').style.display = ''; // 显示ID字段组
    document.getElementById('zlpt_name').value = name;
    document.getElementById('project_name').value = projectName || '';
    document.getElementById('zlpt_base_url').value = url;
    document.getElementById('domain').value = domain;
    document.getElementById('username').value = username;
    document.getElementById('password').value = password;
    document.getElementById('saveBtn').textContent = '更新';
    document.getElementById('environmentModal').style.display = 'block';
}

// 显示删除模态框
function showDeleteModal(id, name) {
    deleteEnvId = id;
    document.getElementById('deleteEnvName').textContent = name;
    document.getElementById('deleteModal').style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('environmentModal').style.display = 'none';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deleteEnvId = '';
}

// 搜索环境
function searchEnvironments() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('environmentTableBody');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length - 1; j++) { // 不搜索操作列
            if (cells[j].textContent.toUpperCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }
        
        if (found) {
            rows[i].style.display = '';
        } else {
            rows[i].style.display = 'none';
        }
    }
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
            alert('环境创建成功');
            closeModal();
            location.reload(); // 刷新页面以显示新环境
        } else {
            alert('创建失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('创建失败: ' + error.message);
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
            alert('环境更新成功');
            closeModal();
            location.reload(); // 刷新页面以显示更新后的环境
        } else {
            alert('更新失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('更新失败: ' + error.message);
    });
}

// 确认删除
function confirmDelete() {
    fetch(`/environment/delete/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            zlpt_base_id: deleteEnvId
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('环境删除成功');
            closeDeleteModal();
            location.reload(); // 刷新页面以移除删除的环境
        } else {
            alert('删除失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败: ' + error.message);
    });
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

// 点击模态框外部关闭模态框
window.onclick = function(event) {
    const environmentModal = document.getElementById('environmentModal');
    const deleteModal = document.getElementById('deleteModal');
    
    if (event.target === environmentModal) {
        closeModal();
    }
    
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}