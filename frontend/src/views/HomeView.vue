<template>
  <div class="home-view">
    <div class="home-container">
      <!-- Hero 区域 -->
      <section class="hero-section">
        <h1 class="hero-title">问答系统召回质量评估报告服务</h1>
        <p class="hero-subtitle">
          基于向量、切片检索结果的质量分析系统，提供精确率、召回率、F1分数等指标分析，
          知识库支持切片精确匹配、向量匹配、llm模型匹配等，问答对支持语义、模糊、TF-IDF等计算方式，支持加权计算
        </p>
      </section>

      <!-- 核心功能模块 -->
      <section class="quick-access-section">
        <h2 class="section-title">核心功能模块</h2>
        <el-row :gutter="24" class="features-grid">
          <el-col 
            v-for="feature in featureModules" 
            :key="feature.path"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            class="feature-col"
          >
            <el-card class="feature-card" shadow="hover" @click="navigateTo(feature.path)">
              <div class="feature-icon">{{ feature.icon }}</div>
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-description">{{ feature.description }}</p>
              <div class="feature-actions">
                <el-button 
                  :type="feature.secondary ? 'info' : 'primary'" 
                  class="feature-btn"
                  @click.stop="navigateTo(feature.path)"
                >
                  {{ feature.buttonText }}
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </section>

      <!-- 快速访问 -->
      <section class="quick-access-section">
        <h2 class="section-title">快速访问</h2>
        <el-row :gutter="20" class="quick-access-grid">
          <el-col
            v-for="link in quickLinks"
            :key="link.path"
            :xs="12"
            :sm="12"
            :md="6"
            :lg="6"
            class="quick-col"
          >
            <div class="quick-link" @click="navigateTo(link.path)">
              <span class="quick-icon">{{ link.icon }}</span>
              <h4 class="quick-title">{{ link.title }}</h4>
              <p class="quick-description">{{ link.description }}</p>
            </div>
          </el-col>
        </el-row>
      </section>

      <!-- 页脚 -->
      <footer class="footer">
        <p>
          问答系统质量评估报告服务 | 服务状态：
          <el-tag :type="serviceStatus.type" effect="light" class="footer-status">
            {{ serviceStatus.text }}
          </el-tag>
          | 版本：2.1.0
        </p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 服务状态
const serviceStatus = ref({
  type: 'success' as 'success' | 'danger',
  text: '正常运行'
})

// 核心功能模块
const featureModules = [
  {
    icon: '🌐',
    title: '环境管理',
    description: '管理知识库环境信息，包括基础URL、认证密钥等配置。支持多环境切换，确保不同部署环境的数据隔离。',
    buttonText: '进入环境管理',
    path: '/environment'
  },
  {
    icon: '🏷️',
    title: 'Label-Studio环境',
    description: '管理Label-Studio标注平台的环境配置，包括API密钥、项目设置等。支持与本地知识库的集成和同步。',
    buttonText: '进入Label-Studio管理',
    path: '/label_studio_env'
  },
  {
    icon: '📚',
    title: '知识库管理',
    description: '创建和管理知识库，配置切片大小、重叠率等参数。支持知识库与本地文档的绑定关系管理。',
    buttonText: '进入知识库管理',
    path: '/local_knowledge'
  },
  {
    icon: '📊',
    title: '评估报告',
    description: '查看和分析召回质量评估报告，包括精确率、召回率、F1分数等指标。支持可视化展示和详细数据分析。',
    buttonText: '查看报告列表',
    path: '/report_list'
  },
  {
    icon: '💬',
    title: '问答对管理',
    description: '管理问答对数据，支持分组、标签、难度分级等功能。提供数据导入导出，用于模型评估和测试。',
    buttonText: '进入问答对管理',
    path: '/qa/groups'
  },
  {
    icon: '🤖',
    title: 'LLM模型管理',
    description: '配置和管理LLM模型，包括API密钥、模型参数等设置。支持模型评估和性能监控。',
    buttonText: '进入模型管理',
    path: '/llm/models'
  },
  {
    icon: '🎯',
    title: '标注任务管理',
    description: '创建和管理标注任务，跟踪任务进度和状态。支持自动标注和手动标注两种模式。',
    buttonText: '查看标注任务',
    path: '/annotation_tasks'
  },
  {
    icon: '📈',
    title: '指标分析仪表板',
    description: '可视化展示各项性能指标，包括检索质量、响应时间等。提供多维度分析和趋势预测。',
    buttonText: '进入仪表板',
    path: '/report_list',
    secondary: true
  }
]

