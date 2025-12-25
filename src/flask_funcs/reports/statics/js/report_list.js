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

// 初始化时设置所有目录为展开状态
document.addEventListener('DOMContentLoaded', function() {
    const toggleIcons = document.querySelectorAll('.directory-header .toggle-icon');
    toggleIcons.forEach(icon => {
        icon.textContent = '▼';
    });
});