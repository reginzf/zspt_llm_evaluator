<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <el-button link @click="goBack">
            <el-icon><Back /></el-icon>
            <span class="back-text">返回模型列表</span>
          </el-button>
          <h1>🤖 LLM评估报告</h1>
        </div>
      </div>

      <!-- 报告基本信息 -->
      <div class="report-info" v-if="reportData">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="文件名">{{ reportFileName }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatDateTime(reportData.evaluation_summary?.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="评估模型数">{{ reportData.evaluation_summary?.total_agents }}</el-descriptions-item>
          <el-descriptions-item label="问答对总数">{{ reportData.evaluation_summary?.total_qa_pairs }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 模型结果展示 -->
      <div v-if="modelResult" class="model-result">
        <!-- 模型信息卡片 -->
        <div class="model-header">
          <h2>{{ modelResult.model_name }}</h2>
          <el-tag size="large" type="info">版本: {{ modelResult.model_version }}</el-tag>
          <el-tag size="large" type="success">{{ modelResult.model_config?.model }}</el-tag>
        </div>

        <!-- 指标卡片区域 -->
        <div class="metrics-section">
          <!-- 基础统计 -->
          <div class="metric-group">
            <h3 class="group-title">📊 基础统计</h3>
            <div class="metric-cards">
              <div class="metric-card">
                <div class="metric-value">{{ modelResult.metrics?.total_samples }}</div>
                <div class="metric-label">总样本数</div>
              </div>
              <div class="metric-card success">
                <div class="metric-value">{{ modelResult.metrics?.successful_predictions }}</div>
                <div class="metric-label">成功预测</div>
              </div>
              <div class="metric-card danger" v-if="modelResult.metrics?.failed_predictions > 0">
                <div class="metric-value">{{ modelResult.metrics?.failed_predictions }}</div>
                <div class="metric-label">失败预测</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatPercent(calculateSuccessRate(modelResult.metrics)) }}</div>
                <div class="metric-label">成功率</div>
              </div>
            </div>
          </div>

          <!-- 准确性指标 -->
          <div class="metric-group">
            <h3 class="group-title">🎯 准确性指标</h3>
            <div class="metric-cards">
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.exact_match)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.exact_match) }}</div>
                <div class="metric-label">精确匹配 (EM)</div>
                <el-tooltip content="预测答案与标准答案完全匹配的比例">
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.f1_score)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.f1_score) }}</div>
                <div class="metric-label">F1分数</div>
                <el-tooltip content="精确率和召回率的调和平均">
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.semantic_similarity)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.semantic_similarity) }}</div>
                <div class="metric-label">语义相似度</div>
                <el-tooltip content="预测答案与标准答案的语义相似程度">
                  <el-icon class="info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
            </div>
          </div>

          <!-- 知识库能力指标 -->
          <div class="metric-group">
            <h3 class="group-title">📚 知识库能力指标</h3>
            <div class="metric-cards">
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.answer_coverage)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.answer_coverage) }}</div>
                <div class="metric-label">答案覆盖率</div>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.answer_relevance)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.answer_relevance) }}</div>
                <div class="metric-label">答案相关性</div>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.context_utilization)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.context_utilization) }}</div>
                <div class="metric-label">上下文利用率</div>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.answer_completeness)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.answer_completeness) }}</div>
                <div class="metric-label">答案完整性</div>
              </div>
              <div class="metric-card" :class="getScoreClass(modelResult.metrics?.answer_conciseness)">
                <div class="metric-value">{{ formatPercent(modelResult.metrics?.answer_conciseness) }}</div>
                <div class="metric-label">答案简洁性</div>
              </div>
            </div>
          </div>

          <!-- 效率指标 -->
          <div class="metric-group">
            <h3 class="group-title">⏱️ 效率指标</h3>
            <div class="metric-cards">
              <div class="metric-card">
                <div class="metric-value">{{ formatTime(modelResult.metrics?.avg_inference_time) }}</div>
                <div class="metric-label">平均推理时间</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatTime(modelResult.metrics?.total_inference_time) }}</div>
                <div class="metric-label">总推理时间</div>
              </div>
            </div>
          </div>

          <!-- 评估配置 -->
          <div class="metric-group">
            <h3 class="group-title">⚙️ 评估配置</h3>
            <div class="config-list">
              <el-tag v-for="(config, key) in matchTypeConfigs" :key="key" class="config-tag">
                {{ config.label }}: {{ config.value }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 问答对详情 -->
        <div class="qa-details-section">
          <div class="section-header">
            <h3 class="group-title">📝 问答对详情 ({{ qaTotal }}条)</h3>
            <div class="header-controls">
              <!-- 列配置按钮 -->
              <el-popover placement="bottom" :width="200" trigger="click">
                <template #reference>
                  <el-button size="small" type="primary" plain>
                    <el-icon><Setting /></el-icon>
                    配置列
                  </el-button>
                </template>
                <div class="column-config">
                  <div class="config-title">显示列配置</div>
                  <el-checkbox-group v-model="visibleColumns">
                    <el-checkbox v-for="col in availableColumns" :key="col.prop" :label="col.prop">
                      {{ col.label }}
                    </el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-popover>
              
              <!-- 排序控制 -->
              <div class="sort-controls">
                <el-select v-model="sortBy" placeholder="排序指标" size="small" @change="handleSort">
                  <el-option label="问题ID" value="question_id" />
                  <el-option label="精确匹配" value="exact_match" />
                  <el-option label="F1分数" value="f1_score" />
                  <el-option label="语义相似度" value="semantic_similarity" />
                  <el-option label="答案覆盖率" value="answer_coverage" />
                  <el-option label="答案相关性" value="answer_relevance" />
                  <el-option label="上下文利用率" value="context_utilization" />
                  <el-option label="答案完整性" value="answer_completeness" />
                  <el-option label="答案简洁性" value="answer_conciseness" />
                  <el-option label="推理时间" value="inference_time" />
                </el-select>
                <el-button size="small" @click="toggleSortOrder">
                  <el-icon><Sort v-if="sortOrder === 'asc'" /><SortDown v-else /></el-icon>
                  {{ sortOrder === 'asc' ? '升序' : '降序' }}
                </el-button>
              </div>
            </div>
          </div>

          <!-- QA列表表格 -->
          <el-table :data="qaList" stripe border class="qa-table" v-loading="qaLoading">
            <!-- ID列 -->
            <el-table-column prop="question_id" label="ID" width="70" fixed="left" v-if="isColumnVisible('question_id')" />
            
            <!-- 问题列 -->
            <el-table-column label="问题" min-width="200" v-if="isColumnVisible('question')" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="question-cell">{{ row.question || '-' }}</div>
              </template>
            </el-table-column>
            
            <!-- 标注答案列 -->
            <el-table-column label="标注答案" min-width="200" v-if="isColumnVisible('ground_truth')" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="answer-cell ground-truth">{{ formatGroundTruth(row.ground_truth) }}</div>
              </template>
            </el-table-column>
            
            <!-- 预测答案列 -->
            <el-table-column label="预测答案" min-width="200" v-if="isColumnVisible('predicted_answer')" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="answer-cell prediction">{{ row.predicted_answer || '-' }}</div>
              </template>
            </el-table-column>
            
            <!-- 指标得分列（可配置显示哪些指标） -->
            <el-table-column label="指标得分" width="220" v-if="isColumnVisible('metrics')">
              <template #default="{ row }">
                <div class="score-bars">
                  <div v-for="metric in visibleMetricColumns" :key="metric.key" class="score-bar-item">
                    <span class="bar-label">{{ metric.shortLabel }}</span>
                    <el-progress :percentage="Math.round(row.metrics[metric.key] * 100)" :color="getScoreColor(row.metrics[metric.key])" :show-text="false" />
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <!-- 推理时间列 -->
            <el-table-column label="推理时间" width="100" v-if="isColumnVisible('inference_time')">
              <template #default="{ row }">
                {{ formatTime(row.metrics.inference_time) }}
              </template>
            </el-table-column>
            
            <!-- 状态列 -->
            <el-table-column label="状态" width="80" v-if="isColumnVisible('status')">
              <template #default="{ row }">
                <el-tag :type="row.metrics.success ? 'success' : 'danger'" size="small">
                  {{ row.metrics.success ? '✓ 成功' : '✗ 失败' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <!-- 操作列 -->
            <el-table-column label="操作" width="100" fixed="right" v-if="isColumnVisible('action')">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showQADetail(row)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="qaPage"
              v-model:page-size="qaPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="qaTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="loadQAData"
              @current-change="loadQAData"
            />
          </div>
        </div>
      </div>
    </el-card>

    <!-- QA详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="问答对详情" width="900px" destroy-on-close>
      <div v-if="selectedQA" class="qa-detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="问题ID">{{ selectedQA.question_id }}</el-descriptions-item>
          <el-descriptions-item label="推理时间">{{ formatTime(selectedQA.metrics?.inference_time) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 指标得分详情 -->
        <div class="detail-metrics">
          <h4>指标得分</h4>
          <div class="detail-metrics-grid">
            <div class="detail-metric-item" v-for="(label, key) in metricLabels" :key="key">
              <span class="metric-name">{{ label }}</span>
              <el-progress 
                :percentage="Math.round((selectedQA.metrics?.[key as keyof QuestionMetrics] || 0) * 100)" 
                :color="getScoreColor(selectedQA.metrics?.[key as keyof QuestionMetrics] || 0)"
                :stroke-width="16"
                striped
              />
            </div>
          </div>
        </div>

        <!-- 问题和答案对比 -->
        <div class="qa-comparison">
          <div class="qa-block">
            <h4>问题</h4>
            <div class="qa-content">{{ selectedQA.question || '(无问题文本)' }}</div>
          </div>
          <div class="qa-block">
            <h4>上下文</h4>
            <div class="qa-content context">{{ selectedQA.context || '(无上下文)' }}</div>
          </div>
          <div class="qa-row">
            <div class="qa-block half">
              <h4>标准答案</h4>
              <div class="qa-content ground-truth">
                <div v-if="selectedQA.ground_truth && selectedQA.ground_truth.length > 0">
                  <div v-for="(answer, idx) in selectedQA.ground_truth" :key="idx" class="answer-item">
                    <el-tag size="small" type="success" class="answer-index">答案{{ idx + 1 }}</el-tag>
                    <span>{{ answer }}</span>
                  </div>
                </div>
                <div v-else class="empty-text">(无标准答案)</div>
              </div>
            </div>
            <div class="qa-block half">
              <h4>预测答案</h4>
              <div class="qa-content prediction">{{ selectedQA.predicted_answer || '(无预测答案)' }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, InfoFilled, Sort, SortDown, Setting } from '@element-plus/icons-vue'
import { getReportView, getReportQuestions } from '@/api/llm'

interface ReportData {
  evaluation_summary: {
    timestamp: string
    total_agents: number
    total_qa_pairs: number
    output_dir: string
  }
  results: Record<string, ModelResult>
  report_info?: {
    id: number
    report_name: string
    model_name: string
    created_at: string
    status: string
  }
}

interface ModelResult {
  model_name: string
  model_version: string
  model_config: {
    name: string
    model: string
    version: string
    temperature: number
    max_tokens: number
    timeout: number
    api_url: string
  }
  metrics: {
    total_samples: number
    successful_predictions: number
    failed_predictions: number
    exact_match: number
    f1_score: number
    semantic_similarity: number
    answer_coverage: number
    answer_relevance: number
    context_utilization: number
    answer_completeness: number
    answer_conciseness: number
    avg_inference_time: number
    total_inference_time: number
    evaluation_time: string
  }
  evaluation_config: {
    match_types: Record<string, any>
    parallel: boolean
    retry_attempts: number
    sample_size: number
    timestamp: string
  }
  question_metrics: Record<string, QuestionMetrics>
}

interface QuestionMetrics {
  exact_match: number
  f1_score: number
  semantic_similarity: number
  answer_coverage: number
  answer_relevance: number
  context_utilization: number
  answer_completeness: number
  answer_conciseness: number
  inference_time: number
  success: number
}

interface QAItem {
  id?: number
  question_id: string
  question: string
  context: string
  predicted_answer: string
  ground_truth: string[]
  metrics: QuestionMetrics
}

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const qaLoading = ref(false)
const reportData = ref<ReportData | null>(null)
const detailDialogVisible = ref(false)
const selectedQA = ref<QAItem | null>(null)

// QA列表数据（从新的API获取）
const qaList = ref<QAItem[]>([])
const qaTotal = ref(0)
const qaPage = ref(1)
const qaPageSize = ref(10)

// 排序相关
const sortBy = ref('f1_score')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 列配置
const availableColumns = [
  { prop: 'question_id', label: 'ID', default: true },
  { prop: 'question', label: '问题', default: true },
  { prop: 'ground_truth', label: '标注答案', default: true },
  { prop: 'predicted_answer', label: '预测答案', default: true },
  { prop: 'metrics', label: '指标得分', default: true },
  { prop: 'inference_time', label: '推理时间', default: true },
  { prop: 'status', label: '状态', default: true },
  { prop: 'action', label: '操作', default: true },
]

// 指标列配置
const metricColumns = [
  { key: 'exact_match', label: '精确匹配', shortLabel: 'EM' },
  { key: 'f1_score', label: 'F1分数', shortLabel: 'F1' },
  { key: 'semantic_similarity', label: '语义相似度', shortLabel: '语义' },
  { key: 'answer_coverage', label: '答案覆盖率', shortLabel: '覆盖' },
  { key: 'answer_relevance', label: '答案相关性', shortLabel: '相关' },
  { key: 'context_utilization', label: '上下文利用率', shortLabel: '上下文' },
  { key: 'answer_completeness', label: '答案完整性', shortLabel: '完整' },
  { key: 'answer_conciseness', label: '答案简洁性', shortLabel: '简洁' },
]

// 可见列（从本地存储读取或默认）
const visibleColumns = ref<string[]>([])
// 可见指标列
const visibleMetricKeys = ref<string[]>(['exact_match', 'f1_score'])

// 指标标签映射
const metricLabels: Record<string, string> = {
  exact_match: '精确匹配',
  f1_score: 'F1分数',
  semantic_similarity: '语义相似度',
  answer_coverage: '答案覆盖率',
  answer_relevance: '答案相关性',
  context_utilization: '上下文利用率',
  answer_completeness: '答案完整性',
  answer_conciseness: '答案简洁性'
}

// 计算属性
const reportId = computed(() => route.params.id as string)

// 修复：使用 report_name 显示文件名
const reportFileName = computed(() => {
  // 优先使用后端返回的 report_name
  if (reportData.value?.report_info?.report_name) {
    return reportData.value.report_info.report_name
  }
  // 回退到 output_dir
  if (reportData.value?.evaluation_summary?.output_dir) {
    const outputDir = reportData.value.evaluation_summary.output_dir
    return outputDir.split('/').pop() || outputDir.split('\\').pop() || outputDir
  }
  return '未知文件'
})

const modelResult = computed(() => {
  if (!reportData.value?.results) return null
  const keys = Object.keys(reportData.value.results)
  const firstKey = keys[0]
  return firstKey ? reportData.value.results[firstKey] : null
})

const matchTypeConfigs = computed(() => {
  if (!modelResult.value?.evaluation_config?.match_types) return []
  
  const configs = []
  const matchTypes = modelResult.value.evaluation_config.match_types
  
  for (const [key, config] of Object.entries(matchTypes)) {
    const label = key.replace('calculate_', '').replace(/_/g, ' ')
    const parts = []
    const cfg = config as Record<string, any>
    
    if (cfg.match_type) parts.push(`match_type=${cfg.match_type}`)
    if (cfg.cal_type) parts.push(`cal_type=${cfg.cal_type}`)
    if (cfg.rel_type) parts.push(`rel_type=${cfg.rel_type}`)
    if (cfg.sim_type) parts.push(`sim_type=${cfg.sim_type}`)
    if (cfg.weights) parts.push(`weights=[${cfg.weights.join(', ')}]`)
    if (cfg.n) parts.push(`n=${cfg.n}`)
    
    configs.push({
      label: label,
      value: parts.length > 0 ? parts.join(', ') : '默认配置'
    })
  }
  
  return configs
})

// 可见的指标列
const visibleMetricColumns = computed(() => {
  return metricColumns.filter(m => visibleMetricKeys.value.includes(m.key))
})

// 方法
function goBack() {
  router.back()
}

function formatPercent(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return (value * 100).toFixed(2) + '%'
}

function formatTime(seconds: number | undefined): string {
  if (seconds === undefined || seconds === null) return '-'
  if (seconds < 1) return (seconds * 1000).toFixed(0) + 'ms'
  return seconds.toFixed(4) + 's'
}

function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function formatGroundTruth(groundTruth: string[] | undefined): string {
  if (!groundTruth || groundTruth.length === 0) return '-'
  return groundTruth.join(' | ')
}

function calculateSuccessRate(metrics: ModelResult['metrics'] | undefined): number {
  if (!metrics) return 0
  return metrics.successful_predictions / metrics.total_samples
}

function getScoreClass(score: number | undefined): string {
  if (score === undefined || score === null) return ''
  if (score >= 0.8) return 'excellent'
  if (score >= 0.6) return 'good'
  if (score >= 0.4) return 'fair'
  return 'poor'
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#95d475'
  if (score >= 0.4) return '#e6a23c'
  return '#f56c6c'
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  loadQAData()
}

function handleSort() {
  loadQAData()
}

function isColumnVisible(prop: string): boolean {
  return visibleColumns.value.includes(prop)
}

// 加载报告基本信息
async function loadReport() {
  loading.value = true
  try {
    const res = await getReportView(parseInt(reportId.value))
    
    if (res.success && res.data) {
      reportData.value = res.data
      // 加载完报告后加载QA数据
      await loadQAData()
    } else {
      ElMessage.error(res.message || '加载报告失败')
    }
  } catch (error) {
    ElMessage.error('加载报告失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载QA详情数据（包含问题、答案等）
async function loadQAData() {
  qaLoading.value = true
  try {
    const res = await getReportQuestions(parseInt(reportId.value), {
      page: qaPage.value,
      limit: qaPageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    })
    
    if (res.success && res.data) {
      qaList.value = res.data.rows.map((row: any) => ({
        id: row.id,
        question_id: row.question_id,
        question: row.question || '',
        context: row.context || '',
        predicted_answer: row.predicted_answer || '',
        ground_truth: row.ground_truth || [],
        metrics: {
          exact_match: row.exact_match || 0,
          f1_score: row.f1_score || 0,
          semantic_similarity: row.semantic_similarity || 0,
          answer_coverage: row.answer_coverage || 0,
          answer_relevance: row.answer_relevance || 0,
          context_utilization: row.context_utilization || 0,
          answer_completeness: row.answer_completeness || 0,
          answer_conciseness: row.answer_conciseness || 0,
          inference_time: row.inference_time || 0,
          success: row.success
        }
      }))
      qaTotal.value = res.data.total
    } else {
      ElMessage.error(res.message || '加载问答对数据失败')
    }
  } catch (error) {
    ElMessage.error('加载问答对数据失败')
    console.error(error)
  } finally {
    qaLoading.value = false
  }
}

function showQADetail(qa: QAItem) {
  selectedQA.value = qa
  detailDialogVisible.value = true
}

// 初始化可见列
function initVisibleColumns() {
  const saved = localStorage.getItem(`report_columns_${reportId.value}`)
  if (saved) {
    visibleColumns.value = JSON.parse(saved)
  } else {
    // 默认显示所有列
    visibleColumns.value = availableColumns.filter(c => c.default).map(c => c.prop)
  }
}

// 监听列配置变化并保存
watch(visibleColumns, (newVal) => {
  localStorage.setItem(`report_columns_${reportId.value}`, JSON.stringify(newVal))
}, { deep: true })

onMounted(() => {
  initVisibleColumns()
  loadReport()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      color: #303133;
    }
    
    .back-text {
      margin-left: 4px;
    }
  }
}

.report-info {
  margin-bottom: 24px;
}

.model-result {
  .model-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;
    
    h2 {
      margin: 0;
      font-size: 20px;
    }
    
    .el-tag {
      background: rgba(255, 255, 255, 0.2);
      border: none;
      color: white;
    }
  }
}

.metrics-section {
  .metric-group {
    margin-bottom: 24px;
    
    .group-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 16px;
      padding-left: 8px;
      border-left: 4px solid #409eff;
    }
  }
}

.metric-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  position: relative;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  }
  
  &.excellent {
    border-top: 3px solid #67c23a;
  }
  
  &.good {
    border-top: 3px solid #95d475;
  }
  
  &.fair {
    border-top: 3px solid #e6a23c;
  }
  
  &.poor {
    border-top: 3px solid #f56c6c;
  }
  
  &.success {
    background: #f0f9eb;
    border-top: 3px solid #67c23a;
  }
  
  &.danger {
    background: #fef0f0;
    border-top: 3px solid #f56c6c;
  }
  
  .metric-value {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
    margin-bottom: 8px;
  }
  
  .metric-label {
    font-size: 12px;
    color: #909399;
  }
  
  .info-icon {
    position: absolute;
    top: 8px;
    right: 8px;
    color: #c0c4cc;
    cursor: help;
  }
}

.config-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  
  .config-tag {
    font-size: 12px;
  }
}

.qa-details-section {
  margin-top: 32px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;
    
    .header-controls {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }
    
    .sort-controls {
      display: flex;
      gap: 8px;
      align-items: center;
    }
  }
}

// 列配置样式
.column-config {
  .config-title {
    font-weight: bold;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #ebeef5;
  }
  
  .el-checkbox {
    display: block;
    margin-bottom: 8px;
  }
}

.qa-table {
  .question-cell {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .answer-cell {
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    
    &.ground-truth {
      color: #67c23a;
    }
    
    &.prediction {
      color: #f56c6c;
    }
  }
  
  .score-bars {
    display: flex;
    flex-direction: column;
    gap: 6px;
    
    .score-bar-item {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .bar-label {
        font-size: 11px;
        color: #909399;
        width: 40px;
        flex-shrink: 0;
      }
      
      :deep(.el-progress) {
        flex: 1;
      }
    }
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

// 详情弹窗样式
.qa-detail-content {
  .detail-metrics {
    margin: 20px 0;
    
    h4 {
      margin-bottom: 16px;
      font-size: 14px;
      color: #606266;
    }
    
    .detail-metrics-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      .detail-metric-item {
        .metric-name {
          display: block;
          font-size: 12px;
          color: #909399;
          margin-bottom: 4px;
        }
      }
    }
  }
  
  .qa-comparison {
    margin-top: 20px;
    
    .qa-block {
      margin-bottom: 16px;
      
      h4 {
        font-size: 13px;
        color: #606266;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ebeef5;
      }
      
      .qa-content {
        padding: 12px;
        background: #f8f9fa;
        border-radius: 6px;
        font-size: 14px;
        line-height: 1.6;
        color: #303133;
        max-height: 200px;
        overflow-y: auto;
        
        &.context {
          background: #f0f9ff;
          color: #409eff;
        }
        
        &.ground-truth {
          background: #f0f9eb;
          color: #67c23a;
        }
        
        &.prediction {
          background: #fff5f5;
          color: #f56c6c;
        }
        
        .answer-item {
          margin-bottom: 8px;
          display: flex;
          align-items: flex-start;
          gap: 8px;
          
          .answer-index {
            flex-shrink: 0;
          }
          
          &:last-child {
            margin-bottom: 0;
          }
        }
        
        .empty-text {
          color: #909399;
          font-style: italic;
        }
      }
    }
    
    .qa-row {
      display: flex;
      gap: 16px;
      
      .qa-block {
        flex: 1;
        
        &.half {
          width: 50%;
        }
      }
    }
  }
}
</style>
