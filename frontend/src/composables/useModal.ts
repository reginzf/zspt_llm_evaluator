import { ref } from 'vue'

/**
 * 对话框状态管理
 */
export function useModal() {
  const visible = ref(false)
  const data = ref<unknown>(null)

  // 打开对话框
  const open = (modalData?: unknown) => {
    data.value = modalData || null
    visible.value = true
  }

  // 关闭对话框
  const close = () => {
    visible.value = false
    data.value = null
  }

  // 切换对话框状态
  const toggle = () => {
    visible.value = !visible.value
  }

  return {
    visible,
    data,
    open,
    close,
    toggle,
  }
}
