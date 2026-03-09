<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <h2>环境管理</h2>
        </div>
      </template>

      <!-- 操作栏：创建按钮 + 搜索 -->
      <div class="action-bar">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>创建环境
        </el-button>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索环境名称、项目名称..."
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
          <el-button @click="loadEnvironments" :icon="Refresh" style="margin-left: 10px">刷新</el-button>
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table :data="filteredEnvironments" stripe border style="width: 100%">
        <el-table-column label="环境名称\ID" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row)">
              {{ row.zlpt_name }}
            </el-link>
            <br>
            <small style="color: #909399">{{ row.zlpt_base_id }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="项目名称" min-width="120" />
        <el-table-column prop="zlpt_base_url" label="基础URL" min-width="250" show-overflow-tooltip />
        <el-table-column prop="domain" label="Domain" min-width="120" />
        <el-table-column prop="username" label="管理账号" min-width="120" />
        <el-table-column label="密码" min-width="120">
          <template #default="{ row }">
            <span v-if="!row.showPassword">********</span>
            <span v-else>{{ row.password }}</span>
            <el-button 
              link 
              size="small" 
              @click="row.showPassword = !row.showPassword"
              style="margin-left: 5px"
            >
              <el-icon><View v-if="!row.showPassword" /><Hide v-else /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 创建/编辑环境模态框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑环境' : '创建环境'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item v-if="isEdit" label="环境ID">
          <el-input v-model="form.zlpt_base_id" disabled />
        </el-form-item>
        <el-form-item label="环境名称" prop="zlpt_name">
          <el-input v-model="form.zlpt_name" placeholder="请输入环境名称" />
        </el-form-item>
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="form.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="基础URL" prop="zlpt_base_url">
          <el-input v-model="form.zlpt_base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="Domain" prop="domain">
          <el-input v-model="form.domain" placeholder="请输入Domain" />
        </el-form-item>
        <el-form-item label="管理账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入管理账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ isEdit ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Hide } from '@element-plus/icons-vue'
import {
  getEnvironmentList,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  type Environment
} from '@/api/environment'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const environments = ref<(Environment & { showPassword?: boolean })[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索
const searchKeyword = ref('')

const form = reactive({
  zlpt_base_id: '',
  zlpt_name: '',
  project_name: '',
  zlpt_base_url: '',
  domain: 'default',
  username: '',
  password: ''
})

const rules = {
  zlpt_name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  zlpt_base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }],
  domain: [{ required: true, message: '请输入Domain', trigger: 'blur' }],
  username: [{ required: true, message: '请输入管理账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 过滤后的环境列表（前端搜索）
const filteredEnvironments = computed(() => {
  let list = environments.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    list = list.filter(env => 
      env.zlpt_name?.toLowerCase().includes(keyword) ||
      env.project_name?.toLowerCase().includes(keyword) ||
      env.zlpt_base_url?.toLowerCase().includes(keyword) ||
      env.domain?.toLowerCase().includes(keyword)
    )
  }
  // 前端分页
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return list.slice(start, end)
})

async function loadEnvironments() {
  loading.value = true
  try {
    const res = await getEnvironmentList()
    if (res.success) {
      environments.value = (res.data || []).map(env => ({
        ...env,
        showPassword: false
      }))
      total.value = environments.value.length
    } else {
      ElMessage.error(res.message || '获取环境列表失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取环境列表失败')
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

function goToDetail(row: Environment) {
  router.push({
    path: '/environment_detail',
    query: {
      zlpt_base_id: row.zlpt_base_id,
      zlpt_name: row.zlpt_name,
      zlpt_base_url: row.zlpt_base_url,
      username: row.username,
      domain: row.domain,
      created_at: row.created_at,
      updated_at: row.updated_at
    }
  })
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, {
    zlpt_base_id: '',
    zlpt_name: '',
    project_name: '',
    zlpt_base_url: '',
    domain: 'default',
    username: '',
    password: ''
  })
  dialogVisible.value = true
}

function showEditDialog(row: Environment) {
  isEdit.value = true
  Object.assign(form, {
    zlpt_base_id: row.zlpt_base_id,
    zlpt_name: row.zlpt_name,
    project_name: row.project_name || '',
    zlpt_base_url: row.zlpt_base_url || '',
    domain: row.domain || 'default',
    username: row.username || '',
    password: row.password || ''
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      const res = await updateEnvironment({
        zlpt_base_id: form.zlpt_base_id,
        zlpt_name: form.zlpt_name,
        project_name: form.project_name,
        zlpt_base_url: form.zlpt_base_url,
        domain: form.domain,
        username: form.username,
        password: form.password
      })
      if (res.success) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        await loadEnvironments()
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } else {
      const res = await createEnvironment({
        zlpt_name: form.zlpt_name,
        project_name: form.project_name,
        zlpt_base_url: form.zlpt_base_url,
        domain: form.domain,
        username: form.username,
        password: form.password
      })
      if (res.success) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        await loadEnvironments()
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || (isEdit.value ? '更新失败' : '创建失败'))
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: Environment) {
  try {
    await ElMessageBox.confirm(`确定删除环境 "${row.zlpt_name}" 吗？此操作不可撤销。`, '确认删除', { type: 'warning' })
    
    const res = await deleteEnvironment(row.zlpt_base_id)
    if (res.success) {
      ElMessage.success('删除成功')
      await loadEnvironments()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error === 'cancel' || error?.message === 'cancel') {
      return
    }
    ElMessage.error(error.message || '删除失败')
  }
}

onMounted(() => loadEnvironments())
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
