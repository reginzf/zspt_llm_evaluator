# XLSX 导入功能测试用例

> 生成时间: 2026-03-17  
> 功能: 支持从 Excel (.xlsx) 文件导入问答对数据

---

## 测试环境准备

### 1. 安装依赖
```bash
pip install pandas openpyxl
```

### 2. 准备测试文件
创建一个包含以下列的 xlsx 文件：

| 问题 | 答案 | 上下文 | 类型 | 难度 | 标签 |
|------|------|--------|------|------|------|
| 什么是Python？ | Python是一种编程语言 | 编程语言介绍 | 概念 | 1 | 编程 |
| 什么是Flask？ | Flask是一个Web框架 | Web开发 | 工具 | 2 | Python,Web |
| ... | ... | ... | ... | ... | ... |

---

## 前端测试用例

### TC-01: 页面显示
**步骤**:
1. 进入 `/qa/groups/:id` 页面
2. 点击"导入"按钮

**期望结果**:
- 提示文本显示: "请选择 HuggingFace 数据集文件夹或单个数据文件或xlsx文件"
- 上传模式有三个选项: 📁 选择文件夹、📄 选择文件、📊 选择xlsx文件

### TC-02: xlsx 文件选择
**步骤**:
1. 点击 "📊 选择xlsx文件"
2. 点击上传区域选择 xlsx 文件
3. 或拖拽 xlsx 文件到上传区域

**期望结果**:
- 文件选择框只显示 .xlsx 文件
- 显示已选文件名和大小
- "下一步" 按钮变为可用状态

### TC-03: 非法文件校验
**步骤**:
1. 选择 xlsx 模式
2. 尝试上传非 .xlsx 文件（如 .txt）

**期望结果**:
- 显示错误提示: "请选择 .xlsx 格式的文件"
- "下一步" 按钮保持不可用

### TC-04: 数据预览
**步骤**:
1. 成功上传 xlsx 文件
2. 点击 "下一步"

**期望结果**:
- 显示数据预览表格
- 展示第一个 sheet 的前 5 行数据
- 显示总记录数、字段数、字段列表

### TC-05: 字段映射
**步骤**:
1. 预览成功后点击 "下一步"
2. 在字段映射页面选择对应字段

**期望结果**:
- 下拉框显示 xlsx 文件的所有列名
- 必填字段 (question, answers) 必须映射
- 支持"-- 不导入--"和"-- 自动生成--"选项

### TC-06: 导入执行
**步骤**:
1. 完成字段映射
2. 点击 "开始导入"

**期望结果**:
- 显示导入进度条
- 导入完成后显示成功/失败统计
- 可以查看错误详情

---

## 后端测试用例

### TC-07: 文件上传 API
**请求**:
```bash
POST /api/qa/groups/{group_id}/items/import/upload
Content-Type: multipart/form-data

file: [xlsx文件]
```

**期望结果**:
```json
{
  "success": true,
  "file_path": "/minio/qa-raw-files/...",
  "minio_prefix": "qa_data/group_1/...",
  "saved_files": [...],
  "storage_type": "minio"
}
```

### TC-08: 预览 API
**请求**:
```bash
POST /api/qa/groups/{group_id}/items/import/preview
Content-Type: application/json

{
  "file_path": "/minio/qa-raw-files/...",
  "minio_prefix": "qa_data/group_1/...",
  "saved_files": [...],
  "preview_rows": 5
}
```

**期望结果**:
```json
{
  "success": true,
  "preview": {
    "file_path": "...",
    "total_records": 100,
    "preview_rows": [
      {"问题": "...", "答案": "...", ...}
    ],
    "columns": ["问题", "答案", "上下文", ...],
    "suggestions": {
      "question": "问题",
      "answers": "答案",
      ...
    }
  }
}
```

### TC-09: 导入执行 API
**请求**:
```bash
POST /api/qa/groups/{group_id}/items/import/execute
Content-Type: application/json

{
  "file_path": "/minio/qa-raw-files/...",
  "mapping": {
    "question": "问题",
    "answers": "答案",
    "context": "上下文"
  },
  "options": {
    "batch_size": 1000,
    "skip_rows": 0
  }
}
```

**期望结果**:
```json
{
  "success": true,
  "task_id": "import_xxx",
  "message": "导入任务已启动"
}
```

### TC-10: 多 Sheet 处理
**步骤**:
1. 上传包含多个 sheet 的 xlsx 文件
2. 调用预览和导入 API

**期望结果**:
- 只读取第一个 sheet
- 其他 sheet 被忽略

### TC-11: 空值处理
**步骤**:
1. 上传包含空单元格的 xlsx 文件
2. 执行导入

**期望结果**:
- 空单元格转换为 None/null
- 不会导致导入失败

### TC-12: 大数据量
**步骤**:
1. 上传包含 10000+ 行的 xlsx 文件
2. 执行导入

**期望结果**:
- 分批处理，不会内存溢出
- 进度回调正常
- 导入成功

---

## 回归测试

### TC-13: 原有功能不受影响
**步骤**:
1. 测试 HuggingFace 数据集导入
2. 测试 JSON/JSONL 文件导入

**期望结果**:
- 原有功能正常工作
- 不会引入回归 bug

---

## 边界测试

### TC-14: 空文件
**步骤**: 上传空的 xlsx 文件

**期望结果**: 提示 "文件为空" 或 "无数据"

### TC-15: 只有表头的文件
**步骤**: 上传只有表头没有数据的 xlsx 文件

**期望结果**: 提示 "无数据记录"

### TC-16: 特殊字符
**步骤**: 上传包含特殊字符（emoji、中文标点等）的 xlsx 文件

**期望结果**: 正常导入，字符不丢失

### TC-17: 超长文本
**步骤**: 上传包含超长文本（>10000字符）的 xlsx 文件

**期望结果**: 正常导入，文本截断或存储成功

---

## 测试执行命令

### 快速测试 xlsx 功能
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator
python3 test_xlsx_simple.py
```

### 完整功能测试（需要数据库）
```bash
# 启动后端
python app.py --debug

# 使用 curl 测试 API
curl -X POST http://localhost:5001/api/qa/groups/1/items/import/upload \
  -F "file=@test.xlsx"
```

---

## 已知限制

1. 只读取第一个 sheet，其他 sheet 被忽略
2. 表头必须在第一行
3. 日期类型会被转换为字符串
4. 公式单元格会被计算后导入

---

*文档版本: 1.0*  
*最后更新: 2026-03-17*
