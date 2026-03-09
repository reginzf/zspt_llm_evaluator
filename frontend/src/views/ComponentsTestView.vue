<template>
  <div class="test-page">
    <h2>基础组件测试</h2>

    <!-- 搜索框测试 -->
    <section class="test-section">
      <h3>SearchBox 搜索框</h3>
      <SearchBox
        v-model="searchQuery"
        placeholder="请输入搜索内容"
        @search="handleSearch"
        @clear="handleClear"
      />
      <p class="result">搜索关键词: {{ searchQuery }}</p>
    </section>

    <!-- 操作栏测试 -->
    <section class="test-section">
      <h3>ActionBar 操作栏</h3>
      <ActionBar
        :has-selection="hasSelection"
        @add="handleAdd"
        @delete="handleDelete"
        @refresh="handleRefresh"
      />
    </section>

    <!-- 数据表格测试 -->
    <section class="test-section">
      <h3>DataTable 数据表格</h3>
      <DataTable
        :data="tableData"
        :loading="tableLoading"
        :current-page="currentPage"
        :page-size="pageSize"
        selectable
        @selection-change="handleSelectionChange"
      >
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default>
            <el-button link type="primary">编辑</el-button>
            <el-button link type="danger">删除</el-button>
          </template>
        </el-table-column>
      </DataTable>
    </section>

    <!-- 分页测试 -->
    <section class="test-section">
      <h3>Pagination 分页</h3>
      <Pagination
        v-model="currentPage"
        v-model:page-size="pageSize"
        :total="100"
        @change="handlePageChange"
      />
    </section>

    <!-- 对话框测试 -->
    <section class="test-section">
      <h3>Modal 对话框</h3>
      <el-button type="primary" @click="modalVisible = true">打开对话框</el-button>
      <Modal
        v-model="modalVisible"
        title="测试对话框"
        @confirm="handleModalConfirm"
        @cancel="handleModalCancel"
      >
        <p>这是一个测试对话框内容</p>
        <el-form :model="formData" label-width="80px">
          <el-form-item label="名称">
            <el-input v-model="formData.name" placeholder="请输入名称" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="formData.desc" type="textarea" placeholder="请输入描述" />
          </el-form-item>
        </el-form>
      </Modal>
    </section>

    <!-- 表单组件测试 -->
    <section class="test-section">
      <h3>Form 表单组件</h3>
      <el-form :model="formData" label-width="100px">
        <FormInput
          v-model="formData.name"
          label="名称"
          prop="name"
          placeholder="请输入名称"
        />
        <FormSelect
          v-model="formData.type"
          label="类型"
          prop="type"
          :options="typeOptions"
          placeholder="请选择类型"
        />
        <FormTextarea
          v-model="formData.desc"
          label="描述"
          prop="desc"
          placeholder="请输入描述"
          :rows="3"
        />
        <FormDatePicker
          v-model="formData.date"
          label="日期"
          prop="date"
          placeholder="请选择日期"
        />
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import SearchBox from '@/components/common/SearchBox.vue'
import ActionBar from '@/components/common/ActionBar.vue'
import DataTable from '@/components/common/DataTable.vue'
import Pagination from '@/components/common/Pagination.vue'
import Modal from '@/components/common/Modal.vue'
import { FormInput, FormSelect, FormTextarea, FormDatePicker } from '@/components/common/Form'

// 搜索
const searchQuery = ref('')
const handleSearch = (val: string) => {
  ElMessage.success(`搜索: ${val}`)
}
const handleClear = () => {
  ElMessage.info('搜索已清空')
}

// 操作栏
const hasSelection = ref(false)
const handleAdd = () => {
  ElMessage.success('点击了新增')
}
const handleDelete = () => {
  ElMessage.warning('点击了删除')
}
const handleRefresh = () => {
  ElMessage.success('点击了刷新')
}

// 表格
const tableLoading = ref(false)
const tableData = ref([
  { name: '问答分组 1', type: 'functional', status: 'active', date: '2024-01-15 10:30:00' },
  { name: '问答分组 2', type: 'performance', status: 'inactive', date: '2024-01-16 14:20:00' },
  { name: '模型配置 A', type: 'model', status: 'active', date: '2024-01-17 09:15:00' },
  { name: '模型配置 B', type: 'model', status: 'active', date: '2024-01-18 16:45:00' },
  { name: '知识库 1', type: 'knowledge', status: 'inactive', date: '2024-01-19 11:00:00' },
])
const handleSelectionChange = (selection: unknown[]) => {
  hasSelection.value = selection.length > 0
}

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const handlePageChange = (page: number, size: number) => {
  ElMessage.success(`页码: ${page}, 每页: ${size}`)
}

// 对话框
const modalVisible = ref(false)
const formData = ref({
  name: '',
  type: '',
  desc: '',
  date: '',
})
const handleModalConfirm = () => {
  ElMessage.success('确认')
  modalVisible.value = false
}
const handleModalCancel = () => {
  ElMessage.info('取消')
}

// 表单选项
const typeOptions = [
  { label: '功能测试', value: 'functional' },
  { label: '性能测试', value: 'performance' },
  { label: '安全测试', value: 'security' },
]
</script>

<style scoped lang="scss">
.test-page {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;

  h2 {
    margin-bottom: 24px;
    color: var(--text-primary);
  }
}

.test-section {
  background-color: var(--bg-color);
  border-radius: var(--border-radius-large);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-light);

  h3 {
    margin-bottom: 16px;
    color: var(--text-regular);
    font-size: var(--font-size-md);
    border-bottom: 1px solid var(--border-light);
    padding-bottom: 12px;
  }
}

.result {
  margin-top: 12px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}
</style>
