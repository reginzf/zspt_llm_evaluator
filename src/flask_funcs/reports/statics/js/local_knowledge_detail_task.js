// AI指标任务管理模块的JavaScript代码

let currentKnowledgeId = null;

// 初始化任务管理模块
function initTaskTab(knoId) {
    currentKnowledgeId = knoId;
    loadTaskList();
}

// 加载任务列表
function loadTaskList() {

    fetch(`/local_knowledge_detail/task/metric/list?knowledge_id=${currentKnowledgeId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 存储任务列表到全局变量
            window.currentTaskList = data.data;
            renderTaskTable(data.data);
        } else {
            console.error('获取任务列表失败:', data.message);
            const tableBody = document.getElementById('metricTaskTableBody');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">获取任务列表失败: ${data.message}</td></tr>`;
            }
        }
    })
    .catch(error => {
        console.error('请求任务列表时出错:', error);
        const tableBody = document.getElementById('metricTaskTableBody');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">网络请求错误: ${error.message}</td></tr>`;
        }
    });
}

// 渲染任务表格
function renderTaskTable(tasks) {

    const tableBody = document.getElementById('metricTaskTableBody');
    if (!tableBody) {
        // 如果找不到元素，稍后再试一次，以防DOM还没完全加载
        setTimeout(() => {
            const retryTableBody = document.getElementById('metricTaskTableBody');
            if (retryTableBody) {
                renderTaskTable(tasks); // 递归调用
            } else {
                console.error('Still could not find metricTaskTableBody element after retry');
            }
        }, 100);
        return;
    }

    tableBody.innerHTML = ''; // 清空现有内容

    if (tasks && tasks.length > 0) {

        tasks.forEach(task => {

            const row = createTaskRow(task);
            if (row) { // 确保row存在

                tableBody.appendChild(row);

            }
        });

    } else {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="8" style="text-align: center;">暂无指标任务</td>`;
        tableBody.appendChild(row);
    }
}

// 创建任务行
function createTaskRow(task) {

    // 确保task对象存在
    if (!task) {
        console.error('Task object is null or undefined');
        return null;
    }

    // 确定状态样式类
    let statusClass = '';
    switch(task.status) {
        case '初始化':
            statusClass = 'status-initial';
            break;
        case '标注中':
            statusClass = 'status-annotating';
            break;
        case '标注完成':
            statusClass = 'status-annotated';
            break;
        case '计算中':
            statusClass = 'status-calculating';
            break;
        case '完成':
            statusClass = 'status-completed';
            break;
        default:
            statusClass = 'status-initial';
    }

    const row = document.createElement('tr');
    // 使用更安全的innerHTML赋值，防止潜在的XSS问题
    row.innerHTML = `
        <td>${task.metric_task_id ? escapeHtml(task.metric_task_id) : 'N/A'}</td>
        <td>
            <div>${task.task_id ? escapeHtml(task.task_id) : 'N/A'}</div>
            <div>${task.task_name ? escapeHtml(task.task_name) : 'N/A'}</div>
        </td>
        <td>${task.annotation_type ? escapeHtml(task.annotation_type) : '未设置'}</td>
        <td>${task.match_type ? escapeHtml(getMatchTypeDisplay(task.match_type)) : 'N/A'}</td>
        <td><span class="${statusClass}">${task.status ? escapeHtml(task.status) : '未知'}</span></td>
        <td class="task-actions-cell">
            <button class="task-action-btn calculate-btn" onclick="showCalculationDialog('${task.task_id ? escapeHtml(task.task_id) : ''}')">
                计算
            </button>
            <button class="task-action-btn report-btn" onclick="showReportDialog('${task.metric_task_id ? escapeHtml(task.metric_task_id) : ''}')">
                报告
            </button>
            <button class="task-action-btn delete-btn" onclick="deleteMetricTask('${task.metric_task_id ? escapeHtml(task.metric_task_id) : ''}')">
                删除
            </button>
        </td>
    `;

    return row;
}

// 辅助函数：转义HTML特殊字符
function escapeHtml(text) {
    if (typeof text !== 'string') {
        return String(text);
    }
    var map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// 显示质量计算方式选择模态框
function showCalculationDialog(taskId) {
    // 存储当前任务ID
    document.getElementById('currentTaskId').value = taskId;

    // 重置下拉框选择
    const selectElement = document.getElementById('searchTypeSelect');
    selectElement.selectedIndex = 0;

    // 显示模态框
    document.getElementById('calculationModal').style.display = 'block';
}

// 隐藏质量计算方式选择模态框
function hideCalculationModal() {
    document.getElementById('calculationModal').style.display = 'none';
}

// 确认计算类型
function confirmCalculationType() {
    const selectedType = document.getElementById('searchTypeSelect').value;
    const taskId = document.getElementById('currentTaskId').value;

    if (!selectedType) {
        alert('请选择召回方式');
        return;
    }

    if (!taskId) {
        alert('任务ID不能为空');
        return;
    }

    // 直接从服务器获取任务信息
    fetch(`/local_knowledge_detail/task/metric/get_task_info?task_id=${taskId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.data) {
                const taskInfo = data.data;
                
                // 检查 match_type
                if (!taskInfo.match_type) {
                    // 如果 match_type 为空，显示更新匹配方式的界面
                    showMatchTypeUpdateSection(taskId, selectedType);
                    return;
                }

                const matchType = taskInfo.match_type;
                const metricTaskId = taskInfo.metric_task_id;

                // 发送请求启动计算
                return fetch('/local_knowledge_detail/task/metric/start_calculation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        task_id: taskId,
                        search_type: selectedType,
                        match_type: matchType,
                        metric_task_id: metricTaskId
                    })
                });
            } else {
                throw new Error(data.message || '无法获取任务信息');
            }
        })
        .then(response => {
            if (!response) {
                // 如果没有返回 response，说明前面已经处理过了
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) {
                // 如果没有数据，说明前面已经处理过了
                return;
            }
            if (data.success) {
                alert('质量计算已启动');
                hideCalculationModal();
                // 刷新任务列表
                loadTaskList();
            } else {
                throw new Error(data.message || '启动计算失败');
            }
        })
        .catch(error => {
            console.error('处理过程中出错:', error);
            alert('操作失败: ' + error.message);
        });
}

