---
name: qdrant-memory
description: 使用 Qdrant 语义搜索作为项目知识库。当用户询问项目代码相关问题、查找特定功能实现、询问 API 用法、或需要了解项目结构时，使用 qdrant_search.py 进行语义搜索获取相关代码片段。使用场景：(1) 用户询问 "xxx 功能在哪里实现"，(2) 用户询问 "如何使用 xxx API"，(3) 用户需要查找特定代码片段，(4) 用户询问项目架构相关问题。
---

# Qdrant 语义搜索 Memory

使用本地 Qdrant 语义搜索引擎作为项目知识库，通过自然语言搜索项目代码。

## 🔍 何时使用

当用户询问以下类型问题时，使用 Qdrant 搜索：

1. **功能定位**
   - "环境列表的 API 在哪里？"
   - "Flask 蓝图是怎么注册的？"
   - "Vue 路由配置在哪里？"

2. **代码查找**
   - "数据库连接代码在哪里？"
   - "Label Studio 登录逻辑在哪？"
   - "知识库 CRUD 操作在哪？"

3. **问题排查**
   - "KeyError 怎么处理？"
   - "405 Method Not Allowed 处理"
   - "CORS 配置在哪里？"

4. **架构理解**
   - "项目结构是怎样的？"
   - "有哪些主要模块？"

## 🚀 使用方法

### 直接执行搜索命令

```bash
# 基本搜索（在项目根目录执行）
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "搜索关键词"

# 交互模式（持续对话）
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py interactive
```

### 执行示例

**场景 1：用户问 "Flask 蓝图怎么注册的？"**

```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "Flask 蓝图注册"
```

**场景 2：用户问 "环境列表 API 在哪？"**

```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "环境列表 API"
```

**场景 3：用户问 "数据库连接代码在哪？"**

```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "PostgreSQL 数据库连接"
```

## 📋 工作流程

### 标准流程

```
用户提问
    │
    ▼
判断是否需要代码搜索
    │
    ├─ 是 → 执行 .agents/skills/qdrant-memory/scripts/qdrant_search.py search "关键词"
    │         │
    │         ▼
    │      分析搜索结果
    │         │
    │         ▼
    │      向用户展示相关代码片段
    │
    └─ 否 → 直接回答
```

### 执行步骤

1. **理解用户问题** - 提取关键词
2. **执行搜索** - 运行 qdrant_search.py
3. **分析结果** - 查看返回的代码片段
4. **回答用户** - 结合搜索结果给出答案

## 💡 搜索关键词建议

### 关键词提取规则

| 用户问题 | 提取关键词 |
|---------|-----------|
| "Flask 蓝图怎么注册？" | "Flask 蓝图注册" |
| "环境列表 API 在哪？" | "环境列表 API" 或 "/api/environment" |
| "数据库连接代码" | "PostgreSQL 连接" 或 "数据库连接池" |
| "KeyError 怎么处理？" | "KeyError 错误处理" |
| "Vue 路由配置" | "Vue Router 配置" |
| "Label Studio 登录" | "Label Studio 登录" |
| "知识库上传文件" | "知识库 文件上传" |
| "CORS 配置" | "CORS 跨域配置" |

### 多语言支持

可以使用中文或英文搜索：
- 中文：".venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "路由配置""
- 英文：".venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "route config""

## 📝 结果解读

搜索结果格式：

```
1. [#########------] 0.623
   文件: src\flask_funcs\static_routes.py
   内容: from flask import Blueprint...
```

- **分数** (0.623)：相似度得分，越高越相关
- **文件**：代码所在文件路径
- **内容**：代码片段预览

## ⚠️ 注意事项

1. **索引已存在** - 项目代码已索引到 `qdrant_index.pkl`，可直接搜索
2. **执行路径** - 必须在项目根目录 `D:\pyworkplace\git_place\ai-ken` 执行
3. **Python 环境** - 使用 `.venv\Scripts\python` 运行
4. **脚本位置** - 脚本已移至 `.agents/skills/qdrant-memory/scripts/`
4. **搜索结果为空** - 可能关键词不匹配，尝试同义词或英文关键词
5. **代码变更** - 如项目代码大幅变更，需重新索引：`.venv\Scripts\python qdrant_search.py index`

## 🔧 故障排除

### 搜索无结果

```bash
# 尝试不同关键词
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "blueprint"  # 英文
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "蓝图"       # 中文
```

### 索引文件损坏

```bash
# 删除旧索引，重新创建
Remove-Item qdrant_index.pkl
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py index
```

## 📚 参考示例

### 示例 1：查找 API 路由

用户问："环境管理的 API 路由在哪？"

执行：
```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "environment API 路由"
```

预期结果：返回 `src/flask_funcs/environment.py` 相关代码

### 示例 2：查找 Vue 组件

用户问："环境列表页面在哪？"

执行：
```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "EnvironmentList Vue"
```

预期结果：返回 `frontend/src/views/environment/EnvironmentList.vue`

### 示例 3：查找错误处理

用户问："405 错误怎么处理？"

执行：
```bash
.venv\Scripts\python .agents/skills/qdrant-memory/scripts/qdrant_search.py search "405 Method Not Allowed"
```

预期结果：返回相关错误处理代码
