<template>
  <div class="page-container">
    <PageHeader title="Label-Studio环境管理">
      <template #extra>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>创建环境
        </el-button>
      </template>
    </PageHeader>
    <el-card v-loading="loading">

      <!-- 搜索区域 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索Label-Studio环境..."
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

      <!-- 数据表格 -->
      <el-table :data="filteredEnvironments" stripe border style="width: 100%">
        <el-table-column prop="label_studio_id" label="环境ID" min-width="180" />
        <el-table-column prop="label_studio_url" label="URL" min-width="250" show-overflow-tooltip />
        <el-table-column label="API Key" min-width="150">
          <template #default="{ row }">
            <span v-if="!row.showApiKey">********</span>
            <span v-else>{{ row.label_studio_api_key }}</span>
            <el-button 
              link 
              size="small" 
              @click="row.showApiKey = !row.showApiKey"
              style="margin-left: 5px"
            >
              <el-icon><View v-if="!row.showApiKey" /><Hide v-else /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="project_count" label="项目数量" width="100" align="center">
          <template #default="{ row }">
            {{ row.project_count || 0 }}
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑Label-Studio环境' : '创建Label-Studio环境'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item v-if="isEdit" label="环境ID">
          <el-input v-model="form.label_studio_id" disabled />
        </el-form-item>
        <el-form-item label="URL" prop="label_studio_url">
          <el-input v-model="form.label_studio_url" placeholder="https://labelstudio.example.com" />
        </el-form-item>
        <el-form-item label="API Key" prop="label_studio_api_key">
          <el-input v-model="form.label_studio_api_key" type="password" show-password placeholder="请输入API Key" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, View, Hide } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  getLabelStudioEnvs,
  createLabelStudioEnv,
  updateLabelStudioEnv,
  deleteLabelStudioEnv
} from '@/api/knowledge'
import type { LabelStudioEnv } from '@/api/knowledge'

const loading = ref(false)
const submitting = ref(false)
const environments = ref<(LabelStudioEnv & { showApiKey?: boolean })[]>([])
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
  label_studio_id: '',
  label_studio_url: '',
  label_studio_api_key: ''
})

const rules = {
  label_studio_url: [{ required: true, message: '请输入URL', trigger: 'blur' }],
  label_studio_api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

// 过滤后的环境列表（前端搜索）
const filteredEnvironments = computed(() => {
  let list = environments.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    list = list.filter(env => 
      env.label_studio_id?.toLowerCase().includes(keyword) ||
      env.label_studio_url?.toLowerCase().includes(keyword)
    )
  }
  // 前端分页
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return list.slice(start, end)
})

async function loadData() {
  loading.value = true
  try {
    const res = await getLabelStudioEnvs()
    if (res.success) {
      environments.value = (res.data || []).map(env => ({
        ...env,
        showApiKey: false
      }))
      total.value = environments.value.length
    } else {
      ElMessage.error(res.message || '获取环境列表失败')
    }
  } catch (error) {
    ElMessage.error('获取环境列表失败')
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

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, {
    label_studio_id: '',
    label_studio_url: '',
    label_studio_api_key: ''
  })
  dialogVisible.value = true
}

function showEditDialog(row: LabelStudioEnv) {
  isEdit.value = true
  Object.assign(form, {
    label_studio_id: row.label_studio_id,
    label_studio_url: row.label_studio_url,
    label_studio_api_key: row.label_studio_api_key || ''
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    let res
    if (isEdit.value) {
      res = await updateLabelStudioEnv({
        label_studio_id: form.label_studio_id,
        label_studio_url: form.label_studio_url,
        label_studio_token: form.label_studio_api_key
      })
    } else {
      res = await createLabelStudioEnv({
        label_studio_url: form.label_studio_url,
        label_studio_token: form.label_studio_api_key
      })
    }

    if (res.success) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      dialogVisible.value = false
      loadData()
    } else {
      ElMessage.error(res.message || (isEdit.value ? '更新失败' : '创建失败'))
    }
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: LabelStudioEnv) {
  try {
    await ElMessageBox.confirm(`确定删除Label-Studio环境 "${row.label_studio_url}" 吗？此操作不可撤销。`, '确认删除', { type: 'warning' })
    const res = await deleteLabelStudioEnv(row.label_studio_id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => loadData())
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
