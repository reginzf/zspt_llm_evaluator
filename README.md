# AI知识库质量评估系统

## 项目概述

本项目是一个完整的AI知识库质量评估系统，用于评估紫鸾平台知识库的召回质量。系统通过自动化流程完成知识库创建、文件上传、切片标注、质量评估和报告生成。

## 核心功能

1. **知识库初始化与文件上传** - 在紫鸾平台创建知识库并上传文档
2. **自动化标注** - 在Label Studio中创建标注任务并自动完成初步标注
3. **质量评估** - 计算不同搜索类型（向量检索、混合检索、增强检索）的召回质量指标
4. **报告生成** - 生成美观的HTML可视化报告，展示评估结果

## 系统架构

```
ai-ken/
├── main.py                    # 主程序入口
├── src/                       # 核心业务逻辑
│   └── lzpt_ls_operate.py    # 紫鸾平台和Label Studio操作
├── check_chunk/               # 质量评估模块
│   ├── do_check.py           # 指标计算主逻辑
│   └── checker_funcs         # 评估函数
├── reports/                   # 报告生成模块
│   └── reports_funcs/
│       └── generate_report.py # 报告生成器
├── label_studio/              # Label Studio集成
├── zlpt/                      # 紫鸾平台集成
├── utils/                     # 工具函数
├── configs/                   # 配置文件
└── env_config_init.py        # 环境配置初始化
```

## 使用流程

### 步骤1：初始化知识库和标注任务
```python
# 调用zlpt_init_and_ls_label，完成文件上传紫鸾平台和在label studio上创建任务，并初步完成标注
knowledge_dict, zlpt_user, ls_user, kno_id, project = zlpt_init_and_ls_label()
```

**功能说明：**
- 登录紫鸾平台并创建知识库
- 上传文档文件到知识库
- 等待知识库学习完成
- 在Label Studio中创建标注项目
- 自动完成初步标注
- 保存知识库信息到本地

### 步骤2：计算质量指标
```python
# 调用cal_metric_all，获取紫鸾平台对应问题的召回和label studio已经标注的数据，算出metric
from check_chunk.do_check import cal_metric_all

knowledge_dict = load_json_file(KNOWLEDGE_PATH)
project_name = knowledge_dict['name']
kno_id = knowledge_dict['kno_id']

for search_type in ["vectorSearch", "hybridSearch", "augmentedSearch"]:
    cal_metric_all(project_name, kno_id, search_type)
```

**功能说明：**
- 针对三种搜索类型分别计算质量指标
- 获取紫鸾平台的召回结果
- 获取Label Studio的已标注数据
- 计算召回率、准确率等指标
- 保存指标数据到JSON文件

### 步骤3：生成评估报告
```python
# 调用generate_reports_from_metric_files，生成html报告
from reports.reports_funcs.generate_report import generate_reports_from_metric_files
generate_reports_from_metric_files(REPORT_PATH)
```

**功能说明：**
1. **读取数据文件** - 从REPORT_PATH读取所有以"metric"开头、".json"结尾的文件
2. **分析数据** - 对每个metric文件进行分析，生成analysis_results
3. **生成报告** - 为每个输入文件生成对应的HTML报告，报告名称与输入文件一一对应
4. **保存报告** - 将生成的报告文件保存到REPORT_PATH目录下

## 配置文件

### 环境配置 (env_config_init.py)
- `REPORT_PATH`: 报告文件保存路径
- `KNOWLEDGE_PATH`: 知识库信息文件路径
- `CHUNK_SIZE`: 切片大小
- `CHUNK_OVERLAP`: 切片重叠大小
- `QUESTION_TYPE`: 问题类型（BASIC/DETAILED/MECHANISM/THEMATIC）

### 设置文件 (configs/settings.toml)
```toml
[default]
ZLPT_BASE_URL = "紫鸾平台基础URL"
USERNAME = "用户名"
PASSWORD = "密码"
DOMAIN = "域"
TEST_PATH = "测试用例路径"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 0
QUESTION_TYPE = "BASIC"
```

## 核心模块详解

### 1. 紫鸾平台操作 (src/lzpt_ls_operate.py)
- `login_zlpt()`: 登录紫鸾平台
- `zlpt_create_knowledge_base()`: 创建知识库
- `zlpt_upload_files()`: 上传文件到知识库
- `zlpt_get_chunk_all_by_doc_id()`: 获取文档所有切片
- `zlpt_get_chunk_by_question()`: 根据问题检索相关切片

### 2. Label Studio操作
- `login_label_studio()`: 获取Label Studio客户端
- `ls_create_project()`: 创建Label Studio项目
- `ls_create_tasks()`: 创建标注任务
- `label_chunks_by_chunk_id()`: 根据切片ID进行标注

### 3. 质量评估 (check_chunk/do_check.py)
- `cal_metric_all()`: 计算所有质量指标
- 支持三种搜索类型：vectorSearch, hybridSearch, augmentedSearch
- 计算指标包括：召回率、准确率、F1分数等

### 4. 报告生成 (reports/reports_funcs/generate_report.py)
- `generate_reports_from_metric_files()`: 从metric文件生成报告
- `analyze_metrics()`: 分析指标数据
- `generate_html_report()`: 生成HTML报告

## 报告生成流程

### 输入文件格式
报告生成器会自动查找REPORT_PATH目录下所有符合以下模式的文件：
- 文件名以"metric"开头
- 文件扩展名为".json"
- 例如：`metric_vectorSearch.json`, `metric_hybridSearch.json`

### 输出报告
为每个输入文件生成对应的HTML报告：
- 报告名称：`report_[输入文件名]_[时间戳].html`
- 例如：`report_metric_vectorSearch_20251215_143645.html`

### 报告内容
生成的HTML报告包含：
1. **总体统计** - 平均指标值
2. **详细指标** - 每个问题的具体指标
3. **可视化图表** - 指标分布图
4. **性能分析** - 不同搜索类型的对比

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
1. 复制`configs/settings.toml.example`为`configs/settings.toml`
2. 修改配置文件中的参数
3. 确保文档文件位于正确的目录

### 运行完整流程
```bash
python main.py
```

### 仅生成报告
```bash
python -m reports.reports_funcs.generate_report
```

### 快速生成示例报告
```bash
python -m reports.reports_funcs.generate_report --quick
```

## 注意事项

1. **网络连接** - 确保可以访问紫鸾平台和Label Studio
2. **文件权限** - 确保有足够的权限读写相关目录
3. **配置正确** - 检查所有配置文件是否正确设置
4. **依赖安装** - 确保所有Python依赖已正确安装

## 扩展与定制

### 添加新的搜索类型
1. 在`main.py`中添加新的search_type到循环中
2. 确保`cal_metric_all`函数支持该类型

### 自定义报告模板
1. 修改`visualize_metrics.py`中的`generate_html_report`函数
2. 调整HTML模板和CSS样式

### 添加新的评估指标
1. 在`check_chunk/checker_funcs.py`中添加新的计算函数
2. 在`cal_metric_all`中调用新函数

## 故障排除

### 常见问题
1. **登录失败** - 检查用户名、密码和域名配置
2. **文件上传失败** - 检查文件路径和权限
3. **报告生成失败** - 检查REPORT_PATH目录是否存在
4. **指标计算错误** - 检查JSON文件格式是否正确

### 日志查看
系统使用标准日志记录，日志文件位于`logs/`目录下，可以查看详细的操作记录和错误信息。
