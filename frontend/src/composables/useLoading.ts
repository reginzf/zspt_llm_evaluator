import { ref } from 'vue'

/**
 * 加载状态管理 Composable
 * 提供加载状态和提交状态的统一管理
 */
export function useLoading() {
  const loading = ref(false)
  const submitting = ref(false)
  const refreshing = ref(false)

  /**
   * 执行异步函数并管理加载状态
   */
  async function withLoading<T>(fn: () => Promise<T>): Promise<T | undefined> {
    loading.value = true
    try {
      return await fn()
    } finally {
      loading.value = false
    }
  }

  /**
   * 执行异步函数并管理提交状态
   */
  async function withSubmitting<T>(fn: () => Promise<T>): Promise<T | undefined> {
    submitting.value = true
    try {
      return await fn()
    } finally {
      submitting.value = false
    }
  }

  /**
   * 执行异步函数并管理刷新状态
   */
  async function withRefreshing<T>(fn: () => Promise<T>): Promise<T | undefined> {
    refreshing.value = true
    try {
      return await fn()
    } finally {
      refreshing.value = false
    }
  }

  return {
    loading,
    submitting,
    refreshing,
    withLoading,
    withSubmitting,
    withRefreshing
  }
}

export type UseLoadingReturn = ReturnType<typeof useLoading>
