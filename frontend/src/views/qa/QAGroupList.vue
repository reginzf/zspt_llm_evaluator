<template>
  <div class="page-container">
    <el-card class="content-card" v-loading="qaStore.loading">
      <template #header>
        <div class="page-header">
          <h2>问答对组管理</h2>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建分组
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选区域 -->
      <div class="search-filter-area">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="8" :md="6">
            <el-select
              v-model="filters.test_type"
              placeholder="测试类型"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="准确率测试" value="accuracy" />
              <el-option label="性能测试" value="performance" />
              <el-option label="鲁棒性测试" value="robustness" />
              <el-option label="综合测试" value="comprehensive" />
              <el-option label="自定义测试" value="custom" />
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="8" :md="6">
            <el-select
              v-model="filters.language"
              placeholder="语言"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="中文" value="zh" />
              <el-option label="英文" value="en" />
              <el-option label="多语言" value="multi" />
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="8" :md="6">
            <el-select
              v-model="filters.is_active"
              placeholder="状态"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="已激活" :value="true" />
              <el-option label="已停用" :value="false" />
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="24" :md="6">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索分组名称或用途..."
              clearable
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-col>
        </el-row>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="qaStore.groups"
        stripe
        border
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable="custom" />
        <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="用途" min-width="150" show-overflow-tooltip />
        <el-table-column prop="test_type" label="测试类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTestTypeType(row.test_type)">
              {{ getTestTypeLabel(row.test_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            {{ getLanguageLabel(row.language) }}
          </template>
        </el-table-column>
        <el-table-column prop="difficulty_range" label="难度范围" width="100" />
        <el-table-column prop="tags" label="标签" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-for="tag in formatTags(row.tags)"
              :key="tag"
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="qa_count" label="问答对数量" width="110" align="center" />
        <el-table-column prop="is_active" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleToggleStatus(row)"
              :loading="qaStore.submitting"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="goToDetail(row.id)"
            >
              详情
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
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
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑问答对分组' : '创建问答对分组'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="用途描述">
          <el-input
            v-model="form.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入分组用途描述"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="测试类型" prop="test_type">
              <el-select v-model="form.test_type" placeholder="请选择" style="width: 100%">
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
              <el-select v-model="form.language" placeholder="请选择" style="width: 100%">
                <el-option label="中文" value="zh" />
                <el-option label="英文" value="en" />
                <el-option label="多语言" value="multi" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="难度范围">
          <el-input v-model="form.difficulty_range" placeholder="如: 1-5" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input
            v-model="form.tagsInput"
            placeholder="输入标签，用逗号分隔，如: 医疗,法律,金融"
          />
        </el-form-item>
        <el-form-item label="额外配置">
          <el-input
            v-model="form.metadataInput"
            type="textarea"
            :rows="3"
            placeholder='{"key": "value"}'
          />
          <div class="form-hint">可选的JSON格式配置信息</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="qaStore.submitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useQAStore } from '@/stores/qa'
import { formatDate } from '@/utils/format'
import Pagination from '@/components/common/Pagination.vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { QAGroup } from '@/api/qa'

const router = useRouter()
const qaStore = useQAStore()
const formRef = ref<FormInstance>()

// 筛选条件
const filters = reactive({
  test_type: '',
  language: '',
  is_active: undefined as boolean | undefined,
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref<number | null>(null)

// 表单
const form = reactive({
  name: '',
  purpose: '',
  test_type: 'custom',
  language: 'zh',
  difficulty_range: '',
  tagsInput: '',
  metadataInput: ''
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  test_type: [
    { required: true, message: '请选择测试类型', trigger: 'change' }
  ],
  language: [
    { required: true, message: '请选择语言', trigger: 'change' }
  ]
}

// 测试类型映射
const testTypeMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' }> = {
  accuracy: { label: '准确率测试', type: 'success' },
  performance: { label: '性能测试', type: 'warning' },
  robustness: { label: '鲁棒性测试', type: 'danger' },
  comprehensive: { label: '综合测试', type: 'success' },
  custom: { label: '自定义测试', type: 'info' }
}

// 语言映射
const languageMap: Record<string, string> = {
  zh: '中文',
  en: '英文',
  multi: '多语言'
}

// 获取测试类型标签
function getTestTypeLabel(type: string): string {
  return testTypeMap[type]?.label || type
}

// 获取测试类型样式
function getTestTypeType(type: string): 'success' | 'warning' | 'danger' | 'info' {
  return testTypeMap[type]?.type ?? 'info'
}

// 获取语言标签
function getLanguageLabel(lang: string): string {
  return languageMap[lang] || lang
}

// 格式化标签
function formatTags(tags: string[] | string | null): string[] {
  if (!tags) return []
  if (Array.isArray(tags)) return tags
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}

// 加载数据
async function loadData() {
  const params = {
    page: pagination.page,
    limit: pagination.limit,
    test_type: filters.test_type || undefined,
    language: filters.language || undefined,
    is_active: filters.is_active,
    keyword: filters.keyword || undefined
  }
  
  const data = await qaStore.fetchGroups(params)
  if (data) {
    pagination.total = data.total
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  loadData()
}

// 筛选变化
function handleFilterChange() {
  pagination.page = 1
  loadData()
}

// 分页变化
function handlePageChange(page: number, limit: number) {
  pagination.page = page
  pagination.limit = limit
  loadData()
}

// 排序变化
function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  if (prop && order) {
    const orderBy = order === 'ascending' ? `${prop} ASC` : `${prop} DESC`
    qaStore.setQueryParams({ order_by: orderBy })
  } else {
    qaStore.setQueryParams({ order_by: 'created_at DESC' })
  }
  loadData()
}

// 跳转到详情
function goToDetail(id: number) {
  router.push(`/qa/groups/${id}`)
}

// 显示创建对话框
function showCreateDialog() {
  isEdit.value = false
  currentId.value = null
  resetForm()
  dialogVisible.value = true
}

// 显示编辑对话框
function showEditDialog(row: QAGroup) {
  isEdit.value = true
  currentId.value = row.id
  form.name = row.name
  form.purpose = row.purpose || ''
  form.test_type = row.test_type
  form.language = row.language
  form.difficulty_range = row.difficulty_range || ''
  form.tagsInput = Array.isArray(row.tags) ? row.tags.join(', ') : row.tags || ''
  form.metadataInput = row.metadata ? JSON.stringify(row.metadata, null, 2) : ''
  dialogVisible.value = true
}

// 重置表单
function resetForm() {
  form.name = ''
  form.purpose = ''
  form.test_type = 'custom'
  form.language = 'zh'
  form.difficulty_range = ''
  form.tagsInput = ''
  form.metadataInput = ''
  formRef.value?.resetFields()
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  // 解析标签
  const tags = form.tagsInput
    .split(',')
    .map(t => t.trim())
    .filter(Boolean)

  // 解析元数据
  let metadata: Record<string, any> | undefined
  if (form.metadataInput.trim()) {
    try {
      metadata = JSON.parse(form.metadataInput)
    } catch {
      ElMessage.error('元数据格式不正确，请检查JSON格式')
      return
    }
  }

  const data = {
    name: form.name,
    purpose: form.purpose || undefined,
    test_type: form.test_type,
    language: form.language,
    difficulty_range: form.difficulty_range || undefined,
    tags: tags.length > 0 ? tags : undefined,
    metadata
  }

  let response
  if (isEdit.value && currentId.value) {
    response = await qaStore.updateGroup(currentId.value, data)
  } else {
    response = await qaStore.addGroup(data)
  }

  if (response?.success) {
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadData()
  } else {
    ElMessage.error(response?.message || '操作失败')
  }
}

// 切换状态
async function handleToggleStatus(row: QAGroup) {
  const response = await qaStore.toggleGroupStatus(row.id)
  if (response?.success) {
    ElMessage.success(row.is_active ? '已激活' : '已停用')
  } else {
    ElMessage.error(response?.message || '操作失败')
    // 恢复原状态
    row.is_active = !row.is_active
  }
}

// 删除
async function handleDelete(row: QAGroup) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await qaStore.removeGroup(row.id)
    if (response?.success) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      // 如果有依赖，提示强制删除
      if (response?.message?.includes('关联')) {
        try {
          await ElMessageBox.confirm(
            `${response.message}，是否强制删除？`,
            '强制删除',
            {
              confirmButtonText: '强制删除',
              cancelButtonText: '取消',
              type: 'error'
            }
          )
          const forceResponse = await qaStore.removeGroup(row.id, true)
          if (forceResponse?.success) {
            ElMessage.success('删除成功')
            loadData()
          } else {
            ElMessage.error(forceResponse?.message || '删除失败')
          }
        } catch {
          // 取消强制删除
        }
      } else {
        ElMessage.error(response?.message || '删除失败')
      }
    }
  } catch {
    // 取消删除
  }
}

// 初始化
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

.content-card {
  max-width: 1400px;
  margin: 0 auto;
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

.search-filter-area {
  margin-bottom: 20px;

  .el-select,
  .el-input {
    width: 100%;
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

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-table) {
  .el-button {
    padding: 0;
    height: auto;
  }
}
</style>
