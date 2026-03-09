<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><Back /></el-icon>
            </el-button>
            <h2>{{ group?.name || '分组详情' }}</h2>
          </div>
          <div class="header-right">
            <el-button @click="showEditDialog">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="primary" @click="showCreateQAItemDialog">
              <el-icon><Plus /></el-icon>
              添加问答对
            </el-button>
            <el-button type="success" @click="goToImport">
              <el-icon><Upload /></el-icon>
              导入
            </el-button>
          </div>
        </div>
      </template>

      <!-- 分组信息 -->
      <el-descriptions v-if="group" :column="3" border class="group-info">
        <el-descriptions-item label="ID">{{ group.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ group.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="group.is_active ? 'success' : 'info'">
            {{ group.is_active ? '已激活' : '已停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="测试类型">
          {{ getTestTypeLabel(group.test_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="语言">
          {{ getLanguageLabel(group.language) }}
        </el-descriptions-item>
        <el-descriptions-item label="难度范围">
          {{ group.difficulty_range || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用途" :span="3">
          {{ group.purpose || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="3">
          <el-tag
            v-for="tag in formatTags(group.tags)"
            :key="tag"
            size="small"
            class="tag-item"
          >
            {{ tag }}
          </el-tag>
          <span v-if="!group.tags || group.tags.length === 0">-</span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 问答对列表 -->
      <div class="qa-items-section">
        <h3>问答对列表</h3>
        <el-table
          :data="qaItems"
          stripe
          border
          style="width: 100%"
          v-loading="qaStore.loading"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="answers" label="答案" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatAnswers(row.answers) }}
            </template>
          </el-table-column>
          <el-table-column prop="question_type" label="问题类型" width="120" />
          <el-table-column prop="difficulty_level" label="难度" width="80" align="center" />
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showEditQAItemDialog(row)">
                编辑
              </el-button>
              <el-button link type="danger" size="small" @click="handleDeleteQAItem(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-area">
          <Pagination
            v-model="pagination.page"
            v-model:page-size="pagination.limit"
            :total="pagination.total"
            @change="handlePageChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 编辑分组对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑分组" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="用途描述">
          <el-input v-model="editForm.purpose" type="textarea" :rows="3" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="测试类型" prop="test_type">
              <el-select v-model="editForm.test_type" style="width: 100%">
                <el-option label="自定义测试" value="custom" />
                <el-option label="准确率测试" value="accuracy" />
                <el-option label="性能测试" value="performance" />
                <el-option label="鲁棒性测试" value="robustness" />
                <el-option label="综合测试" value="comprehensive" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="语言" prop="language">
              <el-select v-model="editForm.language" style="width: 100%">
                <el-option label="中文" value="zh" />
                <el-option label="英文" value="en" />
                <el-option label="多语言" value="multi" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="难度范围">
          <el-input v-model="editForm.difficulty_range" placeholder="如: 1-5" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="editForm.tagsInput" placeholder="用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateGroup" :loading="qaStore.submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 问答对表单对话框 -->
    <el-dialog
      v-model="qaItemDialogVisible"
      :title="isEditQAItem ? '编辑问答对' : '添加问答对'"
      width="700px"
    >
      <el-form ref="qaItemFormRef" :model="qaItemForm" :rules="qaItemRules" label-width="100px">
        <el-form-item label="问题" prop="question">
          <el-input
            v-model="qaItemForm.question"
            type="textarea"
            :rows="3"
            placeholder="请输入问题"
          />
        </el-form-item>
        <el-form-item label="答案" prop="answers">
          <el-input
            v-model="qaItemForm.answersInput"
            type="textarea"
            :rows="4"
            placeholder="请输入答案，多个答案用换行分隔"
          />
        </el-form-item>
        <el-form-item label="上下文">
          <el-input
            v-model="qaItemForm.context"
            type="textarea"
            :rows="3"
            placeholder="可选：输入上下文/背景信息"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="问题类型">
              <el-select v-model="qaItemForm.question_type" style="width: 100%" clearable>
                <el-option label="事实型" value="factual" />
                <el-option label="上下文型" value="contextual" />
                <el-option label="概念型" value="conceptual" />
                <el-option label="推理型" value="reasoning" />
                <el-option label="应用型" value="application" />
                <el-option label="选择题" value="multi_choice" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度等级">
              <el-input-number
                v-model="qaItemForm.difficulty_level"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="分类">
          <el-input v-model="qaItemForm.category" placeholder="可选：输入分类" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="qaItemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitQAItem" :loading="qaStore.submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Edit, Plus, Upload } from '@element-plus/icons-vue'
import { useQAStore } from '@/stores/qa'
import { formatDate } from '@/utils/format'
import Pagination from '@/components/common/Pagination.vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { QAItem, CreateQAItemParams } from '@/api/qa'

const route = useRoute()
const router = useRouter()
const qaStore = useQAStore()

const groupId = Number(route.params.id)
const loading = ref(false)

// 分组信息
const group = computed(() => qaStore.currentGroup)

// 问答对列表
const qaItems = ref<QAItem[]>([])
const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

// 编辑分组
const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  name: '',
  purpose: '',
  test_type: 'custom',
  language: 'zh',
  difficulty_range: '',
  tagsInput: ''
})
const editRules: FormRules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }],
  test_type: [{ required: true, message: '请选择测试类型', trigger: 'change' }],
  language: [{ required: true, message: '请选择语言', trigger: 'change' }]
}

// 问答对表单
const qaItemDialogVisible = ref(false)
const isEditQAItem = ref(false)
const currentQAItemId = ref<number | null>(null)
const qaItemFormRef = ref<FormInstance>()
const qaItemForm = reactive({
  question: '',
  answersInput: '',
  context: '',
  question_type: '',
  difficulty_level: 1,
  category: ''
})
const qaItemRules: FormRules = {
  question: [{ required: true, message: '请输入问题', trigger: 'blur' }],
  answers: [{ required: true, message: '请输入答案', trigger: 'blur' }]
}

// 映射函数
function getTestTypeLabel(type: string): string {
  const map: Record<string, string> = {
    accuracy: '准确率测试',
    performance: '性能测试',
    robustness: '鲁棒性测试',
    comprehensive: '综合测试',
    custom: '自定义测试'
  }
  return map[type] || type
}

function getLanguageLabel(lang: string): string {
  const map: Record<string, string> = { zh: '中文', en: '英文', multi: '多语言' }
  return map[lang] || lang
}

function formatTags(tags: string[] | string | null): string[] {
  if (!tags) return []
  if (Array.isArray(tags)) return tags
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}

function formatAnswers(answers: string[] | { text: string[] } | string): string {
  if (Array.isArray(answers)) return answers.join('; ')
  if (typeof answers === 'object' && answers.text) return answers.text.join('; ')
  return String(answers)
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    await qaStore.fetchGroupDetail(groupId)
    const data = await qaStore.fetchQAItems(groupId, {
      page: pagination.page,
      limit: pagination.limit
    })
    if (data) {
      qaItems.value = data.rows
      pagination.total = data.total
    }
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number, limit: number) {
  pagination.page = page
  pagination.limit = limit
  loadData()
}

function goBack() {
  router.back()
}

function goToImport() {
  router.push(`/qa/groups/${groupId}/import`)
}

// 编辑分组
function showEditDialog() {
  if (!group.value) return
  editForm.name = group.value.name
  editForm.purpose = group.value.purpose || ''
  editForm.test_type = group.value.test_type
  editForm.language = group.value.language
  editForm.difficulty_range = group.value.difficulty_range || ''
  editForm.tagsInput = Array.isArray(group.value.tags) ? group.value.tags.join(', ') : group.value.tags || ''
  editDialogVisible.value = true
}

async function handleUpdateGroup() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  const tags = editForm.tagsInput.split(',').map(t => t.trim()).filter(Boolean)
  const response = await qaStore.updateGroup(groupId, {
    name: editForm.name,
    purpose: editForm.purpose,
    test_type: editForm.test_type,
    language: editForm.language,
    difficulty_range: editForm.difficulty_range,
    tags: tags.length > 0 ? tags : undefined
  })

  if (response?.success) {
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadData()
  } else {
    ElMessage.error(response?.message || '更新失败')
  }
}

// 问答对操作
function showCreateQAItemDialog() {
  isEditQAItem.value = false
  currentQAItemId.value = null
  qaItemForm.question = ''
  qaItemForm.answersInput = ''
  qaItemForm.context = ''
  qaItemForm.question_type = ''
  qaItemForm.difficulty_level = 1
  qaItemForm.category = ''
  qaItemDialogVisible.value = true
}

function showEditQAItemDialog(row: QAItem) {
  isEditQAItem.value = true
  currentQAItemId.value = row.id
  qaItemForm.question = row.question
  qaItemForm.answersInput = formatAnswers(row.answers)
  qaItemForm.context = row.context || ''
  qaItemForm.question_type = row.question_type || ''
  qaItemForm.difficulty_level = row.difficulty_level || 1
  qaItemForm.category = row.category || ''
  qaItemDialogVisible.value = true
}

async function handleSubmitQAItem() {
  const valid = await qaItemFormRef.value?.validate().catch(() => false)
  if (!valid) return

  const answers = qaItemForm.answersInput.split('\n').map(a => a.trim()).filter(Boolean)
  const data: CreateQAItemParams = {
    question: qaItemForm.question,
    answers,
    context: qaItemForm.context || undefined,
    question_type: qaItemForm.question_type || undefined,
    difficulty_level: qaItemForm.difficulty_level,
    category: qaItemForm.category || undefined
  }

  let response
  if (isEditQAItem.value && currentQAItemId.value) {
    response = await qaStore.updateQAItemById(currentQAItemId.value, data)
  } else {
    response = await qaStore.addQAItem(groupId, data)
  }

  if (response?.success) {
    ElMessage.success(isEditQAItem.value ? '更新成功' : '添加成功')
    qaItemDialogVisible.value = false
    loadData()
  } else {
    ElMessage.error(response?.message || '操作失败')
  }
}

async function handleDeleteQAItem(row: QAItem) {
  try {
    await ElMessageBox.confirm('确定要删除这个问答对吗？', '确认删除', {
      type: 'warning'
    })
    const response = await qaStore.removeQAItem(row.id)
    if (response?.success) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      ElMessage.error(response?.message || '删除失败')
    }
  } catch {
    // 取消
  }
}

onMounted(() => {
  loadData()
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

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h2 {
      margin: 0;
      color: #303133;
    }
  }

  .header-right {
    display: flex;
    gap: 8px;
  }
}

.group-info {
  margin-bottom: 30px;
}

.qa-items-section {
  h3 {
    margin: 0 0 16px 0;
    color: #303133;
  }
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 4px;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}
</style>
