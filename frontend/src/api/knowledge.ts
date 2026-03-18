import { legacyGet, legacyPost, legacyPut, legacyDel } from './index'
import type { ApiResponse, PaginationData, PaginationParams } from '@/types'

// 本地知识库
export interface LocalKnowledge {
  kno_id: string
  kno_name: string
  kno_describe?: string
  kno_path?: string
  ls_status: number
  knowledge_domain?: string
  domain_description?: string
  required_background?: string[]
  required_skills?: string[]
  created_at?: string
  updated_at?: string
}

// 知识库文件
export interface LocalKnowledgeFile {
  knol_id: string
  kno_id: string
  kno_name: string
  kno_describe?: string
  ls_status: number
  knol_path?: string
  created_at?: string
}

// 知识库绑定
export interface KnowledgeBinding {
  knowledge_id: string
  knowledge_name?: string
  bind_status: number
}

// 问题集
export interface QuestionSet {
  question_id: string
  question_name: string
  question_set_type?: string
  knowledge_id?: string
  created_at?: string
}

// 问题
export interface Question {
  question_id: string
  question_type: string
  question_content: string
  chunk_ids?: string
  set_id?: string
}

// 标注任务
export interface AnnotationTask {
  task_id: string
  task_name: string
  local_knowledge_id?: string
  question_set_id?: string
  label_studio_env_id?: string
  knowledge_base_id?: string
  label_studio_project_id?: string
  total_chunks?: number
  annotated_chunks?: number
  task_status: string
  task_created_at?: string
  task_updated_at?: string
  annotation_type?: string
  knowledge_base_name?: string
  question_set_name?: string
}

// Label-Studio 环境
export interface LabelStudioEnv {
  label_studio_id: string
  label_studio_url: string
  label_studio_api_key?: string
  project_count?: number
  task_count?: number
}

// ============ 本地知识库 API ============

/**
 * 获取本地知识库列表
 */
export async function getLocalKnowledgeList(): Promise<ApiResponse<LocalKnowledge[]>> {
  return legacyGet<ApiResponse<LocalKnowledge[]>>('/api/local_knowledge/list')
}

/**
 * 创建本地知识库
 */
export async function createLocalKnowledge(data: {
  kno_name: string
  kno_describe?: string
}): Promise<ApiResponse<{ kno_id: string }>> {
  return legacyPost<ApiResponse<{ kno_id: string }>>('/api/local_knowledge/create', data)
}

/**
 * 更新本地知识库
 */
export async function updateLocalKnowledge(data: {
  kno_id: string
  kno_name?: string
  kno_describe?: string
  knowledge_domain?: string
  domain_description?: string
  required_background?: string[]
  required_skills?: string[]
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/api/local_knowledge/edit', data)
}

/**
 * 删除本地知识库
 */
export async function deleteLocalKnowledge(knoId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>(`/api/local_knowledge/delete/${knoId}`)
}

// ============ 知识库详情 API ============

/**
 * 获取知识库文件列表
 */
export async function getKnowledgeFiles(knoId: string, knoName: string): Promise<ApiResponse<LocalKnowledgeFile[]>> {
  return legacyPost<ApiResponse<LocalKnowledgeFile[]>>('/api/local_knowledge_detail', {
    kno_id: knoId,
    kno_name: knoName
  })
}

/**
 * 获取知识库绑定状态
 */
export async function getKnowledgeBindings(knoId: string): Promise<ApiResponse<KnowledgeBinding[]>> {
  return legacyGet<ApiResponse<KnowledgeBinding[]>>(`/api/local_knowledge/bindings/${knoId}`)
}

/**
 * 绑定知识库
 */
export async function bindKnowledge(data: {
  kno_id: string
  knowledge_id: string
  operation: 'bind' | 'unbind' | 'update'
  status?: number
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/api/local_knowledge/bind', {
    local_kno_id: data.kno_id,
    kb_id: data.knowledge_id,
    action: data.operation,
    status: data.status
  })
}

/**
 * 同步知识库
 */
