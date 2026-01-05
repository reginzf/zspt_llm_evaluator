// 从模板传递的数据（这些将在HTML中通过模板引擎提供）
// 注意：这些变量现在在HTML页面中通过script标签定义

// 初始化图表
document.addEventListener('DOMContentLoaded', function() {
    // 确保Chart.js库已加载
    if (typeof Chart === 'undefined') {
        console.error('Chart.js library not loaded');
        // 等待Chart.js加载后再尝试渲染
        waitForChartJs();
        return;
    }

    // 确保数据已定义
    if (typeof metricsData !== 'undefined' && typeof correlationMatrix !== 'undefined') {
        renderCharts();
    } else {
        console.error('metricsData 或 correlationMatrix 未定义');
        console.log('metricsData:', typeof metricsData);
        console.log('correlationMatrix:', typeof correlationMatrix);
        
        // 在页面上显示错误消息
        showErrorMessage('数据加载失败，无法渲染图表');
    }
});

function waitForChartJs() {
    // 检查Chart.js是否加载，最多等待10秒
    let attempts = 0;
    const maxAttempts = 20; // 20次 * 500ms = 10秒

    const checkChart = setInterval(() => {
        if (typeof Chart !== 'undefined') {
            clearInterval(checkChart);
            console.log('Chart.js loaded, rendering charts...');
            if (typeof metricsData !== 'undefined' && typeof correlationMatrix !== 'undefined') {
                renderCharts();
            } else {
                showErrorMessage('数据加载失败，无法渲染图表');
            }
        } else {
            attempts++;
            if (attempts >= maxAttempts) {
                clearInterval(checkChart);
                console.error('Chart.js failed to load after 10 seconds');
                showErrorMessage('图表库加载失败，请刷新页面重试');
            }
        }
    }, 500);
}

// ... existing code for showErrorMessage function ...

