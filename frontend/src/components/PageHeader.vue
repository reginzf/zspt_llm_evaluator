<template>
  <div class="page-header-nav">
    <div class="header-left">
      <el-button 
        text 
        :icon="ArrowLeft" 
        @click="goBack"
        class="back-btn"
      >
        返回
      </el-button>
      <el-divider direction="vertical" />
      <el-breadcrumb :separator="'>'">
        <el-breadcrumb-item :to="{ path: '/' }">
          <el-icon><HomeFilled /></el-icon>
          首页
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="title">{{ title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right" v-if="$slots.extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, HomeFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  title?: string
}>()

const router = useRouter()

const goBack = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.page-header-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .back-btn {
    padding: 8px 15px;
    
    &:hover {
      color: #409eff;
    }
  }

  :deep(.el-breadcrumb) {
    font-size: 14px;
    
    .el-breadcrumb__item {
      display: flex;
      align-items: center;
      
      .el-icon {
        margin-right: 4px;
        font-size: 16px;
      }
    }
  }
}
</style>
