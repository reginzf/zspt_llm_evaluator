<template>
  <div class="filter-bar">
    <el-row :gutter="16">
      <template v-for="opt in options" :key="opt.key">
        <el-col :xs="24" :sm="8" :md="6">
          <!-- 下拉选择 -->
          <el-select
            v-if="opt.type === 'select'"
            v-model="filters[opt.key]"
            :placeholder="opt.placeholder"
            clearable
            @change="handleChange"
            style="width: 100%"
          >
            <el-option
              v-for="item in opt.options"
              :key="String(item.value)"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          
          <!-- 文本输入 -->
          <el-input
            v-else-if="opt.type === 'input'"
            v-model="filters[opt.key]"
            :placeholder="opt.placeholder"
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
      </template>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import type { SelectOption } from '@/types'

export interface FilterOption {
  type: 'select' | 'input'
  key: string
  placeholder?: string
  options?: Array<{ label: string; value: any }>
}

const props = defineProps<{
  modelValue: Record<string, any>
  options: FilterOption[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  search: []
  change: []
}>()

// 本地筛选状态
const filters = reactive<Record<string, any>>({})

// 同步外部值
watch(() => props.modelValue, (val) => {
  Object.assign(filters, val)
}, { immediate: true, deep: true })

// 同步回外部
watch(filters, (val) => {
  emit('update:modelValue', { ...val })
}, { deep: true })

// 搜索
function handleSearch() {
  emit('search')
}

// 筛选变化
function handleChange() {
  emit('change')
}
</script>

<style scoped lang="scss">
.filter-bar {
  margin-bottom: 20px;
  
  :deep(.el-select),
  :deep(.el-input) {
    width: 100%;
  }
}
</style>
