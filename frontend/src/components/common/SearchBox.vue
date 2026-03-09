<template>
  <div class="search-box-wrapper">
    <el-input
      v-model="inputValue"
      :placeholder="placeholder"
      :clearable="clearable"
      :prefix-icon="Search"
      @keyup.enter="handleSearch"
      @clear="handleClear"
    >
      <template #append v-if="showButton">
        <el-button @click="handleSearch">
          <el-icon><Search /></el-icon>
        </el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Search } from '@element-plus/icons-vue'

interface Props {
  modelValue: string
  placeholder?: string
  clearable?: boolean
  showButton?: boolean
  debounce?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请输入搜索关键词',
  clearable: true,
  showButton: false,
  debounce: 300,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'search': [value: string]
  'clear': []
}>()

const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const handleSearch = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    emit('search', inputValue.value)
  }, props.debounce)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  emit('search', '')
}
</script>

<style scoped lang="scss">
.search-box-wrapper {
  width: 100%;
  max-width: 300px;
}
</style>
