# Vue Migration Debugger - Memory MCP 速查表

## 🚀 快速开始

```typescript
// 1. 搜索已知问题（处理用户问题前必须执行！）
const results = await search_nodes({ query: "页面名 错误关键词" })

// 2. 如果找到，获取详细信息
const details = await open_nodes({ names: [results.entities[0].name] })

// 3. 应用解决方案
// ... 直接修复代码 ...

// 4. 存储新问题（如果是新问题）
await create_entities({ entities: [...] })
await create_relations({ relations: [...] })
```

## 📚 预置知识查询

### 常见问题直接查

```typescript
// 🔴 405 Method Not Allowed
await search_nodes({ query: "405 DELETE" })
// → vue_issue_知识库详情_405_Method_Not_Allowed

// 🔴 KeyError: 'xxx'
await search_nodes({ query: "KeyError" })
// → vue_issue_环境列表编辑_KeyError_api_key

// 🔴 列表显示 No Data
await search_nodes({ query: "No Data" })
// → vue_issue_知识库列表_No_Data

// 🔴 CORS 问题
await search_nodes({ query: "CORS" })

// 🔴 字段映射问题
await search_nodes({ query: "字段映射 camelCase" })
```

## 📝 完整存储模板

```typescript
// ========== Step 1: 创建问题实体 ==========
await create_entities({
  entities: [{
    name: "vue_issue_{页面}_{错误简述}",
    entityType: "vue_issue",
    observations: [
      "页面: {页面名称}",
      "路由: {Vue路由}",
      "操作: {用户操作}",
      "现象: {问题描述}",
      "错误信息: {完整错误}",
      "根本原因: {原因分析}",
      "修复文件: {修改的文件路径}",
      "修复代码:\n```typescript\n{代码片段}\n```",
      "验证结果: {测试是否通过}"
    ]
  }]
})

// ========== Step 2: 创建组件/API实体（如不存在）==========
await create_entities({
  entities: [
    { 
      name: "vue_{组件名}", 
      entityType: "vue_component", 
      observations: ["路径: frontend/src/views/xxx.vue"] 
    },
    { 
      name: "api_{路由}", 
      entityType: "api_endpoint", 
      observations: ["后端路由: xxx.py"] 
    },
    { 
      name: "error_{错误类型}", 
      entityType: "error_pattern", 
      observations: ["通用解决方案"] 
    }
  ]
})

// ========== Step 3: 建立关系 ==========
await create_relations({
  relations: [
    { from: "vue_issue_xxx", to: "vue_{组件}", relationType: "occurs_in" },
    { from: "vue_issue_xxx", to: "api_{路由}", relationType: "related_to" },
    { from: "vue_issue_xxx", to: "error_{错误类型}", relationType: "causes" }
  ]
})
```

## 🔍 高级查询技巧

### 多关键词搜索
```typescript
// 使用空格分隔多个关键词
await search_nodes({ query: "环境列表 编辑 500 KeyError" })

// 使用错误类型搜索
await search_nodes({ query: "error_405" })

// 使用组件名搜索
await search_nodes({ query: "vue_component_KnowledgeDetail" })
```

### 浏览所有知识
```typescript
// 查看所有 Vue 问题
await search_nodes({ query: "vue_issue" })

// 查看所有错误模式
await search_nodes({ query: "error_pattern" })

// 查看所有组件
await search_nodes({ query: "vue_component" })
```

### 关系追溯
```typescript
// 获取问题详情后，查看相关实体
const issue = await open_nodes({ names: ["vue_issue_xxx"] })

// 如果问题关联了组件，查看组件的其他问题
await search_nodes({ query: issue.relatedComponentName })
```

## 💡 实战示例

### 示例 1：处理"QA列表编辑报错"

```typescript
// 1. 先搜索 Memory
const results = await search_nodes({ query: "QA 列表 编辑 报错" })

// 2. 未命中，执行调试...
// ... 定位问题，修复代码 ...

// 3. 存储新问题
await create_entities({
  entities: [{
    name: "vue_issue_QA列表编辑_字段缺失",
    entityType: "vue_issue",
    observations: [
      "页面: QA分组列表 (QAGroupList.vue)",
      "路由: /qa",
      "操作: 点击编辑按钮",
      "现象: 弹窗打开但缺少 description 字段",
      "根本原因: 编辑表单未包含 description 字段",
      "修复文件: frontend/src/views/qa/QAGroupEditModal.vue",
      "修复代码:\n```vue\n<el-form-item label=\"描述\">\n  <el-input v-model=\"form.description\" />\n</el-form-item>\n```",
      "验证结果: ✅ 编辑功能正常"
    ]
  }]
})

await create_relations({
  relations: [
    { from: "vue_issue_QA列表编辑_字段缺失", to: "vue_QAGroupList", relationType: "occurs_in" }
  ]
})
```

### 示例 2：复用已有方案

```typescript
// 用户: "知识库删除文件报 405 错误"

// 1. 搜索
const results = await search_nodes({ query: "405 删除" })

// 2. 命中！
const issue = await open_nodes({ names: [results.entities[0].name] })
// issue.observations 包含:
// - 原因: 前端使用 DELETE，后端只支持 POST
// - 修复: 使用 legacyPost 替代 request.delete

// 3. 直接应用方案，5分钟内解决！
```

## 📊 Token 节省估算

| 操作 | 无 Memory | 有 Memory | 节省 |
|-----|----------|----------|------|
| 查询 + 分析 | 3K tokens | 0 | 100% |
| 代码定位 | 2K tokens | 0 | 100% |
| 修复方案 | 3K tokens | 500 tokens | 83% |
| **总计** | **~8K** | **~500** | **~94%** |

## ⚠️ 重要提醒

1. **处理任何问题前，先搜索 Memory！**
2. **命名规范**: `vue_issue_{页面}_{错误简述}`
3. **丰富关键词**: observations 中包含多种搜索词
4. **存储完整代码**: 包含可直接使用的代码片段
5. **建立关系**: 关联组件、API、错误类型

## 🔗 相关文件

- 主 Skill: `SKILL.md`
- 完整 Memory 文档: https://modelcontextprotocol.io/docs/servers/memory