// 快速访问链接
const quickLinks = [
  {
    icon: '📄',
    title: '查看最新报告',
    description: '浏览最近生成的评估报告',
    path: '/report_list'
  },
  {
    icon: '➕',
    title: '创建问答对组',
    description: '新建问答对分组用于测试',
    path: '/qa/groups'
  },
  {
    icon: '⚙️',
    title: '配置环境',
    description: '添加或修改环境配置',
    path: '/environment'
  },
  {
    icon: '🔗',
    title: '连接Label-Studio',
    description: '配置标注平台连接',
    path: '/label_studio_env'
  }
]

// 导航方法
const navigateTo = (path: string) => {
  router.push(path)
}

// 检查服务状态（模拟）
const checkServiceStatus = () => {
  // 这里可以添加实际的服务状态检查 API 调用
  // 例如: await fetch('/api/health')
  const isHealthy = true
  if (isHealthy) {
    serviceStatus.value = { type: 'success', text: '正常运行' }
  } else {
    serviceStatus.value = { type: 'danger', text: '服务异常' }
  }
}

onMounted(() => {
  checkServiceStatus()
})
</script>

<style scoped lang="scss">
.home-view {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 40px;
}

.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

// Hero 区域
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  border-radius: 16px;
  margin-bottom: 40px;
  text-align: center;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.2;
  margin-top: 0;
}

.hero-subtitle {
  font-size: 1.3rem;
  opacity: 0.9;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.6;
}

// 区域标题
.quick-access-section {
  margin-bottom: 50px;
}

.section-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e4e7ed;
}

// 功能模块卡片
.features-grid {
  margin-bottom: 20px;
}

.feature-col {
  margin-bottom: 24px;
}

.feature-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;

  &:hover {
    transform: translateY(-8px);
    border-color: #409eff;
  }

  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 30px;
  }
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 20px;
  display: inline-block;
}

.feature-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  line-height: 1.3;
  margin-top: 0;
}

.feature-description {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 25px;
  flex-grow: 1;
}

.feature-actions {
  margin-top: auto;
}

.feature-btn {
  width: 100%;
}

// 快速访问
.quick-access-grid {
  margin-bottom: 20px;
}

.quick-col {
  margin-bottom: 20px;
}

.quick-link {
  background: white;
  border-radius: 10px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  height: 100%;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
    border-color: #409eff;
  }
}

.quick-icon {
  font-size: 2.2rem;
  margin-bottom: 15px;
  display: block;
}

.quick-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
  margin-top: 0;
}

.quick-description {
  font-size: 0.9rem;
  color: #606266;
  line-height: 1.5;
  margin: 0;
}

// 页脚
.footer {
  text-align: center;
  padding: 30px;
  color: #606266;
  font-size: 0.95rem;
  border-top: 1px solid #e4e7ed;
  margin-top: 50px;

  p {
    margin: 0;
  }
}

.footer-status {
  margin-left: 5px;
  margin-right: 5px;
}

// 响应式设计
@media (max-width: 768px) {
  .hero-section {
    padding: 40px 20px;
  }

  .hero-title {
    font-size: 2.2rem;
  }

  .hero-subtitle {
    font-size: 1.1rem;
  }

  .section-title {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 15px;
  }

  .hero-section {
    padding: 30px 15px;
  }

  .hero-title {
    font-size: 1.8rem;
  }

  .feature-card :deep(.el-card__body) {
    padding: 20px;
  }

  .quick-link {
    padding: 20px;
  }
}
</style>