// 显示匹配方式更新区域
function showMatchTypeUpdateSection(taskId, searchType) {
    document.getElementById('matchTypeUpdateSection').style.display = 'block';
    document.getElementById('currentTaskId').setAttribute('data-search-type', searchType);
    
    // 重置选择框
    document.getElementById('updateMatchTypeSelect').selectedIndex = 0;
    document.getElementById('updateKnowledgeBaseGroup').style.display = 'none';
    document.getElementById('updateKnowledgeBaseSelect').innerHTML = '<option value="" disabled selected>请选择知识库</option>';
}

// 处理更新匹配方式选择变化
function handleUpdateMatchTypeChange() {
    const matchType = document.getElementById('updateMatchTypeSelect').value;
    const knowledgeBaseGroup = document.getElementById('updateKnowledgeBaseGroup');
    const knowledgeBaseSelect = document.getElementById('updateKnowledgeBaseSelect');

    if (matchType === 'chunkTextMatch') {
        // 显示知识库选择
        knowledgeBaseGroup.style.display = 'block';
        // 加载绑定的知识库
        loadBoundKnowledgeBasesForUpdate();
    } else {
        // 隐藏知识库选择
        knowledgeBaseGroup.style.display = 'none';
        knowledgeBaseSelect.innerHTML = '<option value="" disabled selected>请选择知识库</option>';
    }
}

