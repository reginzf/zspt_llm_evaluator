<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <h2>标注任务管理</h2>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>创建任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" stripe border>
        <el-table-column prop="task_name" label="任务名称" min-width="180" />
        <el-table-column prop="task_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.task_status)">{{ row.task_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="annotation_type" label="标注类型" width="120" />
        <el-table-column prop="knowledge_base_name" label="知识库" width="150" />
        <el-table-column prop="question_set_name" label="问题集" width="150" />
        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <span v-if="row.total_chunks">{{ row.annotated_chunks || 0 }} / {{ row.total_chunks }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-area">
        <Pagination v-model="page" v-model:page-size="limit" :total="total" @change="onPageChange" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑任务' : '创建任务'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="form.task_name" />
        </el-form-item>
        <el-form-item label="知识库" prop="knowledge_base_id">
          <el-select v-model="form.knowledge_base_id" style="width: 100%" @change="onKnowledgeChange">
            <el-option v-for="k in knowledgeList" :key="k.kno_id" :label="k.kno_name" :value="k.kno_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题集" prop="question_set_id">
          <el-select v-model="form.question_set_id" style="width: 100%" :disabled="!form.knowledge_base_id || questionSetLoading" :loading="questionSetLoading">
            <el-option v-for="q in questionSetList" :key="q.question_id" :label="q.question_name" :value="q.question_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标注类型" prop="annotation_type">
          <el-select v-model="form.annotation_type" style="width: 100%">
            <el-option label="实体标注" value="ner" />
            <el-option label="分类标注" value="classification" />
            <el-option label="关系标注" value="relation" />
          </el-select>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import Pagination from '@/components/common/Pagination.vue'
import {
  getAnnotationTasks,
  createAnnotationTask,
  updateAnnotationTask,
  deleteAnnotationTask,
  getLocalKnowledgeList,
  getQuestionSets
} from '@/api/knowledge'
import type { AnnotationTask, LocalKnowledge, QuestionSet } from '@/api/knowledge'

const loading = ref(false)
const submitting = ref(false)
const questionSetLoading = ref(false)
const tasks = ref<AnnotationTask[]>([])
const knowledgeList = ref<LocalKnowledge[]>([])
const questionSetList = ref<QuestionSet[]>([])
const page = ref(1)
const limit = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref('')
const formRef = ref()
const form = reactive({
  task_name: '',
  knowledge_base_id: '',
  question_set_id: '',
  annotation_type: ''
})
const rules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  knowledge_base_id: [{ required: true, message: '请选择知识库', trigger: 'change' }],
  question_set_id: [{ required: true, message: '请选择问题集', trigger: 'change' }],
  annotation_type: [{ required: true, message: '请选择标注类型', trigger: 'change' }]
}

function getStatusType(status: string) {
  const map: Record<string, string> = { '未开始': 'info', '进行中': 'warning', '已完成': 'success', '失败': 'danger' }
  return map[status] || 'info'
}

function onPageChange(_page: number, _pageSize: number) {
  // 分页变化时的处理，如果需要可以在这里添加逻辑
}

async function loadTasks(knowledgeId?: string) {
  loading.value = true
  try {
    // 如果没有传入知识库ID，且当前选中了知识库，使用选中的知识库ID
    const knoId = knowledgeId || form.knowledge_base_id
    if (!knoId) {
      tasks.value = []
      total.value = 0
      return
    }
    const res = await getAnnotationTasks(knoId)
    if (res.success) {
      tasks.value = res.data || []
      total.value = tasks.value.length
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

async function loadKnowledges() {
  try {
    const res = await getLocalKnowledgeList()
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

async function loadQuestionSets(knowledgeId: string) {
  if (!knowledgeId) {
    questionSetList.value = []
    return
  }
  questionSetLoading.value = true
  try {
    const res = await getQuestionSets(knowledgeId)
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

function onKnowledgeChange(knowledgeId: string) {
  form.question_set_id = ''
  if (knowledgeId) {
    loadQuestionSets(knowledgeId)
  } else {
    questionSetList.value = []
  }
}

function showCreateDialog() {
  isEdit.value = false
  currentId.value = ''
  Object.assign(form, { task_name: '', knowledge_base_id: '', question_set_id: '', annotation_type: '' })
  questionSetList.value = []
  loadKnowledges()
  dialogVisible.value = true
}

function showEditDialog(row: AnnotationTask) {
  isEdit.value = true
  currentId.value = row.task_id
  Object.assign(form, {
    task_name: row.task_name,
    knowledge_base_id: row.knowledge_base_id || '',
    question_set_id: row.question_set_id || '',
    annotation_type: row.annotation_type || ''
  })
  loadKnowledges()
  if (row.knowledge_base_id) {
    loadQuestionSets(row.knowledge_base_id)
  }
  dialogVisible.value = true
}

async function createTask() {
  try {
    const res = await createAnnotationTask({
      task_name: form.task_name,
      question_set_id: form.question_set_id,
      annotation_type: form.annotation_type,
      local_knowledge_id: form.knowledge_base_id
    })
    if (res.success) {
      ElMessage.success('创建成功')
      dialogVisible.value = false
      loadTasks()
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    ElMessage.error('创建失败')
    console.error(error)
  }
}

async function saveTask() {
  try {
    const res = await updateAnnotationTask({
      task_id: currentId.value,
      task_name: form.task_name
    })
    if (res.success) {
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadTasks()
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
    console.error(error)
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await saveTask()
    } else {
      await createTask()
    }
  } finally {
    submitting.value = false
  }
}

async function deleteTask(row: AnnotationTask) {
  try {
    const res = await deleteAnnotationTask(row.task_id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadTasks()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

function handleDelete(row: AnnotationTask) {
  ElMessageBox.confirm(`确定删除任务 ${row.task_name} 吗？`, '确认删除', { type: 'warning' })
    .then(() => deleteTask(row))
    .catch(() => {})
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped lang="scss">
.page-container { padding: 20px; background-color: #f5f7fa; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; h2 { margin: 0; color: #303133; } }
.pagination-area { display: flex; justify-content: flex-end; padding-top: 20px; }
</style>
