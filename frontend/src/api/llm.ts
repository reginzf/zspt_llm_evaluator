import { get, post, put, del } from './index'
import type { ApiResponse, PaginationData, PaginationParams } from '@/types'

// LLM 模型 - 与后端字段保持一致
export interface LLMModel {
  id?: number
  name: string
  type?: string
  api_key?: string
  api_url: string
  model?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  timeout?: number
  max_retries?: number
  version?: string
  status?: 'connected' | 'error' | 'unknown'
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

// 模型列表响应
export interface ModelListResponse {
  total: number
  page: number
  limit: number
  pages: number
  rows: LLMModel[]
}

// 评估报告
export interface EvaluationReport {
  filename: string
  model_name: string
  created_at: string
  path: string
}

// ============ LLM 模型 API ============

/**
 * 获取模型列表 - 支持分页和筛选
 */
export async function getModelList(params?: {
  page?: number
  limit?: number
  type?: string
  status?: string
  keyword?: string
}): Promise<ApiResponse<ModelListResponse>> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.type) queryParams.append('type', params.type)
  if (params?.status) queryParams.append('status', params.status)
  if (params?.keyword) queryParams.append('keyword', params.keyword)
  
  const query = queryParams.toString()
  return get<ApiResponse<ModelListResponse>>(`/llm/models${query ? '?' + query : ''}`)
}

/**
 * 获取模型详情
 */
export async function getModelDetail(modelName: string): Promise<ApiResponse<{
  config: LLMModel
  connection_status: boolean
  last_evaluation?: string
  evaluation_count: number
  recent_reports: EvaluationReport[]
}>> {
  return get<ApiResponse<{
    config: LLMModel
    connection_status: boolean
    last_evaluation?: string
    evaluation_count: number
    recent_reports: EvaluationReport[]
  }>>(`/llm/models/${modelName}`)
}

/**
 * 创建模型 - 字段名与后端保持一致
 */
export async function createModel(data: {
  name: string
  type: string
  api_key: string
  api_url: string
  model?: string
  temperature?: number
  max_tokens?: number
  timeout?: number
  version?: string
}): Promise<ApiResponse<{ id: number }>> {
  return post<ApiResponse<{ id: number }>>('/llm/models', data)
}

/**
 * 更新模型
 */
export async function updateModel(
  modelName: string, 
  data: Partial<{
    type: string
    api_key: string
    api_url: string
    model?: string
    temperature?: number
    max_tokens?: number
    timeout?: number
    version?: string
  }>
): Promise<ApiResponse<void>> {
  return put<ApiResponse<void>>(`/llm/models/${modelName}`, data)
}

/**
 * 删除模型
 */
export async function deleteModel(modelName: string): Promise<ApiResponse<void>> {
  return del<ApiResponse<void>>(`/llm/models/${modelName}`)
}

/**
 * 检查模型连通性
 */
export async function checkModelConnectivity(modelName: string): Promise<ApiResponse<{
  success: boolean
  message: string
  latency?: number
}>> {
  return post<ApiResponse<{
    success: boolean
    message: string
    latency?: number
  }>>(`/llm/models/${modelName}/check`)
}

/**
 * 开始模型评估
 */
export async function startEvaluation(modelName: string, data: {
  qa_group_id: number
  max_workers?: number
  timeout?: number
}): Promise<ApiResponse<{ task_id: string }>> {
  return post<ApiResponse<{ task_id: string }>>(`/llm/models/${modelName}/evaluate`, data)
}

/**
 * 获取评估报告列表
 */
export async function getEvaluationReports(modelName: string): Promise<ApiResponse<EvaluationReport[]>> {
  return get<ApiResponse<EvaluationReport[]>>(`/llm/models/${modelName}/reports?simple=true`)
}
