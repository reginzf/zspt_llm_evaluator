import { legacyGet } from './index'
import type { ApiResponse } from './qa'

// 报告
export interface Report {
  name: string
  path: string
  object_name?: string  // MinIO 完整对象名称
  directory: string
  created_at?: string
  size?: number
}

// 报告列表响应（包含目录结构）
export interface ReportListResponse {
  success: boolean
  data: Report[]
  directory_structure: Record<string, string[]>
  message?: string
}

// ============ 报告 API ============

/**
 * 获取报告列表
 */
export async function getReportList(): Promise<ReportListResponse> {
  return legacyGet<ReportListResponse>('/report_list/data')
}

/**
 * 获取报告详情
 */
export async function getReportDetail(filename: string): Promise<string> {
  const response = await fetch(`/report/${filename}`)
  if (!response.ok) {
    throw new Error('获取报告失败')
  }
  return response.text()
}