export async function syncKnowledge(knoId: string, knowledgeId: string): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/sync', {
    local_kno_id: knoId,
    knowledge_id: knowledgeId
  })
}

/**
 * 编辑文件描述
 */
export async function editFile(knolId: string, data: { kno_describe?: string }): Promise<ApiResponse<void>> {
  return legacyPut<ApiResponse<void>>(`/local_knowledge_doc/edit/${knolId}`, data)
}

/**
 * 删除文件
 */
export async function deleteFile(knolId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>(`/local_knowledge_doc/delete/${knolId}`)
}

// ============ 问题集 API ============

/**
 * 获取问题集列表
 */
export async function getQuestionSets(knowledgeId: string): Promise<ApiResponse<QuestionSet[]>> {
  return legacyGet<ApiResponse<QuestionSet[]>>(`/api/local_knowledge_detail/question/set/list?knowledge_id=${knowledgeId}`)
}

/**
 * 创建问题集
 */
export async function createQuestionSet(data: {
  question_name: string
  question_set_type: string
  knowledge_id: string
}): Promise<ApiResponse<void>> {
  // 转换字段名以适配后端 API
  const payload = {
    set_name: data.question_name,
    set_type: data.question_set_type,
    knowledge_id: data.knowledge_id
  }
  return legacyPost<ApiResponse<void>>('/api/local_knowledge_detail/question_set/create', payload)
}

/**
 * 删除问题集
 */
export async function deleteQuestionSet(questionId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/api/local_knowledge_detail/question/set/delete', {
    params: { question_id: questionId }
  })
}

/**
 * 获取问题列表
 */
export async function getQuestions(setId: string, questionType: string): Promise<ApiResponse<Question[]>> {
  return legacyPost<ApiResponse<Question[]>>('/api/local_knowledge_detail/question/list', {
    set_id: setId,
    question_type: questionType
  })
}

/**
 * 创建问题
 */
export async function createQuestion(data: {
  question_type: string
  question_content: string
  chunk_ids?: string
  set_id?: string
  question_set_type?: string
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/api/local_knowledge_detail/question/create', data)
}

/**
 * 获取问题详情
 */
export async function getQuestionDetail(questionId: string, questionSetType: string): Promise<ApiResponse<Question>> {
  return legacyPost<ApiResponse<Question>>('/api/local_knowledge_detail/question/detail', {
    question_id: questionId,
    question_set_type: questionSetType
  })
}

/**
 * 更新问题
 */
export async function updateQuestion(questionId: string, data: {
  question_type?: string
  question_content?: string
  chunk_ids?: string
}): Promise<ApiResponse<void>> {
  // 处理空 chunk_ids，避免 JSON 类型错误
  const payload: any = {
    question_id: questionId,
    ...data
  }
  if (payload.chunk_ids === '') {
    payload.chunk_ids = null  // 或 []，让后端处理默认值
  }
  return legacyPut<ApiResponse<void>>('/api/local_knowledge_detail/question/update', payload)
}

/**
 * 删除问题
 */
export async function deleteQuestion(questionId: string, questionSetType: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/api/local_knowledge_detail/question/delete', {
    data: { 
      question_id: questionId,
      question_set_type: questionSetType
    }
  })
}

// ============ 标注任务 API ============

/**
 * 获取标注任务列表（新 API，支持分页和筛选）
 */
export async function getAnnotationTaskList(params?: {
  page?: number
  limit?: number
  keyword?: string
  task_status?: string
  annotation_type?: string
}): Promise<ApiResponse<{
  rows: AnnotationTask[]
  total: number
  page: number
  limit: number
}>> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.keyword) queryParams.append('keyword', params.keyword)
  if (params?.task_status) queryParams.append('task_status', params.task_status)
  if (params?.annotation_type) queryParams.append('annotation_type', params.annotation_type)
  
  const query = queryParams.toString()
  return legacyGet<ApiResponse<{
    rows: AnnotationTask[]
    total: number
    page: number
    limit: number
  }>>(`/api/annotation/tasks/list${query ? '?' + query : ''}`)
}

