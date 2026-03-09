/**
 * LLM 模型模块类型定义
 */

// LLM 模型
export interface LLMModel {
  name: string
  model_type: string
  api_base: string
  api_key?: string
  max_tokens: number
  temperature: number
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

// 评估报告
export interface EvaluationReport {
  filename: string
  model_name: string
  qa_group_id: number
  total_questions: number
  correct_answers: number
  accuracy: number
  avg_latency: number
  created_at: string
}

// 创建模型请求
export interface CreateModelRequest {
  name: string
  model_type: string
  api_base: string
  api_key?: string
  max_tokens?: number
  temperature?: number
}

// 更新模型请求
export interface UpdateModelRequest {
  model_type?: string
  api_base?: string
  api_key?: string
  max_tokens?: number
  temperature?: number
  status?: string
}

// 评估任务请求
export interface EvaluateRequest {
  qa_group_id: number
  max_concurrent?: number
}
