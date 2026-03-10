---
name: vue-migration-debugger
description: 用于 Vue 3 迁移过程中调试新老代码差异。当用户在开发模式测试发现问题时，帮助定位并修复问题。使用场景：(1) 用户报告在 http://localhost:5173/ 某页面操作出现问题，(2) 需要对比新 Vue 代码和 src/flask_funcs/ 下老代码的差异，(3) 修复 Vue 代码使其与原有功能一致或解决具体问题，(4) 排查 API 路由、数据格式、CORS 配置等问题。使用 Qdrant 语义搜索查找项目代码。
---

# Vue 迁移调试助手

使用 Qdrant 语义搜索和代码对比进行 Vue 3 迁移调试。

## 🔍 使用 Qdrant 语义搜索

当需要查找代码或了解项目结构时，使用 `qdrant-memory` skill 进行语义搜索。

### 搜索命令

```bash
# 在项目根目录执行
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "关键词"

# 或使用简化版
python .agents/skills/qdrant-memory/scripts/search_code.py "关键词"
```

### 何时使用搜索

1. **定位代码** - 用户问 "xxx 功能在哪实现？"
2. **查找 API** - 用户问 "xxx API 在哪？"
3. **理解逻辑** - 用户问 "xxx 是怎么处理的？"
4. **排查问题** - 需要查找相关代码片段

### 搜索示例

```bash
# 搜索 Flask 蓝图
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "Flask 蓝图注册"

# 搜索 API 路由
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "environment API"

# 搜索数据库连接
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "PostgreSQL 连接"
```

---

## 工作流程

### 1. 接收问题报告
用户格式：`在 [页面/路由] 进行 [操作] 时，出现 [问题描述]`

示例：
- "在环境列表页面点击编辑按钮，弹窗没有显示密码字段"
- "知识库详情页面，删除文件按钮报错 405"
- "进入页面后列表显示 No Data，但 API 返回了数据"

### 1.1 代码搜索 🔍
如需查找相关代码，执行：

```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "关键词"
```

### 2. 定位代码文件

**页面路由 → 新 Vue 代码映射：**

| 路由 | Vue 文件 | 老模板/JS |
|------|---------|----------|
| / | views/Home.vue | templates/home.html, js/ (home相关) |
| /qa | views/qa/QAGroupList.vue | templates/qa_groups.html, js/qa_groups*.js |
| /qa/:id | views/qa/QAGroupDetail.vue | templates/qa_group_detail.html, js/qa_group_detail.js |
| /llm | views/llm/LLMModelList.vue | templates/llm_models.html |
| /llm/:id | views/llm/LLMModelDetail.vue | templates/llm_model_detail.html |
| /knowledge | views/knowledge/KnowledgeList.vue | templates/local_knowledge.html, js/local_knowledge.js |
| /knowledge/:id | views/knowledge/KnowledgeDetail.vue | templates/local_knowledge_detail*.html, js/local_knowledge_detail*.js |
| /environment | views/environment/EnvironmentList.vue | templates/environment.html, js/environment.js |
| /label-studio | views/environment/LabelStudioEnv.vue | templates/label_studio_env.html, js/label_studio_env.js |
| /tasks | views/tasks/AnnotationTaskList.vue | templates/annotation_tasks.html, js/annotation_tasks.js |
| /reports | views/reports/ReportList.vue | templates/report_list.html, js/report_list.js |

**后端 API 路由文件：**
- `/api/environment/*` → `src/flask_funcs/environment.py`
- `/api/qa/*` → `src/flask_funcs/qa_data*.py`
- `/api/llm/*` → `src/flask_funcs/llm_model_routes.py`
- `/local_knowledge/*` → `src/flask_funcs/local_knowledge.py`
- `/local_knowledge_detail/*` → `src/flask_funcs/local_knowledge_detail*.py`
- `/local_knowledge_doc/*` → `src/flask_funcs/local_knowledge_detail*.py`
- `/api/label_studio/*` → `src/flask_funcs/label_studio_env.py`
- `/api/tasks/*` → `src/flask_funcs/annotation_tasks.py`
- `/api/reports/*` → `src/flask_funcs/report_list.py`

### 3. 常见问题诊断清单

当用户报告问题时，按以下顺序检查：

#### 3.1 API 路由问题（404/405）

**检查点：**
1. 前端调用的 URL 是否与后端路由匹配
2. HTTP 方法是否一致（GET/POST/PUT/DELETE）
3. CORS 配置是否包含该路由