/**
 * 获取 Label-Studio 环境列表
 */
export async function getLabelStudioEnvs(): Promise<ApiResponse<LabelStudioEnv[]>> {
  return legacyGet<ApiResponse<LabelStudioEnv[]>>('/api/label_studio_env/list/')
}

/**
 * 获取 Label-Studio 环境列表（用于标注任务页面）
 */
export async function getLabelStudioEnvironmentsList(): Promise<ApiResponse<LabelStudioEnv[]>> {
  return legacyGet<ApiResponse<LabelStudioEnv[]>>('/api/label_studio/environments/list')
}

/**
 * 获取本地知识库列表（简化版，用于标注任务页面）
 */
export async function getLocalKnowledgeListSimple(): Promise<ApiResponse<{ 
  knowledge_id: string
  knowledge_name: string
}[]>> {
  return legacyGet<ApiResponse<{ knowledge_id: string; knowledge_name: string }[]>>('/api/local_knowledge/list')
}

/**
 * 获取问题集列表（用于标注任务页面）
 */
export async function getQuestionsList(knowledgeId: string): Promise<ApiResponse<{
  question_id: string
  question_name: string
  knowledge_id?: string
}[]>> {
  return legacyGet<ApiResponse<{ question_id: string; question_name: string; knowledge_id?: string }[]>>(`/api/questions/list?knowledge_id=${knowledgeId}`)
}

/**
 * 获取知识库绑定的 Label-Studio 环境列表
 */
export async function getLabelStudioEnvironments(knoId: string): Promise<ApiResponse<{
  environments: LabelStudioEnv[]
  bound_environments: any[]
}>> {
  return legacyPost<ApiResponse<{
    environments: LabelStudioEnv[]
    bound_environments: any[]
  }>>('/local_knowledge_detail/label_studio/get_environments', { kno_id: knoId })
}

/**
 * 绑定 Label-Studio 环境到知识库
 */
export async function bindLabelStudioEnvironment(knoId: string, lsId: string): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/label_studio/bind_environment', {
    kno_id: knoId,
    ls_id: lsId
  })
}

/**
 * 解绑 Label-Studio 环境
 */
export async function unbindLabelStudioEnvironment(knoId: string, lsId: string): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/label_studio/unbind_environment', {
    kno_id: knoId,
    ls_id: lsId
  })
}

/**
 * 创建 Label-Studio 环境
 */
export async function createLabelStudioEnv(data: {
  label_studio_url: string
  label_studio_token?: string
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/api/label_studio_env/create/', data)
}

/**
 * 更新 Label-Studio 环境
 */
export async function updateLabelStudioEnv(data: {
  label_studio_id: string
  label_studio_url?: string
  label_studio_token?: string
}): Promise<ApiResponse<void>> {
  return legacyPut<ApiResponse<void>>('/api/label_studio_env/update/', data)
}

/**
 * 删除 Label-Studio 环境
 */
export async function deleteLabelStudioEnv(labelStudioId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/api/label_studio_env/delete/', {
    data: { label_studio_id: labelStudioId }
  })
}

/**
 * 获取标注任务列表（通过 Label-Studio 项目 API）
 */
export async function getAnnotationTasks(knoId: string): Promise<ApiResponse<AnnotationTask[]>> {
  return legacyPost<ApiResponse<AnnotationTask[]>>(`/local_knowledge_detail/label_studio/get_project`, { kno_id: knoId })
}

/**
 * 获取特定环境下的标注任务列表
 */
export async function getTasksByEnvironment(envId: string, knoId: string): Promise<ApiResponse<AnnotationTask[]>> {
  return legacyPost<ApiResponse<AnnotationTask[]>>('/local_knowledge_detail/label_studio/get_tasks_by_environment', {
    env_id: envId,
    kno_id: knoId
  })
}

/**
 * 创建标注任务
 */
