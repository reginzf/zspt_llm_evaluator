import { ref, reactive, computed } from 'vue'
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

  // 对话框显示状态
  const _visible = ref<boolean>(false)
  const _isEdit = ref<boolean>(false)
  const _editId = ref<string | number>('')
  const formRef = ref<FormInstance>()
  
  const form = reactive<T>({ ...defaultForm })

  // 使用 computed 提供 getter/setter，支持 v-model
  const visible = computed({
    get: () => _visible.value,
    set: (val: boolean) => { _visible.value = val }
  })

  const isEdit = computed({
    get: () => _isEdit.value,
    set: (val: boolean) => { _isEdit.value = val }
  })

  const editId = computed({
    get: () => _editId.value,
    set: (val: string | number) => { _editId.value = val }
  })

  /**
   * 显示创建对话框
   */
  const showCreate = () => {
    _isEdit.value = false
    _editId.value = ''
    Object.assign(form, defaultForm)
    _visible.value = true
  }

  /**
   * 显示编辑对话框
   */
  const showEdit = (data: T & { id?: string | number }) => {
    _isEdit.value = true
    _editId.value = data.id || ''
    Object.assign(form, data)
    _visible.value = true
  }

  /**
   * 关闭对话框
   */
  const close = () => {
    _visible.value = false
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
      await onSubmit(form as T, _isEdit.value)
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

export type UseDialogReturn<T extends Record<string, any> = Record<string, any>> = ReturnType<typeof useDialog<T>>
