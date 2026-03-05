// 通用前端组件和工具函数
// 用于QA模块和其他模块的共享功能

/**
 * 通用分页组件
 */
class PaginationComponent {
    constructor(containerId, onPageChange) {
        this.container = document.getElementById(containerId);
        this.onPageChange = onPageChange;
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalItems = 0;
        this.pageSize = 20;
    }

    /**
     * 更新分页信息并重新渲染
     */
    update(totalItems, currentPage, pageSize) {
        this.totalItems = totalItems;
        this.currentPage = currentPage;
        this.pageSize = pageSize;
        this.totalPages = Math.ceil(totalItems / pageSize);
        this.render();
    }

    /**
     * 渲染分页控件（布局：控制按钮居中，每页数量选择器靠右）
     */
    render() {
        if (!this.container) return;

        const html = `
            <div class="pagination-component">
                <div class="pagination-spacer"></div>
                <div class="pagination-controls">
                    <button class="pagination-btn first-btn" onclick="pagination.goToPage(1)" ${this.currentPage === 1 ? 'disabled' : ''}>首页</button>
                    <button class="pagination-btn prev-btn" onclick="pagination.goToPrevPage()" ${this.currentPage === 1 ? 'disabled' : ''}>上一页</button>
                    <div class="page-input">
                        <input type="number" class="page-input-field" min="1" max="${this.totalPages}" value="${this.currentPage}" onchange="pagination.goToPage(this.value)">
                        <span>/ <span class="max-page">${this.totalPages}</span></span>
                    </div>
                    <button class="pagination-btn next-btn" onclick="pagination.goToNextPage()" ${this.currentPage === this.totalPages ? 'disabled' : ''}>下一页</button>
                    <button class="pagination-btn last-btn" onclick="pagination.goToLastPage()" ${this.currentPage === this.totalPages ? 'disabled' : ''}>末页</button>
                </div>
                <div class="page-size-selector">
                    <span>每页显示：</span>
                    <select class="page-size-select" onchange="pagination.changePageSize(this.value)">
                        <option value="10" ${this.pageSize === 10 ? 'selected' : ''}>10</option>
                        <option value="20" ${this.pageSize === 20 ? 'selected' : ''}>20</option>
                        <option value="50" ${this.pageSize === 50 ? 'selected' : ''}>50</option>
                        <option value="100" ${this.pageSize === 100 ? 'selected' : ''}>100</option>
                    </select>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
        // 绑定全局引用以便onclick调用
        window.pagination = this;
    }

    /**
     * 跳转到指定页
     */
    goToPage(page) {
        const pageNum = parseInt(page);
        if (pageNum >= 1 && pageNum <= this.totalPages && pageNum !== this.currentPage) {
            this.currentPage = pageNum;
            if (this.onPageChange) {
                this.onPageChange(this.currentPage, this.pageSize);
            }
        }
    }

    /**
     * 跳转到上一页
     */
    goToPrevPage() {
        if (this.currentPage > 1) {
            this.goToPage(this.currentPage - 1);
        }
    }

    /**
     * 跳转到下一页
     */
    goToNextPage() {
        if (this.currentPage < this.totalPages) {
            this.goToPage(this.currentPage + 1);
        }
    }

    /**
     * 跳转到首页
     */
    goToFirstPage() {
        this.goToPage(1);
    }

    /**
     * 跳转到末页
     */
    goToLastPage() {
        this.goToPage(this.totalPages);
    }

    /**
     * 改变每页显示数量
     */
    changePageSize(newSize) {
        this.pageSize = parseInt(newSize);
        this.currentPage = 1; // 重置到第一页
        if (this.onPageChange) {
            this.onPageChange(this.currentPage, this.pageSize);
        }
    }
}

/**
 * 通用搜索组件
 */
class SearchComponent {
    constructor(searchInputId, searchButtonId, onSearch) {
        this.searchInput = document.getElementById(searchInputId);
        this.searchButton = document.getElementById(searchButtonId);
        this.onSearch = onSearch;
        this.init();
    }

    /**
     * 初始化搜索组件
     */
    init() {
        if (this.searchInput) {
            // 回车搜索
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }

        if (this.searchButton) {
            this.searchButton.addEventListener('click', () => {
                this.performSearch();
            });
        }
    }

    /**
     * 执行搜索
     */
    performSearch() {
        const keyword = this.searchInput ? this.searchInput.value.trim() : '';
        if (this.onSearch) {
            this.onSearch(keyword);
        }
    }

    /**
     * 获取当前搜索关键词
     */
    getKeyword() {
        return this.searchInput ? this.searchInput.value.trim() : '';
    }

    /**
     * 设置搜索关键词
     */
    setKeyword(keyword) {
        if (this.searchInput) {
            this.searchInput.value = keyword;
        }
    }

    /**
     * 清空搜索
     */
    clear() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        this.performSearch();
    }
}

/**
 * 通用筛选组件
 */
class FilterComponent {
    constructor(filterSelectIds, onFilterChange) {
        this.filters = {};
        this.onFilterChange = onFilterChange;
        this.init(filterSelectIds);
    }

    /**
     * 初始化筛选组件
     */
    init(filterSelectIds) {
        filterSelectIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                this.filters[id] = element;
                element.addEventListener('change', () => {
                    this.applyFilters();
                });
            }
        });
    }

    /**
     * 应用筛选
     */
    applyFilters() {
        const filterValues = {};
        Object.keys(this.filters).forEach(id => {
            const element = this.filters[id];
            if (element && element.value) {
                filterValues[id.replace('filter', '').toLowerCase()] = element.value;
            }
        });

        if (this.onFilterChange) {
            this.onFilterChange(filterValues);
        }
    }

    /**
     * 获取当前筛选值
     */
    getFilterValues() {
        const values = {};
        Object.keys(this.filters).forEach(id => {
            const element = this.filters[id];
            if (element && element.value) {
                values[id.replace('filter', '').toLowerCase()] = element.value;
            }
        });
        return values;
    }

    /**
     * 重置筛选
     */
    reset() {
        Object.values(this.filters).forEach(element => {
            if (element) {
                element.value = '';
            }
        });
        this.applyFilters();
    }
}

/**
 * 通用模态框组件
 */
class ModalComponent {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.isOpen = false;
    }

    /**
     * 显示模态框
     */
    show() {
        if (this.modal) {
            this.modal.style.display = 'block';
            this.isOpen = true;
            document.body.style.overflow = 'hidden';
        }
    }

    /**
     * 隐藏模态框
     */
    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
            this.isOpen = false;
            document.body.style.overflow = 'auto';
        }
    }

    /**
     * 切换模态框显示状态
     */
    toggle() {
        if (this.isOpen) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * 设置模态框内容
     */
    setContent(content) {
        if (this.modal) {
            const modalContent = this.modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.innerHTML = content;
            }
        }
    }
}

/**
 * 通用表格组件
 */
class TableComponent {
    constructor(tableId, columns) {
        this.table = document.getElementById(tableId);
        this.columns = columns;
        this.data = [];
        this.sortColumn = null;
        this.sortDirection = 'asc';
    }

    /**
     * 渲染表格
     */
    render(data) {
        this.data = data || [];
        if (!this.table) return;

        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        if (this.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${this.columns.length}" class="empty-cell">暂无数据</td></tr>`;
            return;
        }

