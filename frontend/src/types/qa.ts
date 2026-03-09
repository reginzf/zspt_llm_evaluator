/**
 * 问答对模块类型定义
 */

// 问答对分组
export interface QAGroup {
  id: number
  name: string
  description: string
  test_type: 'functional' | 'performance' | 'security'
  language: 'zh' | 'en'
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

// 问答对项
export interface QAItem {
  id: number
  group_id: number
  question: string
  answer: string
  created_at: string
  updated_at: string
}

// 创建分组请求
export interface CreateQAGroupRequest {
  name: string
  description?: string
  test_type: string
  language: string
}

// 更新分组请求
export interface UpdateQAGroupRequest {
  name?: string
  description?: string
  test_type?: string
  language?: string
  status?: string
}

// 创建问答对请求
export interface CreateQAItemRequest {
  question: string
  answer: string
}

// 导入配置
export interface ImportConfig {
  source: 'file' | 'huggingface'
  file?: File
  dataset_name?: string
}
