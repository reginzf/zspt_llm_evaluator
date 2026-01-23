# Flask 路由控制器模块

本目录包含项目的 Flask 路由控制器模块，每个文件对应一个功能模块的路由定义。

## 模块列表

### [common_utils.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/common_utils.py)
通用工具函数模块，提供验证和生成唯一ID等功能。

### [local_knowledge_detail.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/local_knowledge_detail.py)
本地知识库详情页面的路由控制器，处理知识库的增删改查等基础操作。

### [local_knowledge_detail_label_studio.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/local_knowledge_detail_label_studio.py)
本地知识库与 Label Studio 集成的路由控制器，处理标注任务的创建、管理和同步功能，包括：
- 环境管理（绑定、解绑 Label Studio 环境）
- 标注任务管理（创建、编辑、删除、同步）
- 自动标注（MLB 和 LLM 标注）
- 任务状态跟踪

### [metric_task_detail.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/metric_task_detail.py)
指标任务详情页面的路由控制器，处理指标任务相关的操作。

### [reports](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/reports) 目录
报告相关功能模块：
- [flask_local_knowledge_detail_renderer.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/reports/flask_local_knowledge_detail_renderer.py) - 本地知识库详情页面渲染器
- [flask_metric_task_detail_renderer.py](file://D:/pyworkplace/git_place/ai-ken/src/flask_funcs/reports/flask_metric_task_detail_renderer.py) - 指标任务详情页面渲染器

## 目录结构规范

根据项目架构，每个功能模块应遵循以下文件组织结构：
- 路由控制器: `src/flask_funcs/[module].py`
- 页面渲染器: `reports/flask_[module]_renderer.py`
- HTML模板: `templates/[module].html`
- CSS样式: `statics/css/[module].css`
- JavaScript文件: `statics/js/[module].js`

## 技术栈

- Flask: Web框架
- SQLAlchemy: ORM框架
- label-studio-sdk: Label Studio 集成
- openai: LLM接口集成

## 使用说明

各模块通过 Flask 蓝图（Blueprint）方式进行组织，便于模块化管理和维护。路由统一使用 JSON 格式进行前后端数据传递，遵循 RESTful API 设计规范。