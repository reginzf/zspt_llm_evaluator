import { get, post, put, del } from './index'
import type { ApiResponse } from './qa'

// LLM 模型
export interface LLMModel {
  model_name: string
  model_type?: string
  api_base: string
  api_key?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  timeout?: number
  max_retries?: number
  description?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
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
 * 获取模型列表
 */
export async function getModelList(): Promise<ApiResponse<LLMModel[]>> {
  return get<ApiResponse<LLMModel[]>>('/llm/models')
}

/**
 * 获取模型详情
 */
export async function getModelDetail(modelName: string): Promise<ApiResponse<LLMModel>> {
  return get<ApiResponse<LLMModel>>(`/llm/models/${modelName}`)
}

/**
 * 创建模型
 */
export async function createModel(data: Omit<LLMModel, 'created_at' | 'updated_at'>): Promise<ApiResponse<void>> {
  return post<ApiResponse<void>>('/llm/models', data)
}

/**
 * 更新模型
 */
export async function updateModel(modelName: string, data: Partial<LLMModel>): Promise<ApiResponse<void>> {
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
  return get<ApiResponse<EvaluationReport[]>>(`/llm/models/${modelName}/reports`)
}
