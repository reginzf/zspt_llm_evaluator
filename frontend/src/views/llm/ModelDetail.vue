<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack"><el-icon><Back /></el-icon></el-button>
            <h2>{{ modelName }}</h2>
            <el-tag :type="getStatusType(model?.status)">{{ getStatusText(model?.status) }}</el-tag>
          </div>
          <div class="header-actions">
            <el-button @click="checkConnection" :loading="checking">
              <el-icon><Connection /></el-icon> 检测连通性
            </el-button>
            <el-button type="danger" @click="deleteModel">
              <el-icon><Delete /></el-icon> 删除模型
            </el-button>
          </div>
        </div>
      </template>

      <!-- 模型配置信息 -->
      <el-descriptions :column="2" border>
        <el-descriptions-item label="模型名称">{{ model?.name }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ getModelTypeText(model?.type) }}</el-descriptions-item>
        <el-descriptions-item label="API地址">{{ model?.api_url }}</el-descriptions-item>
        <el-descriptions-item label="API密钥">
          <span class="api-key-mask">********</span>
        </el-descriptions-item>
        <el-descriptions-item label="具体模型">{{ model?.model || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ model?.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="温度参数">{{ model?.temperature ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="最大Token">{{ model?.max_tokens || '-' }}</el-descriptions-item>
        <el-descriptions-item label="超时时间">{{ model?.timeout ? model.timeout + '秒' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(model?.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <!-- 统计信息卡片 -->
      <h3 class="section-title">评估统计</h3>
      <div class="stats-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.evalCount }}</div>
            <div class="stat-label">评估次数</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">🎯</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgExactMatch }}</div>
            <div class="stat-label">平均精确匹配</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">📈</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgF1Score }}</div>
            <div class="stat-label">平均F1分数</div>
          </div>
        </el-card>
      </div>

      <!-- 历史报告列表 -->
      <h3 class="section-title">评估报告</h3>
      
      <!-- 搜索和操作栏 -->
      <div class="action-bar">
        <el-button type="primary" @click="showEvaluateDialog">
          <el-icon><VideoPlay /></el-icon> 开始评估
        </el-button>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索报告名称..."
          clearable
          style="width: 250px"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        <el-button @click="loadData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-empty v-if="filteredReports.length === 0 && !loading" description="暂无评估报告" />
      <el-table v-else :data="paginatedReports" stripe border>
        <el-table-column prop="report_name" label="报告名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="评估时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="group_name" label="问答对组" width="150" show-overflow-tooltip />
        <el-table-column prop="qa_count" label="问答对数量" width="100" />
        <el-table-column label="精确匹配" width="100">
          <template #default="{ row }">
            {{ row.exact_match ? (row.exact_match * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="F1分数" width="100">
          <template #default="{ row }">
            {{ row.f1_score ? (row.f1_score * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="语义相似度" width="100">
          <template #default="{ row }">
            {{ row.semantic_similarity ? (row.semantic_similarity * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewReport(row)">查看</el-button>
            <el-button link type="danger" size="small" @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-area" v-if="filteredReports.length > 0">
        <Pagination 
          v-model="page" 
          v-model:page-size="pageSize" 
          :total="filteredReports.length" 
          @change="handlePageChange" 
        />
      </div>
    </el-card>

    <!-- 评估配置对话框 -->
    <el-dialog v-model="evaluateDialogVisible" title="配置评估参数" width="700px">
      <el-form :model="evaluateForm" label-width="120px">
        <el-form-item label="问答对组" required>
          <el-select v-model="evaluateForm.group_id" style="width: 100%" placeholder="请选择问答对组">
            <el-option 
              v-for="g in qaGroups" 
              :key="g.id" 
              :label="`${g.name} (${g.qa_count || 0}条)`" 
              :value="g.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="起始位置">
              <el-input-number v-model="evaluateForm.offset" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="评估数量">
              <el-input-number v-model="evaluateForm.limit" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="并行处理">
              <el-select v-model="evaluateForm.parallel" style="width: 100%">
                <el-option label="顺序处理" :value="false" />
                <el-option label="并行处理" :value="true" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="并行工作数">
              <el-input-number v-model="evaluateForm.max_workers" :min="1" :max="10" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 高级评估指标配置 -->
        <el-form-item>
          <el-link type="primary" @click="showAdvancedConfig = !showAdvancedConfig">
            <el-icon><ArrowDown v-if="showAdvancedConfig" /><ArrowRight v-else /></el-icon>
            高级评估指标配置（匹配类型）
          </el-link>
        </el-form-item>

        <div v-show="showAdvancedConfig" class="advanced-config">
          <!-- 精确匹配 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.exactMatch.enabled">精确匹配 (Exact Match)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.exactMatch.enabled">
              <el-select v-model="matchTypes.exactMatch.type" size="small">
                <el-option label="normalized (默认标准化)" value="normalized" />
                <el-option label="strict (严格匹配)" value="strict" />
                <el-option label="fuzzy (模糊匹配)" value="fuzzy" />
                <el-option label="semantic (语义匹配)" value="semantic" />
                <el-option label="rouge (ROUGE匹配)" value="rouge" />
              </el-select>
            </div>
          </div>

          <!-- F1分数 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.f1Score.enabled">F1分数 (F1 Score)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.f1Score.enabled">
              <el-select v-model="matchTypes.f1Score.type" size="small">
                <el-option label="word (默认词汇)" value="" />
                <el-option label="rouge (ROUGE)" value="rouge" />
                <el-option label="semantic (语义)" value="semantic" />
                <el-option label="jaccard (Jaccard)" value="jaccard" />
              </el-select>
            </div>
          </div>

          <!-- 语义相似度 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.semanticSim.enabled">语义相似度 (Semantic Similarity)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.semanticSim.enabled">
              <el-select v-model="matchTypes.semanticSim.type" size="small">
                <el-option label="sentence_transformer (默认)" value="" />
                <el-option label="bert (BERT)" value="bert" />
                <el-option label="tfidf (TF-IDF)" value="tfidf" />
                <el-option label="word2vec (Word2Vec)" value="word2vec" />
              </el-select>
            </div>
          </div>

          <!-- 答案覆盖率 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.coverage.enabled">答案覆盖率 (Answer Coverage)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.coverage.enabled">
              <el-select v-model="matchTypes.coverage.type" size="small">
                <el-option label="simple (默认简单)" value="simple" />
                <el-option label="rouge (ROUGE)" value="rouge" />
                <el-option label="sentence (句子)" value="sentence" />
                <el-option label="weighted (加权)" value="weighted" />
              </el-select>
              <!-- weighted权重配置 -->
              <div v-if="matchTypes.coverage.type === 'weighted'" class="weighted-config">
                <div class="weight-label">权重配置 (和必须为1):</div>
                <div class="weight-inputs">
                  <div class="weight-item">
                    <span>rouge</span>
                    <el-input-number v-model="matchTypes.coverage.weights[0]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>sentence</span>
                    <el-input-number v-model="matchTypes.coverage.weights[1]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 答案相关性 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.relevance.enabled">答案相关性 (Answer Relevance)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.relevance.enabled">
              <el-select v-model="matchTypes.relevance.type" size="small">
                <el-option label="word_overlap (默认词汇重叠)" value="" />
                <el-option label="semantic (语义)" value="semantic" />
                <el-option label="tfidf (TF-IDF)" value="tfidf" />
                <el-option label="rouge (ROUGE)" value="rouge" />
                <el-option label="weighted (加权)" value="weighted" />
              </el-select>
              <!-- weighted权重配置 -->
              <div v-if="matchTypes.relevance.type === 'weighted'" class="weighted-config">
                <div class="weight-label">权重配置 (和必须为1):</div>
                <div class="weight-inputs">
                  <div class="weight-item">
                    <span>word_overlap</span>
                    <el-input-number v-model="matchTypes.relevance.weights[0]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>semantic</span>
                    <el-input-number v-model="matchTypes.relevance.weights[1]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>tfidf</span>
                    <el-input-number v-model="matchTypes.relevance.weights[2]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 上下文利用率 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.utilization.enabled">上下文利用率 (Context Utilization)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.utilization.enabled">
              <el-select v-model="matchTypes.utilization.type" size="small">
                <el-option label="simple (默认简单)" value="simple" />
                <el-option label="semantic (语义)" value="semantic" />
                <el-option label="tfidf (TF-IDF)" value="tfidf" />
                <el-option label="weighted (加权)" value="weighted" />
              </el-select>
              <!-- weighted权重配置 -->
              <div v-if="matchTypes.utilization.type === 'weighted'" class="weighted-config">
                <div class="weight-label">权重配置 (和必须为1):</div>
                <div class="weight-inputs">
                  <div class="weight-item">
                    <span>semantic</span>
                    <el-input-number v-model="matchTypes.utilization.weights[0]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>tfidf</span>
                    <el-input-number v-model="matchTypes.utilization.weights[1]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>rouge</span>
                    <el-input-number v-model="matchTypes.utilization.weights[2]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>ngram</span>
                    <el-input-number v-model="matchTypes.utilization.weights[3]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                </div>
                <div class="weight-item ngram-config">
                  <span>N-gram N值:</span>
                  <el-input-number v-model="matchTypes.utilization.nValue" :min="1" :max="5" :step="1" size="small" style="width: 80px" />
                </div>
              </div>
            </div>
          </div>

          <!-- 答案完整性 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.completeness.enabled">答案完整性 (Answer Completeness)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.completeness.enabled">
              <el-select v-model="matchTypes.completeness.type" size="small">
                <el-option label="simple (默认简单)" value="simple" />
                <el-option label="coverage (覆盖度)" value="coverage" />
                <el-option label="entities (实体)" value="entities" />
                <el-option label="rouge (ROUGE)" value="rouge" />
                <el-option label="weighted (加权)" value="weighted" />
              </el-select>
              <!-- weighted权重配置 -->
              <div v-if="matchTypes.completeness.type === 'weighted'" class="weighted-config">
                <div class="weight-label">权重配置 (和必须为1):</div>
                <div class="weight-inputs">
                  <div class="weight-item">
                    <span>coverage</span>
                    <el-input-number v-model="matchTypes.completeness.weights[0]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>entities</span>
                    <el-input-number v-model="matchTypes.completeness.weights[1]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>rouge</span>
                    <el-input-number v-model="matchTypes.completeness.weights[2]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 答案简洁性 -->
          <div class="match-type-item">
            <el-checkbox v-model="matchTypes.conciseness.enabled">答案简洁性 (Answer Conciseness)</el-checkbox>
            <div class="match-type-config" v-if="matchTypes.conciseness.enabled">
              <el-select v-model="matchTypes.conciseness.type" size="small">
                <el-option label="ratio (默认长度比例)" value="" />
                <el-option label="semantic (语义压缩度)" value="semantic" />
                <el-option label="density (信息密度)" value="density" />
                <el-option label="weighted (加权)" value="weighted" />
              </el-select>
              <!-- weighted权重配置 -->
              <div v-if="matchTypes.conciseness.type === 'weighted'" class="weighted-config">
                <div class="weight-label">权重配置 (和必须为1):</div>
                <div class="weight-inputs">
                  <div class="weight-item">
                    <span>ratio</span>
                    <el-input-number v-model="matchTypes.conciseness.weights[0]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>semantic</span>
                    <el-input-number v-model="matchTypes.conciseness.weights[1]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                  <div class="weight-item">
                    <span>rouge</span>
                    <el-input-number v-model="matchTypes.conciseness.weights[2]" :min="0" :max="1" :step="0.1" size="small" style="width: 80px" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="evaluateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="evaluating" @click="startEvaluate">开始评估</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Connection, Delete, VideoPlay, Search, Refresh, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import Pagination from '@/components/common/Pagination.vue'
import { 
  getModelDetail, 
  getEvaluationReports, 
  startEvaluation,
  deleteModel as deleteModelApi,
  checkModelConnectivity,
  deleteEvaluationReport,
  type LLMModel,
  type EvaluationReport
} from '@/api/llm'
import { getQAGroups } from '@/api/qa'

interface ReportWithMetrics extends EvaluationReport {
  id: number
  report_name: string
  group_name?: string
  qa_count?: number
  exact_match?: number
  f1_score?: number
  semantic_similarity?: number
}

const route = useRoute()
const router = useRouter()
const modelName = route.params.name as string
const loading = ref(false)
const checking = ref(false)
const evaluating = ref(false)
const model = ref<LLMModel | null>(null)
const reports = ref<ReportWithMetrics[]>([])
const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(20)

// 统计数据
const stats = reactive({
  evalCount: 0,
  avgExactMatch: '-',
  avgF1Score: '-'
})

// 评估对话框
const evaluateDialogVisible = ref(false)
const showAdvancedConfig = ref(false)
const qaGroups = ref<Array<{id: number, name: string, qa_count?: number}>>([])

const evaluateForm = reactive({
  group_id: undefined as number | undefined,
  offset: 0,
  limit: 100,
  parallel: false,
  max_workers: 4
})

// 匹配类型配置
const matchTypes = reactive({
  exactMatch: { enabled: true, type: 'normalized' },
  f1Score: { enabled: true, type: '' },
  semanticSim: { enabled: true, type: '' },
  coverage: { enabled: true, type: 'simple', weights: [0.5, 0.5] },
  relevance: { enabled: true, type: '', weights: [0.4, 0.4, 0.2] },
  utilization: { enabled: true, type: 'simple', weights: [0.3, 0.3, 0.2, 0.2], nValue: 2 },
  completeness: { enabled: true, type: 'simple', weights: [0.5, 0.25, 0.25] },
  conciseness: { enabled: true, type: '', weights: [0.4, 0.4, 0.2] }
})

// 过滤后的报告
const filteredReports = computed(() => {
  if (!searchKeyword.value.trim()) return reports.value
  const keyword = searchKeyword.value.toLowerCase()
  return reports.value.filter(r => 
    (r.report_name || '').toLowerCase().includes(keyword) ||
    (r.group_name || '').toLowerCase().includes(keyword)
  )
})

// 分页后的报告
const paginatedReports = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredReports.value.slice(start, start + pageSize.value)
})

async function loadData() {
  loading.value = true
  try {
    const [modelRes, reportsRes] = await Promise.all([
      getModelDetail(modelName),
      getEvaluationReports(modelName)
    ])
    
    if (modelRes.success && modelRes.data) {
      model.value = modelRes.data.config
    }
    
    if (reportsRes.success && reportsRes.data) {
      // API returns paginated format: {rows, total, page, limit, pages}
      const reportData = reportsRes.data as any
      reports.value = (reportData.rows || []) as ReportWithMetrics[]
      updateStats()
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function updateStats() {
  stats.evalCount = reports.value.length
  
  if (reports.value.length === 0) {
    stats.avgExactMatch = '-'
    stats.avgF1Score = '-'
    return
  }
  
  let totalExactMatch = 0
  let totalF1Score = 0
  let count = 0
  
  reports.value.forEach(r => {
    if (r.exact_match !== null && r.exact_match !== undefined) {
      totalExactMatch += r.exact_match
      count++
    }
    if (r.f1_score !== null && r.f1_score !== undefined) {
      totalF1Score += r.f1_score
    }
  })
  
  if (count > 0) {
    stats.avgExactMatch = (totalExactMatch / count * 100).toFixed(2) + '%'
    stats.avgF1Score = (totalF1Score / count * 100).toFixed(2) + '%'
  }
}

function handleSearch() {
  page.value = 1
}

function handlePageChange() {
  // 分页由 computed 自动处理
}

async function checkConnection() {
  checking.value = true
  try {
    const res = await checkModelConnectivity(modelName)
    if (res.success && res.data?.success) {
      ElMessage.success(`${modelName} 连接正常${res.data.latency ? ` (${res.data.latency}ms)` : ''}`)
      loadData()
    } else {
      ElMessage.warning(res.data?.message || `${modelName} 连接失败`)
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '检测连接失败')
  } finally {
    checking.value = false
  }
}

function deleteModel() {
  ElMessageBox.confirm(`确定要删除模型 "${modelName}" 吗？此操作不可恢复！`, '确认删除', {
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  })
    .then(async () => {
      try {
        await deleteModelApi(modelName)
        ElMessage.success('模型删除成功')
        router.push('/llm/models')
      } catch (error: any) {
        ElMessage.error(error?.message || '删除失败')
      }
    })
    .catch(() => {})
}

async function showEvaluateDialog() {
  evaluateDialogVisible.value = true
  // 加载问答对组
  try {
    const res = await getQAGroups({ limit: 100 })
    if (res.success && res.data) {
      qaGroups.value = res.data.rows || []
    }
  } catch (error) {
    console.error('加载问答对组失败:', error)
  }
}

function getMatchTypesConfig() {
  const matchTypesConfig: Record<string, any> = {}
  
  if (matchTypes.exactMatch.enabled) {
    matchTypesConfig.calculate_exact_match = { match_type: matchTypes.exactMatch.type }
  }
  if (matchTypes.f1Score.enabled) {
    matchTypesConfig.calculate_f1_score = matchTypes.f1Score.type ? { cal_type: matchTypes.f1Score.type } : {}
  }
  if (matchTypes.semanticSim.enabled) {
    matchTypesConfig.calculate_semantic_similarity = matchTypes.semanticSim.type ? { sim_type: matchTypes.semanticSim.type } : {}
  }
  if (matchTypes.coverage.enabled) {
    const config: Record<string, any> = { cal_type: matchTypes.coverage.type }
    if (matchTypes.coverage.type === 'weighted') {
      config.weights = matchTypes.coverage.weights
    }
    matchTypesConfig.calculate_answer_coverage = config
  }
  if (matchTypes.relevance.enabled) {
    const config: Record<string, any> = matchTypes.relevance.type ? { rel_type: matchTypes.relevance.type } : {}
    if (matchTypes.relevance.type === 'weighted') {
      config.weights = matchTypes.relevance.weights
    }
    matchTypesConfig.calculate_answer_relevance = config
  }
  if (matchTypes.utilization.enabled) {
    const config: Record<string, any> = { cal_type: matchTypes.utilization.type }
    if (matchTypes.utilization.type === 'weighted') {
      config.weights = matchTypes.utilization.weights
      config.n = matchTypes.utilization.nValue
    }
    matchTypesConfig.calculate_context_utilization = config
  }
  if (matchTypes.completeness.enabled) {
    const config: Record<string, any> = { cal_type: matchTypes.completeness.type }
    if (matchTypes.completeness.type === 'weighted') {
      config.weights = matchTypes.completeness.weights
    }
    matchTypesConfig.calculate_completeness = config
  }
  if (matchTypes.conciseness.enabled) {
    const config: Record<string, any> = matchTypes.conciseness.type ? { cal_type: matchTypes.conciseness.type } : {}
    if (matchTypes.conciseness.type === 'weighted') {
      config.weights = matchTypes.conciseness.weights
    }
    matchTypesConfig.calculate_conciseness = config
  }
  
  return matchTypesConfig
}

async function startEvaluate() {
  if (!evaluateForm.group_id) {
    ElMessage.warning('请选择问答对组')
    return
  }
  
  evaluating.value = true
  try {
    const matchTypesConfig = getMatchTypesConfig()
    
    const res = await startEvaluation(modelName, {
      group_id: evaluateForm.group_id,
      offset: evaluateForm.offset,
      limit: evaluateForm.limit,
      parallel: evaluateForm.parallel,
      max_workers: evaluateForm.max_workers,
      match_types: matchTypesConfig
    })
    
    if (res.success) {
      ElMessage.success(`评估任务已启动，任务ID: ${res.data?.task_id || 'N/A'}`)
      evaluateDialogVisible.value = false
      setTimeout(() => loadData(), 2000)
    } else {
      ElMessage.error(res.message || '启动评估失败')
    }
  } catch (error) {
    ElMessage.error('启动评估失败')
    console.error(error)
  } finally {
    evaluating.value = false
  }
}

function viewReport(row: ReportWithMetrics) {
  // 使用后端 /api/llm/report/<path> 路由，直接返回 HTML 报告页面
  const reportPath = row.path || (row as any).report_path
  if (reportPath) {
    window.open(`/api/llm/report/${reportPath}`, '_blank')
  } else {
    ElMessage.error('报告路径不存在')
  }
}

function deleteReport(row: ReportWithMetrics) {
  ElMessageBox.confirm(`确定要删除报告 "${row.report_name}" 吗？`, '确认删除', { type: 'warning' })
    .then(async () => {
      try {
        await deleteEvaluationReport(row.id)
        ElMessage.success('报告删除成功')
        loadData()
      } catch (error: any) {
        ElMessage.error(error?.message || '删除失败')
      }
    })
    .catch(() => {})
}

function goBack() {
  router.push('/llm/models')
}

function getModelTypeText(type?: string) {
  const typeMap: Record<string, string> = {
    'deepseek': 'DeepSeek',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'qwen': '通义千问',
    'other': '其他'
  }
  return typeMap[type || ''] || type || '未知'
}

function getStatusType(status?: string) {
  switch (status) {
    case 'connected': return 'success'
    case 'error': return 'danger'
    default: return 'info'
  }
}

function getStatusText(status?: string) {
  switch (status) {
    case 'connected': return '✓ 已连接'
    case 'error': return '✗ 连接失败'
    default: return '? 未检测'
  }
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => loadData())
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h2 {
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.api-key-mask {
  color: #909399;
  letter-spacing: 2px;
}

.section-title {
  margin: 24px 0 16px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

// 统计卡片
.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  :deep(.el-card__body) {
    display: flex;
    align-items: center;
    padding: 20px;
  }

  .stat-icon {
    font-size: 36px;
    margin-right: 16px;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #303133;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 14px;
    color: #909399;
  }
}

// 操作栏
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 12px;
}

// 分页
.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}

// 高级配置
.advanced-config {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-top: 10px;
}

.match-type-item {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  margin-bottom: 10px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.match-type-config {
  margin-top: 8px;
  margin-left: 24px;
}

// weighted权重配置
.weighted-config {
  margin-top: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  
  .weight-label {
    font-size: 12px;
    color: #606266;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  .weight-inputs {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  
  .weight-item {
    display: flex;
    align-items: center;
    gap: 8px;
    
    span {
      font-size: 12px;
      color: #606266;
    }
    
    &.ngram-config {
      margin-top: 8px;
    }
  }
}
</style>
