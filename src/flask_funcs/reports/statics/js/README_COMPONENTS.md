# 前端公共组件使用指南

## 概述

本项目抽取了各模块的通用功能，形成了一套完整的前端公共组件库，用于减少代码重复、提高开发效率。

## 组件文件结构

```
src/flask_funcs/reports/statics/js/
├── common_components.js      # 基础组件（分页、搜索、筛选、表格等）
├── ui_components.js          # UI 组件（对话框、表单验证、API 助手等）
├── environment.js            # 环境管理页面专用
├── qa_groups.js              # QA 组管理页面专用
└── ...                       # 其他页面专用脚本
```

## 基础组件 (common_components.js)

### 1. PaginationComponent - 分页组件

```javascript
// 创建分页实例
const pagination = new PaginationComponent('paginationArea', (page, pageSize) => {
    // 页码变化时的回调
    loadData(page, pageSize);
});

// 更新分页信息
pagination.update(totalItems, currentPage, pageSize);

// 跳转方法
pagination.goToPage(5);        // 跳转到第 5 页
pagination.goToPrevPage();     // 上一页
pagination.goToNextPage();     // 下一页
pagination.goToFirstPage();    // 首页
pagination.goToLastPage();     // 末页
pagination.changePageSize(50); // 改变每页数量
```

### 2. SearchComponent - 搜索组件

```javascript
// 创建搜索实例
const search = new SearchComponent('searchInput', 'searchBtn', (keyword) => {
    // 搜索回调
    searchByKeyword(keyword);
});

// 获取/设置关键词
const keyword = search.getKeyword();
search.setKeyword('新的关键词');

// 清空搜索
search.clear();
```

### 3. FilterComponent - 筛选组件

```javascript
// 创建筛选实例（支持多个筛选器）
const filter = new FilterComponent(['filterType', 'filterStatus'], (filterValues) => {
    // 筛选变化回调
    applyFilters(filterValues);
});

// 获取筛选值
const values = filter.getFilterValues();

// 重置筛选
filter.reset();
```

### 4. ModalComponent - 模态框组件

```javascript
// 创建模态框实例
const modal = new ModalComponent('myModal');

// 显示/隐藏
modal.show();
modal.hide();
modal.toggle();

// 设置内容
modal.setContent('<div>新的内容</div>');
```

### 5. TableComponent - 表格组件

```javascript
// 定义列配置
const columns = [
    { key: 'id', label: 'ID' },
    { 
        key: 'name', 
        label: '名称',
        formatter: (value, row) => `<a href="/detail/${row.id}">${value}</a>`
    },
    {
        key: 'status',
        label: '状态',
        formatter: (value) => value ? '✅ 启用' : '❌ 停用'
    }
];

// 创建表格实例
const table = new TableComponent('myTable', columns);

// 渲染数据
table.render(dataArray);

// 排序
table.sort('name');
```

### 6. CommonUtils - 工具函数

```javascript
// 错误提示
CommonUtils.showError('操作失败');

// 成功提示
CommonUtils.showSuccess('保存成功');

// 格式化日期时间
const dateStr = CommonUtils.formatDateTime('2024-01-01T12:00:00');

// 格式化文件大小
const sizeStr = CommonUtils.formatFileSize(1024 * 1024); // "1 MB"

// 生成唯一 ID
const id = CommonUtils.generateId('prefix'); // "prefix_abc123xyz"

// 防抖函数
const debouncedFn = CommonUtils.debounce(() => {
    // 频繁调用的函数
}, 300);

// 节流函数
const throttledFn = CommonUtils.throttle(() => {
    // 需要限制频率的函数
}, 1000);
```

## UI 组件 (ui_components.js)

### 1. DialogManager - 对话框管理器

```javascript
// 确认对话框
DialogManager.confirm(
    '确定要删除吗？',
    () => { /* 确认回调 */ deleteItem(); },
    () => { /* 取消回调 */ }
);

// 成功提示
DialogManager.showSuccess('保存成功', () => {
    // 关闭后的回调
    closeModal();
});

// 错误提示
DialogManager.showError('网络异常', error);

// 警告提示
DialogManager.showWarning('数据未保存');

// 加载指示
DialogManager.showLoading('contentDiv', '正在加载...');
DialogManager.hideLoading('contentDiv');
```

### 2. FormValidator - 表单验证器

