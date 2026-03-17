<template>
  <div class="page-container">
    <PageHeader title="评估报告列表">
      <template #extra>
        <el-button type="primary" @click="loadData">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </template>
    </PageHeader>
    <el-card v-loading="loading">

      <!-- 目录树结构 -->
      <div v-if="Object.keys(directoryStructure).length > 0" class="directory-tree">
        <div
          v-for="(files, directory) in directoryStructure"
          :key="directory"
          class="directory-item"
        >
          <div class="directory-header" @click="toggleDirectory(directory)">
            <el-icon class="toggle-icon">
              <ArrowRight v-if="!expandedDirs[directory]" />
              <ArrowDown v-else />
            </el-icon>
            <el-icon class="folder-icon"><Folder /></el-icon>
            <span class="directory-name">{{ directory }}</span>
            <el-tag size="small" class="file-count">{{ files.length }} 个文件</el-tag>
          </div>
          <el-collapse-transition>
            <div v-show="expandedDirs[directory]" class="file-list">
              <div
                v-for="file in files"
                :key="file"
                class="file-item"
              >
                <el-icon class="file-icon"><Document /></el-icon>
                <a
                  class="file-name"
                  :title="file"
                  @click.prevent="viewReport(directory, file)"
                >
                  {{ file }}
                </a>
                <div class="file-actions">
                  <el-button
                    link
                    type="primary"
                    size="small"
                    @click="viewReport(directory, file)"
                  >
                    查看
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-transition>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无报告文件" />

    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Folder, Document, ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { getReportList } from '@/api/report'
import type { Report } from '@/api/report'

const loading = ref(false)
const directoryStructure = ref<Record<string, string[]>>({})
const expandedDirs = reactive<Record<string, boolean>>({})
const reportsData = ref<Report[]>([])

async function loadData() {
  loading.value = true
  try {
    const response = await getReportList()
    if (response.success) {
      directoryStructure.value = response.directory_structure || {}
      reportsData.value = response.data || []
      // 默认展开第一个目录
      const dirs = Object.keys(directoryStructure.value)
      if (dirs.length > 0 && dirs[0]) {
        expandedDirs[dirs[0]] = true
      }
    } else {
      ElMessage.error(response.message || '获取报告列表失败')
    }
  } catch (error) {
    console.error('获取报告列表失败:', error)
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

function toggleDirectory(directory: string) {
  expandedDirs[directory] = !expandedDirs[directory]
}

function viewReport(directory: string, file: string) {
  // 找到对应的报告对象，使用 object_name 查看
  const report = reportsData.value.find(r => r.directory === directory && r.name === file)
  if (report && report.object_name) {
    // 使用完整的 MinIO 对象名称
    window.open('/api/report/' + encodeURIComponent(report.object_name), '_blank')
  } else {
    // 回退到相对路径
    const path = directory === '根目录' ? file : `${directory}/${file}`
    window.open('/api/report/' + encodeURIComponent(path), '_blank')
  }
}

onMounted(() => loadData())
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.directory-tree {
  .directory-item {
    margin-bottom: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    overflow: hidden;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .directory-header {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background-color: #f5f7fa;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: #e4e7ed;
    }

    .toggle-icon {
      font-size: 16px;
      color: #909399;
      margin-right: 8px;
      transition: transform 0.2s;
    }

    .folder-icon {
      font-size: 20px;
      color: #e6a23c;
      margin-right: 8px;
    }

    .directory-name {
      flex: 1;
      font-size: 15px;
      font-weight: 500;
      color: #303133;
    }

    .file-count {
      margin-left: auto;
    }
  }

  .file-list {
    padding: 8px 0;
    background-color: #fff;
  }

  .file-item {
    display: flex;
    align-items: center;
    padding: 10px 16px 10px 48px;
    border-bottom: 1px solid #f0f2f5;
    transition: background-color 0.2s;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      background-color: #f5f7fa;
    }

    .file-icon {
      font-size: 18px;
      color: #409eff;
      margin-right: 10px;
    }

    .file-name {
      flex: 1;
      font-size: 14px;
      color: #409eff;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      cursor: pointer;
      text-decoration: none;

      &:hover {
        color: #66b1ff;
        text-decoration: underline;
      }
    }

    .file-actions {
      margin-left: auto;
    }
  }
}
</style>
