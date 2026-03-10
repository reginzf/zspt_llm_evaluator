/**
 * 格式化工具函数
 * 统一的格式化逻辑，避免在组件中重复
 */

/**
 * 格式化日期时间
 */
export function formatDateTime(date: Date | string | number | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    ...options
  }

  return d.toLocaleString('zh-CN', defaultOptions)
}

/**
 * 格式化日期（不含时间）
 */
export function formatDate(date: Date | string | number | null | undefined): string {
  if (!date) return '-'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)

  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  if (isNaN(bytes) || bytes < 0) return '-'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化数字（添加千分位）
 */
export function formatNumber(num: number | string | null | undefined): string {
  if (num === null || num === undefined || num === '') return '-'
  const n = Number(num)
  if (isNaN(n)) return String(num)
  return n.toLocaleString('zh-CN')
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, total: number, decimals = 2): string {
  if (!total) return '0%'
  const percent = (value / total) * 100
  return percent.toFixed(decimals) + '%'
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number, suffix = '...'): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + suffix
}

/**
 * 将数组格式化为标签字符串
 */
export function formatTags(tags: string | string[] | null | undefined): string[] {
  if (!tags) return []
  if (Array.isArray(tags)) return tags.filter(Boolean)
  if (typeof tags === 'string') {
    try {
      const parsed = JSON.parse(tags)
      return Array.isArray(parsed) ? parsed.filter(Boolean) : [tags]
    } catch {
      return tags.split(/[,，]/).map(t => t.trim()).filter(Boolean)
    }
  }
  return []
}

/**
 * 将值转换为选项标签
 */
export function valueToLabel(
  value: string | number | boolean | null | undefined,
  options: Array<{ value: any; label: string }>
): string {
  if (value === null || value === undefined) return '-'
  const option = options.find(opt => opt.value === value)
  return option?.label || String(value)
}

// 测试类型选项
export const TEST_TYPE_OPTIONS = [
  { value: 'accuracy', label: '准确率测试', type: 'success' as const },
  { value: 'performance', label: '性能测试', type: 'warning' as const },
  { value: 'robustness', label: '鲁棒性测试', type: 'danger' as const },
  { value: 'comprehensive', label: '综合测试', type: 'primary' as const },
  { value: 'custom', label: '自定义测试', type: 'info' as const }
]

// 语言选项
export const LANGUAGE_OPTIONS = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英文' },
  { value: 'multi', label: '多语言' }
]

// 任务状态选项
export const TASK_STATUS_OPTIONS = [
  { value: '未开始', label: '未开始', type: 'info' as const },
  { value: '标注中', label: '标注中', type: 'warning' as const },
  { value: '已完成', label: '已完成', type: 'success' as const }
]

// 标注类型选项
export const ANNOTATION_TYPE_OPTIONS = [
  { value: 'llm', label: 'LLM 标注' },
  { value: 'manual', label: '人工标注' },
  { value: 'mlb', label: 'MLB 标注' }
]

// LLM 模型类型选项
export const MODEL_TYPE_OPTIONS = [
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'qwen', label: '通义千问' },
  { value: 'other', label: '其他' }
]

// 模型状态选项
export const MODEL_STATUS_OPTIONS = [
  { value: 'connected', label: '已连接', type: 'success' as const },
  { value: 'error', label: '连接失败', type: 'danger' as const },
  { value: 'unknown', label: '未检测', type: 'info' as const }
]
