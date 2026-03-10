<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack"><el-icon><Back /></el-icon></el-button>
            <h2>{{ modelName }}</h2>
          </div>
          <el-button type="primary" @click="showEvaluateDialog">开始评估</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="模型名称">{{ model?.name }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ getModelTypeText(model?.type) }}</el-descriptions-item>
        <el-descriptions-item label="API地址">{{ model?.api_url }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(model?.status)">{{ getStatusText(model?.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="具体模型">{{ model?.model || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ model?.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最大Token">{{ model?.max_tokens || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Temperature">{{ model?.temperature ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="Top P">{{ model?.top_p ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="Timeout">{{ model?.timeout ?? '-' }}s</el-descriptions-item>
      </el-descriptions>

      <h3 class="section-title">评估报告</h3>
      <el-empty v-if="reports.length === 0 && !loading" description="暂无评估报告" />
      <el-table v-else :data="reports" stripe border>
        <el-table-column prop="filename" label="报告名称" min-width="250" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewReport(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="evaluateDialogVisible" title="开始评估" width="500px">
      <el-form :model="evaluateForm" label-width="100px">
        <el-form-item label="问答对组">
          <el-select v-model="evaluateForm.group_id" style="width: 100%">
            <el-option v-for="g in qaGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大并发">
          <el-input-number v-model="evaluateForm.max_workers" :min="1" :max="20" :step="1" />
        </el-form-item>
        <el-form-item label="超时时间">
          <el-input-number v-model="evaluateForm.timeout" :min="10" :max="300" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evaluateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="evaluating" @click="startEvaluate">开始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import { 
  getModelDetail, 
  getEvaluationReports, 
  startEvaluation,
  type LLMModel,
  type EvaluationReport
} from '@/api/llm'

// 详情响应类型
interface ModelDetailResponse {
  config: LLMModel
  connection_status: boolean
  last_evaluation?: string
  evaluation_count: number
  recent_reports: EvaluationReport[]
}

const route = useRoute()
const router = useRouter()
const modelName = route.params.name as string
const loading = ref(false)
const evaluating = ref(false)
const model = ref<LLMModel | null>(null)
const reports = ref<EvaluationReport[]>([])
const evaluateDialogVisible = ref(false)
const evaluateForm = reactive({ 
  group_id: undefined as number | undefined, 
  max_workers: 5,
  timeout: 60
})
const qaGroups = ref([{ id: 1, name: '测试组1' }, { id: 2, name: '测试组2' }])

async function loadData() {
  loading.value = true
  try {
    // Load model details and reports in parallel
    const [modelRes, reportsRes] = await Promise.all([
      getModelDetail(modelName),
      getEvaluationReports(modelName)
    ])
    
    if (modelRes.success && modelRes.data) {
      model.value = modelRes.data.config
    } else {
      ElMessage.error(modelRes.message || '获取模型详情失败')
    }
    
    if (reportsRes.success && reportsRes.data) {
      reports.value = reportsRes.data
    } else {
      ElMessage.error(reportsRes.message || '获取评估报告失败')
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function goBack() { 
  router.back() 
}

function showEvaluateDialog() { 
  evaluateDialogVisible.value = true 
}

async function startEvaluate() {
  if (!evaluateForm.group_id) { 
    ElMessage.warning('请选择问答对组')
    return 
  }
  
  evaluating.value = true
  try {
    const res = await startEvaluation(modelName, {
      qa_group_id: evaluateForm.group_id,
      max_workers: evaluateForm.max_workers,
      timeout: evaluateForm.timeout
    })
    
    if (res.success) {
      ElMessage.success(`评估任务已启动，任务ID: ${res.data?.task_id || 'N/A'}`)
      evaluateDialogVisible.value = false
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
    case 'connected': return '已连接'
    case 'error': return '连接失败'
    default: return '未检测'
  }
}

function viewReport(row: EvaluationReport) { 
  // Open the report file
  window.open(`/api/llm/reports/download?path=${encodeURIComponent(row.path)}`, '_blank')
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
}
.section-title { 
  margin: 24px 0 16px; 
  color: #303133; 
}
</style>
