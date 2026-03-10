---
name: project-architect
description: 项目架构管理与代码清理专家。用于分析项目结构、识别冗余代码、管理代码质量、执行重构和清理任务。使用场景：(1) 项目结构分析和文档化，(2) 识别和删除冗余/未使用代码，(3) 代码重构规划，(4) 清理临时文件和缓存，(5) 管理 git 提交和标签。
---

# 项目架构管理

分析项目结构、识别冗余代码、执行安全清理。

## 📊 项目结构分析

### 标准 Flask + Vue3 项目结构

```
project/
├── frontend/              # Vue3 前端
│   ├── src/
│   │   ├── api/          # API 接口
│   │   ├── components/   # 组件
│   │   ├── composables/  # 组合式函数
│   │   ├── router/       # 路由
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── views/        # 页面视图
│   │   └── ...
│   └── vite.config.ts
├── src/                   # Python 后端
│   ├── flask_funcs/      # Flask 路由
│   ├── sql_funs/         # 数据库操作
│   ├── llm/              # LLM 相关
│   └── utils/            # 工具函数
├── configs/              # 配置文件
├── scripts/              # 脚本
└── tests/                # 测试
```

### 分析方法

```bash
# 1. 统计代码量
find src -name "*.py" | xargs wc -l
find frontend/src -name "*.vue" -o -name "*.ts" | xargs wc -l

# 2. 检查未使用文件
# 对比 git tracked vs 实际引用

# 3. 检查重复代码
git ls-files | grep -E "\.(py|vue|ts|js)$" | xargs -I {} sh -c 'md5sum "$@"' _ {}
```

## 🧹 冗余代码识别

### 检查清单

#### Python 后端

1. **未使用的导入**
   ```bash
   # 使用 vulture 检查
   vulture src/ --min-confidence 80
   ```

2. **未使用的函数/类**
   - 检查 `__pycache__` 外的 .pyc 文件
   - 查找孤立函数

3. **重复的路由定义**
   ```bash
   grep -r "@.*.route" src/flask_funcs/ --include="*.py"
   ```

#### Vue3 前端

1. **未使用的组件**
   - 检查 components/ 中被 import 的情况
   - 查找未引用的 .vue 文件

2. **未使用的 API 函数**
   - 检查 api/ 目录中实际被调用的函数

3. **冗余的样式文件**

### 清理策略

#### 安全删除检查流程

```
1. 查找目标文件
   ├── git grep "文件名"       # 检查引用
   ├── grep -r "import.*文件名" # 检查导入
   └── 检查运行时动态引用

2. 确认未使用
   ├── 没有静态引用
   ├── 没有动态导入
   └── 不是配置文件

3. 执行删除
   ├── 删除文件
   ├── 更新相关导入
   └── 记录变更

4. 验证
   ├── 启动应用测试
   ├── 检查关键功能
   └── git diff 确认
```

#### 常见冗余文件类型

1. **缓存文件**
   - `__pycache__/`
   - `*.pyc`
   - `.pytest_cache/`

2. **临时文件**
   - `*.tmp`
   - `*.log` (已归档的)
   - `test.pkl`

3. **旧版备份**
   - `*.bak`
   - `*_old.*`
   - `backup/`

4. **IDE/编辑器配置**（已.gitignore）
   - `.idea/`
   - `.vscode/`

## 📝 Git 管理

### 提交前检查清单

```bash
# 1. 查看当前状态
git status

# 2. 检查变更内容
git diff

# 3. 识别应该忽略的文件
# - IDE 配置 (.idea/, .vscode/)
# - 缓存文件 (__pycache__/)
# - 临时文件 (*.pyc, *.tmp)
# - 敏感信息 (密码, API key)
```

### 安全提交策略

#### 应该提交的文件

```
✅ 源代码文件 (.py, .vue, .ts)
✅ 配置文件 (非敏感)
✅ 文档文件 (.md)
✅ 静态资源 (图片, 字体)
✅ 测试文件
```

#### 不应该提交的文件

```
❌ IDE 配置 (.idea/, .vscode/)
❌ Python 缓存 (__pycache__/, *.pyc)
❌ 临时文件 (*.tmp, *.log)
❌ 数据文件 (*.pkl, qdrant_index.pkl)
❌ 环境配置 (.env, 含密码)
❌ 依赖目录 (node_modules/)
```

### 标签管理

```bash
# 创建标签
git tag -a "vue3-frontend-ready" -m "Vue3 前端调试完成"

# 推送标签
git push origin "vue3-frontend-ready"

# 查看标签
git tag -l
```

## 🔍 代码质量检查

### 运行测试

```bash
# Python 测试
python -m pytest tests/ -v

# 前端类型检查
cd frontend && npx vue-tsc --noEmit
```

### 验证关键功能

```bash
# 1. 启动后端
python app.py

# 2. 启动前端
cd frontend && npm run dev

# 3. 测试核心页面
# - 首页
# - 环境列表
# - 知识库
# - QA 管理
```

## 🛠️ 清理工作流程

### 标准清理流程

```
1. 备份当前状态
   └── git stash 或创建备份分支

2. 分析项目结构
   ├── 扫描所有文件
   ├── 识别文件类型
   └── 分类文件用途

3. 识别冗余代码
   ├── 查找未引用文件
   ├── 检查重复代码
   └── 识别临时文件

4. 执行清理
   ├── 删除确认冗余的文件
   ├── 更新 .gitignore
   └── 清理缓存

5. 验证
   ├── 运行测试
   ├── 启动应用
   └── 检查关键功能

6. 提交
   ├── git add 必要文件
   ├── git commit
   └── git tag
```

## ⚠️ 安全准则

1. **绝不删除**
   - 源代码文件（除非确认未使用）
   - 数据库迁移文件
   - 配置文件（非 IDE）
   - 测试文件

2. **谨慎处理**
   - 静态资源文件
   - 脚本文件（检查是否被调用）
   - 文档文件

3. **必须验证**
   - 每次删除后启动应用
   - 测试关键功能路径
   - 检查是否有运行时错误
