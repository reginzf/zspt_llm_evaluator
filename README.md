# AI 知识管理系统

AI-ken 是一个基于 Flask 框架开发的智能知识管理系统，集成了本地知识库管理和远程知识库（如 Label Studio）的双向同步功能。该系统旨在帮助用户高效地组织、管理和利用各种形式的知识资源。

## 功能特性

### 1. 环境管理
- 支持多环境配置管理
- 可配置不同的知识库服务端点
- 用户认证和授权管理

### 2. 本地知识库管理
- 创建和管理本地知识库
- 支持多种文档格式上传（PDF、Word、Excel、TXT 等）
- 知识库分类和标签管理
- 本地知识库与远程知识库绑定

### 3. 知识库同步
- 本地知识库与远程知识库（如 Label Studio）的双向同步
- 自动化文档分块处理
- 状态跟踪和同步历史记录

### 4. 报告和分析
- 知识库指标分析
- 文档处理报告
- 系统性能监控

### 5. 问答系统
- 基于知识库的智能问答
- 多种问题类型支持（基础、详细、机制、主题）

## 技术架构

### 后端技术栈
- **Flask**: Web 应用框架
- **SQLAlchemy**: 数据库 ORM
- **PostgreSQL**: 主数据库
- **Celery**: 异步任务处理

### 前端技术栈
- **HTML/CSS/JavaScript**: 基础前端技术
- **Bootstrap**: UI 框架
- **jQuery**: DOM 操作和 AJAX 请求

### AI 和 NLP 组件
- **LangChain**: 大语言模型集成
- **Sentence Transformers**: 语义相似度计算
- **OpenAI API**: 对话模型支持
- **DeepSeek API**: 语言模型支持

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │◄──►│   Flask Backend  │◄──►│   Knowledge DB  │
│                 │    │                  │    │                 │
│  HTML/CSS/JS    │    │  - Routes        │    │  - PostgreSQL   │
│  - Templates    │    │  - Blueprints    │    │                 │
└─────────────────┘    │  - Controllers   │    └─────────────────┘
                       │  - Services      │           ▲
                       └──────────────────┘           │
                              │                      │
                       ┌──────────────────┐          │
                       │   AI Services    │◄─────────┘
                       │                  │
                       │  - LangChain     │
                       │  - Embeddings    │
                       │  - Vector Store  │
                       └──────────────────┘
```

## 安装和部署

### 环境要求
- Python 3.12+
- PostgreSQL 12+
- Redis server
- Node.js (可选，用于构建前端资源)

### 安装步骤

1. **克隆代码仓库**
```bash
git clone https://github.com/your-org/ai-ken.git
cd ai-ken
```

2. **运行初始化脚本**
需要联网或配置代理
```bash
sh init_project_ascli.sh  # Linux/Mac
# 或
./init_project_ascli.ps1
```

3. **根据提示输入基础配置**


4. **启动应用**
```bash
python app.py  --debug
```

## 项目结构

```
ai-ken/
├── app.py                    # Flask 应用入口
├── env_config_init.py        # 环境配置初始化
├── requirements.txt          # Python 依赖
├── configs/                  # 配置文件
│   └── settings.toml         # 项目配置
├── src/
│   └── flask_funcs/          # Flask 路由和控制器
│       ├── common_utils.py   # 通用工具函数
│       ├── home.py           # 首页路由
│       ├── environment.py    # 环境管理路由
│       ├── knowledge_base.py # 知识库管理路由
│       ├── local_knowledge.py # 本地知识库路由
│       ├── local_knowledge_detail.py # 本地知识库详情路由
│       ├── report_list.py    # 报告列表路由
│       └── reports/          # 报告相关功能
│           ├── templates/    # HTML 模板
│           └── statics/      # 静态资源
├── models/                   # AI 模型
├── tests/                    # 测试文件
├── reports/                  # 报告输出
└── utils/                    # 通用工具
```

## API 接口说明

### 环境管理
- `GET /environment/` - 获取环境列表
- `POST /environment/create/` - 创建新环境
- `PUT /environment/update/` - 更新环境
- `DELETE /environment/delete/` - 删除环境

### 知识库管理
- `GET /knowledge_base/list` - 获取知识库列表
- `POST /knowledge_base/create` - 创建知识库
- `PUT /knowledge_base/update/<knowledge_id>` - 更新知识库
- `DELETE /knowledge_base/delete/<knowledge_id>` - 删除知识库

### 本地知识库
- `GET /local_knowledge/` - 获取本地知识库列表
- `POST /local_knowledge/create` - 创建本地知识库
- `POST /local_knowledge/upload` - 上传文件到知识库
- `GET /local_knowledge_detail/<kno_id>/<kno_name>` - 获取知识库详情

### 报告功能
- `GET /report_list/` - 获取报告列表
- `GET /report/<filename>` - 获取具体报告

## 配置说明

### settings.toml 配置项
```toml
[default]
PROJECT_ROOT = '/path/to/project'
SQL_HOST = 'localhost'          # 数据库主机
SQL_PORT = 5432                 # 数据库端口
SQL_DB = 'database_name'        # 数据库名
SQL_USER = 'username'           # 数据库用户名
SQL_PASSWORD = 'password'       # 数据库密码
KNOWLEDGE_LOCAL_PATH = '/path/to/knowledge'  # 本地知识库路径
OVERLAP_THRESHOLD = 0.8         # 字符串重叠阈值
SIMILARITY_THRESHOLD = 0.7      # 语义相似度阈值
SEMANTIC_WEIGHT = 0.9           # 语义匹配权重
MODEL_PATH = '/path/to/model'   # 模型路径
TOP_K = [1, 3, 5, 10]          # 质量参数配置
DEEPSEEK_API_KEY = 'api_key'    # DeepSeek API 密钥
DEEPSEEK_API_BASE = 'https://api.deepseek.com'  # DeepSeek API 地址
MODEL_NAME = 'deepseek-chat'    # 模型名称
```

## 使用说明

### 1. 环境配置
首先配置知识库环境，包括服务地址、用户名和密码。

### 2. 创建知识库
在环境配置完成后，可以创建远程知识库。

### 3. 创建本地知识库
创建本地知识库用于存储文档。

### 4. 上传文档
将文档上传到本地知识库。

### 5. 绑定和同步
将本地知识库与远程知识库绑定，然后执行同步操作。

## 开发指南

### 添加新功能
1. 在 `src/flask_funcs/` 目录下创建新的蓝图文件
2. 实现相应的路由和控制器逻辑
3. 在 `app.py` 中注册新蓝图
4. 创建对应的 HTML 模板



### 代码规范
- 遵循 PEP 8 Python 代码规范
- 函数和类应有适当的文档字符串
- 使用有意义的变量和函数名

## 故障排除

### 常见问题
1. **数据库连接失败**：检查 `configs/settings.toml` 中的数据库配置
2. **API 调用失败**：确认 API 密钥和端点配置正确
3. **文件上传失败**：检查文件权限和路径配置

### 日志
系统日志位于 `logs/` 目录下，按日期滚动保存。
