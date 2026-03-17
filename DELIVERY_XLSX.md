# XLSX 导入功能 - 交付文档

> 交付时间: 2026-03-17  
> 版本: v1.0  
> 状态: ✅ 开发完成，待部署测试

---

## 功能概述

在 AI-KEN 平台的问答对导入功能中，新增支持从 **Excel (.xlsx)** 文件导入数据。

### 用户流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   1. 选择文件    │ ──▶ │   2. 预览数据    │ ──▶ │   3. 字段映射    │ ──▶ │   4. 执行导入    │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │                       │
   点击 📊 选择          显示前5行数据           映射xlsx列到            批量导入到
   xlsx 文件上传                                  ai_qa_data表            数据库
```

---

## 修改内容

### 前端修改 (`frontend/src/views/qa/QAImport.vue`)

| 行号 | 修改项 | 说明 |
|------|--------|------|
| 52 | 提示文本 | 添加 "或xlsx文件" |
| 55-59 | 上传模式 | 新增 📊 选择xlsx文件 选项 |
| 70-80 | 上传区域 | 根据模式动态显示图标和提示 |
| 84-92 | 文件输入 | xlsx 模式下限制文件类型 |
| 282 | 类型定义 | uploadMode 支持 'xlsx' |
| 401-416 | 文件选择 | 添加 xlsx 文件校验 |
| 418-443 | 拖拽处理 | 添加 xlsx 拖拽校验 |

### 后端修改 (`src/sql_funs/ai_qa_data_crud_enhanced.py`)

| 方法 | 修改内容 |
|------|----------|
| `preview_huggingface_dataset` | 添加 xlsx 文件类型检测 |
| `_preview_xlsx_file` (新增) | 使用 pandas 读取 xlsx 第一个 sheet |
| `import_with_mapping` | 添加 xlsx 文件类型检测 |
| `_import_xlsx_file` (新增) | 读取完整 xlsx 并批量导入 |

---

## 技术实现

### 核心逻辑

```python
# 1. 预览 xlsx 文件
def _preview_xlsx_file(file_path, preview_rows=5):
    df = pd.read_excel(file_path, sheet_name=0)  # 只读第一个 sheet
    return {
        'columns': df.columns.tolist(),
        'total_records': len(df),
        'preview_rows': df.head(preview_rows).to_dict('records')
    }

# 2. 导入 xlsx 文件
def _import_xlsx_file(config, ...):
    df = pd.read_excel(config.file_path, sheet_name=0)
    for _, row in df.iterrows():
        qa_data = convert_with_mapping(row, config.mapping)
        create_qa_data(**qa_data)
```

### 依赖

已存在于 `requirements.txt`：
- `pandas==2.3.3`
- `openpyxl==3.1.5`

---

## 文件清单

### 修改的文件
```
frontend/src/views/qa/QAImport.vue                (7处修改)
src/sql_funs/ai_qa_data_crud_enhanced.py          (4处修改+2个新方法)
```

### 新增的文件
```
test_xlsx_simple.py              # 独立测试脚本
test_xlsx_import.py              # 集成测试脚本
PLAN_XLSX_IMPORT.md              # 开发计划文档
TEST_CASES_XLSX.md               # 测试用例文档
CHANGES_XLSX.md                  # 变更汇总文档
DELIVERY_XLSX.md                 # 本文档
```

---

## 测试验证

### 单元测试
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator
python3 test_xlsx_simple.py
```

**结果**: ✅ 通过
- 预览功能: ✅
- 数据转换: ✅

### 测试数据示例

```excel
| 问题          | 答案              | 上下文       | 类型 | 难度 | 标签     |
|---------------|-------------------|--------------|------|------|----------|
| 什么是Python？ | Python是一种...   | 编程语言介绍 | 概念 | 1    | 编程     |
| 什么是Flask？  | Flask是一个...    | Web开发      | 工具 | 2    | Python   |
```

---

## 部署步骤

### 1. 确认依赖
```bash
pip show pandas openpyxl
# 如未安装:
pip install pandas openpyxl
```

### 2. 启动后端
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator
python app.py --host 0.0.0.0 --port 5001 --debug
```

### 3. 启动前端
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator/frontend
npm install  # 如有依赖变更
npm run dev
```

### 4. 访问测试
```
http://localhost:5173/qa/groups/1/import
```

---

## API 接口

所有接口自动支持 xlsx，无需额外参数：

| 接口 | 方法 | 路径 |
|------|------|------|
| 上传 | POST | `/api/qa/groups/{id}/items/import/upload` |
| 预览 | POST | `/api/qa/groups/{id}/items/import/preview` |
| 导入 | POST | `/api/qa/groups/{id}/items/import/execute` |
| 状态 | GET | `/api/qa/groups/{id}/items/import/status/{task_id}` |

---

## 已知限制

1. **只读第一个 sheet** - 多 sheet 文件只处理第一个
2. **表头必须在第一行** - 不支持自定义表头位置
3. **日期转为字符串** - Excel 日期格式转为字符串存储
4. **公式已计算** - 公式单元格存储计算后的值

---

## 后续优化建议

- [ ] 支持多 sheet 选择
- [ ] 数据格式预校验（如难度等级必须是整数）
- [ ] 提供标准 xlsx 模板下载
- [ ] 大文件分片上传
- [ ] 导入进度实时推送（WebSocket）

---

## 回滚方案

如需回滚：
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator
git checkout frontend/src/views/qa/QAImport.vue
git checkout src/sql_funs/ai_qa_data_crud_enhanced.py
```

---

## 联系方式

如有问题，请查看：
- `PLAN_XLSX_IMPORT.md` - 详细开发计划
- `TEST_CASES_XLSX.md` - 测试用例
- `CHANGES_XLSX.md` - 变更详情

---

*文档版本: 1.0*  
*最后更新: 2026-03-17*  
*作者: OpenClaw Agent*
