<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><Back /></el-icon>
              <span class="back-text">返回首页</span>
            </el-button>
            <h2>LLM 模型管理</h2>
          </div>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增模型
          </el-button>
        </div>
      </template>

      <!-- 统计信息卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">🤖</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">模型总数</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">✓</div>
          <div class="stat-content">
            <div class="stat-value" style="color: #67c23a">{{ stats.connected }}</div>
            <div class="stat-label">已连接</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.evaluations }}</div>
            <div class="stat-label">评估次数</div>
          </div>
        </el-card>
      </div>

      <!-- 搜索和筛选 -->
      <div class="action-bar">
        <div class="filter-area">
          <el-select v-model="filters.type" placeholder="所有类型" clearable @change="handleFilterChange">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="通义千问(Qwen)" value="qwen" />
            <el-option label="其他" value="other" />
          </el-select>
          <el-select v-model="filters.status" placeholder="所有状态" clearable @change="handleFilterChange">
            <el-option label="已连接" value="connected" />
            <el-option label="连接失败" value="error" />
            <el-option label="未检测" value="unknown" />
          </el-select>
          <el-input
            v-model="filters.keyword"
            placeholder="搜索模型名称..."
            clearable
            @keyup.enter="handleFilterChange"
            style="width: 200px"
          >
            <template #append>
              <el-button @click="handleFilterChange">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table :data="models" stripe border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="模型名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.name)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getModelTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="api_url" label="API地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="100">
          <template #default="{ row }">
            {{ row.version || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="checkConnection(row)">检测</el-button>
            <el-button link type="primary" size="small" @click="editModel(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-area">
        <Pagination 
          v-model="page" 
          v-model:page-size="limit" 
          :total="total" 
          @change="loadData" 
        />
      </div>
    </el-card>

    <!-- 新增/编辑模型对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEditing ? '编辑模型' : '新增模型'" 
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="模型名称" prop="name">
          <el-input 
            v-model="form.name" 
            placeholder="请输入模型名称"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="form.type" style="width: 100%" placeholder="请选择">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="通义千问(Qwen)" value="qwen" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="API密钥" prop="api_key">
          <el-input 
            v-model="form.api_key" 
            type="password" 
            show-password
            placeholder="请输入API密钥"
          />
        </el-form-item>
        <el-form-item label="API地址" prop="api_url">
          <el-input 
            v-model="form.api_url" 
            placeholder="https://api.example.com/v1/chat/completions"
          />
        </el-form-item>
        <el-form-item label="具体模型名称">
          <el-input 
            v-model="form.model" 
            placeholder="如: gpt-4, deepseek-chat"
          />
        </el-form-item>
        <el-form-item label="温度参数">
          <el-slider v-model="form.temperature" :min="0" :max="1" :step="0.1" show-stops />
          <span class="slider-value">{{ form.temperature }}</span>
        </el-form-item>
        <el-form-item label="最大Token数">
          <el-input-number v-model="form.max_tokens" :min="1" :max="8192" :step="100" />
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="form.timeout" :min="1" :max="300" :step="5" />
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="form.version" placeholder="如: 20240201" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Back, Search, Refresh } from '@element-plus/icons-vue'
import Pagination from '@/components/common/Pagination.vue'
import { getModelList, createModel, updateModel, deleteModel, checkModelConnectivity } from '@/api/llm'
import type { LLMModel } from '@/api/llm'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const models = ref<LLMModel[]>([])
const page = ref(1)
const limit = ref(20)
const total = ref(0)

// 统计数据
const stats = reactive({
  total: 0,
  connected: 0,
  evaluations: 0
})

// 筛选条件
const filters = reactive({
  type: '',
  status: '',
  keyword: ''
})

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingModelName = ref('')
const formRef = ref()

// 表单数据 - 与后端字段保持一致
const form = reactive({
  name: '',
  type: '',
  api_key: '',
  api_url: '',
  model: '',
  temperature: 0.7,
  max_tokens: 2048,
  timeout: 30,
  version: ''
})

const rules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }],
  api_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }]
}

// 获取模型类型显示文本
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

// 获取状态类型
function getStatusType(status?: string) {
  switch (status) {
    case 'connected': return 'success'
    case 'error': return 'danger'
    default: return 'info'
  }
}