        let html = '';
        this.data.forEach(row => {
            html += '<tr>';
            this.columns.forEach(col => {
                let cellValue = row[col.key];
                if (col.formatter) {
                    cellValue = col.formatter(cellValue, row);
                }
                html += `<td>${this.escapeHtml(String(cellValue || ''))}</td>`;
            });
            html += '</tr>';
        });

        tbody.innerHTML = html;
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 排序表格
     */
    sort(columnKey) {
        if (this.sortColumn === columnKey) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = columnKey;
            this.sortDirection = 'asc';
        }

        this.data.sort((a, b) => {
            let aVal = a[columnKey];
            let bVal = b[columnKey];

            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (this.sortDirection === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });

        this.render();
    }
}

/**
 * 通用工具函数
 */
var CommonUtils = {
    /**
     * 显示错误消息
     */
    showError(message) {
        alert('错误: ' + message);
        console.error(message);
    },

    /**
     * 显示成功消息
     */
    showSuccess(message) {
        alert('成功: ' + message);
        console.log(message);
    },

    /**
     * 格式化日期时间
     */
    formatDateTime(dateString) {
        if (!dateString) return '未知';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    },

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * 生成唯一ID
     */
    generateId(prefix = 'id') {
        return prefix + '_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// 全局导出
if (typeof window !== 'undefined') {
    window.PaginationComponent = PaginationComponent;
    window.SearchComponent = SearchComponent;
    window.FilterComponent = FilterComponent;
    window.ModalComponent = ModalComponent;
    window.TableComponent = TableComponent;
    window.CommonUtils = {
        showError: CommonUtils.showError,
        showSuccess: CommonUtils.showSuccess,
        formatDateTime: CommonUtils.formatDateTime,
        formatFileSize: CommonUtils.formatFileSize,
        generateId: CommonUtils.generateId,
        debounce: CommonUtils.debounce,
        throttle: CommonUtils.throttle
    };
}