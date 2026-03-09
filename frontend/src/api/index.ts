import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例 - 用于 /api 前缀的接口
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 创建 axios 实例 - 用于非 /api 前缀的接口
const legacyClient: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
const requestInterceptor = (config: any) => {
  // 可以在这里添加认证 token
  return config
}

const requestErrorInterceptor = (error: any) => {
  return Promise.reject(error)
}

// 响应拦截器
const responseInterceptor = (response: AxiosResponse) => {
  return response.data
}

const responseErrorInterceptor = (error: any) => {
  const message = error.response?.data?.message || error.message || '请求失败'
  ElMessage.error(message)
  return Promise.reject(error)
}

apiClient.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
apiClient.interceptors.response.use(responseInterceptor, responseErrorInterceptor)

legacyClient.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
legacyClient.interceptors.response.use(responseInterceptor, responseErrorInterceptor)

export default apiClient

// 通用请求方法 - /api 前缀
export function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return apiClient.get(url, config)
}

export function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return apiClient.post(url, data, config)
}

export function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return apiClient.put(url, data, config)
}

export function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return apiClient.delete(url, config)
}

export function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return apiClient.patch(url, data, config)
}

// 通用请求方法 - 非 /api 前缀 (兼容旧接口)
export function legacyGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return legacyClient.get(url, config)
}

export function legacyPost<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return legacyClient.post(url, data, config)
}

export function legacyPut<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return legacyClient.put(url, data, config)
}

export function legacyDel<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return legacyClient.delete(url, config)
}
