<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack"><el-icon><Back /></el-icon></el-button>
            <h2>知识平台详细信息</h2>
          </div>
        </div>
      </template>

      <!-- 环境信息 -->
      <div class="environment-detail">
        <h3 class="section-title">环境信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="平台ID">{{ environment?.zlpt_base_id }}</el-descriptions-item>
          <el-descriptions-item label="平台名称">{{ environment?.zlpt_name }}</el-descriptions-item>
          <el-descriptions-item label="平台URL">{{ environment?.zlpt_base_url }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ environment?.username }}</el-descriptions-item>
          <el-descriptions-item label="域">{{ environment?.domain || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ environment?.created_at || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ environment?.updated_at || 'N/A' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 知识库列表 -->
      <div class="knowledge-base-section">
        <div class="section-header">
          <h3 class="section-title">知识库列表</h3>
          <div class="section-actions">
            <el-button type="primary" @click="showCreateDialog">
              <el-icon><Plus /></el-icon>创建知识库
            </el-button>
            <el-select v-model="searchField" style="width: 120px">
              <el-option label="名称" value="knowledge_name" />
              <el-option label="ID" value="knowledge_id" />
              <el-option label="分块大小" value="chunk_size" />
              <el-option label="分块重叠" value="chunk_overlap" />
              <el-option label="可见范围" value="visiblerange" />
              <el-option label="全部" value="all" />
            </el-select>
            <el-input
              v-model="searchValue"
              placeholder="搜索知识库..."
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </div>
        </div>

        <el-table :data="knowledgeBases" stripe border v-loading="tableLoading">
          <el-table-column label="名称/ID" min-width="200">
            <template #default="{ row }">
              <div class="knowledge-name">{{ row.knowledge_name }}</div>
              <div class="knowledge-id">/{{ row.knowledge_id }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="kno_root_id" label="根ID" min-width="150">
            <template #default="{ row }">
              {{ row.kno_root_id || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="chunk_size" label="分块大小" width="100">
            <template #default="{ row }">
              {{ row.chunk_size || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="chunk_overlap" label="分块重叠" width="100">
            <template #default="{ row }">
              {{ row.chunk_overlap || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="visiblerange" label="可见范围" width="100">
            <template #default="{ row }">
              {{ row.visiblerange || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160">
            <template #default="{ row }">
              {{ row.created_at || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="编辑时间" min-width="160">
            <template #default="{ row }">
              {{ row.updated_at || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!knowledgeBases.length && !tableLoading" description="暂无知识库" />
      </div>
    </el-card>

    <!-- 创建知识库弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建知识库"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-width="100px" :rules="createRules" ref="createFormRef">
        <el-form-item label="知识库名称" prop="knowledge_name">
          <el-input v-model="createForm.knowledge_name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="分块大小" prop="chunk_size">
          <el-input-number v-model="createForm.chunk_size" :min="100" :max="2000" :step="50" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分块重叠" prop="chunk_overlap">
          <el-input-number v-model="createForm.chunk_overlap" :min="0" :max="500" :step="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="分隔符" prop="slice_identifier">
          <el-input
            v-model="createForm.slice_identifier"
            placeholder="请输入分隔符，用逗号分隔"
          />
          <div class="form-tip">默认：。,！,!,？,?,，,:,：,.</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑知识库弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑知识库"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="editForm" label-width="100px" :rules="editRules" ref="editFormRef">
        <el-form-item label="知识库名称" prop="knowledge_name">
          <el-input v-model="editForm.knowledge_name" placeholder="请输入新的知识库名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="editLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Plus } from '@element-plus/icons-vue'
import {
  getEnvironmentKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  type KnowledgeBase
} from '@/api/environment'

const route = useRoute()
const router = useRouter()
const zlptBaseId = route.query.zlpt_base_id as string

// 加载状态
const loading = ref(false)
const tableLoading = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)

// 环境信息
const environment = ref({
  zlpt_base_id: zlptBaseId,
  zlpt_name: (route.query.zlpt_name as string) || '',
  zlpt_base_url: (route.query.zlpt_base_url as string) || '',
  username: (route.query.username as string) || '',
  domain: (route.query.domain as string) || '',
  created_at: (route.query.created_at as string) || '',
  updated_at: (route.query.updated_at as string) || ''
})

// 知识库列表
const knowledgeBases = ref<KnowledgeBase[]>([])

// 搜索
const searchField = ref('knowledge_name')
const searchValue = ref('')

// 创建弹窗
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({
  knowledge_name: '',
  chunk_size: 400,
  chunk_overlap: 50,
  slice_identifier: '。,！,!,？,?,，,:,：,.'
})
const createRules = {
  knowledge_name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  chunk_size: [{ required: true, message: '请输入分块大小', trigger: 'blur' }],
  chunk_overlap: [{ required: true, message: '请输入分块重叠', trigger: 'blur' }],
  slice_identifier: [{ required: true, message: '请输入分隔符', trigger: 'blur' }]
}

// 编辑弹窗
const editDialogVisible = ref(false)
const editFormRef = ref()
const editForm = reactive({
  knowledge_id: '',
  knowledge_name: ''
})
const editRules = {
  knowledge_name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }]
}

// 加载知识库列表
async function loadKnowledgeBases() {
  if (!zlptBaseId) {
    ElMessage.error('无法获取环境ID')
    return
  }

  tableLoading.value = true
  try {
    const res = await getEnvironmentKnowledgeBases(
      zlptBaseId,
      searchField.value === 'all' ? undefined : searchField.value,
      searchValue.value || undefined
    )
    if (res.success) {
      knowledgeBases.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取知识库列表失败')
    }
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    tableLoading.value = false
  }
}

// 搜索
function handleSearch() {
  loadKnowledgeBases()
}

// 显示创建弹窗
function showCreateDialog() {
  createForm.knowledge_name = ''
  createForm.chunk_size = 400
  createForm.chunk_overlap = 50
  createForm.slice_identifier = '。,！,!,？,?,，,:,：,.'
  createDialogVisible.value = true
}

// 创建知识库
async function handleCreate() {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    if (!zlptBaseId) {
      ElMessage.error('无法获取环境 ID，请返回环境列表页面重新进入')
      createDialogVisible.value = false
      return
    }

    createLoading.value = true
    try {
      const sliceIdentifier = createForm.slice_identifier
        .split(',')
        .map(item => item.trim())
        .filter(item => item !== '')

      const res = await createKnowledgeBase({
        knowledge_name: createForm.knowledge_name,
        zlpt_base_id: zlptBaseId,
        chunk_size: createForm.chunk_size,
        chunk_overlap: createForm.chunk_overlap,
        sliceidentifier: sliceIdentifier
      })

      if (res.success) {
        ElMessage.success('知识库创建成功')
        createDialogVisible.value = false
        loadKnowledgeBases()
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    } catch (error) {
      console.error('Failed to create knowledge base:', error)
      ElMessage.error('创建知识库失败')
    } finally {
      createLoading.value = false
    }
  })
}

// 显示编辑弹窗
function showEditDialog(row: KnowledgeBase) {
  editForm.knowledge_id = row.knowledge_id
  editForm.knowledge_name = row.knowledge_name
  editDialogVisible.value = true
}

// 编辑知识库
async function handleEdit() {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    editLoading.value = true
    try {
      const res = await updateKnowledgeBase(editForm.knowledge_id, {
        knowledge_name: editForm.knowledge_name
      })

      if (res.success) {
        ElMessage.success('知识库更新成功')
        editDialogVisible.value = false
        loadKnowledgeBases()
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } catch (error) {
      console.error('Failed to update knowledge base:', error)
      ElMessage.error('更新知识库失败')
    } finally {
      editLoading.value = false
    }
  })
}

// 删除知识库
async function handleDelete(row: KnowledgeBase) {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库 ${row.knowledge_name} 吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await deleteKnowledgeBase(row.knowledge_id)
    if (res.success) {
      ElMessage.success('知识库删除成功')
      loadKnowledgeBases()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete knowledge base:', error)
      ElMessage.error('删除知识库失败')
    }
  }
}

// 返回上一页
function goBack() {
  router.back()
}

onMounted(() => {
  loadKnowledgeBases()
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
    }
  }
}

.section-title {
  margin: 24px 0 16px;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.knowledge-base-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .section-title {
    margin: 0;
  }

  .section-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.knowledge-name {
  font-weight: 500;
  color: #303133;
}

.knowledge-id {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
