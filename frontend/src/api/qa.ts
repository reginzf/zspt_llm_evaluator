import { get, post, put, del } from './index'

// 问答对组接口
export interface QAGroup {
  id: number
  name: string
  purpose?: string
  test_type: 'accuracy' | 'performance' | 'robustness' | 'comprehensive' | 'custom'
  language: 'zh' | 'en' | 'multi'
  difficulty_range?: string
  tags: string[]
  metadata?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
  qa_count?: number
}

// 问答对接口
export interface QAItem {
  id: number
  group_id: number
  question: string
  answers: string[] | { text: string[]; answer_start: number[] }
  context?: string
  question_type?: 'factual' | 'contextual' | 'conceptual' | 'reasoning' | 'application' | 'multi_choice'
  source_dataset?: string
  hf_dataset_id?: string
  language?: string
  difficulty_level?: number
  category?: string
  sub_category?: string
  tags?: string[]
  fixed_metadata?: Record<string, any>
  dynamic_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

// 分页响应
export interface PaginationData<T> {
  total: number
  page: number
  limit: number
  pages: number
  rows: T[]
}

// API 响应格式
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
}

// 查询参数
export interface QAGroupQueryParams {
  page?: number
  limit?: number
  keyword?: string
  test_type?: string
  language?: string
  is_active?: boolean
  order_by?: string
}

// 创建分组参数
export interface CreateQAGroupParams {
  name: string
  purpose?: string
  test_type?: string
  language?: string
  difficulty_range?: string
  tags?: string[]
  metadata?: Record<string, any>
}

// 更新分组参数
export interface UpdateQAGroupParams {
  name?: string
  purpose?: string
  test_type?: string
  language?: string
  difficulty_range?: string
  tags?: string[]
  metadata?: Record<string, any>
  is_active?: boolean
}

// 查询问答对参数
export interface QAItemQueryParams {
  page?: number
  limit?: number
  question_type?: string
  difficulty_level?: number
  category?: string
  language?: string
  question_keyword?: string
  context_keyword?: string
  order_by?: string
}

// 创建问答对参数
export interface CreateQAItemParams {
  question: string
  answers: string[] | { text: string[]; answer_start: number[] }
  context?: string
  question_type?: string
  source_dataset?: string
  hf_dataset_id?: string
  language?: string
  difficulty_level?: number
  category?: string
  sub_category?: string
  tags?: string[]
  fixed_metadata?: Record<string, any>
  dynamic_metadata?: Record<string, any>
}

// ============ 问答对组 API ============

/**
 * 获取问答对组列表
 */
export async function getQAGroups(params: QAGroupQueryParams = {}): Promise<ApiResponse<PaginationData<QAGroup>>> {
  const queryParams = new URLSearchParams()
  if (params.page) queryParams.append('page', String(params.page))
  if (params.limit) queryParams.append('limit', String(params.limit))
  if (params.keyword) queryParams.append('keyword', params.keyword)
  if (params.test_type) queryParams.append('test_type', params.test_type)
  if (params.language) queryParams.append('language', params.language)
  if (params.is_active !== undefined) queryParams.append('is_active', String(params.is_active))
  if (params.order_by) queryParams.append('order_by', params.order_by)

  const queryString = queryParams.toString()
  return get<ApiResponse<PaginationData<QAGroup>>>(`/qa/groups${queryString ? `?${queryString}` : ''}`)
}

/**
 * 创建问答对组
 */
export async function createQAGroup(data: CreateQAGroupParams): Promise<ApiResponse<{ group_id: number }>> {
  return post<ApiResponse<{ group_id: number }>>('/qa/groups', data)
}

/**
 * 获取分组详情
 */
export async function getQAGroupDetail(id: number): Promise<ApiResponse<QAGroup>> {
  return get<ApiResponse<QAGroup>>(`/qa/groups/${id}`)
}

/**
 * 更新分组
 */
export async function updateQAGroup(id: number, data: UpdateQAGroupParams): Promise<ApiResponse<void>> {
  return put<ApiResponse<void>>(`/qa/groups/${id}`, data)
}

/**
 * 删除分组
 */
export async function deleteQAGroup(id: number, force: boolean = false): Promise<ApiResponse<void>> {
  return del<ApiResponse<void>>(`/qa/groups/${id}${force ? '?force=true' : ''}`)
}

/**
 * 切换分组状态
 */
export async function toggleQAGroupStatus(id: number, status?: boolean): Promise<ApiResponse<{ status: boolean }>> {
  return post<ApiResponse<{ status: boolean }>>(`/qa/groups/${id}/toggle`, { status })
}

/**
 * 获取分组统计信息
 */
export async function getQAGroupStatistics(id: number): Promise<ApiResponse<Record<string, any>>> {
  return get<ApiResponse<Record<string, any>>>(`/qa/groups/${id}/statistics`)
}

// ============ 问答对 API ============

/**
 * 获取问答对列表
 */
