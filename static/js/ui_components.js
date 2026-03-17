// 增强的通用前端组件库
// 整合各模块常用功能，提供统一的 UI 组件和工具函数

/**
 * 对话框管理器 - 统一处理消息提示
 */
const DialogManager = {
    /**
     * 显示确认对话框
     * @param {string} message - 确认消息
     * @param {function} onConfirm - 确认回调
     * @param {function} onCancel - 取消回调
     */
    confirm(message, onConfirm, onCancel) {
        if (confirm(message)) {
            if (onConfirm) onConfirm();
        } else {
            if (onCancel) onCancel();
        }
    },

    /**
     * 显示成功提示
     * @param {string} message - 成功消息
     * @param {function} callback - 关闭后的回调
     */
    showSuccess(message, callback) {
        alert('✓ ' + message);
        if (callback) callback();
    },

    /**
     * 显示错误提示
     * @param {string} message - 错误消息
     * @param {Error} error - 错误对象
     */
    showError(message, error) {
        console.error('错误:', message, error || '');
        alert('✗ 错误：' + message);
    },

    /**
     * 显示警告提示
     * @param {string} message - 警告消息
     */
    showWarning(message) {
        alert('⚠ ' + message);
    },

    /**
     * 显示加载提示
     * @param {string} elementId - 目标元素 ID
     * @param {string} loadingText - 加载文本
     */
    showLoading(elementId, loadingText = '加载中...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<span class="loading-indicator">${loadingText}</span>`;
        }
    },

    /**
     * 隐藏加载提示
     * @param {string} elementId - 目标元素 ID
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '';
        }
    }
};

/**
 * 表单验证器 - 统一表单字段验证
 */
const FormValidator = {
    /**
     * 验证必填字段
     * @param {HTMLFormElement} form - 表单元素
     * @param {Array<string>} requiredFields - 必填字段名数组
     * @returns {boolean} - 验证结果
     */
    validateRequired(form, requiredFields) {
        let isValid = true;
        requiredFields.forEach(field => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input && !input.value.trim()) {
                input.classList.add('input-error');
                isValid = false;
            } else if (input) {
                input.classList.remove('input-error');
            }
        });
        return isValid;
    },

    /**
     * 验证邮箱格式
     * @param {string} email - 邮箱地址
     * @returns {boolean} - 验证结果
     */
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * 验证 URL 格式
     * @param {string} url - URL 地址
     * @returns {boolean} - 验证结果
     */
    validateURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * 验证数字范围
     * @param {number} value - 值
     * @param {number} min - 最小值
     * @param {number} max - 最大值
     * @returns {boolean} - 验证结果
     */
    validateNumberRange(value, min, max) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    },

    /**
     * 清除验证错误样式
     * @param {HTMLFormElement} form - 表单元素
     */
    clearValidationErrors(form) {
        const errorInputs = form.querySelectorAll('.input-error');
        errorInputs.forEach(input => {
            input.classList.remove('input-error');
        });
    }
};

/**
 * API 请求助手 - 统一处理 API 调用
 */
const APIHelper = {
    /**
     * GET 请求
     * @param {string} url - 请求 URL
     * @param {Object} params - 查询参数
     * @returns {Promise<Object>} - 响应数据
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        try {
            const response = await fetch(fullUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API GET 请求失败:', url, error);
            throw error;
        }
    },

    /**
     * POST 请求
     * @param {string} url - 请求 URL
     * @param {Object} data - 请求数据
     * @returns {Promise<Object>} - 响应数据
     */
    async post(url, data = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API POST 请求失败:', url, error);
            throw error;
        }
    },

    /**
     * PUT 请求
     * @param {string} url - 请求 URL
     * @param {Object} data - 请求数据
     * @returns {Promise<Object>} - 响应数据
     */
    async put(url, data = {}) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API PUT 请求失败:', url, error);
            throw error;
        }
    },

    /**
     * DELETE 请求
     * @param {string} url - 请求 URL
     * @returns {Promise<Object>} - 响应数据
     */
    async delete(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API DELETE 请求失败:', url, error);
            throw error;
        }
    }
};

/**
 * 表格渲染器 - 统一表格数据渲染
 */
