import { ref, computed } from 'vue'
import type { PaginationParams, PaginationData } from '@/types'

/**
 * 分页逻辑 Composable
 * 提供统一的分页状态管理和分页计算
 */
export function usePagination<T>(defaultLimit = 20) {
  // 分页状态
  const page = ref(1)
  const limit = ref(defaultLimit)
  const total = ref(0)
  const pages = ref(0)
  const data = ref<T[]>([])
  const loading = ref(false)

  // 计算属性
  const isFirstPage = computed(() => page.value === 1)
  const isLastPage = computed(() => page.value >= pages.value)
  const hasData = computed(() => data.value.length > 0)
  const offset = computed(() => (page.value - 1) * limit.value)

  // 获取分页参数
  const getParams = (): PaginationParams => ({
    page: page.value,
    limit: limit.value
  })

  // 更新分页数据
  const updatePagination = (paginationData: PaginationData<T>) => {
    total.value = paginationData.total
    page.value = paginationData.page
    limit.value = paginationData.limit
    pages.value = paginationData.pages
    data.value = paginationData.rows
  }

  // 重置分页
  const reset = () => {
    page.value = 1
    limit.value = defaultLimit
    total.value = 0
    pages.value = 0
    data.value = []
  }

  // 跳转到指定页
  const goToPage = (targetPage: number) => {
    if (targetPage >= 1 && targetPage <= pages.value) {
      page.value = targetPage
    }
  }

  // 下一页
  const nextPage = () => {
    if (!isLastPage.value) {
      page.value++
    }
  }

  // 上一页
  const prevPage = () => {
    if (!isFirstPage.value) {
      page.value--
    }
  }

  // 改变每页数量
  const changeLimit = (newLimit: number) => {
    limit.value = newLimit
    page.value = 1 // 重置到第一页
  }

  return {
    // 状态
    page,
    limit,
    total,
    pages,
    data,
    loading,
    // 计算属性
    isFirstPage,
    isLastPage,
    hasData,
    offset,
    // 方法
    getParams,
    updatePagination,
    reset,
    goToPage,
    nextPage,
    prevPage,
    changeLimit
  }
}

export type UsePaginationReturn<T> = ReturnType<typeof usePagination<T>>