export async function createAnnotationTask(data: {
  task_name: string
  local_knowledge_id: string
  question_set_id: string
  label_studio_env_id: string
  annotation_type: string
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/api/annotation/tasks/create', data)
}

/**
 * 更新标注任务
 */
export async function updateAnnotationTask(data: {
  task_id: string
  task_name?: string
  task_status?: string
}): Promise<ApiResponse<void>> {
  return legacyPut<ApiResponse<void>>('/api/annotation/tasks/update', data)
}

/**
 * 删除标注任务
 */
export async function deleteAnnotationTask(taskId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/api/annotation/tasks/delete', {
    data: { task_id: taskId }
  })
}

/**
 * 更新标注类型
 */
export async function updateAnnotationType(taskId: string, annotationType: string): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/label_studio/update_annotation', {
    task_id: taskId,
    annotation_type: annotationType
  })
}

/**
 * 同步标注任务
 */
export async function syncAnnotationTask(taskId: string): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/label_studio/sync_project', {
    task_id: taskId
  })
}

/**
 * 获取已完成的标注任务列表（用于创建指标任务）
 */
export async function getCompletedAnnotationTasks(knowledgeId: string): Promise<ApiResponse<any[]>> {
  return legacyPost<ApiResponse<any[]>>('/local_knowledge_detail/task/metric/completed_tasks', {
    local_knowledge_id: knowledgeId
  })
}

/**
 * 创建指标任务
 */
export async function createMetricTask(data: {
  task_id: string
  match_type: string
  knowledge_base_id?: string
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/task/metric/create', data)
}

/**
 * 获取指标任务信息
 */
export async function getMetricTaskInfo(taskId: string): Promise<ApiResponse<any>> {
  return legacyGet<ApiResponse<any>>(`/local_knowledge_detail/task/metric/get_task_info?task_id=${taskId}`)
}

/**
 * 启动质量计算
 */
export async function startCalculation(data: {
  task_id: string
  search_type: string
  match_type: string
  metric_task_id: string
}): Promise<ApiResponse<void>> {
  return legacyPost<ApiResponse<void>>('/local_knowledge_detail/task/metric/start_calculation', data)
}

/**
 * 获取报告列表
 */
export async function getMetricReports(metricTaskId: string): Promise<ApiResponse<any[]>> {
  return legacyGet<ApiResponse<any[]>>(`/local_knowledge_detail/task/metric/get_report?metric_task_id=${metricTaskId}`)
}

/**
 * 删除报告
 */
export async function deleteMetricReport(reportId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/local_knowledge_detail/task/metric/delete_report', {
    data: { report_id: reportId }
  })
}

/**
 * 删除指标任务
 */
export async function deleteMetricTaskApi(metricTaskId: string): Promise<ApiResponse<void>> {
  return legacyDel<ApiResponse<void>>('/local_knowledge_detail/task/metric/delete_task', {
    data: { metric_task_id: metricTaskId }
  })
}

// ============ 问题导入 API ============

/**
 * 问题导入预览数据项
 */
export interface QuestionImportPreviewItem {
  row_index: number
  question_type: string
  question_content: string
  chunk_ids: string[]
  is_valid: boolean
  error_msg: string | null
}

/**
 * 上传问题导入文件并获取预览
 */
export async function uploadQuestionImport(
  file: File,
  setId: string,
  setType: string
): Promise<ApiResponse<{
  import_token: string
  preview: QuestionImportPreviewItem[]
  total_count: number
  valid_count: number
  invalid_count: number
}>> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('set_id', setId)
  formData.append('set_type', setType)

  return legacyPost('/api/local_knowledge_detail/question/import/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 确认导入问题
 */
export async function confirmQuestionImport(
  importToken: string,
  setId: string,
  setType: string
): Promise<ApiResponse<{
  inserted_count: number
  failed_count: number
}>> {
  return legacyPost('/api/local_knowledge_detail/question/import/confirm', {
    import_token: importToken,
    set_id: setId,
    set_type: setType
  })
}

/**
 * 下载问题导入模板
 */
export function downloadQuestionTemplate(): void {
  // 创建一个临时链接来下载文件
  const link = document.createElement('a')
  link.href = '/api/local_knowledge_detail/question/import/template'
  link.download = 'question_import_template.xlsx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
