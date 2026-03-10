import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getQAGroups,
  createQAGroup,
  getQAGroupDetail,
  updateQAGroup,
  deleteQAGroup,
  toggleQAGroupStatus,
  getQAGroupStatistics,
  getQAItems,
  createQAItem,
  updateQAItem,
  deleteQAItem,
  batchDeleteQAItems,
  type QAGroup,
  type QAItem,
  type QAGroupQueryParams,
  type CreateQAGroupParams,
  type UpdateQAGroupParams,
  type QAItemQueryParams,
  type CreateQAItemParams
} from '@/api/qa'

/**
 * QA Store - 专注于数据管理，不处理 UI 状态（如 loading）
 * UI 状态应使用 useLoading composable 在组件中处理
 */
export const useQAStore = defineStore('qa', () => {
  // ============ State ============
  const groups = ref<QAGroup[]>([])
  const currentGroup = ref<QAGroup | null>(null)
  const qaItems = ref<QAItem[]>([])
  
  // 分页信息（缓存）
  const paginationCache = ref({
    total: 0,
    page: 1,
    limit: 20,
    pages: 0
  })

  // 查询参数（缓存）
  const queryParams = ref<QAGroupQueryParams>({
    page: 1,
    limit: 20
  })

  // ============ Getters ============
  const hasGroups = computed(() => groups.value.length > 0)

  // ============ Actions ============

  /**
   * 获取分组列表
   * @returns 分页数据，组件应使用 useLoading 处理加载状态
   */
  async function fetchGroups(params?: QAGroupQueryParams) {
    const mergedParams = { ...queryParams.value, ...params }
    const response = await getQAGroups(mergedParams)
    
    if (response.success && response.data) {
      groups.value = response.data.rows
      paginationCache.value = {
        total: response.data.total,
        page: response.data.page,
        limit: response.data.limit,
        pages: response.data.pages
      }
      return response.data
    }
    return null
  }

  /**
   * 创建分组
   */
  async function addGroup(data: CreateQAGroupParams) {
    const response = await createQAGroup(data)
    if (response.success) {
      await fetchGroups() // 刷新列表
    }
    return response
  }

  /**
   * 获取分组详情
   */
  async function fetchGroupDetail(id: number) {
    const response = await getQAGroupDetail(id)
    if (response.success && response.data) {
      currentGroup.value = response.data
      return response.data
    }
    return null
  }

  /**
   * 更新分组
   */
  async function updateGroup(id: number, data: UpdateQAGroupParams) {
    const response = await updateQAGroup(id, data)
    if (response.success) {
      // 更新当前分组缓存
      if (currentGroup.value?.id === id) {
        Object.assign(currentGroup.value, data)
      }
      await fetchGroups()
    }
    return response
  }

  /**
   * 删除分组
   */
  async function removeGroup(id: number, force: boolean = false) {
    const response = await deleteQAGroup(id, force)
    if (response.success) {
      groups.value = groups.value.filter(g => g.id !== id)
      await fetchGroups()
    }
    return response
  }

  /**
   * 切换分组状态
   */
  async function toggleGroupStatus(id: number, status?: boolean) {
    const response = await toggleQAGroupStatus(id, status)
    if (response.success) {
      // 更新本地状态
      const group = groups.value.find(g => g.id === id)
      if (group) {
        group.is_active = response.data?.status ?? !group.is_active
      }
      if (currentGroup.value?.id === id) {
        currentGroup.value.is_active = response.data?.status ?? !currentGroup.value.is_active
      }
    }
    return response
  }

  /**
   * 获取分组统计
   */
  async function fetchGroupStatistics(id: number) {
    const response = await getQAGroupStatistics(id)
    return response.data
  }

  // ============ 问答对操作 ============

  /**
   * 获取问答对列表
   */
  async function fetchQAItems(groupId: number, params?: QAItemQueryParams) {
    const response = await getQAItems(groupId, params)
    if (response.success && response.data) {
      qaItems.value = response.data.rows
      return response.data
    }
    return null
  }

  /**
   * 创建问答对
   */
  async function addQAItem(groupId: number, data: CreateQAItemParams) {
    return await createQAItem(groupId, data)
  }

  /**
   * 更新问答对
   */
  async function updateQAItemById(id: number, data: Partial<CreateQAItemParams>) {
    return await updateQAItem(id, data)
  }

  /**
   * 删除问答对
   */
  async function removeQAItem(id: number) {
    return await deleteQAItem(id)
  }

  /**
   * 批量删除问答对
   */
  async function batchRemoveQAItems(groupId: number, ids: number[]) {
    return await batchDeleteQAItems(groupId, ids)
  }

  /**
   * 设置查询参数
   */
  function setQueryParams(params: QAGroupQueryParams) {
    queryParams.value = { ...queryParams.value, ...params }
  }

  /**
   * 重置查询参数
   */
  function resetQueryParams() {
    queryParams.value = { page: 1, limit: 20 }
  }

  /**
   * 重置所有状态
   */
  function $reset() {
    groups.value = []
    currentGroup.value = null
    qaItems.value = []
    paginationCache.value = { total: 0, page: 1, limit: 20, pages: 0 }
    queryParams.value = { page: 1, limit: 20 }
  }

  return {
    // State
    groups,
    currentGroup,
    qaItems,
    pagination: paginationCache,
    queryParams,
    
    // Getters
    hasGroups,
    
    // Actions
    fetchGroups,
    addGroup,
    fetchGroupDetail,
    updateGroup,
    removeGroup,
    toggleGroupStatus,
    fetchGroupStatistics,
    fetchQAItems,
    addQAItem,
    updateQAItemById,
    removeQAItem,
    batchRemoveQAItems,
    setQueryParams,
    resetQueryParams,
    $reset
  }
})
