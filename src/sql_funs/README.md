# SQL Functions 模块

本目录包含项目的数据库操作模块，提供了一套完整的 CRUD（创建、读取、更新、删除）操作接口，用于与 PostgreSQL 数据库进行交互。

## 目录结构

```
src/sql_funs/
├── __init__.py              # 模块初始化文件
├── sql_base.py             # PostgreSQL 数据库管理基类
├── environment_crud.py     # 环境信息 CRUD 操作
├── local_knowledge_crud.py # 本地知识库 CRUD 操作
├── knowledge_crud.py       # 知识库 CRUD 操作
├── knowledge_path_crud.py  # 知识库路径 CRUD 操作
├── questions_crud.py       # 问题配置 CRUD 操作
├── label_studio_crud.py    # Label Studio 集成 CRUD 操作
├── metric_tasks_crud.py    # 指标任务 CRUD 操作
├── annotation_metric_tasks_crud.py # 标注与指标任务 CRUD 操作
├── creaters/               # 数据库表和视图创建脚本
│   ├── create_tables.py    # 数据库表创建脚本
│   └── create_views.py     # 数据库视图创建脚本
```

## 核心功能

### [sql_base.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/sql_base.py)
- **PostgreSQLManager**: 数据库管理基类，提供连接、查询、增删改查等基础操作
- **单例模式**: 使用类名和主机作为键实现单例模式，确保每个子类有独立实例
- **通用查询方法**: `gen_select_query()` 生成查询语句，支持精确匹配和模糊匹配
- **JSON 数据处理**: 自动处理 JSON/JSONB 类型数据的序列化和反序列化
- **事务管理**: 自动处理事务提交和回滚
- **更新触发器**: 自动为表创建 `updated_at` 字段的更新触发器

### [environment_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/environment_crud.py)
- **环境信息管理**: 管理 ZLPT（紫鸾平台）环境信息
- **知识库基础信息**: 管理知识库基础信息，包括切分参数、可见范围等
- **环境绑定**: 管理环境与知识库的绑定关系

### [local_knowledge_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/local_knowledge_crud.py)
- **本地知识库管理**: 管理本地知识库信息（ai_local_knowledge 表）
- **知识库文件列表**: 管理本地知识库文件列表（ai_local_knowledge_list 表）
- **文件上传记录**: 管理文件上传状态记录（ai_local_knowledge_file_upload 表）
- **知识库绑定**: 管理本地知识库与知识库的绑定关系
- **综合视图查询**: 提供本地知识库及其绑定信息的综合查询

### [label_studio_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/label_studio_crud.py)
- **Label Studio 环境管理**: 管理 Label Studio 环境信息
- **环境绑定**: 管理本地知识库与 Label Studio 的绑定关系
- **标注任务管理**: 管理标注任务的创建、更新和查询
- **扩展视图**: 提供标注任务扩展信息的查询视图

### [questions_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/questions_crud.py)
- **问题集配置**: 管理问题集配置信息
- **多类型问题**: 支持基础、详细、机制、主题等多种类型的问题管理
- **问题分类**: 按类型动态访问不同的问题表
- **JSON 生成**: 提供问题数据到 JSON 格式的转换功能

### [metric_tasks_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/metric_tasks_crud.py)
- **指标任务管理**: 管理指标任务的创建、更新和查询
- **标注指标关联**: 提供标注任务与指标任务的关联视图
- **报告管理**: 管理报告生成和状态跟踪

### [knowledge_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/knowledge_crud.py) 和 [knowledge_path_crud.py](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/knowledge_path_crud.py)
- **知识库管理**: 管理知识库中的文档信息
- **知识库路径管理**: 管理知识库的目录结构

## 数据库表结构

### 主要数据表
- `ai_environment_info`: 环境信息表
- `ai_knowledge_base`: 知识库基础信息表
- `ai_local_knowledge`: 本地知识库表
- `ai_local_knowledge_list`: 本地知识库文件列表表
- `ai_label_studio_info`: Label Studio 环境信息表
- `ai_annotation_tasks`: 标注任务表
- `ai_metric_tasks`: 指标任务表
- `ai_question_config`: 问题配置表
- `ai_basic_questions`, `ai_detailed_questions`, `ai_mechanism_questions`, `ai_thematic_questions`: 多类型问题表

### 关系表
- `ai_knowledge_bind`: 知识库绑定关系表
- `ai_label_studio_bind`: Label Studio 绑定关系表
- `ai_local_knowledge_file_upload`: 本地知识库文件上传记录表

### 视图表
- `ai_annotation_task_extended_view`: 标注任务扩展视图
- `ai_annotation_metric_tasks_view`: 标注与指标任务关联视图
- `ai_local_knowledge_comprehensive_view`: 本地知识库综合视图

## 使用方法

### 基本用法
```python
from src.sql_funs import LocalKnowledgeCrud

# 使用上下文管理器
with LocalKnowledgeCrud() as crud:
    # 创建记录
    result = crud.local_knowledge_insert(
        kno_id="kno_123",
        kno_name="测试知识库",
        kno_describe="这是一个测试知识库",
        kno_path="/path/to/knowledge"
    )
    
    # 查询记录
    knowledge_list = crud.get_local_knowledge(kno_id="kno_123")
    
    # 更新记录
    result = crud.local_knowledge_update(
        kno_id="kno_123",
        kno_name="更新后的知识库名称"
    )
    
    # 删除记录
    result = crud.local_knowledge_delete(kno_id="kno_123")
```

### 高级查询
```python
# 使用多种条件查询
with LabelStudioCrud() as ls_crud:
    # 精确匹配和模糊匹配结合
    tasks = ls_crud.annotation_task_list(
        task_status='已完成',
        task_name='test'  # 模糊匹配
    )
    
    # 多条件查询
    environments = ls_crud.label_studio_list(
        label_studio_url='http://example.com'
    )
```

## 设计特点

1. **继承架构**: 所有 CRUD 类都继承自 [PostgreSQLManager](file://D:/pyworkplace/git_place/ai-ken/src/sql_funs/sql_base.py#L14-L177)，共享通用的数据库操作功能
2. **单例模式**: 使用主机和类名作为键实现单例模式，避免重复连接
3. **类型安全**: 使用类型提示明确方法参数和返回值类型
4. **JSON 支持**: 自动处理 JSON/JSONB 字段的序列化
5. **安全查询**: 使用参数化查询防止 SQL 注入
6. **错误处理**: 完善的异常处理和日志记录
7. **灵活查询**: 支持精确匹配和模糊匹配的动态查询生成
8. **视图支持**: 提供复杂的关联查询视图

## 数据库配置

数据库连接信息通过 `env_config_init.settings` 模块获取，支持以下配置项：
- `SQL_HOST`: 数据库主机地址
- `SQL_PORT`: 数据库端口
- `SQL_DB`: 数据库名称
- `SQL_USER`: 用户名
- `SQL_PASSWORD`: 密码