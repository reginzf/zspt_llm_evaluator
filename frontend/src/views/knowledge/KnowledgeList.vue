<template>
  <div class="page-container">
    <PageHeader title="知识库管理" />
    <el-card v-loading="loading">

      <!-- 操作栏：创建按钮 + 搜索 -->
      <div class="action-bar">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>创建知识库
        </el-button>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索知识库名称、知识域..."
            clearable
            @keyup.enter="handleSearch"
            @clear="handleClear"
            style="width: 300px"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button @click="loadData" :icon="Refresh" style="margin-left: 10px">刷新</el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table :data="filteredKnowledgeList" stripe border style="width: 100%">
        <el-table-column prop="kno_name" label="名称" width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row)">{{ row.kno_name }}</el-link>
            <br>
            <small style="color: #909399">{{ row.kno_id }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="kno_describe" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="knowledge_domain" label="知识域" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.knowledge_domain" style="color: #409eff; cursor: pointer; text-decoration: underline;" @click="showDomainDetails(row)">
              {{ row.knowledge_domain }}
            </span>
            <span v-else style="color: #909399">暂无知识域</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="绑定的知识库数量" width="140" align="center">
          <template #default="{ row }">
            {{ row.bindingCount ?? '加载中...' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="goToDetail(row)">详情</el-button>
            <el-button type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建知识库" width="500px">
      <el-form :model="createForm" :rules="rules" ref="createFormRef" label-width="100px">
        <el-form-item label="名称" prop="kno_name">
          <el-input v-model="createForm.kno_name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.kno_describe" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑知识库对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑知识库" width="550px">
      <el-form :model="editForm" :rules="rules" ref="editFormRef" label-width="120px">
        <el-form-item label="知识库ID">
          <el-input v-model="editForm.kno_id" disabled />
        </el-form-item>
        <el-form-item label="名称" prop="kno_name">
          <el-input v-model="editForm.kno_name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.kno_describe" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="知识域名">
          <el-input v-model="editForm.knowledge_domain" placeholder="请输入知识域名" />
        </el-form-item>
        <el-form-item label="知识域描述">
          <el-input v-model="editForm.domain_description" type="textarea" :rows="2" placeholder="请输入知识域描述" />
        </el-form-item>
        <el-form-item label="背景知识">
          <el-select
            v-model="editForm.required_background"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入背景知识，按回车确认"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="标注LLM能力">
          <el-select
            v-model="editForm.required_skills"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入标注LLM能力，按回车确认"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  getLocalKnowledgeList,
  createLocalKnowledge,
  updateLocalKnowledge,
  deleteLocalKnowledge,
  getKnowledgeBindings
} from '@/api/knowledge'
import type { LocalKnowledge } from '@/api/knowledge'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const knowledgeList = ref<(LocalKnowledge & { bindingCount?: number })[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索
const searchKeyword = ref('')

// 创建对话框
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({ kno_name: '', kno_describe: '' })

// 编辑对话框
const editDialogVisible = ref(false)
const editFormRef = ref()
const editForm = reactive({
  kno_id: '',
  kno_name: '',
  kno_describe: '',
  knowledge_domain: '',
  domain_description: '',
  required_background: [] as string[],
  required_skills: [] as string[]
})

const rules = {
  kno_name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

function getStatusType(status: number) {
  const map: Record<number, string> = { 0: 'success', 1: 'info', 2: 'warning', 3: 'danger' }
  return map[status] || 'info'
}
function getStatusLabel(status: number) {
  const map: Record<number, string> = { 0: '已同步', 1: '未开始', 2: '同步中', 3: '失败' }
  return map[status] || '未知'
}

// 加载所有知识库的绑定数量
async function loadBindingCounts() {
  for (const item of knowledgeList.value) {
    try {
      const res = await getKnowledgeBindings(item.kno_id)
      if (res.success && res.data) {
        item.bindingCount = res.data.length
      } else {
        item.bindingCount = 0
      }
    } catch (error) {
      item.bindingCount = 0
    }
  }
}

// 过滤后的知识库列表
const filteredKnowledgeList = computed(() => {
  let list = [...knowledgeList.value]
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    list = list.filter(item => 
      item.kno_name?.toLowerCase().includes(keyword) ||
      item.kno_describe?.toLowerCase().includes(keyword) ||
      item.knowledge_domain?.toLowerCase().includes(keyword)
    )
  }
  
  // 按创建时间排序（保持顺序稳定）
  list.sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
    return timeB - timeA  // 降序，最新的在前
  })
  
  // 前端分页
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return list.slice(start, end)
})

async function loadData() {
  loading.value = true
  try {
    const res = await getLocalKnowledgeList()
    if (res.success) {
      knowledgeList.value = res.data || []
      total.value = res.data?.length || 0
      // 加载绑定数量
      await loadBindingCounts()
    } else {
      ElMessage.error(res.message || '获取知识库列表失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  // 搜索已在前端计算属性中处理
}

function handleClear() {
  searchKeyword.value = ''
  currentPage.value = 1
}

function handleSizeChange(val: number) {
  pageSize.value = val
  currentPage.value = 1
}

function handleCurrentChange(val: number) {
  currentPage.value = val
}

function goToDetail(row: LocalKnowledge) {
  router.push(`/local_knowledge_detail/${row.kno_id}/${row.kno_name}`)
}

function showCreateDialog() {
  createForm.kno_name = ''
  createForm.kno_describe = ''
  createDialogVisible.value = true
}

function showEditDialog(row: LocalKnowledge) {
  editForm.kno_id = row.kno_id
  editForm.kno_name = row.kno_name
  editForm.kno_describe = row.kno_describe || ''
  editForm.knowledge_domain = row.knowledge_domain || ''
  editForm.domain_description = row.domain_description || ''
  editForm.required_background = row.required_background || []
  editForm.required_skills = row.required_skills || []
  editDialogVisible.value = true
}

async function handleCreateSubmit() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    const res = await createLocalKnowledge({
      kno_name: createForm.kno_name,
      kno_describe: createForm.kno_describe
    })
    if (res.success) {
      ElMessage.success('创建成功')
      createDialogVisible.value = false
      await loadData()
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleEditSubmit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
  const res = await updateLocalKnowledge({
      kno_id: editForm.kno_id,
      kno_name: editForm.kno_name,
      kno_describe: editForm.kno_describe,
      knowledge_domain: editForm.knowledge_domain,
      domain_description: editForm.domain_description,
      required_background: editForm.required_background,
      required_skills: editForm.required_skills
    })
    if (res.success) {
      ElMessage.success('编辑成功')
      editDialogVisible.value = false
      await loadData()
    } else {
      ElMessage.error(res.message || '编辑失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '编辑失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: LocalKnowledge) {
  try {
    await ElMessageBox.confirm(`确定删除知识库 "${row.kno_name}" 吗？`, '确认删除', { type: 'warning' })
    const res = await deleteLocalKnowledge(row.kno_id)
    if (res.success) {
      ElMessage.success('删除成功')
      await loadData()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel' && error?.message !== 'cancel') {
      ElMessage.error(error?.message || '删除失败')
    }
  }
}

// 显示知识域详情
function showDomainDetails(row: LocalKnowledge) {
  const background = row.required_background?.join(', ') || '无'
  const skills = row.required_skills?.join(', ') || '无'
  
  ElMessageBox.alert(
    `<div style="line-height: 1.8;">
      <p><strong>知识域名：</strong>${row.knowledge_domain}</p>
      <p><strong>知识域描述：</strong>${row.domain_description || '暂无描述'}</p>
      <p><strong>背景知识：</strong>${background}</p>
      <p><strong>标注LLM能力：</strong>${skills}</p>
    </div>`,
    '知识域详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '确定'
    }
  )
}

onMounted(() => loadData())
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}



.action-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .search-box {
    display: flex;
    align-items: center;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