```javascript
const form = document.getElementById('myForm');

// 验证必填字段
if (!FormValidator.validateRequired(form, ['name', 'email', 'phone'])) {
    return; // 验证失败
}

// 验证邮箱
if (!FormValidator.validateEmail(email)) {
    DialogManager.showError('请输入正确的邮箱地址');
    return;
}

// 验证 URL
if (!FormValidator.validateURL(apiUrl)) {
    DialogManager.showError('请输入有效的 URL');
    return;
}

// 验证数字范围
if (!FormValidator.validateNumberRange(age, 18, 100)) {
    DialogManager.showError('年龄必须在 18-100 之间');
    return;
}

// 清除验证错误样式
FormValidator.clearValidationErrors(form);
```

### 3. APIHelper - API 请求助手

```javascript
// GET 请求
try {
    const data = await APIHelper.get('/api/items', { page: 1, limit: 20 });
    renderTable(data);
} catch (error) {
    DialogManager.showError('加载失败', error);
}

// POST 请求
try {
    const result = await APIHelper.post('/api/items', {
        name: '新物品',
        price: 100
    });
    DialogManager.showSuccess('创建成功');
} catch (error) {
    DialogManager.showError('创建失败', error);
}

// PUT 请求
try {
    await APIHelper.put('/api/items/123', {
        name: '更新的名称'
    });
    DialogManager.showSuccess('更新成功');
} catch (error) {
    DialogManager.showError('更新失败', error);
}

// DELETE 请求
try {
    await APIHelper.delete('/api/items/123');
    DialogManager.showSuccess('删除成功');
} catch (error) {
    DialogManager.showError('删除失败', error);
}
```

### 4. TableRenderer - 表格渲染器

```javascript
// 创建表格渲染器
const renderer = new TableRenderer('myTable', {
    emptyText: '暂无数据',
    loadingText: '加载中...',
    errorText: '加载失败'
});

// 设置列
renderer.setColumns([
    { key: 'id', label: 'ID' },
    { 
        key: 'name', 
        label: '名称',
        formatter: (value, row) => `<a href="/detail/${row.id}">${value}</a>`
    }
]);

// 显示加载状态
renderer.showLoading();

// 渲染数据
fetchData().then(data => {
    renderer.render(data);
}).catch(() => {
    renderer.showError();
});
```

### 5. ModalController - 模态框控制器

```javascript
// 创建模态框控制器
const modal = new ModalController('myModal', {
    closeOnOutsideClick: true,  // 点击外部关闭
    closeOnEsc: true            // ESC 键关闭
});

// 设置回调
modal.setOnOpen(() => {
    console.log('模态框打开');
});

modal.setOnClose(() => {
    console.log('模态框关闭');
});

// 显示/隐藏
modal.show();
modal.hide();
modal.toggle();

// 检查状态
if (modal.isOpen()) {
    console.log('模态框已打开');
}
```

### 6. StorageHelper - 本地存储助手

```javascript
// 保存数据
StorageHelper.set('userSettings', { theme: 'dark', lang: 'zh' });

// 获取数据
const settings = StorageHelper.get('userSettings', { theme: 'light' });

// 删除数据
StorageHelper.remove('userSettings');

// 清空所有
StorageHelper.clear();
```

## 在 HTML 中引用

### 基础引用方式

```html
<!DOCTYPE html>
<html>
<head>
    <title>页面标题</title>
    <!-- 先引用公共组件 -->
    <script src="/static/js/common_components.js"></script>
    <script src="/static/js/ui_components.js"></script>
    <!-- 再引用页面专用脚本 -->
    <script src="/static/js/my_page.js"></script>
</head>
<body>
    <!-- 页面内容 -->
</body>
</html>
```

### Flask 模板中的引用

```html
{% extends "base.html" %}

{% block extra_js %}
<script src="{{ url_for('static_bp.static_files', filename='js/common_components.js') }}"></script>
<script src="{{ url_for('static_bp.static_files', filename='js/ui_components.js') }}"></script>
<script src="{{ url_for('static_bp.static_files', filename='js/qa_groups.js') }}"></script>
{% endblock %}
```

## 最佳实践

### 1. 组件组合使用