export async function getQAItems(groupId: number, params: QAItemQueryParams = {}): Promise<ApiResponse<PaginationData<QAItem>>> {
  const queryParams = new URLSearchParams()
  if (params.page) queryParams.append('page', String(params.page))
  if (params.limit) queryParams.append('limit', String(params.limit))
  if (params.question_type) queryParams.append('question_type', params.question_type)
  if (params.difficulty_level) queryParams.append('difficulty_level', String(params.difficulty_level))
  if (params.category) queryParams.append('category', params.category)
  if (params.language) queryParams.append('language', params.language)
  if (params.question_keyword) queryParams.append('question_keyword', params.question_keyword)
  if (params.context_keyword) queryParams.append('context_keyword', params.context_keyword)
  if (params.order_by) queryParams.append('order_by', params.order_by)

  const queryString = queryParams.toString()
  return get<ApiResponse<PaginationData<QAItem>>>(`/qa/groups/${groupId}/items${queryString ? `?${queryString}` : ''}`)
}

/**
 * 创建问答对
 */
export async function createQAItem(groupId: number, data: CreateQAItemParams): Promise<ApiResponse<{ qa_id: number }>> {
  return post<ApiResponse<{ qa_id: number }>>(`/qa/groups/${groupId}/items`, data)
}

/**
 * 获取问答对详情
 */
export async function getQAItemDetail(id: number): Promise<ApiResponse<QAItem>> {
  return get<ApiResponse<QAItem>>(`/qa/items/${id}`)
}

/**
 * 更新问答对
 */
export async function updateQAItem(id: number, data: Partial<CreateQAItemParams>): Promise<ApiResponse<void>> {
  return put<ApiResponse<void>>(`/qa/items/${id}`, data)
}

/**
 * 删除问答对
 */
export async function deleteQAItem(id: number): Promise<ApiResponse<void>> {
  return del<ApiResponse<void>>(`/qa/items/${id}`)
}

/**
 * 批量删除问答对
 */
export async function batchDeleteQAItems(groupId: number, ids: number[]): Promise<ApiResponse<{ deleted_count: number; failed_count: number; failed_ids: number[] }>> {
  return post<ApiResponse<{ deleted_count: number; failed_count: number; failed_ids: number[] }>>(`/qa/groups/${groupId}/items/batch-delete`, { ids })
}

/**
 * 批量创建问答对
 */
export async function batchCreateQAItems(groupId: number, items: CreateQAItemParams[]): Promise<ApiResponse<{
  total: number
  success: number
  failed: number
  skipped: number
  duration: number
}>> {
  return post<ApiResponse<{
    total: number
    success: number
    failed: number
    skipped: number
    duration: number
  }>>(`/qa/groups/${groupId}/items/batch`, { items })
}

/**
 * 搜索相似问题
 */
export async function searchSimilarQuestions(question: string, groupId?: number, limit: number = 10): Promise<ApiResponse<QAItem[]>> {
  const params = new URLSearchParams()
  params.append('question', question)
  if (groupId) params.append('group_id', String(groupId))
  params.append('limit', String(limit))
  return get<ApiResponse<QAItem[]>>(`/qa/items/search?${params.toString()}`)
}

// ============ 导入 API ============

/**
 * 从 HuggingFace 导入
 */
export async function importFromHuggingFace(groupId: number, datasetPath: string, batchSize: number = 1000): Promise<ApiResponse<{
  total: number
  success: number
  failed: number
  skipped: number
  duration: number
  error_count: number
}>> {
  return post<ApiResponse<{
    total: number
    success: number
    failed: number
    skipped: number
    duration: number
    error_count: number
  }>>(`/qa/groups/${groupId}/items/import/huggingface`, { dataset_path: datasetPath, batch_size: batchSize })
}

/**
 * 上传文件
 */
export async function uploadQAFile(groupId: number, files: FileList): Promise<ApiResponse<{
  file_path: string
  minio_prefix: string
  saved_files: Array<{ object_name: string; relative_path: string; original_name: string }>
  is_folder: boolean
  folder_name: string
  file_count: number
  storage_type: string
}>> {
  const formData = new FormData()
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (file) {
      formData.append('file', file)
    }
  }
  
  // 使用 fetch 直接发送，因为需要 multipart/form-data
  const response = await fetch(`/api/qa/groups/${groupId}/items/import/upload`, {
    method: 'POST',
    body: formData
  })
  return response.json() as Promise<ApiResponse<{
    file_path: string
    minio_prefix: string
    saved_files: Array<{ object_name: string; relative_path: string; original_name: string }>
    is_folder: boolean
    folder_name: string
    file_count: number
    storage_type: string
  }>>
}

/**
 * 预览数据集
 */
export async function previewDataset(groupId: number, filePath: string, previewRows: number = 5, minioPrefix?: string, savedFiles?: any[]): Promise<ApiResponse<{
  preview: {
    file_path: string
    total_records: number
    preview_rows: number
    columns: string[]
    suggestions: Record<string, string>
  }
  temp_path: string | null
}>> {
  return post<ApiResponse<{
    preview: {
      file_path: string
      total_records: number
      preview_rows: number
      columns: string[]
      suggestions: Record<string, string>
    }
    temp_path: string | null
  }>>(`/qa/groups/${groupId}/items/import/preview`, {
    file_path: filePath,
    preview_rows: previewRows,
    minio_prefix: minioPrefix,
    saved_files: savedFiles
  })
}
