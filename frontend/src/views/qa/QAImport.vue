<template>
  <div class="page-container">
    <el-card v-loading="importing">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><Back /></el-icon>
            </el-button>
            <h2>导入问答对</h2>
          </div>
        </div>
      </template>

      <el-alert
        title="导入说明"
        description="支持从 HuggingFace 数据集导入或上传本地文件。导入过程可能需要一些时间，请耐心等待。"
        type="info"
        show-icon
        :closable="false"
        class="import-info"
      />

      <!-- 导入方式选择 -->
      <el-tabs v-model="activeTab" class="import-tabs">
        <!-- HuggingFace 导入 -->
        <el-tab-pane label="HuggingFace 导入" name="huggingface">
          <el-form :model="hfForm" label-width="120px">
            <el-form-item label="数据集路径">
              <el-input
                v-model="hfForm.datasetPath"
                placeholder="如: squad, glue/sst2 或本地路径"
              />
            </el-form-item>
            <el-form-item label="批次大小">
              <el-input-number v-model="hfForm.batchSize" :min="100" :max="5000" :step="100" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleHuggingFaceImport" :loading="importing">
                开始导入
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 文件上传 -->
        <el-tab-pane label="文件上传" name="upload">
          <el-upload
            drag
            multiple
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 JSON, JSONL, CSV 格式文件
              </div>
            </template>
          </el-upload>
          <div class="upload-actions">
            <el-button type="primary" @click="handleUpload" :loading="importing" :disabled="fileList.length === 0">
              开始上传
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 导入进度 -->
      <div v-if="showProgress" class="progress-section">
        <h4>导入进度</h4>
        <el-progress :percentage="progress" :status="progressStatus" />
        <p class="progress-text">{{ progressText }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, UploadFilled } from '@element-plus/icons-vue'
import { importFromHuggingFace, uploadQAFile } from '@/api/qa'
import type { UploadFile } from 'element-plus'

const route = useRoute()
const router = useRouter()
const groupId = Number(route.params.id)

const activeTab = ref('huggingface')
const importing = ref(false)
const showProgress = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('准备导入...')
const fileList = ref<UploadFile[]>([])

// HuggingFace 表单
const hfForm = reactive({
  datasetPath: '',
  batchSize: 1000
})

function goBack() {
  router.back()
}

function handleFileChange(file: UploadFile) {
  fileList.value.push(file)
}

async function handleHuggingFaceImport() {
  if (!hfForm.datasetPath.trim()) {
    ElMessage.warning('请输入数据集路径')
    return
  }

  importing.value = true
  showProgress.value = true
  progress.value = 10
  progressText.value = '正在连接 HuggingFace...'

  try {
    const response = await importFromHuggingFace(groupId, hfForm.datasetPath, hfForm.batchSize)
    
    if (response.success) {
      progress.value = 100
      progressStatus.value = 'success'
      progressText.value = `导入完成！成功 ${response.data?.success} 条，失败 ${response.data?.failed} 条`
      ElMessage.success('导入完成')
    } else {
      progress.value = 0
      progressStatus.value = 'exception'
      progressText.value = response.message || '导入失败'
      ElMessage.error(response.message || '导入失败')
    }
  } catch (error) {
    progress.value = 0
    progressStatus.value = 'exception'
    progressText.value = '导入过程发生错误'
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

async function handleUpload() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  importing.value = true
  showProgress.value = true
  progress.value = 10
  progressText.value = '正在上传文件...'

  try {
    const files = fileList.value.map(f => f.raw).filter(Boolean) as File[]
    const fileListObj = { length: files.length, item: (i: number) => files[i] } as FileList
    
    for (let i = 0; i < files.length; i++) {
      Object.defineProperty(fileListObj, i, { value: files[i] })
    }

    const response = await uploadQAFile(groupId, fileListObj)
    
    if (response.success) {
      progress.value = 100
      progressStatus.value = 'success'
      progressText.value = `上传成功！共 ${response.data?.file_count} 个文件`
      ElMessage.success('上传成功')
      fileList.value = []
    } else {
      progress.value = 0
      progressStatus.value = 'exception'
      progressText.value = response.message || '上传失败'
      ElMessage.error(response.message || '上传失败')
    }
  } catch (error) {
    progress.value = 0
    progressStatus.value = 'exception'
    progressText.value = '上传过程发生错误'
    ElMessage.error('上传失败')
  } finally {
    importing.value = false
  }
}
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

  h2 {
    margin: 0;
    color: #303133;
  }
}

.import-info {
  margin-bottom: 20px;
}

.import-tabs {
  margin-top: 20px;
}

.upload-area {
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 200px;
  }
}

.upload-actions {
  margin-top: 20px;
  text-align: center;
}

.progress-section {
  margin-top: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;

  h4 {
    margin: 0 0 16px 0;
    color: #303133;
  }
}

.progress-text {
  margin-top: 10px;
  color: #606266;
  text-align: center;
}
</style>
