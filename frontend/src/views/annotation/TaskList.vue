<template>
  <div class="page-container">
    <PageHeader title="标注任务管理">
      <template #extra>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>创建任务
        </el-button>
      </template>
    </PageHeader>
    <el-card v-loading="loading">

      <!-- 搜索和筛选 -->
      <div class="action-bar">
        <div class="filter-area">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索任务名称..."
            clearable
            @keyup.enter="handleSearch"
            style="width: 200px"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-select v-model="filters.task_status" placeholder="任务状态" clearable @change="handleSearch">
            <el-option label="未开始" value="未开始" />
            <el-option label="标注中" value="标注中" />
            <el-option label="已完成" value="已完成" />
          </el-select>
          <el-select v-model="filters.annotation_type" placeholder="标注类型" clearable @change="handleSearch">
            <el-option label="LLM 标注" value="llm" />
            <el-option label="人工标注" value="manual" />
            <el-option label="MLB 标注" value="mlb" />
          </el-select>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table :data="tasks" stripe border>
        <el-table-column prop="task_id" label="任务 ID" width="100" show-overflow-tooltip />
        <el-table-column prop="task_name" label="任务名称" min-width="150" />
        <el-table-column prop="local_knowledge_id" label="本地知识库 ID" width="130" show-overflow-tooltip />
        <el-table-column prop="knowledge_base_name" label="本地知识库名称" min-width="150" />
        <el-table-column prop="question_set_id" label="问题集 ID" width="120" show-overflow-tooltip />
        <el-table-column prop="question_set_name" label="问题集名称" min-width="150" />
        <el-table-column prop="label_studio_env_id" label="Label Studio 环境 ID" width="160" show-overflow-tooltip />
        <el-table-column label="标注进度" width="120">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress 
                :percentage="getProgressPercent(row)" 
                :show-text="false"
                :stroke-width="8"
              />
              <span class="progress-text">{{ row.annotated_chunks || 0 }}/{{ row.total_chunks || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="task_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.task_status)">{{ row.task_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="annotation_type" label="标注类型" width="100">
          <template #default="{ row }">
            {{ getAnnotationTypeText(row.annotation_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="task_created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.task_created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
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
          @change="loadTasks" 
        />
      </div>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑标注任务' : '创建标注任务'" 
      width="550px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="140px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="form.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="本地知识库" prop="local_knowledge_id">
          <el-select 
            v-model="form.local_knowledge_id" 
            style="width: 100%" 
            placeholder="请选择知识库"
            :disabled="isEdit"
            @change="onKnowledgeChange"
          >
            <el-option 
              v-for="k in knowledgeList" 
              :key="k.knowledge_id" 
              :label="`${k.knowledge_name}(${k.knowledge_id})`" 
              :value="k.knowledge_id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="问题集" prop="question_set_id">
          <el-select 
            v-model="form.question_set_id" 
            style="width: 100%" 
            placeholder="请选择问题集"
            :disabled="isEdit || !form.local_knowledge_id || questionSetLoading"
            :loading="questionSetLoading"
          >
            <el-option 
              v-for="q in questionSetList" 
              :key="q.question_id" 
              :label="`${q.question_name}(${q.question_id})`" 
              :value="q.question_id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Label Studio 环境" prop="label_studio_env_id">
          <el-select 
            v-model="form.label_studio_env_id" 
            style="width: 100%" 
            placeholder="请选择环境"
            :disabled="isEdit"
          >
            <el-option 
              v-for="env in environmentList" 
              :key="env.label_studio_id" 
              :label="`${env.label_studio_id} - ${env.label_studio_url}`" 
              :value="env.label_studio_id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标注类型" prop="annotation_type">
          <el-select 
            v-model="form.annotation_type" 
            style="width: 100%" 
            placeholder="请选择标注类型"
            :disabled="isEdit"
          >
            <el-option label="LLM 标注" value="llm" />
            <el-option label="人工标注" value="manual" />
            <el-option label="MLB 标注" value="mlb" />
          </el-select>
        </el-form-item>
        
        <!-- 编辑时显示任务状态 -->
        <el-form-item v-if="isEdit" label="任务状态" prop="task_status">
          <el-select v-model="form.task_status" style="width: 100%" placeholder="请选择状态">
            <el-option label="未开始" value="未开始" />
            <el-option label="标注中" value="标注中" />
            <el-option label="已完成" value="已完成" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import Pagination from '@/components/common/Pagination.vue'
import {
  getAnnotationTaskList,
  createAnnotationTask,
  updateAnnotationTask,
  deleteAnnotationTask,
  getLocalKnowledgeListSimple,
  getQuestionsList,
  getLabelStudioEnvironmentsList
} from '@/api/knowledge'
import type { AnnotationTask } from '@/api/knowledge'

const loading = ref(false)
const submitting = ref(false)
const questionSetLoading = ref(false)
const tasks = ref<AnnotationTask[]>([])
const page = ref(1)
const limit = ref(20)
const total = ref(0)

// 筛选条件
const filters = reactive({
  keyword: '',
  task_status: '',
  annotation_type: ''
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentTaskId = ref('')
const formRef = ref()

// 表单数据
const form = reactive({
  task_name: '',
  local_knowledge_id: '',
  question_set_id: '',
  label_studio_env_id: '',
  annotation_type: '',
  task_status: ''
})

const rules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  local_knowledge_id: [{ required: true, message: '请选择本地知识库', trigger: 'change' }],
  question_set_id: [{ required: true, message: '请选择问题集', trigger: 'change' }],
  label_studio_env_id: [{ required: true, message: '请选择 Label Studio 环境', trigger: 'change' }],
  annotation_type: [{ required: true, message: '请选择标注类型', trigger: 'change' }]
}

// 下拉列表数据
const knowledgeList = ref<{ knowledge_id: string; knowledge_name: string }[]>([])
const questionSetList = ref<{ question_id: string; question_name: string }[]>([])
const environmentList = ref<{ label_studio_id: string; label_studio_url: string }[]>([])

// 获取状态类型
function getStatusType(status?: string) {
  const map: Record<string, string> = {
    '未开始': 'info',
    '标注中': 'warning',
    '已完成': 'success'
  }
  return map[status || ''] || 'info'
}

// 获取标注类型显示文本
function getAnnotationTypeText(type?: string) {
  const map: Record<string, string> = {
    'llm': 'LLM 标注',
    'manual': '人工标注',
    'mlb': 'MLB 标注'
  }
  return map[type || ''] || type || '-'
}

// 获取进度百分比
function getProgressPercent(row: AnnotationTask) {
  const annotated = row.annotated_chunks || 0
  const total = row.total_chunks || 0
  return total ? Math.round((annotated / total) * 100) : 0
}

// 格式化日期时间
function formatDateTime(dateStr?: string | null) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

// 加载任务列表
async function loadTasks() {
  loading.value = true
  try {
    const res = await getAnnotationTaskList({
      page: page.value,
      limit: limit.value,
      keyword: filters.keyword || undefined,
      task_status: filters.task_status || undefined,
      annotation_type: filters.annotation_type || undefined
    })
    if (res.success && res.data) {
      tasks.value = res.data.rows || []
      total.value = res.data.total || 0
    } else {
      ElMessage.error(res.message || '获取任务列表失败')
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  page.value = 1
  loadTasks()
}

// 重置筛选
function resetFilters() {
  filters.keyword = ''
  filters.task_status = ''
  filters.annotation_type = ''
  page.value = 1
  loadTasks()
}

// 加载知识库列表
async function loadKnowledges() {
  try {
    const res = await getLocalKnowledgeListSimple()
    if (res.success) {
      knowledgeList.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取知识库列表失败')
    }
  } catch (error) {
    ElMessage.error('获取知识库列表失败')
    console.error(error)
  }
}

// 加载问题集列表
async function loadQuestionSets(knowledgeId: string) {
  if (!knowledgeId) {
    questionSetList.value = []
    return
  }
  questionSetLoading.value = true
  try {
    const res = await getQuestionsList(knowledgeId)
    if (res.success) {
      questionSetList.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取问题集列表失败')
      questionSetList.value = []
    }
  } catch (error) {
    ElMessage.error('获取问题集列表失败')
    console.error(error)
    questionSetList.value = []
  } finally {
    questionSetLoading.value = false
  }
}

// 加载环境列表
async function loadEnvironments() {
  try {
    const res = await getLabelStudioEnvironmentsList()
    if (res.success) {
      environmentList.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取环境列表失败')
    }
  } catch (error) {
    ElMessage.error('获取环境列表失败')
    console.error(error)
  }
}

// 知识库变化
function onKnowledgeChange(knowledgeId: string) {
  form.question_set_id = ''
  if (knowledgeId) {
    loadQuestionSets(knowledgeId)
  } else {
    questionSetList.value = []
  }
}

// 显示创建对话框
function showCreateDialog() {
  isEdit.value = false
  currentTaskId.value = ''
  // 重置表单
  form.task_name = ''
  form.local_knowledge_id = ''
  form.question_set_id = ''
  form.label_studio_env_id = ''
  form.annotation_type = ''
  form.task_status = ''
  questionSetList.value = []
  // 加载下拉数据
  loadKnowledges()
  loadEnvironments()
  dialogVisible.value = true
}

// 显示编辑对话框
function showEditDialog(row: AnnotationTask) {
  isEdit.value = true
  currentTaskId.value = row.task_id
  // 填充表单
  form.task_name = row.task_name
  form.local_knowledge_id = row.local_knowledge_id || ''
  form.question_set_id = row.question_set_id || ''
  form.label_studio_env_id = row.label_studio_env_id || ''
  form.annotation_type = row.annotation_type || ''
  form.task_status = row.task_status || '未开始'
  // 加载下拉数据
  loadKnowledges()
  loadEnvironments()
  // 加载问题集
  if (row.local_knowledge_id) {
    loadQuestionSets(row.local_knowledge_id)
  }
  dialogVisible.value = true
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      // 更新任务
      const res = await updateAnnotationTask({
        task_id: currentTaskId.value,
        task_name: form.task_name,
        task_status: form.task_status
      })
      if (res.success) {
        ElMessage.success('任务更新成功')
        dialogVisible.value = false
        loadTasks()
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } else {
      // 创建任务
      const res = await createAnnotationTask({
        task_name: form.task_name,
        local_knowledge_id: form.local_knowledge_id,
        question_set_id: form.question_set_id,
        label_studio_env_id: form.label_studio_env_id,
        annotation_type: form.annotation_type
      })
      if (res.success) {
        ElMessage.success('任务创建成功')
        dialogVisible.value = false
        loadTasks()
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    }
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 删除任务
function handleDelete(row: AnnotationTask) {
  ElMessageBox.confirm(`确定要删除任务 "${row.task_name}" 吗？`, '确认删除', { type: 'warning' })
    .then(async () => {
      try {
        const res = await deleteAnnotationTask(row.task_id)
        if (res.success) {
          ElMessage.success('任务删除成功')
          loadTasks()
        } else {
          ElMessage.error(res.message || '删除失败')
        }
      } catch (error) {
        ElMessage.error('删除失败')
        console.error(error)
      }
    })
    .catch(() => {})
}

onMounted(() => {
  loadTasks()
})
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

  h2 {
    margin: 0;
    color: #303133;
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

// 进度单元格
.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .progress-text {
    font-size: 12px;
    color: #606266;
    white-space: nowrap;
  }
}

// 分页
.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}
</style>
