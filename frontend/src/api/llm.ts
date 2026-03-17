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
  id: number
  report_name: string
  model_name: string
  group_name?: string
  qa_count?: number
  created_at: string
  path: string
  exact_match?: number
  f1_score?: number
  semantic_similarity?: number
}

// 开始评估参数
export interface StartEvaluationParams {
  group_id: number
  offset?: number
  limit?: number
  parallel?: boolean
  max_workers?: number
  match_types?: Record<string, any>
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
export async function startEvaluation(
  modelName: string, 
  data: StartEvaluationParams
): Promise<ApiResponse<{ task_id: string }>> {
  return post<ApiResponse<{ task_id: string }>>(`/llm/models/${modelName}/evaluate`, data)
}

/**
 * 获取评估报告列表
 */
export async function getEvaluationReports(modelName: string): Promise<ApiResponse<EvaluationReport[]>> {
  return get<ApiResponse<EvaluationReport[]>>(`/llm/models/${modelName}/reports`)
}

/**
 * 删除评估报告
 */
export async function deleteEvaluationReport(reportId: number): Promise<ApiResponse<void>> {
  return del<ApiResponse<void>>(`/api/llm/reports/${reportId}`)
}

/**
 * 获取报告问题详情
 */
export async function getReportDetails(
  reportId: number, 
  params?: {
    page?: number
    limit?: number
    sort_by?: string
    sort_order?: 'asc' | 'desc'
    metric?: string
    min_score?: number
  }
): Promise<ApiResponse<{
  total: number
  page: number
  limit: number
  rows: Array<{
    id: number
    question_id: string
    question: string
    context: string
    ground_truth: string[]
    predicted_answer: string
    metrics: Record<string, number>
    inference_time: number
    created_at: string
  }>
}>> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order)
  if (params?.metric) queryParams.append('metric', params.metric)
  if (params?.min_score !== undefined) queryParams.append('min_score', String(params.min_score))

  const query = queryParams.toString()
  return get<ApiResponse<any>>(`/api/llm/reports/${reportId}/details${query ? '?' + query : ''}`)
}

/**
 * 获取报告统计信息
 */
export async function getReportStatistics(reportId: number): Promise<ApiResponse<{
  overall_metrics: Record<string, number>
  metric_distributions: Record<string, { ranges: string[], counts: number[] }>
  total_questions: number
  success_count: number
  error_count: number
}>> {
  return get<ApiResponse<any>>(`/api/llm/reports/${reportId}/statistics`)
}

/**
 * 获取最佳/最差问题
 */
export async function getBestWorstQuestions(
  reportId: number,
  params?: {
    metric?: string
    limit?: number
  }
): Promise<ApiResponse<{
  best: Array<{
    question_id: string
    question: string
    metric_value: number
    metrics: Record<string, number>
  }>
  worst: Array<{
    question_id: string
    question: string
    metric_value: number
    metrics: Record<string, number>
  }>
}>> {
  const queryParams = new URLSearchParams()
  if (params?.metric) queryParams.append('metric', params.metric)
  if (params?.limit) queryParams.append('limit', String(params.limit))
  
  const query = queryParams.toString()
  return get<ApiResponse<any>>(`/api/llm/reports/${reportId}/best-worst${query ? '?' + query : ''}`)
}

/**
 * 获取评估报告完整内容（用于报告查看页面）
 */
export async function getReportView(reportId: number): Promise<ApiResponse<any>> {
  return get<ApiResponse<any>>(`/api/llm/reports/${reportId}/view`)
}

/**
 * 获取报告的问题详情列表（包含问题文本、上下文、答案等）
 */
export async function getReportQuestions(
  reportId: number,
  params?: {
    page?: number
    limit?: number
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }
): Promise<ApiResponse<{
  total: number
  page: number
  limit: number
  pages: number
  rows: Array<{
    id: number
    report_id: number
    question_id: string
    question: string
    context: string
    predicted_answer: string
    ground_truth: string[]
    success: boolean
    inference_time: number
    exact_match: number
    f1_score: number
    semantic_similarity: number
    answer_coverage: number
    answer_relevance: number
    context_utilization: number
    answer_completeness: number
    answer_conciseness: number
  }>
}>> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order)

  const query = queryParams.toString()
  return get<ApiResponse<any>>(`/api/llm/reports/${reportId}/details${query ? '?' + query : ''}`)
}
