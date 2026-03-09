<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <h2>LLM 模型管理</h2>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
      </template>

      <el-table :data="models" stripe border>
        <el-table-column prop="model_name" label="模型名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.model_name)">{{ row.model_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="model_type" label="类型" width="120" />
        <el-table-column prop="api_base" label="API地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已启用' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="checkConnection(row)">检测</el-button>
            <el-button link type="primary" size="small" @click="goToDetail(row.model_name)">详情</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-area">
        <Pagination v-model="page" v-model:page-size="limit" :total="total" @change="loadData" />
      </div>
    </el-card>

    <!-- 创建模型对话框 -->
    <el-dialog v-model="dialogVisible" title="添加模型" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如: gpt-4" />
        </el-form-item>
        <el-form-item label="模型类型" prop="model_type">
          <el-select v-model="form.model_type" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址" prop="api_base">
          <el-input v-model="form.api_base" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API密钥" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="模型描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import Pagination from '@/components/common/Pagination.vue'
import { getModelList, createModel, deleteModel, checkModelConnectivity } from '@/api/llm'
import type { LLMModel } from '@/api/llm'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const models = ref<LLMModel[]>([])
const page = ref(1)
const limit = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  model_name: '',
  model_type: 'openai',
  api_base: '',
  api_key: '',
  description: ''
})
const rules = {
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  api_base: [{ required: true, message: '请输入API地址', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const res = await getModelList()
    if (res.data) {
      models.value = res.data
      total.value = res.data.length
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '获取模型列表失败')
  } finally {
    loading.value = false
  }
}

function goToDetail(modelName: string) {
  router.push(`/llm/models/${modelName}`)
}

function showCreateDialog() {
  dialogVisible.value = true
  // Reset form
  form.model_name = ''
  form.model_type = 'openai'
  form.api_base = ''
  form.api_key = ''
  form.description = ''
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await createModel({
      model_name: form.model_name,
      model_type: form.model_type,
      api_base: form.api_base,
      api_key: form.api_key,
      description: form.description
    })
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

async function checkConnection(row: LLMModel) {
  ElMessage.info(`正在检测 ${row.model_name} 的连接状态...`)
  try {
    const res = await checkModelConnectivity(row.model_name)
    if (res.data?.success) {
      ElMessage.success(`${row.model_name} 连接正常${res.data.latency ? ` (${res.data.latency}ms)` : ''}`)
    } else {
      ElMessage.warning(res.data?.message || `${row.model_name} 连接失败`)
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '检测连接失败')
  }
}

function handleDelete(row: LLMModel) {
  ElMessageBox.confirm(`确定删除模型 ${row.model_name} 吗？`, '确认删除', { type: 'warning' })
    .then(async () => {
      try {
        await deleteModel(row.model_name)
        ElMessage.success('删除成功')
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
.page-container { padding: 20px; background-color: #f5f7fa; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; h2 { margin: 0; color: #303133; } }
.pagination-area { display: flex; justify-content: flex-end; padding-top: 20px; }
</style>