// 为更新功能加载绑定的知识库
function loadBoundKnowledgeBasesForUpdate() {
    const knowledgeBaseSelect = document.getElementById('updateKnowledgeBaseSelect');
    const knoId = currentKnowledgeId;

    if (!knoId) {
        knowledgeBaseSelect.innerHTML = '<option value="" disabled>未找到本地知识库ID</option>';
        return;
    }

    fetch('/local_knowledge/bindings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: knoId
        })
    })
    .then(response => response.json())
    .then(data => {
        knowledgeBaseSelect.innerHTML = '<option value="" disabled selected>请选择知识库</option>';
        if (Array.isArray(data) && data.length > 0) {
            data.forEach(binding => {
                if (binding.bind_status === 2) { // 已绑定状态
                    const option = document.createElement('option');
                    option.value = binding.knowledge_id;
                    option.textContent = binding.knowledge_name || binding.knowledge_id;
                    knowledgeBaseSelect.appendChild(option);
                }
            });
        } else {
            knowledgeBaseSelect.innerHTML = '<option value="" disabled>暂无绑定的知识库</option>';
        }
    })
    .catch(error => {
        console.error('加载知识库列表时出错:', error);
        knowledgeBaseSelect.innerHTML = '<option value="" disabled>加载失败</option>';
    });
}

// 更新任务匹配方式
function updateTaskMatchType() {
    const taskId = document.getElementById('currentTaskId').value;
    const searchType = document.getElementById('currentTaskId').getAttribute('data-search-type');
    const matchType = document.getElementById('updateMatchTypeSelect').value;
    const knowledgeBaseId = document.getElementById('updateKnowledgeBaseSelect').value;

    // 验证必填字段
    if (!matchType) {
        alert('请选择匹配方式');
        return;
    }

    if (!searchType) {
        alert('召回方式不能为空');
        return;
    }

    // 如果是切片语义匹配，还需要选择知识库
    if (matchType === 'chunkTextMatch' && !knowledgeBaseId) {
        alert('请选择知识库');
        return;
    }

    // 构造请求数据
    const requestData = {
        task_id: taskId,
        match_type: matchType,
        search_type: searchType
    };

    // 如果是切片语义匹配，添加知识库ID
    if (matchType === 'chunkTextMatch') {
        requestData.knowledge_base_id = knowledgeBaseId;
    }

    // 发送更新请求
    fetch('/local_knowledge_detail/task/metric/update_match_type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('匹配方式更新成功');
            // 隐藏更新区域
            document.getElementById('matchTypeUpdateSection').style.display = 'none';
            // 重新尝试启动计算
            confirmCalculationType();
        } else {
            alert('更新失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('更新匹配方式时出错:', error);
        alert('更新匹配方式时发生错误');
    });
}

// 显示报告查看对话框
function showReportDialog(metricTaskId) {
    // 存储当前计算任务ID
    document.getElementById('currentTaskId').value = metricTaskId;

    // 显示模态框
    document.getElementById('reportModal').style.display = 'block';

    // 加载报告内容
    loadReportContent(metricTaskId);
}

// 隐藏报告查看对话框
function hideReportModal() {
    document.getElementById('reportModal').style.display = 'none';
}

// 定义映射关系
const searchTypeMap = {
    'vectorSearch': '向量检索',
    'hybridSearch': '混合检索',
    'augmentedSearch': '增强检索'
};

const matchTypeMap = {
    'chunkTextMatch': '切片语义匹配',
    'chunkIdMatch': '切片ID匹配'
};

// 获取匹配方式的中文显示
function getMatchTypeDisplay(matchType) {
    return matchTypeMap[matchType] || matchType;
}

// 获取搜索类型的中文显示
function getSearchTypeDisplay(searchType) {
    return searchTypeMap[searchType] || searchType;
}

