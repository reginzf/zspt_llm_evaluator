# AI-KEN 项目记忆文件

> 项目路径: `/root/.openclaw/workspace/zspt_llm_evaluator`  
> 生成时间: 2026-03-17  
> 项目描述: LLM 模型评估平台 - 用于评估 LLM 模型在 QA 数据集上的表现

---

## 1. 技术架构

### 1.1 技术栈
- **后端**: Python Flask + PostgreSQL + MinIO
- **前端**: Vue 3 + TypeScript + Vite + Element Plus
- **评估引擎**: 支持 DeepSeek 等 LLM API
- **集成**: Label Studio (数据标注平台)

### 1.2 目录结构
```
zspt_llm_evaluator/
├── app.py                    # Flask 应用入口
├── src/
│   ├── flask_funcs/          # Flask 蓝图/API路由
│   ├── sql_funs/             # 数据库 CRUD 操作
│   ├── llm/                  # LLM 评估引擎
│   ├── label_studio_api/     # Label Studio 集成
│   └── utils/                # 工具类
├── frontend/                 # Vue3 前端项目
│   ├── src/
│   │   ├── api/              # API 接口定义
│   │   ├── views/            # 页面组件
│   │   ├── router/           # 路由配置
│   │   ├── types/            # TypeScript 类型
│   │   └── components/       # 公共组件
│   └── vite.config.ts        # Vite 配置(含代理)
├── configs/                  # 配置文件
├── scripts/                  # 启动脚本
└── check_chunk/              # 召回质量检查模块
```

---

## 2. 后端路由信息 (Flask Blueprints)

### 2.1 蓝图注册 (app.py)
所有蓝图在 `app.py` 中注册，按以下顺序：

```python
app.register_blueprint(qa_data_group_bp)      # 问答对组管理
app.register_blueprint(qa_data_bp)            # 问答对管理
app.register_blueprint(llm_model_bp)          # LLM模型管理
app.register_blueprint(annotation_tasks_bp)   # 标注任务管理
app.register_blueprint(knowledge_base_bp)     # 知识库管理
app.register_blueprint(local_knowledge_bp)    # 本地知识库
app.register_blueprint(local_knowledge_detail_bp)      # 知识库详情
app.register_blueprint(label_studio_env_bp)            # Label Studio环境
app.register_blueprint(local_knowledge_question_bp)    # 知识库问题
app.register_blueprint(local_knowledge_label_studio_bp) # LS标注集成
app.register_blueprint(local_knowledge_detail_task_bp) # 知识库任务
app.register_blueprint(environment_bp)        # 环境管理
app.register_blueprint(report_list_bp)        # 报告列表
app.register_blueprint(static_bp)             # 静态文件
```

### 2.2 各模块路由详情

#### QA 数据管理 (`qa_data_group.py`, `qa_data.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/qa/groups` | GET | 查询问答对组列表(分页) |
| `/api/qa/groups` | POST | 创建问答对组 |
| `/api/qa/groups/<id>` | GET | 获取单个分组详情 |
| `/api/qa/groups/<id>` | PUT | 更新分组信息 |
| `/api/qa/groups/<id>` | DELETE | 删除分组 |
| `/api/qa/groups/<id>/activate` | POST | 激活/停用分组 |
| `/api/qa/groups/<id>/qa_count` | GET | 获取分组下的问答对数量 |
| `/api/qa/data` | GET | 查询问答对列表(分页) |
| `/api/qa/data` | POST | 创建问答对 |
| `/api/qa/data/<id>` | GET | 获取问答对详情 |
| `/api/qa/data/<id>` | PUT | 更新问答对 |
| `/api/qa/data/<id>` | DELETE | 删除问答对 |
| `/api/qa/data/batch` | POST | 批量创建问答对 |
| `/api/qa/data/import` | POST | 导入问答对(文件) |
| `/api/qa/data/<id>/metadata` | PATCH | 更新元数据 |

#### LLM 模型管理 (`llm_model_routes.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/llm/models` | GET | 获取模型列表 |
| `/llm/models` | POST | 创建模型配置 |
| `/llm/models/<name>` | GET | 获取模型详情 |
| `/llm/models/<name>` | PUT | 更新模型配置 |
| `/llm/models/<name>` | DELETE | 删除模型 |
| `/llm/models/<name>/test` | POST | 测试模型连接 |
| `/llm/evaluations` | POST | 创建评估任务 |
| `/llm/evaluations/<task_id>` | GET | 获取评估任务状态 |
| `/llm/evaluations/<task_id>/stop` | POST | 停止评估任务 |
| `/llm/evaluations/<task_id>/results` | GET | 获取评估结果 |
| `/llm/reports` | GET | 获取评估报告列表 |
| `/llm/reports/<report_id>` | GET | 获取报告详情 |
| `/llm/reports/<report_id>/export` | GET | 导出报告 |

