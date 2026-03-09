<template>
  <el-form-item :label="label" :prop="prop" :rules="rules">
    <el-select
      v-model="selectValue"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      :multiple="multiple"
      :collapse-tags="collapseTags"
      :filterable="filterable"
      :remote="remote"
      :remote-method="remoteMethod"
      :loading="loading"
      style="width: 100%"
      @change="handleChange"
      @visible-change="handleVisibleChange"
    >
      <el-option
        v-for="item in options"
        :key="item.value"
        :label="item.label"
        :value="item.value"
        :disabled="item.disabled"
      />
    </el-select>
  </el-form-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormRules } from 'element-plus'

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

interface Props {
  modelValue: string | number | string[] | number[]
  options: SelectOption[]
  label?: string
  prop?: string
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
  multiple?: boolean
  collapseTags?: boolean
  filterable?: boolean
  remote?: boolean
  remoteMethod?: (query: string) => void
  loading?: boolean
  rules?: FormRules
}

const props = withDefaults(defineProps<Props>(), {
  clearable: true,
  disabled: false,
  multiple: false,
  collapseTags: false,
  filterable: false,
  remote: false,
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number | string[] | number[]]
  'change': [value: string | number | string[] | number[]]
  'visible-change': [visible: boolean]
}>()

const selectValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const handleChange = (value: string | number | string[] | number[]) => {
  emit('change', value)
}

const handleVisibleChange = (visible: boolean) => {
  emit('visible-change', visible)
}
</script>
