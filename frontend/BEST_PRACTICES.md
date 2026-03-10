# Vue 前端最佳实践指南

## 已完成改进

### 1. 类型定义集中管理

**文件**: `src/types/index.ts`

- 统一存放所有共享类型
- 避免循环依赖
- 提供常用的基础类型

```typescript
import type { ApiResponse, PaginationData } from '@/types'
```

### 2. Composables - 逻辑复用

**目录**: `src/composables/`

| Composable | 用途 | 示例 |
|------------|------|------|
| `usePagination` | 分页状态管理 | `const { page, limit, total, updatePagination } = usePagination<T>()` |
| `useLoading` | 加载状态管理 | `const { loading, withLoading } = useLoading()` |
| `useDialog` | 对话框管理 | `const dialog = useDialog({ defaultForm, onSubmit })` |

**使用示例**:
```typescript
import { useLoading, useDialog } from '@/composables'

const { loading, submitting, withLoading } = useLoading()

const dialog = useDialog({
  defaultForm: { name: '' },
  onSubmit: async (form, isEdit) => {
    // 提交逻辑
  }
})
```

### 3. 工具函数集中管理

**文件**: `src/utils/formatters.ts`

提供统一的格式化函数:
- `formatDateTime()` - 日期时间格式化
- `formatFileSize()` - 文件大小格式化
- `formatTags()` - 标签格式化
- `valueToLabel()` - 值转标签
- 常用选项数组 (TEST_TYPE_OPTIONS, LANGUAGE_OPTIONS 等)

### 4. Store 设计原则

**原则**: Store 专注于数据管理，不处理 UI 状态

```typescript
// ✅ Good - Store 只管理数据
export const useQAStore = defineStore('qa', () => {
  const groups = ref<QAGroup[]>([])
  
  async function fetchGroups(params?: QAGroupQueryParams) {
    const response = await getQAGroups(params)
    if (response.success) {
      groups.value = response.data.rows
      return response.data
    }
    return null
  }
  
  return { groups, fetchGroups }
})

// ❌ Bad - Store 不应该管理 loading 状态
const loading = ref(false) // 移到组件中使用 useLoading
```

### 5. 组件结构最佳实践

```vue
<script setup lang="ts">
// 1. 导入（按类型分组）
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

// 组件
import Pagination from '@/components/common/Pagination.vue'

// Store & Composables
import { useQAStore } from '@/stores/qa'
import { useLoading, useDialog } from '@/composables'

// 工具函数
import { formatDateTime, TEST_TYPE_OPTIONS } from '@/utils/formatters'

// 类型
import type { QAGroup } from '@/api/qa'

// 2. 初始化
const router = useRouter()
const store = useQAStore()

// 3. 使用 Composables
const { loading, withLoading } = useLoading()
const dialog = useDialog({ /* ... */ })

// 4. 本地状态
const data = ref<QAGroup[]>([])
const pagination = reactive({ page: 1, limit: 20, total: 0 })

// 5. 方法
async function loadData() {
  await withLoading(async () => {
    const result = await store.fetchGroups()
    if (result) {
      data.value = result.rows
      pagination.total = result.total
    }
  })
}

// 6. 生命周期
onMounted(loadData)
</script>
```

### 6. API 模块设计

**原则**:
- 统一使用集中定义的类型
- 避免在 API 模块中定义 UI 相关的类型

```typescript
import { get, post } from './index'
import type { ApiResponse, PaginationData } from '@/types'

// 定义领域模型
export interface QAGroup {
  id: number
  name: string
  // ...
}

// API 函数
export async function getQAGroups(params?: PaginationParams): Promise<ApiResponse<PaginationData<QAGroup>>> {
  return get('/qa/groups', { params })
}
```

### 7. 可复用组件

**FilterBar 组件** - 统一的筛选栏
```vue
<FilterBar 
  v-model="filters" 
  :options="filterOptions" 
  @search="handleSearch" 
/>
```

## 迁移指南

### 将旧组件迁移到新最佳实践

1. **替换 format 函数**
   ```typescript
   // 旧
   import { formatDate } from '@/utils/format'
   
   // 新
   import { formatDateTime } from '@/utils/formatters'
   ```

2. **使用 useLoading**
   ```typescript
   // 旧
   const loading = ref(false)
   async function load() {
     loading.value = true
     try {
       await fetchData()
     } finally {
       loading.value = false
     }
   }
   
   // 新
   const { withLoading } = useLoading()
   async function load() {
     await withLoading(() => fetchData())
   }
   ```

3. **使用 useDialog**
   ```typescript
   // 旧
   const dialogVisible = ref(false)
   const isEdit = ref(false)
   const form = reactive({ name: '' })
   
   // 新
   const dialog = useDialog({
     defaultForm: { name: '' },
     onSubmit: async (form, isEdit) => { /* ... */ }
   })
   ```

## 目录结构

```
frontend/src/
├── api/              # API 接口
│   ├── index.ts      # axios 配置
│   ├── qa.ts         # QA 模块 API
│   └── ...
├── components/       # 组件
│   └── common/       # 通用组件
├── composables/      # 组合式函数
│   ├── usePagination.ts
│   ├── useLoading.ts
│   └── useDialog.ts
├── stores/           # Pinia Store
├── types/            # 全局类型定义
│   └── index.ts
├── utils/            # 工具函数
│   └── formatters.ts
└── views/            # 页面组件
```

## 注意事项

1. **不要在 Store 中管理 loading 状态** - 使用 `useLoading`
2. **不要在多个组件中重复格式化逻辑** - 使用 `formatters.ts`
3. **类型定义要集中** - 使用 `types/index.ts`
4. **对话框逻辑要复用** - 使用 `useDialog`
5. **分页逻辑要复用** - 使用 `usePagination`