// 加载报告内容
function loadReportContent(metricTaskId) {
    fetch(`/local_knowledge_detail/task/metric/get_report?metric_task_id=${metricTaskId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const reportContentDiv = document.getElementById('reportContent');
        if (data.success) {
            if (data.data && data.data.length > 0) {
                // 显示报告列表表格
                let reportRows = '';
                data.data.forEach(report => {
                    reportRows += `
                        <tr>
                            <td>
                                <div class="report-name clickable-report" onclick="openReport('${data.knowledgeBaseId}', '${report.filepath || 'N/A'}')">${report.filepath || 'N/A'}</div>
                                <div class="report-id">ID: ${report.report_id || 'N/A'}</div>
                            </td>
                            <td>${searchTypeMap[report.search_type]  || 'N/A'}</td>
                            <td>${matchTypeMap[report.match_type]  || 'N/A'}</td>
                            <td>${report.status || 'N/A'}</td>
                            <td>${report.error_msg || 'N/A'}</td>
                            <td>
                                <button class="action-btn delete-btn" onclick="deleteReport('${report.report_id}', this)">删除</button>
                            </td>
                        </tr>
                    `;
                });

                reportContentDiv.innerHTML = `
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>报告名称/ID</th>
                                <th>召回方式</th>
                                <th>匹配方式</th>
                                <th>状态</th>
                                <th>错误信息</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${reportRows}
                        </tbody>
                    </table>
                `;
            } else {
                reportContentDiv.innerHTML = '<p>暂无报告数据</p>';
            }
        } else {
            reportContentDiv.innerHTML = `<p>加载报告失败: ${data.message}</p>`;
        }
    })
    .catch(error => {
        console.error('加载报告内容时出错:', error);
        const reportContentDiv = document.getElementById('reportContent');
        reportContentDiv.innerHTML = `<p>加载报告内容时发生错误: ${error.message}</p>`;
    });
}

// 打开报告页面
function openReport(knowledgeBaseId, filepath) {
    // 构建报告页面URL
    const reportUrl = `/report/${knowledgeBaseId}/${filepath}`;
    // 在新窗口或标签页中打开报告
    window.open(reportUrl, '_blank');
}

// 删除报告
function deleteReport(reportId, buttonElement) {
    if (confirm('确定要删除这个报告吗？此操作不可撤销。')) {
        fetch('/local_knowledge_detail/task/metric/delete_report', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                report_id: reportId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('报告删除成功');
                // 重新加载报告列表
                const taskId = document.getElementById('currentTaskId').value;
                loadReportContent(taskId);
            } else {
                alert('删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('删除报告时出错:', error);
            alert('删除报告时发生错误: ' + error.message);
        });
    }
}

// 导出报告
function exportReport() {
    const taskId = document.getElementById('currentTaskId').value;
    alert(`正在导出任务 ${taskId} 的报告...`);
    // TODO: 实现报告导出功能
}

// 显示创建指标任务对话框
function showCreateMetricTaskDialog() {
    // 重置表单
    document.getElementById('taskSelect').innerHTML = '<option value="" disabled selected>请选择任务</option>';
    document.getElementById('knowledgeBaseGroup').style.display = 'none';
    document.getElementById('knowledgeBaseSelect').innerHTML = '<option value="" disabled selected>请选择知识库</option>';

    // 加载已完成的标注任务
    loadCompletedTasks();

    // 显示模态框
    document.getElementById('createMetricTaskModal').style.display = 'block';
}

// 处理匹配方式变化
function handleMatchTypeChange() {
    const matchType = document.getElementById('matchTypeSelect').value;
    const knowledgeBaseGroup = document.getElementById('knowledgeBaseGroup');
    const knowledgeBaseSelect = document.getElementById('knowledgeBaseSelect');

    if (matchType === 'chunkTextMatch') {
        // 显示知识库选择
        knowledgeBaseGroup.style.display = 'block';
        // 加载绑定的知识库
        loadBoundKnowledgeBases();
    } else {
        // 隐藏知识库选择
        knowledgeBaseGroup.style.display = 'none';
        knowledgeBaseSelect.innerHTML = '<option value="" disabled selected>请选择知识库</option>';
    }
}

// 加载已完成的标注任务
function loadCompletedTasks() {
    const taskSelect = document.getElementById('taskSelect');

    fetch('/local_knowledge_detail/task/metric/completed_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            local_knowledge_id: currentKnowledgeId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            taskSelect.innerHTML = '<option value="" disabled selected>请选择任务</option>';
            (data.data || []).forEach(task => {
                const option = document.createElement('option');
                option.value = task.task_id;
                option.textContent = `${task.task_name} (${task.task_id})`;
                taskSelect.appendChild(option);
            });
        } else {
            taskSelect.innerHTML = '<option value="" disabled>加载任务失败</option>';
        }
    })
    .catch(error => {
        console.error('加载任务列表时出错:', error);
        taskSelect.innerHTML = '<option value="" disabled>加载失败</option>';
    });
}

// 加载绑定的知识库
function loadBoundKnowledgeBases() {
    const knowledgeBaseSelect = document.getElementById('knowledgeBaseSelect');
    const knoId = currentKnowledgeId;

    if (!knoId) {
        knowledgeBaseSelect.innerHTML = '<option value="" disabled>未找到本地知识库ID</option>';
        return;
    }

    fetch('/local_knowledge/bindings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kno_id: knoId
        })
    })
    .then(response => response.json())
    .then(data => {
        knowledgeBaseSelect.innerHTML = '<option value="" disabled selected>请选择知识库</option>';
        if (Array.isArray(data) && data.length > 0) {
            data.forEach(binding => {
                if (binding.bind_status === 2) { // 已绑定状态
                    const option = document.createElement('option');
                    option.value = binding.knowledge_id;
                    option.textContent = binding.knowledge_name || binding.knowledge_id;
                    knowledgeBaseSelect.appendChild(option);
                }
            });
        } else {
            knowledgeBaseSelect.innerHTML = '<option value="" disabled>暂无绑定的知识库</option>';
        }
    })
    .catch(error => {
        console.error('加载知识库列表时出错:', error);
        knowledgeBaseSelect.innerHTML = '<option value="" disabled>加载失败</option>';
    });
}

// 创建指标任务
function createMetricTask() {
    const matchType = document.getElementById('matchTypeSelect').value;
    const taskId = document.getElementById('taskSelect').value;
    const knowledgeBaseId = document.getElementById('knowledgeBaseSelect').value;

    // 验证必填字段
    if (!matchType) {
        alert('请选择匹配方式');
        return;
    }

    if (!taskId) {
        alert('请选择标注任务');
        return;
    }

    // 如果是切片语义匹配，还需要选择知识库
    if (matchType === 'chunkTextMatch' && !knowledgeBaseId) {
        alert('请选择知识库');
        return;
    }

    // 构造请求数据
    const requestData = {
        match_type: matchType,
        task_id: taskId
    };

    // 如果是切片语义匹配，添加知识库ID
    if (matchType === 'chunkTextMatch') {
        requestData.knowledge_base_id = knowledgeBaseId;
    }

    // 发送创建请求
    fetch('/local_knowledge_detail/task/metric/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('指标任务创建成功');
            hideCreateMetricTaskModal();
            // 重新加载任务列表
            loadTaskList();
        } else {
            alert('创建失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('创建指标任务时出错:', error);
        alert('创建指标任务时发生错误');
    });
}

// 隐藏创建指标任务模态框
function hideCreateMetricTaskModal() {
    document.getElementById('createMetricTaskModal').style.display = 'none';
}

// 删除指标任务函数
function deleteMetricTask(metricTaskId) {
    if (!metricTaskId) {
        alert('任务ID不能为空');
        return;
    }

    // 弹出确认对话框
    if (!confirm('确定要删除此任务吗？将同时删除相关的报告文件和数据库记录。')) {
        return;
    }

    // 发送删除请求
    fetch('/local_knowledge_detail/task/metric/delete_task', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            metric_task_id: metricTaskId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('任务删除成功');
            // 刷新任务列表
            loadTaskList();
        } else {
            throw new Error(data.message || '删除任务失败');
        }
    })
    .catch(error => {
        console.error('删除任务时出错:', error);
        alert('删除任务失败: ' + error.message);
    });
}
