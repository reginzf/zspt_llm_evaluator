<template>
  <div class="page-container">
    <PageHeader title="问答对组管理">
      <template #extra>
        <el-button type="primary" @click="dialog.showCreate">
          <el-icon><Plus /></el-icon>
          创建分组
        </el-button>
      </template>
    </PageHeader>
    <el-card class="content-card" v-loading="loading">

      <!-- 搜索和筛选区域 -->
      <FilterBar v-model="filters" :options="filterOptions" @search="handleSearch" />

      <!-- 数据表格 -->
      <el-table
        :data="groups"
        stripe
        border
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
            <el-tag :type="getTestTypeOption(row.test_type)?.type">
              {{ getTestTypeOption(row.test_type)?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            {{ valueToLabel(row.language, LANGUAGE_OPTIONS) }}
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
              :loading="submitting"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="goToDetail(row.id)">
              详情
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
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
          @change="loadData"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑问答对分组' : '创建问答对分组'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="dialog.formRef" :model="dialog.form" :rules="formRules" label-width="100px">
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="dialog.form.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="用途描述">
          <el-input
            v-model="dialog.form.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入分组用途描述"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="测试类型" prop="test_type">
              <el-select v-model="dialog.form.test_type" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="opt in TEST_TYPE_OPTIONS"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="语言" prop="language">
              <el-select v-model="dialog.form.language" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="opt in LANGUAGE_OPTIONS"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="难度范围">
          <el-input v-model="dialog.form.difficulty_range" placeholder="如: 1-5" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input
            v-model="dialog.form.tagsInput"
            placeholder="输入标签，用逗号分隔，如: 医疗,法律,金融"
          />
        </el-form-item>
        <el-form-item label="额外配置">
          <el-input
            v-model="dialog.form.metadataInput"
            type="textarea"
            :rows="3"
            placeholder='{"key": "value"}'
          />
          <div class="form-hint">可选的JSON格式配置信息</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.close">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import Pagination from '@/components/common/Pagination.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import { useQAStore } from '@/stores/qa'
import { useDialog, useLoading } from '@/composables'
import { 
  formatDateTime, 
  formatTags, 
  valueToLabel,
  TEST_TYPE_OPTIONS,
  LANGUAGE_OPTIONS
} from '@/utils/formatters'
import type { QAGroup, CreateQAGroupParams } from '@/api/qa'

// 路由
const router = useRouter()
const qaStore = useQAStore()

// 使用 composables
const { loading, submitting, withLoading, withSubmitting } = useLoading()

// 数据
const groups = ref<QAGroup[]>([])

// 分页
const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

// 筛选条件
const filters = reactive({
  test_type: '',
  language: '',
  is_active: undefined as boolean | undefined,
  keyword: ''
})

// 筛选选项配置
import type { FilterOption } from '@/components/common/FilterBar.vue'

const filterOptions: FilterOption[] = [
  { type: 'select', key: 'test_type', placeholder: '测试类型', options: TEST_TYPE_OPTIONS },
  { type: 'select', key: 'language', placeholder: '语言', options: LANGUAGE_OPTIONS },
  { type: 'select', key: 'is_active', placeholder: '状态', options: [
    { label: '已激活', value: true },
    { label: '已停用', value: false }
  ]},
  { type: 'input', key: 'keyword', placeholder: '搜索分组名称或用途...' }
]

// 对话框
const dialog = useDialog<{
  name: string
  purpose: string
  test_type: string
  language: string
  difficulty_range: string
  tagsInput: string
  metadataInput: string
}>({
  defaultForm: {
    name: '',
    purpose: '',
    test_type: 'custom',
    language: 'zh',
    difficulty_range: '',
    tagsInput: '',
    metadataInput: ''
  },
  rules: {
    name: [
      { required: true, message: '请输入分组名称', trigger: 'blur' },
      { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
    ],
    test_type: [{ required: true, message: '请选择测试类型', trigger: 'change' }],
    language: [{ required: true, message: '请选择语言', trigger: 'change' }]
  },
  onSubmit: async (form, isEditMode) => {
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
        throw new Error('Invalid JSON')
      }
    }

    const data: CreateQAGroupParams = {
      name: form.name,
      purpose: form.purpose || undefined,
      test_type: form.test_type,
      language: form.language,
      difficulty_range: form.difficulty_range || undefined,
      tags: tags.length > 0 ? tags : undefined,
      metadata
    }

    const response = isEditMode && dialog.editId.value
      ? await qaStore.updateGroup(Number(dialog.editId.value), data)
      : await qaStore.addGroup(data)

    if (response?.success) {
      ElMessage.success(isEditMode ? '更新成功' : '创建成功')
      loadData()
    } else {
      ElMessage.error(response?.message || '操作失败')
      throw new Error(response?.message)
    }
  }
})

// 表单规则（用于对话框提交时验证）
const formRules: FormRules = dialog.rules

// 辅助函数
const getTestTypeOption = (type: string) => TEST_TYPE_OPTIONS.find(opt => opt.value === type)

// 加载数据
async function loadData() {
  await withLoading(async () => {
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
      groups.value = data.rows
      pagination.total = data.total
    }
  })
}

// 搜索
function handleSearch() {
  pagination.page = 1
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

// 编辑
function handleEdit(row: QAGroup) {
  console.log('[QAGroupList] handleEdit called for row:', row.id, row.name)
  dialog.showEdit({
    id: row.id,
    name: row.name,
    purpose: row.purpose || '',
    test_type: row.test_type,
    language: row.language,
    difficulty_range: row.difficulty_range || '',
    tagsInput: Array.isArray(row.tags) ? row.tags.join(', ') : row.tags || '',
    metadataInput: row.metadata ? JSON.stringify(row.metadata, null, 2) : ''
  })
}

// 提交表单
async function handleSubmit() {
  await withSubmitting(() => dialog.submit())
}

// 切换状态
async function handleToggleStatus(row: QAGroup) {
  const response = await qaStore.toggleGroupStatus(row.id)
  if (response?.success) {
    ElMessage.success(row.is_active ? '已激活' : '已停用')
  } else {
    ElMessage.error(response?.message || '操作失败')
    row.is_active = !row.is_active
  }
}

// 删除
async function handleDelete(row: QAGroup) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${row.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    const response = await qaStore.removeGroup(row.id)
    if (response?.success) {
      ElMessage.success('删除成功')
      loadData()
    } else if (response?.message?.includes('关联')) {
      // 有依赖，提示强制删除
      try {
        await ElMessageBox.confirm(
          `${response.message}，是否强制删除？`,
          '强制删除',
          { confirmButtonText: '强制删除', type: 'error' }
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
  } catch {
    // 取消删除
  }
}

// 初始化
onMounted(loadData)
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