#### 知识库管理 (`local_knowledge.py`, `local_knowledge_detail.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/local_knowledge/list` | GET | 获取知识库列表 |
| `/local_knowledge/create` | POST | 创建知识库 |
| `/local_knowledge/<kno_id>` | GET | 获取知识库详情 |
| `/local_knowledge/<kno_id>` | PUT | 更新知识库 |
| `/local_knowledge/<kno_id>` | DELETE | 删除知识库 |
| `/local_knowledge/<kno_id>/files` | GET | 获取知识库文件列表 |
| `/local_knowledge/upload` | POST | 上传文件到知识库 |
| `/local_knowledge_detail/<kno_id>/sync` | POST | 同步知识库到 Label Studio |
| `/local_knowledge_detail/question_sets` | GET | 获取问题集列表 |
| `/local_knowledge_detail/question_sets` | POST | 创建问题集 |
| `/local_knowledge_detail/questions` | GET | 获取问题列表 |
| `/local_knowledge_detail/questions` | POST | 创建问题 |
| `/local_knowledge_detail/task/create` | POST | 创建标注任务 |
| `/local_knowledge_detail/task/<task_id>` | GET | 获取任务详情 |
| `/local_knowledge_detail/label_studio/projects` | GET | 获取 LS 项目列表 |
| `/local_knowledge_detail/label_studio/sync` | POST | 同步到 LS |

#### 环境管理 (`environment.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/environment/list/` | GET | 获取环境列表 |
| `/environment/create/` | POST | 创建环境 |
| `/environment/update/` | PUT | 更新环境 |
| `/environment/delete/` | DELETE | 删除环境 |
| `/environment_detail/<id>` | GET | 获取环境详情 |
| `/environment_detail_list` | POST | 查询环境详情列表 |
| `/label_studio_env/list` | GET | 获取 LS 环境列表 |
| `/label_studio_env/create` | POST | 创建 LS 环境 |

#### 标注任务管理 (`annotation_tasks.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/annotation_tasks/list` | GET | 获取标注任务列表 |
| `/annotation_tasks/create` | POST | 创建标注任务 |
| `/annotation_tasks/<task_id>` | GET | 获取任务详情 |
| `/annotation_tasks/<task_id>/status` | PUT | 更新任务状态 |
| `/annotation_tasks/<task_id>/results` | GET | 获取标注结果 |

#### 报告管理 (`report_list.py`)
| 路由 | 方法 | 功能 |
|------|------|------|
| `/report_list/data` | GET | 获取报告数据列表 |
| `/report_list/<report_id>` | GET | 获取报告详情 |
| `/report_list/<report_id>/delete` | DELETE | 删除报告 |

### 2.3 CORS 配置
CORS 配置在 `app.py` 中，支持以下来源：
```python
_base_origins = [
    "http://localhost:5001",
    "http://127.0.0.1:5001", 
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://10.0.112.72:5173"  # 服务器IP
]
```

可通过环境变量扩展：
- `CORS_ORIGINS`: 逗号分隔的额外来源
- `CORS_ALLOW_ALL=true`: 允许所有来源(仅开发)

---

## 3. 前端路由信息 (Vue Router)

### 3.1 路由配置 (`frontend/src/router/index.ts`)

使用 `createWebHistory` 模式，基础路径由 `import.meta.env.BASE_URL` 决定。

| 路径 | 名称 | 组件 | 页面标题 |
|------|------|------|----------|
| `/` | home | HomeView.vue | 问答系统召回质量评估报告服务 |
| `/qa/groups` | qa-groups | QAGroupList.vue | 问答对组管理 |
| `/qa/groups/:id` | qa-group-detail | QAGroupDetail.vue | 问答对组详情 |
| `/qa/groups/:id/import` | qa-import | QAImport.vue | 导入问答对 |
| `/llm/models` | llm-models | ModelList.vue | LLM模型管理 |
| `/llm/models/:name` | llm-model-detail | ModelDetail.vue | 模型详情 |
| `/local_knowledge` | local-knowledge | KnowledgeList.vue | 知识库管理 |
| `/local_knowledge_detail/:kno_id/:kno_name` | knowledge-detail | KnowledgeDetail.vue | 知识库详情 |
| `/environment` | environment | EnvironmentList.vue | 环境管理 |
| `/environment_detail` | environment-detail | EnvironmentDetail.vue | 环境详情 |
| `/label_studio_env` | label-studio-env | LabelStudioEnv.vue | Label-Studio环境 |
| `/annotation_tasks` | annotation-tasks | TaskList.vue | 标注任务管理 |
| `/report_list` | report-list | ReportList.vue | 评估报告列表 |
| `/components-test` | components-test | ComponentsTestView.vue | 组件测试(隐藏) |
| `/:pathMatch(.*)*` | not-found | NotFoundView.vue | 页面不存在 |

