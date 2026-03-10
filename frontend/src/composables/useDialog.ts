import { ref, reactive } from 'vue'
import type { FormInstance } from 'element-plus'

/**
 * 对话框管理 Composable
 * 统一处理创建/编辑对话框的状态和逻辑
 */
export function useDialog<T extends Record<string, any> = Record<string, any>>(options: {
  defaultForm: T
  rules?: Record<string, any>
  onSubmit: (form: T, isEdit: boolean) => Promise<void>
}) {
  const { defaultForm, rules = {}, onSubmit } = options

  const visible = ref(false)
  const isEdit = ref(false)
  const editId = ref<string | number>('')
  const formRef = ref<FormInstance>()
  
  const form = reactive<T>({ ...defaultForm })

  /**
   * 显示创建对话框
   */
  const showCreate = () => {
    isEdit.value = false
    editId.value = ''
    Object.assign(form, defaultForm)
    visible.value = true
  }

  /**
   * 显示编辑对话框
   */
  const showEdit = (data: T & { id?: string | number }) => {
    isEdit.value = true
    editId.value = data.id || ''
    Object.assign(form, data)
    visible.value = true
  }

  /**
   * 关闭对话框
   */
  const close = () => {
    visible.value = false
    formRef.value?.resetFields()
  }

  /**
   * 提交表单
   */
  const submit = async (): Promise<boolean> => {
    if (!formRef.value) return false
    
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return false

    try {
      await onSubmit(form as T, isEdit.value)
      close()
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * 重置表单
   */
  const reset = () => {
    Object.assign(form, defaultForm)
    formRef.value?.resetFields()
  }

  return {
    visible,
    isEdit,
    editId,
    form,
    formRef,
    rules,
    showCreate,
    showEdit,
    close,
    submit,
    reset
  }
}

export type UseDialogReturn<T> = ReturnType<typeof useDialog<T>>
