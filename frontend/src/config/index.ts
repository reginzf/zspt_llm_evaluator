/**
 * 前端配置文件
 * 根据环境变量自动适配开发/生产环境
 */

// API 基础 URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 后端服务地址（用于代理配置参考）
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:5001'

// 应用标题
export const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'AI-KEN'

// 是否开发环境
export const IS_DEV = import.meta.env.DEV

// 是否生产环境
export const IS_PROD = import.meta.env.PROD

// 是否启用 Mock
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 是否启用日志
export const ENABLE_LOG = import.meta.env.VITE_ENABLE_LOG !== 'false'

// 日志工具
export const logger = {
  log: (...args: any[]) => ENABLE_LOG && console.log('[AI-KEN]', ...args),
  error: (...args: any[]) => ENABLE_LOG && console.error('[AI-KEN]', ...args),
  warn: (...args: any[]) => ENABLE_LOG && console.warn('[AI-KEN]', ...args),
  info: (...args: any[]) => ENABLE_LOG && console.info('[AI-KEN]', ...args),
}
