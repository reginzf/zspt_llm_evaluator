// 从模板传递的数据（这些将在HTML中通过模板引擎提供）
// 注意：这些变量现在在HTML页面中通过script标签定义

// 初始化图表
document.addEventListener('DOMContentLoaded', function() {
    // 确保数据已定义
    if (typeof metricsData !== 'undefined' && typeof correlationMatrix !== 'undefined') {
        renderCharts();
    } else {
        console.error('metricsData 或 correlationMatrix 未定义');
    }
});

function renderCharts() {
    // 1. Top K准确率图表
    const precisionCtx = document.getElementById('precisionChart').getContext('2d');
    new Chart(precisionCtx, {
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

    // 2. Top K召回率图表
    const recallCtx = document.getElementById('recallChart').getContext('2d');
    new Chart(recallCtx, {
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

    // 3. F1分数分布图表
    const f1Ctx = document.getElementById('f1DistributionChart').getContext('2d');
    new Chart(f1Ctx, {
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

    // 4. 排序指标图表
    const rankingCtx = document.getElementById('rankingMetricsChart').getContext('2d');
    new Chart(rankingCtx, {
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

    // 5. 相关性分析图表
    const correlationCtx = document.getElementById('correlationChart').getContext('2d');
    new Chart(correlationCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '问题性能分布',
                data: metricsData.correlation_data,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: '#667eea',
                borderWidth: 1,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '准确率 vs 召回率 相关性分析'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const data = context.raw;
                            return [
                                `问题: ${data.label}`,
                                `准确率: ${(data.x * 100).toFixed(2)}%`,
                                `召回率: ${(data.y * 100).toFixed(2)}%`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '准确率'
                    },
                    min: 0,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            return (value * 100) + '%';
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '召回率'
                    },
                    min: 0,
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
    
    // 6. 性能热力图
    renderPerformanceHeatmap();
}

function renderPerformanceHeatmap() {
    const heatmapCtx = document.getElementById('performanceHeatmap').getContext('2d');
    
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
    
    new Chart(heatmapCtx, {
        type: 'matrix',
        data: {
            datasets: [{
                label: '指标相关性',
                data: heatmapData,
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    // 根据相关性值设置颜色
                    if (value >= 0.7) return 'rgba(40, 167, 69, 0.7)';
                    if (value >= 0.4) return 'rgba(255, 193, 7, 0.7)';
                    if (value >= 0) return 'rgba(220, 53, 69, 0.7)';
                    return 'rgba(108, 117, 125, 0.7)';
                },
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1,
                width: function(context) {
                    const chart = context.chart;
                    const {chartArea} = chart;
                    if (!chartArea) return 0;
                    return (chartArea.right - chartArea.left) / heatmapData.length - 2;
                },
                height: function(context) {
                    const chart = context.chart;
                    const {chartArea} = chart;
                    if (!chartArea) return 0;
                    return (chartArea.bottom - chartArea.top) / heatmapData.length - 2;
                }
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
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const row = Math.floor(context.dataIndex / heatmapData.length);
                            const col = context.dataIndex % heatmapData.length;
                            return `${labels[row]} vs ${labels[col]}: ${heatmapData[row][col].toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: labels,
                    offset: true,
                    ticks: {
                        display: true
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: labels,
                    offset: true,
                    ticks: {
                        display: true
                    },
                    grid: {
                        display: false
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