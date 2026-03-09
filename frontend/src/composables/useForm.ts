import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

export interface UseFormOptions<T> {
  initialValues: T
  rules?: FormRules
  onSubmit?: (values: T) => Promise<void>
}

/**
 * 表单逻辑封装
 */
export function useForm<T extends Record<string, unknown>>(options: UseFormOptions<T>) {
  const { initialValues, rules = {}, onSubmit } = options

  const formRef = ref<FormInstance>()
  const form = reactive<T>({ ...initialValues })
  const loading = ref(false)

  // 重置表单
  const reset = () => {
    Object.assign(form, initialValues)
    formRef.value?.resetFields()
  }

  // 设置表单值
  const setValues = (values: Partial<T>) => {
    Object.assign(form, values)
  }

  // 验证并提交
  const submit = async (): Promise<boolean> => {
    if (!formRef.value) return false
    
    loading.value = true
    try {
      const valid = await formRef.value.validate()
      if (valid && onSubmit) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        await onSubmit(form as any)
      }
      return valid
    } catch {
      return false
    } finally {
      loading.value = false
    }
  }

  // 验证表单
  const validate = async (): Promise<boolean> => {
    if (!formRef.value) return false
    try {
      return await formRef.value.validate()
    } catch {
      return false
    }
  }

  return {
    formRef,
    form,
    rules,
    loading,
    reset,
    setValues,
    submit,
    validate,
  }
}
