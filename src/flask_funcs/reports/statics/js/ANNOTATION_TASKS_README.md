# 标注任务管理模块使用说明

## 概述

标注任务管理模块提供了对标注任务的完整管理功能，包括创建、查询、编辑和删除标注任务。

## 文件结构

```
src/flask_funcs/
├── annotation_tasks.py                          # 路由文件
└── reports/
    ├── flask_annotation_tasks_renderer.py       # 页面渲染器
    ├── templates/
    │   └── annotation_tasks.html                # HTML 模板
    └── statics/
        ├── css/
        │   └── annotation_tasks.css             # 样式文件
        └── js/
            └── annotation_tasks.js              # JavaScript 文件
```

## 功能特性

### 1. 任务列表展示
- 支持分页显示（默认每页 20 条）
- 支持按任务名称搜索
- 显示完整的任务信息，包括：
  - 任务 ID、任务名称
  - 本地知识库 ID 和名称
  - 问题集 ID 和名称
  - Label Studio 环境 ID
  - 标注进度（已标注/总数）
  - 任务状态
  - 标注类型
  - 创建时间

### 2. 任务管理
- **创建任务**：填写任务名称、选择知识库、问题集、环境和标注类型
- **编辑任务**：修改任务名称、状态和标注类型（知识库和问题集不可修改）
- **删除任务**：确认后可删除指定任务

### 3. 数据关联
- 自动加载本地知识库列表
- 根据选择的知识库动态加载对应的问题集
- 加载所有可用的 Label Studio 环境

## API 接口

### 页面路由
- `GET /annotation_tasks` - 标注任务管理页面

### 数据接口
- `GET /api/annotation/tasks/list` - 获取任务列表（支持分页、搜索）
  - 查询参数：
    - `page`: 页码（默认 1）
    - `limit`: 每页数量（默认 20）
    - `keyword`: 搜索关键词（按任务名称模糊匹配）
- `POST /api/annotation/tasks/create` - 创建标注任务
- `PUT /api/annotation/tasks/update` - 更新标注任务
- `DELETE /api/annotation/tasks/delete` - 删除标注任务
- `GET /api/local_knowledge/list` - 获取本地知识库列表
- `GET /api/questions/list?knowledge_id={id}` - 获取问题集列表
- `GET /api/label_studio/environments/list` - 获取 Label Studio 环境列表

## 使用示例

### 访问页面
在浏览器中访问：`http://localhost:5001/annotation_tasks`

### 创建任务
1. 点击"+ 创建任务"按钮
2. 填写任务名称
3. 选择本地知识库
4. 选择对应的问题集
5. 选择 Label Studio 环境
6. 选择标注类型（可选）
7. 点击"保存"

### 编辑任务
1. 在任务列表中找到要编辑的任务
2. 点击"编辑"按钮
3. 修改任务名称、状态或标注类型
4. 点击"保存"

### 删除任务
1. 在任务列表中找到要删除的任务
2. 点击"删除"按钮
3. 确认删除操作

## 技术实现

### 前端组件
- **PaginationComponent**: 分页组件
- **SearchComponent**: 搜索组件
- **DialogManager**: 对话框管理器
- **APIHelper**: API 请求助手

### 后端 CRUD
使用 `LabelStudioCrud` 类提供的方法：
- `view_annotation_task_extended_list()`: 查询扩展视图（包含知识库和问题集名称）
- `annotation_task_create()`: 创建任务
- `annotation_task_update()`: 更新任务
- `annotation_task_delete()`: 删除任务
- `_view_annotation_task_extended_list_to_json()`: 数据格式转换

### 数据库表
- **ai_annotation_tasks**: 标注任务主表
- **ai_annotation_task_extended_view**: 标注任务扩展视图（包含关联信息）

## 注意事项

1. **字段说明**
   - `task_id`: 任务唯一标识（自动生成）
   - `local_knowledge_id`: 本地知识库 ID
   - `question_set_id`: 问题集 ID
   - `label_studio_env_id`: Label Studio 环境 ID
   - `task_status`: 任务状态（未开始/标注中/已完成）
   - `annotation_type`: 标注类型（llm/manual/mlb）

2. **数据验证**
   - 任务名称为必填项
   - 本地知识库、问题集、环境必须选择
   - 编辑模式下知识库和问题集不可修改

3. **错误处理**
   - 所有 API 调用都有异常捕获
   - 失败时会显示详细的错误信息
   - 网络错误会单独提示

## 依赖关系

### 导入的模块
- `src.sql_funs.LabelStudioCrud`: 标注任务 CRUD 操作
- `src.sql_funs.QuestionsCRUD`: 问题集管理
- `src.flask_funcs.reports.flask_annotation_tasks_renderer`: 页面渲染
- `env_config_init.settings`: 配置信息

### 前端依赖
- `common_components.js`: 通用组件（分页、搜索、筛选）
- `ui_components.js`: UI 组件（对话框、表单验证等）
