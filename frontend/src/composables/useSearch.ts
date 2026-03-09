import { ref, computed } from 'vue'
import { debounce } from '@/utils/helpers'

export interface SearchOptions {
  debounceMs?: number
  fields?: string[]
}

/**
 * 搜索逻辑封装
 */
export function useSearch<T extends Record<string, unknown>>(
  items: T[],
  options: SearchOptions = {}
) {
  const { debounceMs = 300, fields = [] } = options

  const searchQuery = ref('')
  const searchFields = ref<string[]>(fields)

  // 执行搜索
  const performSearch = (query: string): T[] => {
    if (!query.trim()) return items

    const lowerQuery = query.toLowerCase()
    return items.filter((item) => {
      const fieldsToSearch = searchFields.value.length > 0 
        ? searchFields.value 
        : Object.keys(item)
      
      return fieldsToSearch.some((field) => {
        const value = item[field]
        if (value === null || value === undefined) return false
        return String(value).toLowerCase().includes(lowerQuery)
      })
    })
  }

  // 防抖搜索
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const debouncedSearch = debounce((query: string) => {
    return performSearch(query)
  }, debounceMs)

  // 搜索结果
  const results = computed(() => {
    return performSearch(searchQuery.value)
  })

  // 设置搜索关键词
  const setQuery = (query: string) => {
    searchQuery.value = query
  }

  // 设置搜索字段
  const setFields = (fields: string[]) => {
    searchFields.value = fields
  }

  // 清空搜索
  const clear = () => {
    searchQuery.value = ''
  }

  return {
    searchQuery,
    searchFields,
    results,
    setQuery,
    setFields,
    clear,
    debouncedSearch,
  }
}