**常见错误：**
```typescript
// ❌ 错误：路径不匹配
await request.post('/local_knowledge_detail', { kno_id, kno_name })
// 后端路由：POST /api/local_knowledge_detail

// ❌ 错误：方法不匹配
await request.get('/local_knowledge/upload')
// 后端路由：POST /local_knowledge/upload

// ✅ 正确
await request.post('/api/local_knowledge_detail', { kno_id, kno_name })
```

#### 3.2 数据格式问题（500/数据不显示）

**后端期望 vs 前端发送：**
```typescript
// ❌ 错误：后端期望表单，前端发送 JSON
// 后端：request.form.get('knol_describe')
// 前端：{ "kno_describe": "xxx" }

// ✅ 修复后端支持 JSON
data = request.get_json()
knol_describe = data.get('kno_describe') or data.get('knol_describe')
```

**响应格式不匹配：**
```typescript
// ❌ 后端直接返回数组
return jsonify(file_list)

// ✅ 应该返回标准格式
return jsonify({
  'success': True,
  'data': file_list
})
```

#### 3.3 CORS 配置问题

**检查 `app.py` 的 CORS 配置：**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    },
    r"/local_knowledge/*": { ... },
    r"/local_knowledge_detail/*": { ... },
    # 确保每个路由前缀都有配置
})
```

**常见遗漏：**
- `/api/*` 路径
- `/local_knowledge/upload` 等具体路径
- PUT/DELETE 方法

#### 3.4 数据库字段索引错误

当后端返回 500 且涉及数据库查询时，检查字段索引：
```python
# ❌ 错误：字段顺序不匹配
'created_at': item[10].isoformat()  # 实际是第6列

# ✅ 正确（根据实际表结构）
# 表结构: id, kno_id, kno_name, kno_describe, kno_path, ls_status, 
#        created_at, updated_at, knowledge_domain, domain_description,
#        required_background, required_skills
'created_at': item[6].isoformat() if item[6] else None
```

### 4. 修复策略

**优先级：**
1. **路由匹配**（404/405）→ 修正 URL 或 CORS 配置
2. **数据格式**（500/数据不显示）→ 统一前后端格式
3. **功能缺失**（缺少字段/功能）→ 补充 Vue 代码
4. **样式问题**（UI 显示异常）→ 调整样式

**常见修复模式：**

```typescript
// 1. API 路径修正
// 错误
await legacyPost('/local_knowledge_detail', data)
// 正确（注意 /api 前缀）
await legacyPost('/api/local_knowledge_detail', data)

// 2. 使用正确的 HTTP 客户端
// apiClient: baseURL = '/api'
// legacyClient: baseURL = '/'
await legacyPost('/local_knowledge/upload', formData)  // 非 /api 路由

// 3. 响应格式兼容
const res = await getKnowledgeFiles(knoId, knoName)
// 检查 res.success 和 res.data 是否存在
if (res.success && res.data) {
  fileList.value = res.data
}
```

### 5. 验证修复

修复后检查：
- [ ] 页面功能与原版一致
- [ ] 没有引入新的 console 错误
- [ ] API 请求响应正常（200 + 正确数据格式）
- [ ] 数据正确显示在表格/表单中

---

## 代码查找快捷方式

```bash
# 查找 Vue 组件
grep -r "页面名" frontend/src/views/ --include="*.vue"

# 查找老模板
grep -r "功能关键词" src/flask_funcs/reports/templates/ --include="*.html"

# 查找 API 调用
grep -r "路由路径" frontend/src/ --include="*.ts" --include="*.vue"

# 查找后端路由
grep -r "@.*.route" src/flask_funcs/ --include="*.py"

# 语义搜索（推荐）
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "关键词"
```

---

## 自动化测试流程

### 测试执行步骤

#### Step 1: 访问页面
使用 Playwright MCP 工具访问页面：
```typescript
await browser_navigate({ url: 'http://localhost:5173/environment' })
await browser_wait_for({ time: 2 })  // 等待页面加载
const snapshot = await browser_snapshot()
```

#### Step 2: 检查页面基础状态
- [ ] 页面标题正确
- [ ] 无明显的加载错误（如 404/500 提示）
- [ ] 控制台无红色错误（使用 `browser_console_messages` 检查）

#### Step 3: 遍历页面组件
按照以下顺序测试每个组件：

| 组件类型 | 测试要点 |
|---------|---------|
| **搜索框** | 输入关键词 → 检查列表过滤 |
| **刷新按钮** | 点击 → 检查 API 调用 → 检查列表更新 |
| **新建按钮** | 点击 → 检查弹窗 → 检查表单字段 |
| **列表/表格** | 检查数据加载 → 检查分页 → 检查空状态 |
| **编辑按钮** | 点击 → 检查表单预填充数据 |
| **删除按钮** | 点击 → 检查确认弹窗 |
| **详情/查看** | 点击 → 检查跳转或弹窗 |

#### Step 4: 表单验证（弹窗/抽屉）
对于每个表单：
1. **字段完整性**：与后端 API 对比，确认所有字段都存在
2. **数据预填充**（编辑模式）：检查已有数据是否正确显示
3. **必填验证**：提交空表单，检查验证提示
4. **提交测试**：填写正确数据，点击提交

#### Step 5: 接口验证
使用 `browser_network_requests` 检查 API：
- [ ] 请求 URL 正确
- [ ] HTTP 方法正确（GET/POST/PUT/DELETE）
- [ ] 请求参数/Body 正确
- [ ] 响应状态 200
- [ ] 响应格式符合预期 `{ success: true, data: [...] }`

### 文件上传处理

当遇到文件上传按钮时：

```
提示用户：
"检测到文件上传功能。请手动选择文件进行测试。
文件路径：________"
```

用户确认后，使用 `browser_file_upload` 或让用户手动操作。

### 诊断与日志分析

#### 查看后端日志
当出现以下情况时读取 Flask 日志：
- API 返回 500 错误
- 数据没有正确保存
- 页面功能异常但前端无错误

```powershell
# 读取标准输出（最后 50 行）
Get-Content logs\app_stdout.log -Tail 50

# 读取错误日志（关键！）
Get-Content logs\app_stderr.log -Tail 50
```

#### 查看前端控制台
```typescript
const messages = await browser_console_messages({ level: 'error' })
```

#### 网络请求分析
```typescript
const requests = await browser_network_requests({ includeStatic: false })
```

### 测试报告模板

```markdown
## 页面测试报告：/environment

### 基础状态
- ✅ 页面加载成功
- ✅ 无控制台错误

### 组件测试
| 组件 | 状态 | 备注 |
|-----|------|------|
| 搜索框 | ✅ | 正常过滤 |
| 刷新按钮 | ✅ | API 返回 200 |
| 新建按钮 | ⚠️ | 弹窗正常，但缺少 password 字段 |
| 列表 | ✅ | 数据正确显示 |
| 编辑 | ❌ | 500 错误（见日志） |

### 发现问题
1. **编辑功能 500 错误**
   - 日志：`KeyError: 'api_key'` in environment.py:156
   - 原因：后端期望字段名 `api_key`，前端发送 `apiKey`

### 修复建议
```typescript
// frontend/src/api/environment.ts
export async function updateEnvironment(data) {
  return legacyPost('/environment/update', {
    ...data,
    api_key: data.apiKey  // 字段映射
  })
}
```

---

## Qdrant 搜索工具参考

### 常用搜索命令

```bash
# 在项目根目录执行

# 搜索 Vue 相关问题
.venv\Scripts\python qdrant_search.py search "Vue 路由配置"

# 搜索 Flask 后端代码
.venv\Scripts\python qdrant_search.py search "Flask 蓝图注册"

# 搜索数据库相关
.venv\Scripts\python qdrant_search.py search "PostgreSQL 连接"

# 搜索 API 路由
.venv\Scripts\python qdrant_search.py search "/api/environment"

# 搜索特定错误
.venv\Scripts\python qdrant_search.py search "KeyError 字段映射"

# 搜索 Label Studio 相关
.venv\Scripts\python qdrant_search.py search "Label Studio 登录"
```

### 索引更新

当项目代码变更后，重新索引：

```bash
# 重新索引所有代码
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py index
```

### 交互模式

持续对话式搜索：

```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py interactive
```

命令：
- 输入搜索词 - 执行搜索
- `/index` - 重新索引
- `/quit` 或 `/q` - 退出

---

## 注意事项

1. **端口检查**：开发模式下前端是 5173，后端是 5001，确保 `vite.config.ts` 代理配置正确
2. **CORS 问题**：如果看到 405/Network Error，检查 `app.py` 的 CORS 配置
3. **字段一致性**：特别注意 password、api_key 等敏感字段在新旧代码间的传递
4. **数据格式**：后端可能期望表单或 JSON，前端发送的格式必须匹配
5. **响应格式**：统一使用 `{ success: boolean, data: any, message?: string }` 格式
6. **数据库字段**：修改 API 时注意检查字段索引是否正确
7. **日志诊断**：优先读取 `logs\app_stderr.log` 的最后 50 行定位后端问题
8. **语义搜索优先**：处理问题前可先执行 Qdrant 搜索，快速定位相关代码
9. **命令行方式**：Qdrant 仅支持命令行调用，在项目根目录执行
