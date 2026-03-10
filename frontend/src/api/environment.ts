import { legacyGet, legacyPost, legacyPut, legacyDel } from './index'
import type { ApiResponse } from '@/types'

// 环境 - 匹配数据库字段
export interface Environment {
  zlpt_base_id: string
  zlpt_name: string
  project_name?: string
  project_id?: string
  zlpt_base_url?: string
  domain?: string
  username?: string
  password?: string
  zlpt_key?: string  // 兼容旧字段
  zlpt_describe?: string  // 兼容旧字段
  created_at?: string
  updated_at?: string
}

// ============ 环境管理 API ============

/**
 * 获取环境列表
 */
export async function getEnvironmentList(): Promise<ApiResponse<Environment[]>> {
  return legacyGet<ApiResponse<Environment[]>>('/api/environment/list/')
}

/**
 * 创建环境
 */
export async function createEnvironment(data: {
  zlpt_name: string
  project_name: string
  zlpt_base_url: string
  domain: string
  username: string
  password: string
}): Promise<ApiResponse<{ zlpt_base_id: string }>> {
  return legacyPost<ApiResponse<{ zlpt_base_id: string }>>('/api/environment/create/', data)
}

/**
 * 更新环境
 */
export async function updateEnvironment(data: {
  zlpt_base_id: string
  zlpt_name?: string
  project_name?: string
  zlpt_base_url?: string
  domain?: string
  username?: string
  password?: string
}): Promise<ApiResponse<void>> {
  return legacyPut<ApiResponse<void>>('/api/environment/update/', data)
}

/**
 * 删除环境
 */
export async function deleteEnvironment(envId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/api/environment/delete/', {
    data: { zlpt_base_id: envId }
  })
}

// 知识库
export interface KnowledgeBase {
  knowledge_id: string
  knowledge_name: string
  kno_root_id?: string
  chunk_size?: number
  chunk_overlap?: number
  visiblerange?: string
  created_at?: string
  updated_at?: string
}

/**
 * 获取环境详情中的知识库列表
 */
export async function getEnvironmentKnowledgeBases(
  envId: string,
  searchField?: string,
  searchValue?: string
): Promise<ApiResponse<KnowledgeBase[]>> {
  const params: any = { zlpt_id: envId }
  if (searchField && searchValue) {
    params.search_field = searchField
    params.search_value = searchValue
  }
  return legacyPost<ApiResponse<KnowledgeBase[]>>('/api/environment_detail_list', params)
}

/**
 * 创建知识库
 */
export async function createKnowledgeBase(data: {
  knowledge_name: string
  zlpt_base_id: string
  chunk_size: number
  chunk_overlap: number
  sliceidentifier: string[]
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/knowledge_base/create', data)
}

/**
 * 更新知识库
 */
export async function updateKnowledgeBase(
  knowledgeId: string,
  data: { knowledge_name: string }
): Promise<ApiResponse<void>> {
  return legacyPut<ApiResponse<void>>(`/knowledge_base/update/${knowledgeId}`, data)
}

/**
 * 删除知识库
 */
export async function deleteKnowledgeBase(knowledgeId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>(`/knowledge_base/delete/${knowledgeId}`)
}
