<template>
  <div class="not-found">
    <el-empty description="页面不存在">
      <template #image>
        <div class="error-code">404</div>
      </template>
      <template #description>
        <div class="error-message">
          <h2>页面不存在</h2>
          <p>您访问的页面可能已经删除或地址错误</p>
        </div>
      </template>
      <el-button type="primary" @click="goHome">
        <el-icon><HomeFilled /></el-icon>
        返回首页
      </el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: #909399;
  line-height: 1;
  margin-bottom: 20px;
}

.error-message {
  text-align: center;
  margin-bottom: 20px;

  h2 {
    font-size: 24px;
    color: #303133;
    margin: 0 0 10px 0;
  }

  p {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }
}
</style>
