/**
 * 全局类型定义
 * 统一存放所有模块共享的类型
 */

// API 统一响应格式
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
}

// 分页请求参数
export interface PaginationParams {
  page?: number
  limit?: number
}

// 分页响应数据
export interface PaginationData<T> {
  total: number
  page: number
  limit: number
  pages: number
  rows: T[]
}

// 分页 API 响应
export type PaginatedResponse<T> = ApiResponse<PaginationData<T>>

// 排序方向
export type SortDirection = 'asc' | 'desc'

// 表格排序参数
export interface SortParams {
  prop: string
  order: SortDirection
}

// 通用的选项类型（用于下拉选择）
export interface SelectOption {
  label: string
  value: string | number | boolean
  disabled?: boolean
}

// 状态类型
export type StatusType = 'success' | 'warning' | 'info' | 'danger'

// 表单验证规则
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  validator?: (rule: any, value: any, callback: any) => void
}

// 文件信息
export interface FileInfo {
  name: string
  size: number
  type: string
  url?: string
}

// 日期范围
export interface DateRange {
  start: string | null
  end: string | null
}

// 树形结构节点
export interface TreeNode {
  id: string | number
  label: string
  children?: TreeNode[]
  disabled?: boolean
  [key: string]: any
}

// 列表筛选参数基类
export interface BaseFilterParams extends PaginationParams {
  keyword?: string
  status?: string
  start_date?: string
  end_date?: string
}
