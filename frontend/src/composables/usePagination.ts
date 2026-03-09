import { ref, computed } from 'vue'

export interface PaginationOptions {
  pageSize?: number
  pageSizes?: number[]
  total?: number
}

/**
 * 分页逻辑封装
 */
export function usePagination(options: PaginationOptions = {}) {
  const { pageSize = 10, pageSizes = [10, 20, 50, 100], total = 0 } = options

  const currentPage = ref(1)
  const pageSizeRef = ref(pageSize)
  const totalRef = ref(total)

  // 计算总页数
  const totalPages = computed(() => {
    return Math.ceil(totalRef.value / pageSizeRef.value)
  })

  // 计算当前页的起始索引
  const startIndex = computed(() => {
    return (currentPage.value - 1) * pageSizeRef.value
  })

  // 计算当前页的结束索引
  const endIndex = computed(() => {
    return Math.min(startIndex.value + pageSizeRef.value, totalRef.value)
  })

  // 设置当前页
  const setPage = (page: number) => {
    currentPage.value = page
  }

  // 设置每页数量
  const setPageSize = (size: number) => {
    pageSizeRef.value = size
    currentPage.value = 1 // 重置到第一页
  }

  // 设置总数
  const setTotal = (count: number) => {
    totalRef.value = count
  }

  // 下一页
  const nextPage = () => {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  // 上一页
  const prevPage = () => {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  // 重置分页
  const reset = () => {
    currentPage.value = 1
    pageSizeRef.value = pageSize
  }

  return {
    currentPage,
    pageSize: pageSizeRef,
    pageSizes,
    total: totalRef,
    totalPages,
    startIndex,
    endIndex,
    setPage,
    setPageSize,
    setTotal,
    nextPage,
    prevPage,
    reset,
  }
}
