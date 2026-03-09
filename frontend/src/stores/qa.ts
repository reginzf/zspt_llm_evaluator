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
  type CreateQAItemParams,
  type PaginationData
} from '@/api/qa'

export const useQAStore = defineStore('qa', () => {
  // ============ State ============
  const groups = ref<QAGroup[]>([])
  const currentGroup = ref<QAGroup | null>(null)
  const qaItems = ref<QAItem[]>([])
  const loading = ref(false)
  const submitting = ref(false)
  
  // 分页信息
  const pagination = ref({
    total: 0,
    page: 1,
    limit: 20,
    pages: 0
  })

  // 查询参数
  const queryParams = ref<QAGroupQueryParams>({
    page: 1,
    limit: 20
  })

  // ============ Getters ============
  const hasGroups = computed(() => groups.value.length > 0)
  const isFirstPage = computed(() => pagination.value.page === 1)
  const isLastPage = computed(() => pagination.value.page >= pagination.value.pages)

  // ============ Actions ============

  /**
   * 获取分组列表
   */
  async function fetchGroups(params?: QAGroupQueryParams) {
    loading.value = true
    try {
      const mergedParams = { ...queryParams.value, ...params }
      const response = await getQAGroups(mergedParams)
      
      if (response.success && response.data) {
        groups.value = response.data.rows
        pagination.value = {
          total: response.data.total,
          page: response.data.page,
          limit: response.data.limit,
          pages: response.data.pages
        }
        return response.data
      }
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建分组
   */
  async function addGroup(data: CreateQAGroupParams) {
    submitting.value = true
    try {
      const response = await createQAGroup(data)
      if (response.success) {
        // 刷新列表
        await fetchGroups()
      }
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 获取分组详情
   */
  async function fetchGroupDetail(id: number) {
    loading.value = true
    try {
      const response = await getQAGroupDetail(id)
      if (response.success && response.data) {
        currentGroup.value = response.data
        return response.data
      }
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新分组
   */
  async function updateGroup(id: number, data: UpdateQAGroupParams) {
    submitting.value = true
    try {
      const response = await updateQAGroup(id, data)
      if (response.success) {
        // 更新当前分组
        if (currentGroup.value?.id === id) {
          Object.assign(currentGroup.value, data)
        }
        // 刷新列表
        await fetchGroups()
      }
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 删除分组
   */
  async function removeGroup(id: number, force: boolean = false) {
    submitting.value = true
    try {
      const response = await deleteQAGroup(id, force)
      if (response.success) {
        // 从列表中移除
        groups.value = groups.value.filter(g => g.id !== id)
        // 刷新列表
        await fetchGroups()
      }
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 切换分组状态
   */
  async function toggleGroupStatus(id: number, status?: boolean) {
    submitting.value = true
    try {
      const response = await toggleQAGroupStatus(id, status)
      if (response.success) {
        // 更新列表中的状态
        const group = groups.value.find(g => g.id === id)
        if (group) {
          group.is_active = response.data?.status ?? !group.is_active
        }
        // 更新当前分组
        if (currentGroup.value?.id === id) {
          currentGroup.value.is_active = response.data?.status ?? !currentGroup.value.is_active
        }
      }
      return response
    } finally {
      submitting.value = false
    }
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
    loading.value = true
    try {
      const response = await getQAItems(groupId, params)
      if (response.success && response.data) {
        qaItems.value = response.data.rows
        return response.data
      }
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建问答对
   */
  async function addQAItem(groupId: number, data: CreateQAItemParams) {
    submitting.value = true
    try {
      const response = await createQAItem(groupId, data)
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 更新问答对
   */
  async function updateQAItemById(id: number, data: Partial<CreateQAItemParams>) {
    submitting.value = true
    try {
      const response = await updateQAItem(id, data)
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 删除问答对
   */
  async function removeQAItem(id: number) {
    submitting.value = true
    try {
      const response = await deleteQAItem(id)
      return response
    } finally {
      submitting.value = false
    }
  }

  /**
   * 批量删除问答对
   */
  async function batchRemoveQAItems(groupId: number, ids: number[]) {
    submitting.value = true
    try {
      const response = await batchDeleteQAItems(groupId, ids)
      return response
    } finally {
      submitting.value = false
    }
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
    queryParams.value = {
      page: 1,
      limit: 20
    }
  }

  return {
    // State
    groups,
    currentGroup,
    qaItems,
    loading,
    submitting,
    pagination,
    queryParams,
    
    // Getters
    hasGroups,
    isFirstPage,
    isLastPage,
    
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
    resetQueryParams
  }
})
