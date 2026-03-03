// 报告列表页面 JavaScript
// 使用公共组件重构版本

/**
 * 切换目录显示状态
 * @param {HTMLElement} element - 点击的目录头部元素
 */
function toggleDirectory(element) {
    const fileList = element.nextElementSibling;
    const toggleIcon = element.querySelector('.toggle-icon');

    if (fileList.style.display === 'none') {
        fileList.style.display = 'block';
        toggleIcon.textContent = '▼';
    } else {
        fileList.style.display = 'none';
        toggleIcon.textContent = '▶';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置所有目录为折叠状态
    const toggleIcons = document.querySelectorAll('.directory-header .toggle-icon');
    toggleIcons.forEach(icon => {
        icon.textContent = '▶';
    });
    
    console.log('报告列表页面已加载');
});