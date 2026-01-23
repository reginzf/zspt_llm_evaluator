# Label Studio API 模块

本目录包含与 Label Studio 平台进行交互的各种工具和类，提供了一系列高级功能来支持标注任务的自动化和智能化。

## 目录结构

```
src/label_studio_api/
├── __init__.py
├── annotator.py          # 标注工具类，提供高级标注操作
├── export.py            # 导出工具，用于将标注结果转换为自定义格式
├── label_studio_client.py  # Label Studio 客户端单例类
├── labels.py            # 标签配置生成器，用于生成 Label Studio 的 XML 配置
├── task.py              # 任务管理工具，提供批量创建和查询任务功能
└── ml_backed/           # 机器学习后端服务
    ├── __init__.py
    ├── ml_banked_server.py    # 基于 BGE 模型的 ML 后端服务器
    └── prediction_creator.py  # 预测创建器，用于将模型预测结果上传到 Label Studio
```

## 模块功能说明

### [annotator.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/annotator.py)
提供高级标注操作功能，包括：
- `Annotator`: 标注器主类，提供各种标注操作方法
- `AnnotationGenerator`: 标注数据生成器，支持多种标注类型（选择题、文本、数字、评分、标签等）
- `AnnotateToCreate`, `AnnotateToAdd`, `AnnotateToDelete`: 不同类型的标注操作配置类
- 支持标注的创建、添加、删除和合并操作
- 提供对预测和标注的统一操作接口

### [labels.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/labels.py)
标签配置生成器，用于动态生成 Label Studio 的界面配置：
- `LabelStudioXMLGenerator`: XML 配置生成器，支持网格布局
- 支持多种问题类型（事实型、上下文型、概念型、推理型、应用型）
- 可从 JSON 数据生成 XML 配置
- 支持自定义颜色和布局

### [task.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/task.py)
任务管理工具，提供批量操作功能：
- `create_tasks`: 批量创建任务，支持分批处理
- `get_tasks_with_specific_choice`: 根据特定选择查找任务

### [export.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/export.py)
导出工具，用于将标注结果转换为自定义格式：
- `export_custom_json_format`: 导出为自定义 JSON 格式
- 支持项目元数据和标注结果的结构化导出

### [label_studio_client.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/label_studio_client.py)
Label Studio 客户端单例实现：
- `LabelStudioLogin`: 基于 label_studio_sdk.Client 的单例类
- 确保相同配置的客户端只创建一次实例

### [ml_backed/](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/ml_backed) 目录

#### [ml_banked_server.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/ml_backed/ml_banked_server.py)
基于 BGE 模型的机器学习后端服务器：
- `MyModel`: 继承自 LabelStudioMLBase 的模型类
- 使用 BGE 模型进行文本相似度计算
- 支持单例模式，线程安全
- 提供 `/predict`、`/health`、`/setup` 等 REST API
- 实现基于语义相似度的自动标注

#### [prediction_creator.py](file://D:/pyworkplace/git_place/ai-ken/src/label_studio_api/ml_backed/prediction_creator.py)
预测创建器，用于将模型预测结果上传到 Label Studio：
- `LabelStudioPredictionCreator`: 预测创建器主类
- 将 ML 模型的预测结果转换为 Label Studio 预测格式
- 支持单个和批量任务预测创建

## 主要特性

1. **智能标注**: 通过 BGE 模型实现基于语义相似度的自动标注
2. **灵活配置**: 支持动态生成 Label Studio 界面配置
3. **批量操作**: 提供任务的批量创建和处理功能
4. **单例模式**: 客户端和服务类采用单例模式，优化资源使用
5. **API 接口**: 提供完整的 REST API 接口支持
6. **格式转换**: 支持多种数据格式的导入和导出

## 使用示例

```python
from src.label_studio_api import LabelStudioLogin, LabelStudioXMLGenerator

# 登录 Label Studio
client = LabelStudioLogin(url="http://localhost:8080", api_key="your_api_key")

# 生成标签配置
generator = LabelStudioXMLGenerator()
xml_config = generator.generate_from_json(your_json_data)

# 创建预测
from src.label_studio_api.ml_backed.prediction_creator import LabelStudioPredictionCreator
creator = LabelStudioPredictionCreator(client, your_question_json)
prediction = creator.create_prediction_for_task(task_data, project)
```

## 技术栈

- label-studio-sdk: Label Studio 官方 SDK
- transformers: Hugging Face 模型库
- torch: PyTorch 深度学习框架
- Flask: Web 框架（用于 ML 后端）
- numpy: 数值计算库