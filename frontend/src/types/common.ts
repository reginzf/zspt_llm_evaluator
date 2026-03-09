/**
 * 通用类型定义
 */

// API 响应格式
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 分页请求参数
export interface PaginationParams {
  page: number
  page_size: number
}

// 分页响应数据
export interface PaginationData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 表格列配置
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  fixed?: 'left' | 'right'
  formatter?: (row: unknown, column: unknown, cellValue: unknown) => string
}

// 表单字段
export interface FormField {
  name: string
  label: string
  type: 'input' | 'select' | 'textarea' | 'date' | 'datetime' | 'number'
  required?: boolean
  placeholder?: string
  options?: Array<{ label: string; value: string | number }>
  rules?: unknown[]
}

// 筛选条件
export interface FilterCondition {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in'
  value: unknown
}

// 排序参数
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}
