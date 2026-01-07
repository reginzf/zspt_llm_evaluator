let currentAction = 'create'; // 'create' or 'edit'
let currentEnvironmentId = '';

function showCreateModal() {
    currentAction = 'create';
    document.getElementById('modalTitle').textContent = '创建Label-Studio环境';
    document.getElementById('environmentForm').reset();
    document.getElementById('label_studio_id_group').style.display = 'none';
    document.getElementById('saveBtn').textContent = '创建';
    document.getElementById('environmentModal').style.display = 'block';
}

function showEditModal(id, url, apiKey) {
    currentAction = 'edit';
    currentEnvironmentId = id;
    document.getElementById('modalTitle').textContent = '编辑Label-Studio环境';
    document.getElementById('label_studio_id').value = id;
    document.getElementById('label_studio_url').value = url;
    document.getElementById('label_studio_api_key').value = apiKey;
    document.getElementById('label_studio_id_group').style.display = 'block';
    document.getElementById('saveBtn').textContent = '更新';
    document.getElementById('environmentModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('environmentModal').style.display = 'none';
}

function showDeleteModal(id, name) {
    currentEnvironmentId = id;
    document.getElementById('deleteEnvName').textContent = name;
    document.getElementById('deleteModal').style.display = 'block';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

function confirmDelete() {
    fetch('/label_studio_env/delete/', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            label_studio_id: currentEnvironmentId
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('删除成功');
                location.reload();
            } else {
                alert('删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('删除过程中发生错误');
        });
}

// 确保DOM加载完成后再绑定事件监听器
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        bindFormSubmitHandler();
    });
} else {
    // DOM已经加载完成
    bindFormSubmitHandler();
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
                        alert('更新成功');
                        location.reload();
                    } else {
                        alert('更新失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('更新过程中发生错误');
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
                        alert('创建成功');
                        location.reload();
                    } else {
                        alert('创建失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('创建过程中发生错误');
                });
        }
    });
}

function togglePasswordVisibility(element, fullText) {
    const passwordSpan = element.previousElementSibling;
    if (passwordSpan.style.display === 'none') {
        // 显示星号掩码
        passwordSpan.style.display = 'inline';
        passwordSpan.textContent = '*'.repeat(fullText.length);
        element.textContent = '👁️';
    } else {
        // 显示真实密码
        passwordSpan.style.display = 'inline';
        passwordSpan.textContent = fullText;
        element.textContent = '🔒';
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