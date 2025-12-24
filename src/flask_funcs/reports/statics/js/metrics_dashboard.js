// 从模板传递的数据（这些将在HTML中通过模板引擎提供）
// 注意：这些变量现在在HTML页面中通过script标签定义

// 初始化图表
document.addEventListener('DOMContentLoaded', function() {
    // 确保数据已定义
    if (typeof metricsData !== 'undefined' && typeof correlationMatrix !== 'undefined') {
        renderCharts();
    } else {
        console.error('metricsData 或 correlationMatrix 未定义');
        console.log('metricsData:', typeof metricsData);
        console.log('correlationMatrix:', typeof correlationMatrix);
    }
});

function renderCharts() {
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
    }

    // 6. 性能热力图 - 只有在相关性矩阵数据存在时才渲染
    if (document.getElementById('performanceHeatmap')) {
        renderPerformanceHeatmap();
    }
}

// 注意：matrix类型需要Chart.js Matrix插件，但该插件不是标准插件
// 这里使用热力图替代方案
function renderPerformanceHeatmap() {
    const heatmapCtx = document.getElementById('performanceHeatmap').getContext('2d');
    
    if (!heatmapCtx || !correlationMatrix) {
        console.warn('Heatmap context or correlationMatrix not available');
        return;
    }
    
    // 准备热力图数据
    const metrics = ['precision', 'recall', 'f1_score', 'average_precision', 'ndcg', 'mrr'];
    const labels = ['精确率', '召回率', 'F1分数', '平均精确率', 'NDCG', 'MRR'];
    
    // 创建相关性矩阵数据
    const heatmapData = [];
    for (let i = 0; i < metrics.length; i++) {
        const row = [];
        for (let j = 0; j < metrics.length; j++) {
            if (correlationMatrix[metrics[i]] && correlationMatrix[metrics[i]][metrics[j]]) {
                row.push(correlationMatrix[metrics[i]][metrics[j]]);
            } else {
                row.push(0);
            }
        }
        heatmapData.push(row);
    }
    
    // 使用散点图模拟热力图效果
    const dataPoints = [];
    for (let i = 0; i < heatmapData.length; i++) {
        for (let j = 0; j < heatmapData[i].length; j++) {
            dataPoints.push({
                x: j,
                y: i,
                r: Math.abs(heatmapData[i][j]) * 20, // 半径表示相关性强度
                value: heatmapData[i][j]
            });
        }
    }
    
    new Chart(heatmapCtx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: '指标相关性',
                data: dataPoints,
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex].value;
                    // 根据相关性值设置颜色
                    if (value >= 0.7) return 'rgba(40, 167, 69, 0.7)';
                    if (value >= 0.4) return 'rgba(255, 193, 7, 0.7)';
                    if (value >= 0) return 'rgba(220, 53, 69, 0.7)';
                    return 'rgba(108, 117, 125, 0.7)';
                },
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '指标相关性热力图'
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const dataPoint = context.raw;
                            const xIndex = Math.round(dataPoint.x);
                            const yIndex = Math.round(dataPoint.y);
                            return `${labels[yIndex]} vs ${labels[xIndex]}: ${dataPoint.value.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    min: -0.5,
                    max: labels.length - 0.5,
                    ticks: {
                        callback: function(value) {
                            return labels[Math.round(value)];
                        },
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: '指标'
                    }
                },
                y: {
                    type: 'linear',
                    min: -0.5,
                    max: labels.length - 0.5,
                    ticks: {
                        callback: function(value) {
                            return labels[Math.round(value)];
                        },
                        stepSize: 1,
                        reverse: true // 颠倒Y轴，使矩阵显示更符合常规
                    },
                    title: {
                        display: true,
                        text: '指标'
                    }
                }
            }
        }
    });
}

function toggleDetails() {
    const detailsSection = document.getElementById('detailsSection');
    detailsSection.classList.toggle('active');
}

// 添加窗口调整大小时重新渲染图表
window.addEventListener('resize', function() {
    // 这里可以添加图表重新渲染的逻辑
});