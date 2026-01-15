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
        row.innerHTML = `<td colspan="5" style="text-align: center;">暂无指标任务</td>`;
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
        <td>${task.task_id ? escapeHtml(task.task_id) : 'N/A'}</td>
        <td>${task.task_name ? escapeHtml(task.task_name) : 'N/A'}</td>
        <td>${task.annotation_type ? escapeHtml(task.annotation_type) : '未设置'}</td>
        <td><span class="${statusClass}">${task.status ? escapeHtml(task.status) : '未知'}</span></td>
        <td class="task-actions-cell">
            <button class="task-action-btn calculate-btn" onclick="showCalculationDialog('${task.task_id ? escapeHtml(task.task_id) : ''}')">
                质量计算
            </button>
            <button class="task-action-btn report-btn" onclick="showReportDialog('${task.task_id ? escapeHtml(task.task_id) : ''}')">
                查看报告
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

// 显示质量计算方式选择对话框
function showCalculationDialog(taskId) {
    // 存储当前任务ID
    document.getElementById('currentTaskId').value = taskId;

    // 显示模态框
    document.getElementById('calculationModal').style.display = 'block';
}

// 隐藏质量计算方式选择对话框
function hideCalculationModal() {
    document.getElementById('calculationModal').style.display = 'none';
}

// 确认计算类型
function confirmCalculationType() {
    const selectedType = document.querySelector('input[name="searchType"]:checked').value;
    const taskId = document.getElementById('currentTaskId').value;

    fetch('/local_knowledge_detail/task/metric/start_calculation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_id: taskId,
            search_type: selectedType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('质量计算已启动');
            hideCalculationModal();
            // 重新加载任务列表
            loadTaskList();
        } else {
            alert('启动计算失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('启动质量计算时出错:', error);
        alert('启动质量计算时发生错误');
    });
}

// 显示报告查看对话框
function showReportDialog(taskId) {
    // 存储当前任务ID
    document.getElementById('currentTaskId').value = taskId;

    // 显示模态框
    document.getElementById('reportModal').style.display = 'block';

    // 加载报告内容
    loadReportContent(taskId);
}

// 隐藏报告查看对话框
function hideReportModal() {
    document.getElementById('reportModal').style.display = 'none';
}

// 加载报告内容
function loadReportContent(taskId) {
    fetch(`/local_knowledge_detail/task/metric/get_report?task_id=${taskId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const reportContentDiv = document.getElementById('reportContent');
        if (data.success) {
            // TODO: 实现具体的报告内容展示逻辑
            reportContentDiv.innerHTML = `
                <h4>任务ID: ${taskId}</h4>
                <p>状态: ${data.data.status}</p>
                <p>报告路径: ${data.data.report_path || '报告尚未生成'}</p>
                <div class="report-placeholder">
                    <p>这里是质量评估报告的详细内容...</p>
                    <p>包括质量指标、检索效果对比、可视化图表等。</p>
                </div>
            `;
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

// 导出报告
function exportReport() {
    const taskId = document.getElementById('currentTaskId').value;
    alert(`正在导出任务 ${taskId} 的报告...`);
    // TODO: 实现报告导出功能
}

// 显示创建指标任务对话框
function showCreateMetricTaskDialog() {
    // 先加载已完成的标注任务列表
    loadCompletedAnnotationTasks();
    
    // 显示模态框
    document.getElementById('createMetricTaskModal').style.display = 'block';
}

// 隐藏创建指标任务对话框
function hideCreateMetricTaskModal() {
    document.getElementById('createMetricTaskModal').style.display = 'none';
}

// 加载已完成的标注任务列表
function loadCompletedAnnotationTasks() {
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
            renderCompletedAnnotationTasks(data.data);
        } else {
            console.error('获取已完成的标注任务失败:', data.message);
            const taskListElement = document.getElementById('completedTaskList');
            if (taskListElement) {
                taskListElement.innerHTML = `<p style="color: red;">获取任务列表失败: ${data.message}</p>`;
            }
        }
    })
    .catch(error => {
        console.error('请求已完成的标注任务时出错:', error);
        const taskListElement = document.getElementById('completedTaskList');
        if (taskListElement) {
            taskListElement.innerHTML = `<p style="color: red;">网络请求错误: ${error.message}</p>`;
        }
    });
}

// 渲染已完成的标注任务列表
function renderCompletedAnnotationTasks(tasks) {
    const taskListElement = document.getElementById('completedTaskList');
    if (!taskListElement) {
        console.error('找不到已完成任务列表元素');
        return;
    }
    
    if (tasks && tasks.length > 0) {
        let html = '';
        tasks.forEach(task => {
            html += `
                <div class="completed-task-item">
                    <input type="radio" name="selectedTask" value="${task.task_id}" id="task_${task.task_id}">
                    <label for="task_${task.task_id}">
                        <strong>${task.task_name}</strong> 
                        (<em>${task.knowledge_base_name}</em> - ${task.question_set_name})
                        <br>
                        <small>进度: ${task.annotated_chunks}/${task.total_chunks} | 状态: ${task.task_status}</small>
                    </label>
                </div>
            `;
        });
        taskListElement.innerHTML = html;
    } else {
        taskListElement.innerHTML = '<p>暂无已完成的标注任务</p>';
    }
}

// 创建指标任务
function createMetricTask() {
    const selectedTaskId = document.querySelector('input[name="selectedTask"]:checked');
    if (!selectedTaskId) {
        alert('请先选择一个已完成的标注任务');
        return;
    }
    
    const taskId = selectedTaskId.value;
    
    // 将任务信息写入ai_metric_tasks表
    fetch('/local_knowledge_detail/task/metric/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_id: taskId,
            annotation_type: 'metric_task' // 标记这是一个指标任务
        })
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