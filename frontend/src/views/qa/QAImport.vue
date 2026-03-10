<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><Back /></el-icon>
              <span class="back-text">返回详情</span>
            </el-button>
            <h2>导入问答对数据 - {{ groupName }}</h2>
          </div>
        </div>
      </template>

      <!-- 导入步骤 -->
      <div class="import-steps">
        <div class="step-line"></div>
        <div 
          v-for="step in steps" 
          :key="step.num"
          class="step"
          :class="{ 
            active: currentStep === step.num, 
            completed: currentStep > step.num 
          }"
        >
          <div class="step-circle">{{ step.num }}</div>
          <div class="step-label">{{ step.label }}</div>
        </div>
      </div>

      <!-- 步骤1: 选择文件 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>选择数据文件</h3>
        <p class="step-desc">请选择 HuggingFace 数据集文件夹或单个数据文件</p>

        <!-- 上传模式切换 -->
        <el-radio-group v-model="uploadMode" class="upload-mode">
          <el-radio-button label="folder">📁 选择文件夹</el-radio-button>
          <el-radio-button label="file">📄 选择文件</el-radio-button>
        </el-radio-group>

        <!-- 文件上传区域 -->
        <div
          class="file-upload-area"
          :class="{ dragover: isDragging }"
          @click="triggerFileSelect"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <el-icon class="upload-icon"><FolderOpened v-if="uploadMode === 'folder'" /><Document v-else /></el-icon>
          <div class="upload-text">
            {{ uploadMode === 'folder' ? '点击选择文件夹，或拖拽到此处' : '点击选择文件，或拖拽到此处' }}
          </div>
          <div class="upload-hint">支持 JSON, JSONL, CSV, Parquet 格式</div>
        </div>

        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInputRef"
          type="file"
          class="file-input"
          :webkitdirectory="uploadMode === 'folder'"
          :directory="uploadMode === 'folder'"
          :multiple="uploadMode === 'file'"
          @change="handleFileSelect"
        />

        <!-- 已选文件信息 -->
        <div v-if="selectedFiles.length > 0" class="file-selected">
          <div class="file-info">
            <div class="file-details">
              <div class="file-name">{{ displayFileName }}</div>
              <div class="file-meta">{{ formatFileSize(totalFileSize) }} · 共 {{ selectedFiles.length }} 个文件</div>
            </div>
            <el-button @click="clearFileSelection">重新选择</el-button>
          </div>
        </div>

        <el-alert
          v-if="selectedFiles.length > 0"
          title="请确保选择的是 HuggingFace 数据集文件夹或数据文件"
          type="warning"
          show-icon
          :closable="false"
          class="file-warning"
        />

        <div class="step-actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" @click="nextStep" :disabled="!uploadedFilePath">下一步</el-button>
        </div>
      </div>

      <!-- 步骤2: 预览数据 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>数据预览</h3>
        <p v-if="!previewData" class="step-desc">正在加载数据预览...</p>

        <el-alert
          v-if="previewError"
          :title="previewError"
          type="error"
          show-icon
          :closable="false"
        />

        <div v-if="previewData" class="preview-container">
          <el-table :data="previewData.preview_rows" border stripe max-height="400">
            <el-table-column
              v-for="col in previewData.columns"
              :key="col"
              :prop="col"
              :label="col"
              show-overflow-tooltip
            />
          </el-table>

          <div class="preview-info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总记录数">{{ previewData.total_records }} 条</el-descriptions-item>
              <el-descriptions-item label="显示记录">前 {{ previewData.preview_rows.length }} 条</el-descriptions-item>
              <el-descriptions-item label="字段数">{{ previewData.columns.length }} 个</el-descriptions-item>
              <el-descriptions-item label="字段列表">{{ previewData.columns.join(', ') }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="nextStep" :disabled="!previewData">下一步</el-button>
        </div>
      </div>

      <!-- 步骤3: 字段映射 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>字段映射配置</h3>
        <p class="step-desc">请将数据文件字段映射到问答对表的字段</p>

        <el-alert
          title="标有 * 的字段为必填项。同一字段不能映射到多个目标字段。"
          type="warning"
          show-icon
          :closable="false"
          class="mapping-warning"
        />

        <el-table :data="fieldMappings" border stripe class="mapping-table">
          <el-table-column prop="name" label="问答对表字段" width="180">
            <template #default="{ row }">
              <span :class="{ required: row.required }">{{ row.name }}</span>
              <el-tag v-if="row.required" type="danger" size="small" class="required-tag">*</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="数据文件字段" width="250">
            <template #default="{ row }">
              <el-select
                v-model="row.mapping"
                placeholder="请选择..."
                clearable
                @change="validateMapping"
                :class="{ 'is-error': row.hasError }"
              >
                <el-option label="-- 不导入 --" value="" />
                <el-option label="-- 自动生成 --" value="__auto__" />
                <el-option
                  v-for="col in previewData?.columns"
                  :key="col"
                  :label="col"
                  :value="col"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" />
        </el-table>

        <!-- 导入选项 -->
        <div class="import-options">
          <h4>导入选项</h4>
          <el-form :model="importOptions" label-width="120px">
            <el-form-item label="批次大小">
              <el-input-number v-model="importOptions.batch_size" :min="100" :max="10000" :step="100" />
              <span class="option-hint">每批次处理的记录数</span>
            </el-form-item>
            <el-form-item label="跳过行数">
              <el-input-number v-model="importOptions.skip_rows" :min="0" :step="1" />
              <span class="option-hint">从开始跳过的记录数</span>
            </el-form-item>
            <el-form-item label="未映射字段">
              <el-select v-model="importOptions.unmapped_fields">
                <el-option label="忽略" value="ignore" />
                <el-option label="存入 metadata" value="metadata" />
              </el-select>
              <span class="option-hint">未映射字段的处理方式</span>
            </el-form-item>
          </el-form>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="success" @click="startImport" :disabled="!isMappingValid">开始导入</el-button>
        </div>
      </div>

      <!-- 步骤4: 执行导入 -->
      <div v-if="currentStep === 4" class="step-content">
        <h3>执行导入</h3>

        <div class="progress-container">
          <el-progress
            :percentage="importProgress"
            :status="importStatus"
            :stroke-width="20"
            striped
            striped-flow
          />
          <div class="progress-info">
            <span>{{ importMessage }}</span>
            <span>{{ importProgress }}%</span>
          </div>
        </div>

        <!-- 导入结果 -->
        <div v-if="importResult" class="import-results">
          <el-result
            :icon="importResult.success ? 'success' : 'error'"
            :title="importResult.success ? '导入完成' : '导入失败'"
            :sub-title="importResult.message"
          />

          <el-descriptions v-if="importResult.stats" :column="3" border>
            <el-descriptions-item label="总记录数">{{ importResult.stats.total }}</el-descriptions-item>
            <el-descriptions-item label="成功">
              <span style="color: #67c23a">{{ importResult.stats.success }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="失败">
              <span style="color: #f56c6c">{{ importResult.stats.failed }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="跳过">{{ importResult.stats.skipped }}</el-descriptions-item>
            <el-descriptions-item label="错误数">{{ importResult.stats.error_count }}</el-descriptions-item>
            <el-descriptions-item label="耗时">{{ importResult.stats.duration?.toFixed(2) }}s</el-descriptions-item>
          </el-descriptions>

          <!-- 错误列表 -->
          <div v-if="importResult.stats?.errors?.length" class="error-list">
            <h4>错误详情</h4>
            <el-scrollbar max-height="200">
              <div v-for="(error, index) in importResult.stats.errors" :key="index" class="error-item">
                {{ error }}
              </div>
            </el-scrollbar>
          </div>
        </div>

        <div class="step-actions">
          <el-button v-if="!importResult" @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="finishImport" :disabled="!importResult">完成</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, FolderOpened, Document } from '@element-plus/icons-vue'
import { 
  uploadQAFile, 
  previewDataset, 
  executeImport, 
  getImportTaskStatus,
  cleanupImportFiles,
  getQAGroupDetail 
} from '@/api/qa'

const route = useRoute()
const router = useRouter()
const groupId = Number(route.params.id)

// 步骤定义
const steps = [
  { num: 1, label: '选择文件' },
  { num: 2, label: '预览数据' },
  { num: 3, label: '字段映射' },
  { num: 4, label: '执行导入' }
]

// 状态
const currentStep = ref(1)
const loading = ref(false)
const groupName = ref('')

// 步骤1: 文件选择
const uploadMode = ref<'folder' | 'file'>('folder')
const selectedFiles = ref<File[]>([])
const uploadedFilePath = ref('')
const uploadedFileInfo = ref<{
  minio_prefix?: string
  saved_files?: any[]
  is_folder?: boolean
  folder_name?: string
  file_count?: number
}>({})
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement>()

// 步骤2: 预览
interface PreviewData {
  file_path: string
  total_records: number
  preview_rows: any[]
  columns: string[]
  suggestions: Record<string, string>
}
const previewData = ref<PreviewData | null>(null)
const previewError = ref('')
const tempPath = ref<string | null>(null)

// 步骤3: 字段映射
interface FieldMapping {
  name: string
  required: boolean
  description: string
  mapping: string
  hasError?: boolean
}

const fieldMappings = ref<FieldMapping[]>([
  { name: 'id', required: false, description: '主键，唯一标识', mapping: '' },
  { name: 'question', required: true, description: '问题内容', mapping: '' },
  { name: 'answers', required: true, description: '答案内容', mapping: '' },
  { name: 'context', required: false, description: '上下文信息', mapping: '' },
  { name: 'question_type', required: false, description: '问题类型', mapping: '' },
  { name: 'source_dataset', required: false, description: '数据来源', mapping: '' },
  { name: 'hf_dataset_id', required: false, description: 'HuggingFace原始ID', mapping: '' },
  { name: 'language', required: false, description: '语言', mapping: '' },
  { name: 'difficulty_level', required: false, description: '难度等级', mapping: '' },
  { name: 'category', required: false, description: '分类标签', mapping: '' },
  { name: 'sub_category', required: false, description: '子分类', mapping: '' },
  { name: 'tags', required: false, description: '标签列表', mapping: '' },
  { name: 'fixed_metadata', required: false, description: '固定元数据', mapping: '' },
  { name: 'dynamic_metadata', required: false, description: '动态元数据', mapping: '' }
])

const importOptions = reactive({
  batch_size: 1000,
  skip_rows: 0,
  unmapped_fields: 'ignore'
})

// 步骤4: 导入
const importProgress = ref(0)
const importStatus = ref('')
const importMessage = ref('准备中...')
const importResult = ref<{
  success: boolean
  message: string
  stats?: {
    total: number
    success: number
    failed: number
    skipped: number
    duration: number
    error_count: number
    errors?: string[]
  }
} | null>(null)
const currentTaskId = ref('')
const progressInterval = ref<number | null>(null)

// 计算属性
const displayFileName = computed(() => {
  if (selectedFiles.value.length === 0) return ''
  if (selectedFiles.value.length === 1) return selectedFiles.value[0]?.name || ''
  if (uploadMode.value === 'folder') {
    const firstFile = selectedFiles.value[0]
    if (!firstFile) return `${selectedFiles.value.length} 个文件`
    const path = firstFile.webkitRelativePath || ''
    return path.split('/')[0] || `${selectedFiles.value.length} 个文件`
  }
  return `${selectedFiles.value.length} 个文件`
})

const totalFileSize = computed(() => {
  return selectedFiles.value.reduce((sum, f) => sum + f.size, 0)
})

const isMappingValid = computed(() => {
  // 检查必填字段
  const requiredFields = fieldMappings.value.filter(f => f.required)
  const allRequiredMapped = requiredFields.every(f => f.mapping && f.mapping !== '')
  
  // 检查重复映射
  const usedMappings = new Set<string>()
  let hasDuplicate = false
  for (const field of fieldMappings.value) {
    if (field.mapping && field.mapping !== '' && field.mapping !== '__auto__') {
      if (usedMappings.has(field.mapping)) {
        hasDuplicate = true
        break
      }
      usedMappings.add(field.mapping)
    }
  }
  
  return allRequiredMapped && !hasDuplicate
})

// 方法
function goBack() {
  cleanupFiles()
  router.back()
}

function triggerFileSelect() {
  fileInputRef.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFiles.value = Array.from(input.files)
    uploadFiles()
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const items = event.dataTransfer?.items
  if (items && items.length > 0) {
    const files: File[] = []
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item && item.kind === 'file') {
        const file = item.getAsFile()
        if (file) files.push(file)
      }
    }
    if (files.length > 0) {
      selectedFiles.value = files
      uploadFiles()
    }
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function uploadFiles() {
  if (selectedFiles.value.length === 0) return
  
  loading.value = true
  try {
    // 构建 FileList
    const fileList = { 
      length: selectedFiles.value.length, 
      item: (i: number) => selectedFiles.value[i] 
    } as FileList
    
    for (let i = 0; i < selectedFiles.value.length; i++) {
      Object.defineProperty(fileList, i, { value: selectedFiles.value[i] })
    }

    const response = await uploadQAFile(groupId, fileList)
    
    if (response.success) {
      const data = response.data || response as any
      uploadedFilePath.value = data.file_path
      uploadedFileInfo.value = {
        minio_prefix: data.minio_prefix,
        saved_files: data.saved_files,
        is_folder: data.is_folder,
        folder_name: data.folder_name,
        file_count: data.file_count
      }
      ElMessage.success('文件上传成功')
    } else {
      ElMessage.error(response.message || '文件上传失败')
      clearFileSelection()
    }
  } catch (error) {
    console.error('上传文件失败:', error)
    ElMessage.error('上传文件失败')
    clearFileSelection()
  } finally {
    loading.value = false
  }
}

function clearFileSelection() {
  selectedFiles.value = []
  uploadedFilePath.value = ''
  uploadedFileInfo.value = {}
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

async function loadPreview() {
  if (!uploadedFilePath.value) return
  
  loading.value = true
  previewError.value = ''
  
  try {
    const response = await previewDataset(
      groupId,
      uploadedFilePath.value,
      5,
      uploadedFileInfo.value.minio_prefix,
      uploadedFileInfo.value.saved_files
    )
    
    if (response.success) {
      const preview = response.data?.preview
      if (preview) {
        previewData.value = {
          file_path: preview.file_path,
          total_records: preview.total_records,
          preview_rows: Array.isArray(preview.preview_rows) ? preview.preview_rows : [],
          columns: preview.columns,
          suggestions: preview.suggestions
        }
      } else {
        previewData.value = null
      }
      tempPath.value = response.data?.temp_path || null
      
      // 应用智能映射建议
      if (previewData.value?.suggestions) {
        applyMappingSuggestions(previewData.value.suggestions)
      }
    } else {
      previewError.value = response.message || '预览数据失败'
    }
  } catch (error) {
    console.error('加载预览失败:', error)
    previewError.value = '加载预览失败'
  } finally {
    loading.value = false
  }
}

function applyMappingSuggestions(suggestions?: Record<string, string>) {
  if (!suggestions) return
  fieldMappings.value.forEach(field => {
    const suggestion = suggestions[field.name]
    if (suggestion) {
      field.mapping = suggestion
    }
  })
}

function validateMapping() {
  // 清除所有错误标记
  fieldMappings.value.forEach(f => f.hasError = false)
  
  // 检查重复映射
  const usedMappings = new Map<string, string>()
  fieldMappings.value.forEach(field => {
    if (field.mapping && field.mapping !== '' && field.mapping !== '__auto__') {
      if (usedMappings.has(field.mapping)) {
        // 标记重复
        field.hasError = true
        const otherField = fieldMappings.value.find(f => f.name === usedMappings.get(field.mapping!))
        if (otherField) otherField.hasError = true
      } else {
        usedMappings.set(field.mapping, field.name)
      }
    }
  })
}

async function startImport() {
  if (!isMappingValid.value) {
    ElMessage.warning('请完成字段映射配置')
    return
  }
  
  currentStep.value = 4
  importProgress.value = 0
  importStatus.value = ''
  importMessage.value = '准备中...'
  importResult.value = null
  
  // 构建映射配置
  const mapping: Record<string, string> = {}
  fieldMappings.value.forEach(field => {
    if (field.mapping && field.mapping !== '') {
      mapping[field.name] = field.mapping
    }
  })
  
  try {
    const response = await executeImport(
      groupId,
      uploadedFilePath.value,
      mapping,
      {
        batch_size: importOptions.batch_size,
        skip_rows: importOptions.skip_rows,
        unmapped_fields: importOptions.unmapped_fields
      },
      uploadedFileInfo.value.minio_prefix,
      uploadedFileInfo.value.saved_files,
      tempPath.value
    )
    
    if (response.success && response.data?.task_id) {
      currentTaskId.value = response.data.task_id
      startProgressPolling()
    } else {
      importStatus.value = 'exception'
      importMessage.value = response.message || '启动导入任务失败'
      importResult.value = {
        success: false,
        message: response.message || '启动导入任务失败'
      }
    }
  } catch (error) {
    console.error('启动导入任务失败:', error)
    importStatus.value = 'exception'
    importMessage.value = '启动导入任务失败'
    importResult.value = {
      success: false,
      message: '启动导入任务失败'
    }
  }
}

function startProgressPolling() {
  // 立即查询一次
  pollTaskStatus()
  
  // 每2秒轮询一次
  progressInterval.value = window.setInterval(pollTaskStatus, 2000)
}

async function pollTaskStatus() {
  if (!currentTaskId.value) return
  
  try {
    const response = await getImportTaskStatus(groupId, currentTaskId.value)
    
    if (response.success && response.data) {
      const task = response.data
      importProgress.value = task.progress || 0
      importMessage.value = task.message || '处理中...'
      
      if (task.status === 'completed') {
        stopProgressPolling()
        importStatus.value = 'success'
        importResult.value = {
          success: true,
          message: '导入完成',
          stats: task.stats
        }
        ElMessage.success('导入完成')
      } else if (task.status === 'failed') {
        stopProgressPolling()
        importStatus.value = 'exception'
        importResult.value = {
          success: false,
          message: task.message || '导入失败'
        }
        ElMessage.error(task.message || '导入失败')
      }
    }
  } catch (error) {
    console.error('查询任务状态失败:', error)
  }
}

function stopProgressPolling() {
  if (progressInterval.value) {
    clearInterval(progressInterval.value)
    progressInterval.value = null
  }
}

function finishImport() {
  stopProgressPolling()
  cleanupFiles()
  router.push(`/qa/groups/${groupId}`)
}

async function cleanupFiles() {
  if (uploadedFilePath.value) {
    try {
      await cleanupImportFiles(groupId, uploadedFilePath.value)
    } catch (error) {
      console.error('清理文件失败:', error)
    }
  }
}

function nextStep() {
  if (currentStep.value === 1) {
    if (!uploadedFilePath.value) {
      ElMessage.warning('请先选择文件')
      return
    }
    currentStep.value = 2
    loadPreview()
  } else if (currentStep.value === 2) {
    if (!previewData.value) {
      ElMessage.warning('请先预览数据')
      return
    }
    currentStep.value = 3
    validateMapping()
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// 加载分组信息
async function loadGroupInfo() {
  try {
    const response = await getQAGroupDetail(groupId)
    if (response.success) {
      groupName.value = response.data?.name || ''
    }
  } catch (error) {
    console.error('加载分组信息失败:', error)
  }
}

// 页面卸载时清理
onUnmounted(() => {
  stopProgressPolling()
  cleanupFiles()
})

// 初始化
loadGroupInfo()
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .back-text {
    margin-left: 4px;
  }

  h2 {
    margin: 0;
    color: #303133;
  }
}

// 步骤条
.import-steps {
  display: flex;
  justify-content: space-between;
  margin: 30px 0;
  position: relative;

  .step-line {
    position: absolute;
    top: 15px;
    left: 10%;
    right: 10%;
    height: 2px;
    background-color: #e4e7ed;
    z-index: 1;
  }

  .step {
    position: relative;
    z-index: 2;
    text-align: center;
    flex: 1;

    .step-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: #e4e7ed;
      color: #606266;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 8px;
      font-weight: bold;
      transition: all 0.3s ease;
    }

    .step-label {
      font-size: 14px;
      color: #606266;
    }

    &.active {
      .step-circle {
        background-color: #409eff;
        color: white;
      }
      .step-label {
        color: #409eff;
        font-weight: bold;
      }
    }

    &.completed {
      .step-circle {
        background-color: #67c23a;
        color: white;
      }
      .step-label {
        color: #67c23a;
      }
    }
  }
}

// 步骤内容
.step-content {
  min-height: 400px;

  h3 {
    margin: 0 0 10px 0;
    color: #303133;
  }

  .step-desc {
    color: #606266;
    margin-bottom: 20px;
  }
}

// 上传模式
.upload-mode {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

// 文件上传区域
.file-upload-area {
  border: 2px dashed #409eff;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;

  &:hover, &.dragover {
    background-color: #f5f7fa;
    border-color: #66b1ff;
  }

  .upload-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
  }

  .upload-text {
    font-size: 16px;
    color: #303133;
    margin-bottom: 8px;
  }

  .upload-hint {
    font-size: 14px;
    color: #909399;
  }
}

.file-input {
  display: none;
}

// 已选文件
.file-selected {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;

  .file-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .file-details {
    .file-name {
      font-weight: bold;
      color: #303133;
      margin-bottom: 4px;
    }

    .file-meta {
      color: #909399;
      font-size: 14px;
    }
  }
}

.file-warning {
  margin-bottom: 20px;
}

// 预览区域
.preview-container {
  margin-top: 20px;

  .preview-info {
    margin-top: 20px;
  }
}

// 字段映射
.mapping-warning {
  margin-bottom: 20px;
}

.mapping-table {
  margin-bottom: 20px;

  .required {
    font-weight: bold;
  }

  .required-tag {
    margin-left: 4px;
  }
}

.import-options {
  margin-top: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;

  h4 {
    margin: 0 0 16px 0;
    color: #303133;
  }

  .option-hint {
    margin-left: 10px;
    color: #909399;
    font-size: 14px;
  }
}

// 进度区域
.progress-container {
  margin: 30px 0;

  .progress-info {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    color: #606266;
  }
}

// 导入结果
.import-results {
  margin-top: 30px;

  .error-list {
    margin-top: 20px;

    h4 {
      margin-bottom: 10px;
      color: #f56c6c;
    }

    .error-item {
      padding: 8px;
      color: #f56c6c;
      font-size: 14px;
      border-bottom: 1px solid #fde2e2;

      &:last-child {
        border-bottom: none;
      }
    }
  }
}

// 步骤操作按钮
.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

// 错误标记
:deep(.el-select.is-error) {
  .el-input__wrapper {
    box-shadow: 0 0 0 1px #f56c6c inset;
  }
}
</style>