### 3.2 路由守卫
- 全局前置守卫 `beforeEach`：根据 `meta.title` 设置页面标题，自动添加 `- AI-KEN` 后缀

---

## 4. 代理配置 (Vite Dev Server)

### 4.1 代理配置 (`frontend/vite.config.ts`)

开发服务器运行在 `5173` 端口，API 请求代理到后端 `5001` 端口。

```typescript
server: {
  port: 5173,
  host: '0.0.0.0',
  proxy: {
    '^/api': { target: backendUrl, changeOrigin: true, secure: false },
    '^/local_knowledge/': { target: backendUrl, ... },
    '^/local_knowledge_detail/sync': { target: backendUrl, ... },
    '^/local_knowledge_detail/question': { target: backendUrl, ... },
    '^/environment/list/': { target: backendUrl, ... },
    '^/environment/create/': { target: backendUrl, ... },
    '^/knowledge_base/': { target: backendUrl, ... },
    '^/label_studio_env': { target: backendUrl, ... },
    '^/annotation_tasks': { target: backendUrl, ... },
    '^/qa/groups$': { target: backendUrl, ... },
    '^/api/qa/': { target: backendUrl, ... },
    '^/llm/': { target: backendUrl, ... },
    '^/report_list/data': { target: backendUrl, ... },
    '^/static': { target: backendUrl, ... },
    '^/css': { target: backendUrl, ... },
    '^/js': { target: backendUrl, ... },
  }
}
```

### 4.2 后端地址检测
```typescript
const detectBackendUrl = () => {
  if (env.VITE_BACKEND_URL) return env.VITE_BACKEND_URL
  return 'http://127.0.0.1:5001'
}
```

可通过 `.env.development.local` 中的 `VITE_BACKEND_URL` 覆盖。

---

## 5. 前端 API 模块

### 5.1 HTTP 客户端 (`frontend/src/api/index.ts`)

两个 axios 实例：
- `apiClient`: baseURL = `/api`, 用于标准 API
- `legacyClient`: baseURL = `/`, 用于遗留接口

统一拦截器：
- 请求拦截器：可添加认证 token
- 响应拦截器：错误时显示 ElMessage 提示

### 5.2 API 模块列表

| 文件 | 功能模块 | 主要接口 |
|------|----------|----------|
| `qa.ts` | 问答对管理 | 分组 CRUD、问答对 CRUD、导入导出 |
| `knowledge.ts` | 知识库管理 | 知识库 CRUD、文件管理、问题集、标注任务 |
| `llm.ts` | LLM 模型 | 模型 CRUD、评估任务、报告管理 |
| `environment.ts` | 环境管理 | 环境 CRUD、LS 环境配置 |
| `report.ts` | 报告管理 | 报告列表、详情、删除 |

### 5.3 类型定义 (`frontend/src/types/`)

| 文件 | 内容 |
|------|------|
| `index.ts` | 通用类型(ApiResponse, PaginationData, PaginationParams) |
| `qa.ts` | QAGroup, QAItem, QuestionType 等 |
| `llm.ts` | LLMModel, EvaluationTask, Report 等 |
| `common.ts` | 通用组件类型 |

---

## 6. 重要基础模块

### 6.1 数据库管理 (`src/sql_funs/sql_base.py`)

**PostgreSQLManager** - 数据库连接池管理

- 单例模式：每个主机 + 子类 只有一个实例
- 连接池：类级别共享，初始化时创建 `minconn=10, maxconn=50`
- 配置来源：`env_config_init.settings`

关键方法：
```python
PostgreSQLManager.initialize_pool(minconn=10, maxconn=50)  # 应用启动时调用
execute_query(sql, params)      # 执行查询
execute_insert(sql, params)     # 执行插入
execute_update(sql, params)     # 执行更新
execute_delete(sql, params)     # 执行删除
execute_batch(sql, params_list) # 批量执行
```

### 6.2 评估引擎 (`src/llm/`)

| 文件 | 功能 |
|------|------|
| `api_agent_evaluator.py` | 主评估引擎 LLMEvaluator |
| `llm_agent_basic.py` | LLM 基础接口包装 |
| `llm_interface.py` | LLM 调用接口 |
| `data_loaders.py` | 数据加载器 |
| `config_manager.py` | 配置管理 |

