<template>
  <div class="data-table-wrapper">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="data"
      :stripe="stripe"
      :border="border"
      :height="height"
      :max-height="maxHeight"
      :row-key="rowKey"
      :default-sort="defaultSort"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
        align="center"
      />
      
      <!-- 序号列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="#"
        width="60"
        align="center"
        :index="indexMethod"
      />
      
      <!-- 动态列 -->
      <slot />
      
      <!-- 空数据 -->
      <template #empty>
        <el-empty :description="emptyText" />
      </template>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { TableInstance, Sort } from 'element-plus'

interface Props {
  data: unknown[]
  loading?: boolean
  stripe?: boolean
  border?: boolean
  height?: string | number
  maxHeight?: string | number
  rowKey?: string | ((row: unknown) => string)
  selectable?: boolean
  showIndex?: boolean
  emptyText?: string
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  pageSize?: number
  currentPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  stripe: true,
  border: true,
  selectable: false,
  showIndex: true,
  emptyText: '暂无数据',
  pageSize: 10,
  currentPage: 1,
})

const emit = defineEmits<{
  'selection-change': [selection: unknown[]]
  'sort-change': [sort: Sort]
  'row-click': [row: unknown, column: unknown, event: Event]
}>()

const tableRef = ref<TableInstance>()

const indexMethod = (index: number) => {
  return (props.currentPage - 1) * props.pageSize + index + 1
}

const handleSelectionChange = (selection: unknown[]) => {
  emit('selection-change', selection)
}

const handleSortChange = (sort: Sort) => {
  emit('sort-change', sort)
}

const handleRowClick = (row: unknown, column: unknown, event: Event) => {
  emit('row-click', row, column, event)
}

// 暴露方法
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row: unknown, selected?: boolean) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const getSelectionRows = () => {
  return tableRef.value?.getSelectionRows() || []
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  getSelectionRows,
})
</script>

<style scoped lang="scss">
.data-table-wrapper {
  width: 100%;
}
</style>
