// 问题集管理相关的JavaScript代码
let currentKnoIdForQuestions = null;
let currentQuestionSetId = null; // 全局变量存储当前问题集ID

// 初始化问题集管理页面
function initQuestionTab(knoId) {
    currentKnoIdForQuestions = knoId;
    loadQuestionSets();
}

// 加载问题集列表
function loadQuestionSets() {
    fetch(`/local_knowledge_detail/question/set/list?knowledge_id=${currentKnoIdForQuestions}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderQuestionSetList(data.data);
            } else {
                console.error('获取问题集列表失败:', data.message);
                document.getElementById('questionSetList').innerHTML = `<div class="error">加载失败: ${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('请求问题集列表时出错:', error);
            document.getElementById('questionSetList').innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
        });
}

// 渲染问题集列表
function renderQuestionSetList(questionSets) {
    const container = document.getElementById('questionSetList');
    
    if (!questionSets || questionSets.length === 0) {
        container.innerHTML = `<div class="empty-state">暂无问题集，请点击"创建问题集"按钮创建</div>`;
        return;
    }
    
    let html = '';
    questionSets.forEach(set => {
        html += `
            <div class="question-set-item">
                <div class="question-set-header">
                    <div>
                        <div class="question-set-title">${set.question_name}</div>
                        <div class="question-set-meta">ID: ${set.question_id} | 类型: ${set.question_set_type || 'N/A'} | 创建时间: ${set.created_at || 'N/A'}</div>
                    </div>
                    <div class="question-set-actions">
                        <button class="question-set-expand-btn" onclick="toggleQuestionSetDetails('${set.question_id}', this)">展开</button>
                        <button class="question-set-create-btn" onclick="event.stopPropagation(); showCreateQuestionForSet('${set.question_id}', '${set.question_set_type || 'basic'}')">创建问题</button>
                        <button class="question-set-edit-btn" onclick="event.stopPropagation(); editQuestionSet('${set.question_id}')">编辑</button>
                        <button class="question-set-delete-btn" onclick="event.stopPropagation(); deleteQuestionSet('${set.question_id}', '${set.question_name}')">删除</button>
                    </div>
                </div>
                <div class="expandable-content" id="questionSetContent-${set.question_id}">
                    <!-- 问题列表将在这里动态加载 -->
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 展开/收起问题集详情
function toggleQuestionSetDetails(setId, btnElement) {
    const contentElement = document.getElementById(`questionSetContent-${setId}`);
    const isExpanded = contentElement.classList.contains('expanded');
    
    // 收起所有其他展开的内容
    const allContents = document.querySelectorAll('.expandable-content');
    allContents.forEach(content => {
        content.classList.remove('expanded');
    });
    
    // 收起所有展开按钮的文本
    const allExpandButtons = document.querySelectorAll('.question-set-expand-btn');
    allExpandButtons.forEach(btn => {
        btn.textContent = '展开';
    });
    
    // 如果当前内容是展开的，则收起；否则展开并加载问题列表
    if (isExpanded) {
        contentElement.classList.remove('expanded');
        if (btnElement) {
            btnElement.textContent = '展开';
        }
    } else {
        // 展开当前内容
        contentElement.classList.add('expanded');
        if (btnElement) {
            btnElement.textContent = '收起';
        }
        
        // 加载问题列表
        loadQuestionsForSet(setId, contentElement);
    }
}

// 加载问题集下的问题列表
function loadQuestionsForSet(setId, containerElement) {
    if (!containerElement) {
        containerElement = document.getElementById(`questionSetContent-${setId}`);
    }
    
    containerElement.innerHTML = `<div class="loading">正在加载问题...</div>`;
    
    // 获取问题集详情以获取问题类型
    fetch(`/local_knowledge_detail/question/set/detail?set_id=${setId}`)
        .then(response => response.json())
        .then(detailData => {
            if (detailData.success) {
                const questionSetType = detailData.data.question_set_type || 'basic';
                
                // 获取该问题集下的所有问题 - 改为POST请求并使用JSON格式
                fetch('/local_knowledge_detail/question/list', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        set_id: setId,
                        question_type: questionSetType
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        renderQuestionList(data.data, containerElement, questionSetType);  // 传递问题集类型
                    } else {
                        containerElement.innerHTML = `<div class="error">加载问题失败: ${data.message}</div>`;
                    }
                })
                .catch(error => {
                    containerElement.innerHTML = `<div class="error">加载问题时出错: ${error.message}</div>`;
                });
            } else {
                containerElement.innerHTML = `<div class="error">获取问题集详情失败: ${detailData.message}</div>`;
            }
        })
        .catch(error => {
            containerElement.innerHTML = `<div class="error">获取问题集详情时出错: ${error.message}</div>`;
        });
}

// 渲染问题列表
function renderQuestionList(questions, containerElement, questionSetType) {  // 添加参数
    if (!questions || questions.length === 0) {
        containerElement.innerHTML = `<div class="empty-state">暂无问题，请创建问题</div>`;
        return;
    }
    
    let html = `
        <div class="question-list-section">
            <table class="question-table" style="margin-top: 15px;">
                <thead>
                    <tr>
                        <th>问题类型</th>
                        <th>问题ID</th>
                        <th>问题正文</th>
                        <th>问题切片</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    questions.forEach(question => {
        const type = question.question_type || 'unknown';
        const questionId = question.question_id || 'N/A';
        const content = question.question_content || '无内容';
        const chunks = Array.isArray(question.chunk_ids) ? question.chunk_ids.join(', ') : (question.chunk_ids || '无关联切片');
        
        html += `
                <tr class="question-row">
                    <td class="question-type" data-label="问题类型">
                        <span class="question-type-tag ${type}">${getTypeDisplayName(type)}</span>
                    </td>
                    <td class="question-id" data-label="问题ID">${questionId}</td>
                    <td class="question-content" data-label="问题正文">${content}</td>
                    <td class="question-chunks" data-label="问题切片">${chunks}</td>
                    <td class="question-actions" data-label="操作">
                        <button class="question-detail-btn" onclick="viewQuestionDetail('${question.question_id}', '${questionSetType}')">详情</button>
                        <button class="question-edit-btn" onclick="editQuestion('${question.question_id}', '${questionSetType}')">编辑</button>
                        <button class="question-delete-btn" onclick="deleteQuestion('${question.question_id}', '${questionSetType}')">删除</button>
                    </td>
                </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    containerElement.innerHTML = html;
}

// 获取问题类型显示名称
function getTypeDisplayName(type) {
    const typeMap = {
        'factual': '事实型',
        'contextual': '上下文型',
        'conceptual': '概念型',
        'reasoning': '推理型',
        'application': '应用型',
        'basic': '基础问题',
        'detailed': '详细问题',
        'mechanism': '机制问题',
        'thematic': '主题问题'
    };
    return typeMap[type] || type;
}

// 显示创建问题集模态框
function showCreateQuestionSetModal() {
    // 重置模态框标题
    const modalHeader = document.querySelector('#createQuestionSetModal .modal-header h2');
    if (modalHeader) {
        modalHeader.textContent = '创建问题集';
    }
    
    // 重置按钮文本
    const submitButton = document.getElementById('questionSetSubmitBtn');
    if (submitButton) {
        submitButton.textContent = '创建';
        submitButton.onclick = function() { createQuestionSet(); };
    }
    
    document.getElementById('questionSetName').value = '';
    document.getElementById('questionSetType').value = 'basic';
    
    // 清除编辑状态
    window.currentEditingSetId = null;
    
    document.getElementById('createQuestionSetModal').style.display = 'block';
}

// 隐藏创建问题集模态框
function hideCreateQuestionSetModal() {
    document.getElementById('createQuestionSetModal').style.display = 'none';
    
    // 重置模态框标题
    const modalHeader = document.querySelector('#createQuestionSetModal .modal-header h2');
    if (modalHeader) {
        modalHeader.textContent = '创建问题集';
    }
    
    // 重置按钮文本
    const submitButton = document.getElementById('questionSetSubmitBtn');
    if (submitButton) {
        submitButton.textContent = '创建';
    }
    
    // 清除编辑状态
    window.currentEditingSetId = null;
    
    // 清空表单
    document.getElementById('questionSetName').value = '';
    document.getElementById('questionSetType').value = 'basic';
}

// 创建或更新问题集（复用同一个函数）
function createQuestionSet() {
    const setName = document.getElementById('questionSetName').value;
    const setType = document.getElementById('questionSetType').value;
    
    if (!setName.trim()) {
        DialogManager.showWarning('请输入问题集名称');
        return;
    }
    
    // 检查是否是编辑模式
    if (window.currentEditingSetId) {
        // 编辑模式
        fetch('/local_knowledge_detail/question/set/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                set_id: window.currentEditingSetId,
                set_name: setName,
                set_type: setType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                DialogManager.showSuccess('问题集更新成功', () => {
                    hideCreateQuestionSetModal();
                    loadQuestionSets();
                });
            } else {
                DialogManager.showError('更新失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('更新问题集时出错:', error);
            DialogManager.showError('更新问题集时发生错误');
        });
        
        // 清除编辑状态
        window.currentEditingSetId = null;
    } else {
        // 创建模式
        fetch('/local_knowledge_detail/question_set/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                knowledge_id: currentKnoIdForQuestions,
                set_name: setName,
                set_type: setType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                DialogManager.showSuccess('问题集创建成功', () => {
                    hideCreateQuestionSetModal();
                    loadQuestionSets();
                });
            } else {
                DialogManager.showError('创建失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('创建问题集时出错:', error);
            DialogManager.showError('创建问题集时发生错误');
        });
    }
}

// 编辑问题集
function editQuestionSet(setId) {
    // 首先获取问题集当前信息
    fetch(`/local_knowledge_detail/question/set/detail?set_id=${setId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const setInfo = data.data;
                
                // 填充表单
                document.getElementById('questionSetName').value = setInfo.question_name;
                document.getElementById('questionSetType').value = setInfo.question_set_type || 'basic';  // 使用正确的字段名
                
                // 修改模态框标题
                const modalHeader = document.querySelector('#createQuestionSetModal .modal-header h2');
                if (modalHeader) {
                    modalHeader.textContent = '编辑问题集';
                }
                
                // 修改按钮文本
                const submitButton = document.getElementById('questionSetSubmitBtn');
                if (submitButton) {
                    submitButton.textContent = '确定';
                }
                
                // 存储当前问题集ID
                window.currentEditingSetId = setId;
                
                // 显示模态框
                document.getElementById('createQuestionSetModal').style.display = 'block';
            } else {
                DialogManager.showError('获取问题集详情失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('获取问题集详情时出错:', error);
            DialogManager.showError('获取问题集详情时发生错误');
        });
}

// 删除问题集
function deleteQuestionSet(setId, setName) {
    DialogManager.confirm(
        `确定要删除问题集 "${setName}" 吗？此操作不可撤销。`,
        async () => {
            try {
                const response = await fetch('/local_knowledge_detail/question/set/delete', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        set_id: setId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    DialogManager.showSuccess('问题集删除成功', () => {
                        loadQuestionSets();
                    });
                } else {
                    DialogManager.showError('删除失败：' + data.message);
                }
            } catch (error) {
                console.error('删除问题集时出错:', error);
                DialogManager.showError('删除问题集时发生错误');
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}

// 查看问题集详情
function viewQuestionSet(setId) {
    fetch(`/local_knowledge_detail/question/set/detail?set_id=${setId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const setInfo = data.data;
                
                document.getElementById('questionSetDetailTitle').textContent = setInfo.question_name;
                document.getElementById('detailSetName').textContent = setInfo.question_name;
                document.getElementById('detailSetType').textContent = getTypeDisplayName(setInfo.question_set_type || setInfo.set_type || 'basic');
                document.getElementById('detailSetCreatedAt').textContent = setInfo.created_at || 'N/A';
                
                // 记录当前问题集ID
                currentQuestionSetId = setId;
                
                // 加载问题列表 - 这里也需要获取问题集类型
                const container = document.getElementById('questionList');
                loadQuestionsForSet(setId, container);
            } else {
                DialogManager.showError('获取问题集详情失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('获取问题集详情时出错:', error);
            DialogManager.showError('获取问题集详情时发生错误');
        });
}

// 为特定问题集显示创建问题模态框
function showCreateQuestionForSet(setId, setType) {
    // 设置当前问题集ID，以便在创建问题时使用
    currentQuestionSetId = setId;
    currentQuestionSetType = setType; // 存储问题集类型
    
    // 清空表单
    document.getElementById('questionType').value = 'factual';
    document.getElementById('questionContent').value = '';
    document.getElementById('chunkIds').value = '';
    
    // 修改模态框标题
    const modalHeader = document.querySelector('#createQuestionModal .modal-header h2');
    if (modalHeader) {
        modalHeader.textContent = '为问题集创建问题';
    }
    
    // 清除编辑状态
    window.currentEditingQuestionId = null;
    window.currentEditingQuestionType = null;
    
    // 显示模态框
    document.getElementById('createQuestionModal').style.display = 'block';
}

// 隐藏问题集详情模态框
function hideQuestionSetDetailModal() {
    document.getElementById('questionSetDetailModal').style.display = 'none';
    // 清除当前问题集ID
    currentQuestionSetId = null;
}

// 显示创建问题模态框
function showCreateQuestionModal() {
    document.getElementById('questionType').value = 'factual';
    document.getElementById('questionContent').value = '';
    document.getElementById('chunkIds').value = '';
    
    // 重置模态框标题
    const modalHeader = document.querySelector('#createQuestionModal .modal-header h2');
    if (modalHeader) {
        modalHeader.textContent = '创建问题';
    }
    
    // 重置按钮文本
    const submitButton = document.getElementById('questionSubmitBtn');
    if (submitButton) {
        submitButton.textContent = '创建';
    }
    
    document.getElementById('createQuestionModal').style.display = 'block';
}

// 隐藏创建问题模态框
function hideCreateQuestionModal() {
    document.getElementById('createQuestionModal').style.display = 'none';
    
    // 重置模态框标题
    const modalHeader = document.querySelector('#createQuestionModal .modal-header h2');
    if (modalHeader) {
        modalHeader.textContent = '创建问题';
    }
    
    // 重置按钮文本
    const submitButton = document.getElementById('questionSubmitBtn');
    if (submitButton) {
        submitButton.textContent = '创建';
    }
    
    // 清除编辑状态
    window.currentEditingQuestionId = null;
    window.currentEditingQuestionType = null;
    
    // 清空表单
    document.getElementById('questionType').value = 'factual';
    document.getElementById('questionContent').value = '';
    document.getElementById('chunkIds').value = '';
}

// 创建或更新问题（复用同一个函数）
function createQuestion() {
    const questionType = document.getElementById('questionType').value;
    const questionContent = document.getElementById('questionContent').value;
    const chunkIdsValue = document.getElementById('chunkIds').value;
    
    if (!questionContent.trim()) {
        DialogManager.showWarning('请输入问题内容');
        return;
    }
    
    // 解析切片ID（逗号分隔）
    const chunkIds = chunkIdsValue ? chunkIdsValue.split(',').map(id => id.trim()).filter(id => id) : [];
    
    // 检查是否是编辑模式
    if (window.currentEditingQuestionId && window.currentEditingQuestionType) {
        // 编辑模式
        fetch('/local_knowledge_detail/question/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_id: window.currentEditingQuestionId,
                question_type: window.currentEditingQuestionType,
                question_content: questionContent,
                chunk_ids: chunkIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                DialogManager.showSuccess('问题更新成功', () => {
                    hideCreateQuestionModal();
                            
                    // 如果在问题集详情模态框中，刷新问题列表
                    if (document.getElementById('questionSetDetailModal').style.display === 'block') {
                        const container = document.getElementById('questionList');
                        if (currentQuestionSetId) {
                            loadQuestionsForSet(currentQuestionSetId, container);
                        }
                    } else {
                        // 如果在主页面，刷新当前展开的问题集
                        if (currentQuestionSetId) {
                            const contentElement = document.getElementById(`questionSetContent-${currentQuestionSetId}`);
                            if (contentElement && contentElement.classList.contains('expanded')) {
                                loadQuestionsForSet(currentQuestionSetId, contentElement);
                            }
                        } else {
                            loadQuestionSets();
                        }
                    }
                });
            } else {
                DialogManager.showError('更新失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('更新问题时出错:', error);
            DialogManager.showError('更新问题时发生错误');
        });
        
        // 清除编辑状态
        window.currentEditingQuestionId = null;
        window.currentEditingQuestionType = null;
    } else {
        // 创建模式
        // 获取当前打开的问题集 ID
        const openQuestionSetId = getCurrentOpenQuestionSetId();
        if (!openQuestionSetId) {
            DialogManager.showWarning('请先选择一个问题集');
            return;
        }
        
        // 获取当前问题集类型（从全局变量或问题集详情中获取）
        const questionSetType = currentQuestionSetType || 'basic'; // 默认为基础类型
        
        // 发送创建问题请求
        fetch('/local_knowledge_detail/question/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                set_id: openQuestionSetId,
                question_set_type: questionSetType,
                question_type: questionType,
                question_content: questionContent,
                chunk_ids: chunkIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                DialogManager.showSuccess('问题创建成功', () => {
                    hideCreateQuestionModal();
                            
                    // 如果在问题集详情模态框中，刷新问题列表
                    if (document.getElementById('questionSetDetailModal').style.display === 'block') {
                        const container = document.getElementById('questionList');
                        if (currentQuestionSetId) {
                            loadQuestionsForSet(currentQuestionSetId, container);
                        }
                    } else {
                        // 如果在主页面，刷新当前展开的问题集
                        if (openQuestionSetId) {
                            const contentElement = document.getElementById(`questionSetContent-${openQuestionSetId}`);
                            if (contentElement && contentElement.classList.contains('expanded')) {
                                loadQuestionsForSet(openQuestionSetId, contentElement);
                            }
                        } else {
                            loadQuestionSets();
                        }
                    }
                });
            } else {
                DialogManager.showError('创建失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('创建问题时出错:', error);
            DialogManager.showError('创建问题时发生错误');
        });
    }
}

// 获取当前打开的问题集ID（用于判断在哪个问题集中创建问题）
function getCurrentOpenQuestionSetId() {
    // 优先检查全局变量中的问题集ID
    if (currentQuestionSetId) {
        return currentQuestionSetId;
    }
    
    // 检查页面上是否有展开的问题集
    const expandedContent = document.querySelector('.expandable-content.expanded');
    if (expandedContent) {
        const idMatch = expandedContent.id.match(/questionSetContent-(.*)/);
        if (idMatch) {
            return idMatch[1];
        }
    }
    
    return null;
}

// 查看问题详情
function viewQuestionDetail(questionId, questionSetType) {
    fetch('/local_knowledge_detail/question/detail', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question_id: questionId,
            question_set_type: questionSetType
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const question = data.data;
                DialogManager.showInfo(`问题详情:\n类型：${question.question_type}\n内容：${question.question_content || 'N/A'}\n切片 ID: ${question.chunk_ids || 'N/A'}`);
            } else {
                DialogManager.showError('获取问题详情失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('获取问题详情时出错:', error);
            DialogManager.showError('获取问题详情时发生错误');
        });
}

// 编辑问题
function editQuestion(questionId, questionSetType) {
    // 首先获取问题当前信息
    fetch('/local_knowledge_detail/question/detail', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question_id: questionId,
            question_set_type: questionSetType
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const question = data.data;
                
                // 填充表单
                document.getElementById('questionType').value = question.question_type;
                document.getElementById('questionContent').value = question.question_content || '';
                document.getElementById('chunkIds').value = Array.isArray(question.chunk_ids) ? question.chunk_ids.join(',') : question.chunk_ids || '';
                
                // 修改模态框标题
                const modalHeader = document.querySelector('#createQuestionModal .modal-header h2');
                if (modalHeader) {
                    modalHeader.textContent = '编辑问题';
                }
                
                // 修改按钮文本
                const submitButton = document.getElementById('questionSubmitBtn');
                if (submitButton) {
                    submitButton.textContent = '确定';
                }
                
                // 存储当前问题ID和类型
                window.currentEditingQuestionId = questionId;
                window.currentEditingQuestionType = questionSetType;  // 修正：保存的是questionSetType
                
                // 显示模态框
                document.getElementById('createQuestionModal').style.display = 'block';
            } else {
                DialogManager.showError('获取问题详情失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('获取问题详情时出错:', error);
            DialogManager.showError('获取问题详情时发生错误');
        });
}

// 删除问题
function deleteQuestion(questionId, questionSetType) {
    DialogManager.confirm(
        '确定要删除这个问题吗？此操作不可撤销。',
        async () => {
            try {
                const response = await fetch('/local_knowledge_detail/question/delete', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question_id: questionId,
                        question_set_type: questionSetType
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    DialogManager.showSuccess('问题删除成功', () => {
                        // 刷新问题列表
                        if (document.getElementById('questionSetDetailModal').style.display === 'block') {
                            const container = document.getElementById('questionList');
                            if (currentQuestionSetId) {
                                loadQuestionsForSet(currentQuestionSetId, container);
                            }
                        } else {
                            if (currentQuestionSetId) {
                                const contentElement = document.getElementById(`questionSetContent-${currentQuestionSetId}`);
                                if (contentElement && contentElement.classList.contains('expanded')) {
                                    loadQuestionsForSet(currentQuestionSetId, contentElement);
                                }
                            } else {
                                loadQuestionSets();
                            }
                        }
                    });
                } else {
                    DialogManager.showError('删除失败：' + data.message);
                }
            } catch (error) {
                console.error('删除问题时出错:', error);
                DialogManager.showError('删除问题时发生错误');
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}