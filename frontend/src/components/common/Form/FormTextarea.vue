<template>
  <el-form-item :label="label" :prop="prop" :rules="rules">
    <el-input
      v-model="inputValue"
      type="textarea"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      :readonly="readonly"
      :rows="rows"
      :maxlength="maxlength"
      :show-word-limit="showWordLimit"
      :autosize="autosize"
      @blur="handleBlur"
      @focus="handleFocus"
      @change="handleChange"
    />
  </el-form-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormRules } from 'element-plus'

interface Props {
  modelValue: string
  label?: string
  prop?: string
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
  readonly?: boolean
  rows?: number
  maxlength?: number
  showWordLimit?: boolean
  autosize?: boolean | { minRows?: number; maxRows?: number }
  rules?: FormRules
}

const props = withDefaults(defineProps<Props>(), {
  clearable: true,
  disabled: false,
  readonly: false,
  rows: 3,
  showWordLimit: false,
  autosize: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'blur': [event: FocusEvent]
  'focus': [event: FocusEvent]
  'change': [value: string]
}>()

const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleChange = (value: string) => {
  emit('change', value)
}
</script>
