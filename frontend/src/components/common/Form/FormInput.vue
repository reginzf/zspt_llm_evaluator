<template>
  <el-form-item :label="label" :prop="prop" :rules="rules">
    <el-input
      v-model="inputValue"
      :type="type"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      :readonly="readonly"
      :maxlength="maxlength"
      :show-word-limit="showWordLimit"
      :prefix-icon="prefixIcon"
      :suffix-icon="suffixIcon"
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
  type?: 'text' | 'password' | 'textarea'
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
  readonly?: boolean
  maxlength?: number
  showWordLimit?: boolean
  prefixIcon?: unknown
  suffixIcon?: unknown
  rules?: FormRules
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  clearable: true,
  disabled: false,
  readonly: false,
  showWordLimit: false,
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
