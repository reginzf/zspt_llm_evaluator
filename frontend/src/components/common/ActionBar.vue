<template>
  <div class="action-bar-wrapper">
    <div class="action-bar-left">
      <slot name="left">
        <el-button
          v-if="showAdd"
          type="primary"
          :icon="Plus"
          @click="handleAdd"
        >
          {{ addText }}
        </el-button>
        <el-button
          v-if="showDelete"
          type="danger"
          :icon="Delete"
          :disabled="!hasSelection"
          @click="handleDelete"
        >
          {{ deleteText }}
        </el-button>
        <slot name="extra-left" />
      </slot>
    </div>
    <div class="action-bar-right">
      <slot name="right">
        <el-button
          v-if="showRefresh"
          :icon="Refresh"
          circle
          @click="handleRefresh"
        />
        <slot name="extra-right" />
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, Delete, Refresh } from '@element-plus/icons-vue'

interface Props {
  showAdd?: boolean
  showDelete?: boolean
  showRefresh?: boolean
  addText?: string
  deleteText?: string
  hasSelection?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showAdd: true,
  showDelete: true,
  showRefresh: true,
  addText: '新增',
  deleteText: '删除',
  hasSelection: false,
})

const emit = defineEmits<{
  'add': []
  'delete': []
  'refresh': []
}>()

const handleAdd = () => {
  emit('add')
}

const handleDelete = () => {
  emit('delete')
}

const handleRefresh = () => {
  emit('refresh')
}
</script>

<style scoped lang="scss">
.action-bar-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .action-bar-left {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .action-bar-right {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}
</style>