评估流程：
1. 加载 QA 数据
2. 调用 LLM API 获取回答
3. 与标准答案对比（精确匹配、语义相似度、LLM-as-judge）
4. 计算指标（准确率、召回率、F1）
5. 生成报告存储到数据库

### 6.3 Label Studio 集成 (`src/label_studio_api/`)

| 文件 | 功能 |
|------|------|
| `label_studio_client.py` | LS 客户端封装 |
| `annotator.py` | 标注器接口 |
| `task.py` | 任务管理 |
| `export.py` | 数据导出 |
| `ml_backed/` | ML 辅助预测后端 |

### 6.4 MinIO 客户端 (`src/utils/minio_client.py`)

用于文件存储（知识库文件、评估结果等）。

配置项：
```toml
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'admin123'
MINIO_BUCKET_NAME = 'knowledge-files'
```

### 6.5 配置管理

配置文件路径：`configs/settings.toml`（从 `settings_example.toml` 复制）

主要配置节：
```toml
[default]
PROJECT_ROOT = '/path/to/project'

# PostgreSQL
SQL_HOST = 'localhost'
SQL_PORT = 5432
SQL_DB = 'label_studio'
SQL_USER = 'user'
SQL_PASSWORD = 'password'

# MinIO
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'admin123'
MINIO_BUCKET_NAME = 'knowledge-files'

# LLM API
DEEPSEEK_API_KEY = "sk-..."
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# 向量模型
MODEL_PATH = '/path/to/bge-base-zh-v1.5'
```

---

## 7. 数据库表结构

### 7.1 主要表（通过 CRUD 推断）

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `ai_qa_data_groups` | 问答对组 | id, name, purpose, test_type, language, difficulty_range, tags, is_active |
| `ai_qa_data` | 问答对 | id, group_id, question, answers, context, question_type, difficulty_level |
| `llm_models` | LLM 模型配置 | name, api_config, model_params |
| `llm_evaluation_reports` | 评估报告 | report_id, model_name, group_id, metrics, created_at |
| `llm_evaluation_details` | 评估详情 | detail_id, report_id, question_id, answer, is_correct, similarity |
| `local_knowledge` | 本地知识库 | kno_id, kno_name, kno_describe, kno_path, ls_status |
| `local_knowledge_files` | 知识库文件 | file_id, kno_id, file_path, file_type |
| `environments` | 测试环境 | id, zlpt_name, project_name, zlpt_base_url, project_id |
| `annotation_tasks` | 标注任务 | task_id, task_name, knowledge_id, status, ls_project_id |

---

## 8. 启动命令

### 8.1 后端启动
```bash
# 基础启动
python app.py

# 指定参数
python app.py --host 0.0.0.0 --port 5001 --debug

# 使用脚本
python scripts/start_backend.py --debug
```

### 8.2 前端启动
```bash
cd frontend
npm install
npm run dev      # 开发服务器
npm run build    # 生产构建
npm run type-check  # 类型检查
```

### 8.3 完整开发环境
```bash
# Terminal 1 - 后端
python scripts/start_backend.py --debug

# Terminal 2 - 前端
cd frontend && npm run dev

# 访问 http://localhost:5173
# API http://localhost:5001
```

---

## 9. 环境变量

### 9.1 后端环境变量
| 变量 | 说明 |
|------|------|
| `CORS_ALLOW_ALL` | 设置为 `true` 允许所有 CORS 来源 |
| `CORS_ORIGINS` | 逗号分隔的额外 CORS 来源 |
| `VUE_FRONTEND_MODE` | `auto`/`force`/`disable` 控制 Vue 前端模式 |

### 9.2 前端环境变量
| 变量 | 说明 |
|------|------|
| `VITE_BACKEND_URL` | 后端 API 地址，默认 `http://127.0.0.1:5001` |

---

## 10. 开发注意事项

1. **前后端路由冲突**: 前端路由使用 `/api/*` 区分 API 和非 API 请求，Vite 代理配置需要精确匹配
2. **数据库连接**: 应用启动时调用 `PostgreSQLManager.initialize_pool()` 初始化连接池
3. **Vue 前端模式**: 
   - `auto`: 自动检测 `frontend/dist/index.html` 是否存在
   - `force`: 强制使用 Vue 前端
   - `disable`: 使用传统 Flask 模板
4. **日志**: 请求日志写入 `logs/request.log`，错误日志写入 `logs/error.log`
5. **评估任务**: 后台评估使用 threading，任务状态存储在内存字典 `_evaluation_tasks` 中

---

*文件生成时间: 2026-03-17*  
*后续更新: 如有路由变更、API 增减，请及时更新此文件*