function renderCharts() {
    // 确保Chart.js已定义
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not available');
        showErrorMessage('图表库未加载，无法渲染图表');
        return;
    }

    // 1. Top K准确率图表
    const precisionCtx = document.getElementById('precisionChart');
    if (precisionCtx && 
        metricsData && 
        metricsData.top_k_labels && 
        Array.isArray(metricsData.top_k_labels) && 
        metricsData.avg_precision_at_k && 
        Array.isArray(metricsData.avg_precision_at_k) && 
        metricsData.top_k_labels.length > 0 && 
        metricsData.avg_precision_at_k.length > 0) {
        
        const precisionChart = new Chart(precisionCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: metricsData.top_k_labels,
                datasets: [{
                    label: '准确率@K',
                    data: metricsData.avg_precision_at_k,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '不同K值下的准确率变化'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `准确率@${context.label}: ${(context.raw * 100).toFixed(2)}%`;
                            }
                        }
                    },
                    // 添加数据标签插件配置
                    datalabels: {
                        display: false // 默认不显示，可根据需要启用
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                }
            }
        });
    } else {
        console.warn('Precision chart data not available or invalid');
        console.log('top_k_labels:', metricsData ? metricsData.top_k_labels : 'undefined');
        console.log('avg_precision_at_k:', metricsData ? metricsData.avg_precision_at_k : 'undefined');
        
        // 显示错误消息
        const canvas = document.getElementById('precisionChart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#fff3cd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#856404';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('准确率图表数据无效', canvas.width / 2, canvas.height / 2);
        }
    }

    // 2. Top K召回率图表
    const recallCtx = document.getElementById('recallChart');
    if (recallCtx && 
        metricsData && 
        metricsData.top_k_labels && 
        Array.isArray(metricsData.top_k_labels) && 
        metricsData.avg_recall_at_k && 
        Array.isArray(metricsData.avg_recall_at_k) && 
        metricsData.top_k_labels.length > 0 && 
        metricsData.avg_recall_at_k.length > 0) {
        
        const recallChart = new Chart(recallCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: metricsData.top_k_labels,
                datasets: [{
                    label: '召回率@K',
                    data: metricsData.avg_recall_at_k,
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '不同K值下的召回率变化'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `召回率@${context.label}: ${(context.raw * 100).toFixed(2)}%`;
                            }
                        }
                    },
                    // 添加数据标签插件配置
                    datalabels: {
                        display: false // 默认不显示，可根据需要启用
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                }
            }
        });
    } else {
        console.warn('Recall chart data not available or invalid');
        console.log('top_k_labels:', metricsData ? metricsData.top_k_labels : 'undefined');
        console.log('avg_recall_at_k:', metricsData ? metricsData.avg_recall_at_k : 'undefined');
        
        // 显示错误消息
        const canvas = document.getElementById('recallChart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#fff3cd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#856404';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('召回率图表数据无效', canvas.width / 2, canvas.height / 2);
        }
    }

    // 3. F1分数分布图表
    const f1Ctx = document.getElementById('f1DistributionChart');
    if (f1Ctx && 
        metricsData && 
        metricsData.f1_distribution_labels && 
        Array.isArray(metricsData.f1_distribution_labels) && 
        metricsData.f1_distribution_data && 
        Array.isArray(metricsData.f1_distribution_data) && 
        metricsData.f1_distribution_labels.length > 0 && 
        metricsData.f1_distribution_data.length > 0) {
        
        const f1Chart = new Chart(f1Ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: metricsData.f1_distribution_labels,
                datasets: [{
                    label: '问题数量',
                    data: metricsData.f1_distribution_data,
                    backgroundColor: [
                        'rgba(220, 53, 69, 0.7)',  // 差
                        'rgba(255, 193, 7, 0.7)',   // 中
                        'rgba(40, 167, 69, 0.7)'    // 好
                    ],
                    borderColor: [
                        'rgb(220, 53, 69)',
                        'rgb(255, 193, 7)',
                        'rgb(40, 167, 69)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'F1分数分布（按性能等级）'
                    },
                    datalabels: {
                        color: '#fff',
                        font: {
                            weight: 'bold'
                        },
                        formatter: function(value) {
                            return value;
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '问题数量'
                        }
                    }
                }
            }
        });
    } else {
        console.warn('F1 distribution chart data not available or invalid');
        console.log('f1_distribution_labels:', metricsData ? metricsData.f1_distribution_labels : 'undefined');
        console.log('f1_distribution_data:', metricsData ? metricsData.f1_distribution_data : 'undefined');
        
        // 显示错误消息
        const canvas = document.getElementById('f1DistributionChart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#fff3cd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#856404';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('F1分布图表数据无效', canvas.width / 2, canvas.height / 2);
        }
    }

    // 4. 排序指标图表
    const rankingCtx = document.getElementById('rankingMetricsChart');
    if (rankingCtx && metricsData) {
        const rankingChart = new Chart(rankingCtx.getContext('2d'), {
            type: 'radar',
            data: {
                labels: ['平均准确率', 'NDCG', 'MRR', '命中率', '覆盖率'],
                datasets: [{
                    label: '排序质量指标',
                    data: [
                        metricsData.avg_average_precision || 0,
                        metricsData.avg_ndcg || 0,
                        metricsData.avg_mrr || 0,
                        metricsData.avg_hit_rate || 0,
                        metricsData.avg_coverage || 0
                    ],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '排序质量指标雷达图'
                    },
                    // 添加数据标签插件配置
                    datalabels: {
                        display: false // 默认不显示，可根据需要启用
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    }
                }
            }
        });
    } else {
        console.warn('Ranking metrics chart data not available or invalid');
        
        // 显示错误消息
        const canvas = document.getElementById('rankingMetricsChart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#fff3cd';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#856404';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('排序指标图表数据无效', canvas.width / 2, canvas.height / 2);
        }
    }

}

// ... existing code for toggleDetails and window resize ...

function toggleDetails() {
    const detailsSection = document.getElementById('detailsSection');
    detailsSection.classList.toggle('active');
}

// 添加窗口调整大小时重新渲染图表
window.addEventListener('resize', function() {
    // 这里可以添加图表重新渲染的逻辑
    if (typeof Chart !== 'undefined' && typeof metricsData !== 'undefined') {
        // 重新渲染图表，可能需要先销毁现有图表
        // 目前我们简单地重新调用renderCharts
        setTimeout(() => {
            // 清除现有图表实例
            Chart.helpers ? Object.values(Chart.instances || {}).forEach(chart => chart.destroy()) : null;
            // 重新渲染图表
            renderCharts();
        }, 300);
    }
});