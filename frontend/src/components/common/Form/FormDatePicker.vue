<template>
  <el-form-item :label="label" :prop="prop" :rules="rules">
    <el-date-picker
      v-model="dateValue"
      :type="type"
      :placeholder="placeholder"
      :start-placeholder="startPlaceholder"
      :end-placeholder="endPlaceholder"
      :format="format"
      :value-format="valueFormat"
      :clearable="clearable"
      :disabled="disabled"
      :disabled-date="disabledDate"
      style="width: 100%"
      @change="handleChange"
    />
  </el-form-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormRules } from 'element-plus'

interface Props {
  modelValue: Date | string | number | [Date | string | number, Date | string | number]
  label?: string
  prop?: string
  type?: 'date' | 'datetime' | 'datetimerange' | 'daterange' | 'week' | 'month' | 'year'
  placeholder?: string
  startPlaceholder?: string
  endPlaceholder?: string
  format?: string
  valueFormat?: string
  clearable?: boolean
  disabled?: boolean
  disabledDate?: (time: Date) => boolean
  rules?: FormRules
}

const props = withDefaults(defineProps<Props>(), {
  type: 'date',
  clearable: true,
  disabled: false,
  startPlaceholder: '开始日期',
  endPlaceholder: '结束日期',
})

const emit = defineEmits<{
  'update:modelValue': [value: Date | string | number | [Date | string | number, Date | string | number]]
  'change': [value: Date | string | number | [Date | string | number, Date | string | number]]
}>()

const dateValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const handleChange = (value: Date | string | number | [Date | string | number, Date | string | number]) => {
  emit('change', value)
}
</script>