// 获取状态显示文本
function getStatusText(status?: string) {
  switch (status) {
    case 'connected': return '✓ 已连接'
    case 'error': return '✗ 连接失败'
    default: return '? 未检测'
  }
}

// 格式化日期
function formatDate(dateStr?: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const res = await getModelList({
      page: page.value,
      limit: limit.value,
      type: filters.type || undefined,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined
    })
    if (res.success && res.data) {
      models.value = res.data.rows || []
      total.value = res.data.total || 0
      // 更新统计
      stats.total = res.data.total || 0
      stats.connected = models.value.filter(m => m.status === 'connected').length
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '获取模型列表失败')
  } finally {
    loading.value = false
  }
}

// 筛选变化
function handleFilterChange() {
  page.value = 1
  loadData()
}

// 重置筛选
function resetFilters() {
  filters.type = ''
  filters.status = ''
  filters.keyword = ''
  page.value = 1
  loadData()
}

// 返回首页
function goBack() {
  router.push('/')
}

// 跳转到详情
function goToDetail(modelName: string) {
  router.push(`/llm/models/${modelName}`)
}

// 显示创建对话框
function showCreateDialog() {
  isEditing.value = false
  editingModelName.value = ''
  // 重置表单
  form.name = ''
  form.type = ''
  form.api_key = ''
  form.api_url = ''
  form.model = ''
  form.temperature = 0.7
  form.max_tokens = 2048
  form.timeout = 30
  form.version = ''
  dialogVisible.value = true
}

// 编辑模型
async function editModel(row: LLMModel) {
  isEditing.value = true
  editingModelName.value = row.name
  // 填充表单
  form.name = row.name
  form.type = row.type || ''
  form.api_key = row.api_key || ''
  form.api_url = row.api_url || ''
  form.model = row.model || ''
  form.temperature = row.temperature ?? 0.7
  form.max_tokens = row.max_tokens ?? 2048
  form.timeout = row.timeout ?? 30
  form.version = row.version || ''
  dialogVisible.value = true
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value) {
      // 更新模型
      await updateModel(editingModelName.value, {
        type: form.type,
        api_key: form.api_key,
        api_url: form.api_url,
        model: form.model || undefined,
        temperature: form.temperature,
        max_tokens: form.max_tokens,
        timeout: form.timeout,
        version: form.version || undefined
      })
      ElMessage.success('模型更新成功')
    } else {
      // 创建模型 - 字段名与后端保持一致
      await createModel({
        name: form.name,
        type: form.type,
        api_key: form.api_key,
        api_url: form.api_url,
        model: form.model || undefined,
        temperature: form.temperature,
        max_tokens: form.max_tokens,
        timeout: form.timeout,
        version: form.version || undefined
      })
      ElMessage.success('模型创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error?.message || (isEditing.value ? '更新失败' : '创建失败'))
  } finally {
    submitting.value = false
  }
}

// 检测连接
async function checkConnection(row: LLMModel) {
  ElMessage.info(`正在检测 ${row.name} 的连接状态...`)
  try {
    const res = await checkModelConnectivity(row.name)
    if (res.success && res.data?.success) {
      ElMessage.success(`${row.name} 连接正常${res.data.latency ? ` (${res.data.latency}ms)` : ''}`)
      // 刷新列表更新状态
      loadData()
    } else {
      ElMessage.warning(res.data?.message || `${row.name} 连接失败`)
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '检测连接失败')
  }
}

// 删除模型
function handleDelete(row: LLMModel) {
  ElMessageBox.confirm(`确定要删除模型 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    .then(async () => {
      try {
        await deleteModel(row.name)
        ElMessage.success('模型删除成功')
        loadData()
      } catch (error: any) {
        ElMessage.error(error?.message || '删除失败')
      }
    })
    .catch(() => {})
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
  }

  .back-text {
    margin-left: 4px;
  }

  h2 {
    margin: 0;
    color: #303133;
  }
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
  margin-bottom: 20px;

  .filter-area {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
}

// 分页
.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}

// 滑块值
.slider-value {
  margin-left: 12px;
  color: #606266;
}
</style>