class TableRenderer {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.options = {
            emptyText: options.emptyText || '暂无数据',
            loadingText: options.loadingText || '加载中...',
            errorText: options.errorText || '加载失败',
            ...options
        };
        this.columns = [];
        this.data = [];
    }

    /**
     * 设置表格列
     * @param {Array<Object>} columns - 列配置 [{key, label, formatter}]
     */
    setColumns(columns) {
        this.columns = columns;
        this.renderHeader();
    }

    /**
     * 渲染表头
     */
    renderHeader() {
        if (!this.table) return;
        
        const thead = this.table.querySelector('thead tr');
        if (!thead) return;
        
        thead.innerHTML = this.columns.map(col => 
            `<th>${col.label || col.key}</th>`
        ).join('');
    }

    /**
     * 渲染表格数据
     * @param {Array<Object>} data - 数据数组
     */
    render(data) {
        this.data = data || [];
        if (!this.table) return;
        
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        if (this.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${this.columns.length}" class="empty-cell">${this.options.emptyText}</td></tr>`;
            return;
        }
        
        tbody.innerHTML = this.data.map(row => {
            const cells = this.columns.map(col => {
                let value = row[col.key];
                if (col.formatter) {
                    value = col.formatter(value, row);
                }
                return `<td>${this.escapeHtml(String(value || ''))}</td>`;
            });
            return `<tr>${cells.join('')}</tr>`;
        }).join('');
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        if (!this.table) return;
        const tbody = this.table.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="${this.columns.length}" class="loading-cell">${this.options.loadingText}</td></tr>`;
        }
    }

    /**
     * 显示错误状态
     */
    showError() {
        if (!this.table) return;
        const tbody = this.table.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="${this.columns.length}" class="error-cell">${this.options.errorText}</td></tr>`;
        }
    }

    /**
     * HTML 转义
     * @param {string} text - 待转义文本
     * @returns {string} - 转义后文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

/**
 * 模态框控制器 - 统一模态框操作
 */
class ModalController {
    constructor(modalId, options = {}) {
        this.modal = document.getElementById(modalId);
        this.options = {
            closeOnOutsideClick: options.closeOnOutsideClick !== false,
            closeOnEsc: options.closeOnEsc !== false,
            ...options
        };
        this.onOpen = null;
        this.onClose = null;
        this.init();
    }

    /**
     * 初始化事件监听
     */
    init() {
        if (!this.modal) return;

        // 点击外部关闭
        if (this.options.closeOnOutsideClick) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });
        }

        // ESC 键关闭
        if (this.options.closeOnEsc) {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen()) {
                    this.hide();
                }
            });
        }
    }

    /**
     * 显示模态框
     */
    show() {
        if (this.modal) {
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            if (this.onOpen) this.onOpen();
        }
    }

    /**
     * 隐藏模态框
     */
    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            if (this.onClose) this.onClose();
        }
    }

    /**
     * 切换模态框显示状态
     */
    toggle() {
        if (this.isOpen()) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * 检查模态框是否打开
     * @returns {boolean} - 是否打开
     */
    isOpen() {
        return this.modal && this.modal.style.display === 'block';
    }

    /**
     * 设置打开回调
     * @param {function} callback - 回调函数
     */
    setOnOpen(callback) {
        this.onOpen = callback;
    }

    /**
     * 设置关闭回调
     * @param {function} callback - 回调函数
     */
    setOnClose(callback) {
        this.onClose = callback;
    }
}

/**
 * 本地存储助手 - 统一 localStorage 操作
 */
const StorageHelper = {
    /**
     * 保存数据
     * @param {string} key - 键
     * @param {any} value - 值
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage set error:', error);
        }
    },

    /**
     * 获取数据
     * @param {string} key - 键
     * @param {any} defaultValue - 默认值
     * @returns {any} - 值
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    },

    /**
     * 删除数据
     * @param {string} key - 键
     */
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Storage remove error:', error);
        }
    },

    /**
     * 清空所有数据
     */
    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Storage clear error:', error);
        }
    }
};

// 全局导出
if (typeof window !== 'undefined') {
    window.DialogManager = DialogManager;
    window.FormValidator = FormValidator;
    window.APIHelper = APIHelper;
    window.TableRenderer = TableRenderer;
    window.ModalController = ModalController;
    window.StorageHelper = StorageHelper;
}