```javascript
// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    // 1. 创建表格渲染器
    const tableRenderer = new TableRenderer('groupsTable');
    
    // 2. 创建分页组件
    const pagination = new PaginationComponent('paginationArea', (page, pageSize) => {
        loadGroups(page, pageSize);
    });
    
    // 3. 创建搜索组件
    const search = new SearchComponent('searchInput', 'searchBtn', (keyword) => {
        loadGroups(1, pagination.pageSize, keyword);
    });
    
    // 4. 加载初始数据
    loadGroups(1, 20);
});

// 加载数据函数
async function loadGroups(page = 1, pageSize = 20, keyword = '') {
    try {
        tableRenderer.showLoading();
        
        const data = await APIHelper.get('/api/groups', {
            page,
            limit: pageSize,
            keyword
        });
        
        if (data.success) {
            tableRenderer.render(data.data.rows);
            pagination.update(data.data.total, page, pageSize);
        } else {
            tableRenderer.showError();
            DialogManager.showError(data.message);
        }
    } catch (error) {
        tableRenderer.showError();
        DialogManager.showError('加载失败', error);
    }
}
```

### 2. 表单提交处理

```javascript
async function submitForm() {
    const form = document.getElementById('myForm');
    
    // 1. 清除之前的错误
    FormValidator.clearValidationErrors(form);
    
    // 2. 验证必填字段
    if (!FormValidator.validateRequired(form, ['name', 'email'])) {
        DialogManager.showError('请填写所有必填字段');
        return;
    }
    
    // 3. 收集表单数据
    const formData = {
        name: form.querySelector('[name="name"]').value,
        email: form.querySelector('[name="email"]').value
    };
    
    // 4. 验证邮箱格式
    if (!FormValidator.validateEmail(formData.email)) {
        DialogManager.showError('邮箱格式不正确');
        return;
    }
    
    // 5. 提交数据
    try {
        const result = await APIHelper.post('/api/items', formData);
        
        if (result.success) {
            DialogManager.showSuccess('保存成功', () => {
                // 关闭模态框
                modal.hide();
                // 刷新列表
                loadItems();
            });
        } else {
            DialogManager.showError(result.message);
        }
    } catch (error) {
        DialogManager.showError('保存失败', error);
    }
}
```

### 3. 删除确认操作

```javascript
async function deleteItem(id) {
    DialogManager.confirm(
        '确定要删除此项吗？此操作不可撤销。',
        async () => {
            try {
                const result = await APIHelper.delete(`/api/items/${id}`);
                
                if (result.success) {
                    DialogManager.showSuccess('删除成功', () => {
                        // 刷新列表
                        loadItems();
                    });
                } else {
                    DialogManager.showError(result.message);
                }
            } catch (error) {
                DialogManager.showError('删除失败', error);
            }
        },
        () => {
            console.log('用户取消删除');
        }
    );
}
```

## 迁移指南

### 从旧代码迁移到新组件

#### 旧代码
```javascript
// 分散的分页逻辑
function goToPage(page) {
    currentPage = page;
    loadItems();
}

function goToPrevPage() {
    if (currentPage > 1) {
        goToPage(currentPage - 1);
    }
}

// 手动 API 调用
fetch('/api/items?page=' + currentPage)
    .then(res => res.json())
    .then(data => {
        // 渲染逻辑
    })
    .catch(err => {
        alert('错误：' + err.message);
    });
```

#### 新代码（使用组件）
```javascript
// 使用分页组件
const pagination = new PaginationComponent('paginationArea', (page) => {
    loadItems(page);
});

// 使用 API 助手
try {
    const data = await APIHelper.get('/api/items', { page });
    renderItems(data);
} catch (error) {
    DialogManager.showError('加载失败', error);
}
```

## 注意事项

1. **引用顺序**: 必须先引用 `common_components.js` 和 `ui_components.js`，再引用页面专用脚本
2. **全局命名空间**: 所有组件都挂载到 `window` 对象，避免命名冲突
3. **浏览器兼容性**: 使用了 ES6+ 语法，需要现代浏览器支持
4. **错误处理**: 建议使用 `try-catch` 包裹异步操作
5. **内存管理**: 页面卸载时注意清理事件监听器

## 扩展组件

如需添加新的公共组件，请遵循以下规范：

1. 在对应文件中添加组件类或工具函数
2. 在文件末尾导出到 `window` 对象
3. 编写清晰的 JSDoc 注释
4. 提供使用示例
5. 确保组件可复用、无副作用
