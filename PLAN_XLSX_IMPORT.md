# 功能开发计划：XLSX 导入问答对数据

> 创建时间: 2026-03-17  
> 任务: 支持从 Excel (.xlsx) 文件导入问答对数据

---

## 需求概述

在现有的 HuggingFace 数据集导入功能基础上，新增支持从 **Excel (.xlsx)** 文件导入问答对数据。

---

## 实施计划

### 阶段一：前端修改

#### 1.1 修改提示文本
**文件**: `frontend/src/views/qa/QAImport.vue`

- 修改第 52 行的提示文本：
```vue
<!-- 修改前 -->
<p class="step-desc">请选择 HuggingFace 数据集文件夹或单个数据文件</p>

<!-- 修改后 -->
<p class="step-desc">请选择 HuggingFace 数据集文件夹或单个数据文件或xlsx文件</p>
```

#### 1.2 新增上传模式选项
**文件**: `frontend/src/views/qa/QAImport.vue`

- 修改上传模式切换（约第 55-59 行）：
```vue
<!-- 修改前 -->
<el-radio-group v-model="uploadMode" class="upload-mode">
  <el-radio-button label="folder">📁 选择文件夹</el-radio-button>
  <el-radio-button label="file">📄 选择文件</el-radio-button>
</el-radio-group>

<!-- 修改后 -->
<el-radio-group v-model="uploadMode" class="upload-mode">
  <el-radio-button label="folder">📁 选择文件夹</el-radio-button>
  <el-radio-button label="file">📄 选择文件</el-radio-button>
  <el-radio-button label="xlsx">📊 选择xlsx文件</el-radio-button>
</el-radio-group>
```

#### 1.3 修改上传区域逻辑
**文件**: `frontend/src/views/qa/QAImport.vue`

- 修改文件上传区域显示逻辑：
```vue
<!-- 动态显示上传提示 -->
<div class="upload-text">
  {{ uploadMode === 'folder' ? '点击选择文件夹，或拖拽到此处' : 
     uploadMode === 'xlsx' ? '点击选择xlsx文件，或拖拽到此处' : 
     '点击选择文件，或拖拽到此处' }}
</div>
<div class="upload-hint">
  {{ uploadMode === 'xlsx' ? '支持 xlsx 格式' : '支持 JSON, JSONL, CSV, Parquet 格式' }}
</div>
```

#### 1.4 修改文件输入框
**文件**: `frontend/src/views/qa/QAImport.vue`

- 修改 `fileInputRef` 的 accept 属性（当 uploadMode === 'xlsx' 时）：
```vue
<input
  ref="fileInputRef"
  type="file"
  class="file-input"
  :webkitdirectory="uploadMode === 'folder'"
  :directory="uploadMode === 'folder'"
  :multiple="uploadMode === 'file'"
  :accept="uploadMode === 'xlsx' ? '.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : ''"
  @change="handleFileSelect"
/>
```

#### 1.5 新增 xlsx 文件处理逻辑
**文件**: `frontend/src/views/qa/QAImport.vue`

- 修改 `handleFileSelect` 和 `handleDrop` 方法，处理 xlsx 文件类型校验
- 校验文件扩展名为 .xlsx
- 校验通过后设置 `uploadedFilePath` 和 `selectedFiles`

#### 1.6 预览 xlsx 数据
**文件**: `frontend/src/views/qa/QAImport.vue`

- 复用现有的 preview 逻辑，但需要确保后端支持 xlsx 格式
- 预览时展示 xlsx 第一个 sheet 的前 5 行
- 已有 `previewDataset` API 调用，需要确保 file_type 参数传递为 'xlsx'

#### 1.7 字段映射页面
**文件**: `frontend/src/views/qa/QAImport.vue`

- 字段映射逻辑复用现有实现
- 目标字段参考 `ai_qa_data` 表：
  - `question` (必填) - 问题文本
  - `answers` (必填) - 答案
  - `context` - 上下文
  - `question_type` - 问题类型
  - `source_dataset` - 源数据集
  - `language` - 语言
  - `difficulty_level` - 难度等级
  - `category` - 分类
  - `sub_category` - 子分类
  - `tags` - 标签
  - `fixed_metadata` - 固定元数据
  - `dynamic_metadata` - 动态元数据

---

### 阶段二：后端修改

#### 2.1 支持 xlsx 文件上传
**文件**: `src/flask_funcs/qa_data.py`

- 在 `/api/qa/groups/<int:group_id>/items/import` 接口中
- 修改文件格式校验，支持 'xlsx' 类型
- 上传逻辑保持不变，将 xlsx 文件存入 MinIO `qa-raw-files` 桶

#### 2.2 新增 xlsx 预览功能
**文件**: `src/flask_funcs/qa_data.py`

- 修改 `/api/qa/groups/<int:group_id>/items/import/preview` 接口
- 当检测到文件类型为 xlsx 时：
  1. 从 MinIO 下载文件到临时目录
  2. 使用 `pandas` 或 `openpyxl` 读取第一个 sheet
  3. 获取列名和前 5 行数据
  4. 按现有 preview 格式返回

新增依赖：
```bash
pip install pandas openpyxl
```

示例代码：
```python
import pandas as pd

def preview_xlsx_file(file_path, preview_rows=5):
    """预览 xlsx 文件内容"""
    df = pd.read_excel(file_path, sheet_name=0, nrows=preview_rows)
    columns = df.columns.tolist()
    preview_rows_data = df.head(preview_rows).to_dict('records')
    
    # 获取总行数（需要读取全部）
    total_df = pd.read_excel(file_path, sheet_name=0, usecols=[0])
    total_records = len(total_df)
    
    return {
        'columns': columns,
        'preview_rows': preview_rows_data,
        'total_records': total_records,
        'file_path': file_path
    }
```

#### 2.3 支持 xlsx 数据导入
**文件**: `src/flask_funcs/qa_data.py` 或相关 CRUD 模块

- 修改导入执行逻辑
- 当文件类型为 xlsx 时：
  1. 从 MinIO 下载文件到临时目录
  2. 使用 pandas 读取整个 sheet
  3. 根据字段映射配置转换数据
  4. 批量插入到 `ai_qa_data` 表

---

### 阶段三：API 模块修改

#### 3.1 修改前端 API 调用
**文件**: `frontend/src/api/qa.ts`

- 确保 `previewDataset` 和 `importDataset` 函数支持传递 `file_type: 'xlsx'`
- 可能需要新增 `file_type` 参数到请求体

---

## 文件修改清单

### 前端文件
| 文件路径 | 修改内容 |
|----------|----------|
| `frontend/src/views/qa/QAImport.vue` | 1. 修改提示文本<br>2. 新增 xlsx 上传模式<br>3. 修改文件选择逻辑<br>4. 新增 xlsx 文件校验 |
| `frontend/src/api/qa.ts` | 新增 file_type 参数支持 |

### 后端文件
| 文件路径 | 修改内容 |
|----------|----------|
| `src/flask_funcs/qa_data.py` | 1. 支持 xlsx 文件上传<br>2. 新增 xlsx 预览逻辑<br>3. 新增 xlsx 导入逻辑 |
| `requirements.txt` | 新增 pandas, openpyxl 依赖 |

---

## 数据库表结构参考

### ai_qa_data 表字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | SERIAL | ✅ | 主键 |
| group_id | INTEGER | ✅ | 所属分组ID |
| question | TEXT | ✅ | 问题文本 |
| answers | JSONB | ✅ | 答案，支持字符串或字典格式 |
| context | TEXT | ❌ | 上下文/背景信息 |
| question_type | VARCHAR | ❌ | 问题类型 |
| source_dataset | VARCHAR | ❌ | 源数据集名称 |
| hf_dataset_id | VARCHAR | ❌ | HuggingFace ID |
| language | VARCHAR | ❌ | 语言，默认'zh' |
| difficulty_level | INTEGER | ❌ | 难度等级 1-10 |
| category | VARCHAR | ❌ | 分类 |
| sub_category | VARCHAR | ❌ | 子分类 |
| tags | JSONB | ❌ | 标签列表 |
| fixed_metadata | JSONB | ❌ | 固定元数据 |
| dynamic_metadata | JSONB | ❌ | 动态元数据 |
| created_at | TIMESTAMP | ✅ | 创建时间 |
| updated_at | TIMESTAMP | ✅ | 更新时间 |

---

## 测试计划

### 功能测试
1. 上传有效的 xlsx 文件，验证能否正确识别
2. 上传无效的 xlsx 文件（如损坏文件），验证错误提示
3. 验证预览功能，确保显示前 5 行数据
4. 验证字段映射功能
5. 验证导入功能，检查数据是否正确写入数据库
6. 测试大文件导入（性能测试）

### 边界测试
1. 空 xlsx 文件
2. xlsx 文件只有一个 sheet
3. xlsx 文件有多个 sheet（确保只读取第一个）
4. xlsx 文件包含特殊字符
5. xlsx 文件列名与目标字段完全匹配/部分匹配/完全不匹配

---

## 预估工时

| 阶段 | 任务 | 预估时间 |
|------|------|----------|
| 前端 | 修改提示文本、上传模式、文件选择 | 2h |
| 前端 | 预览和字段映射逻辑调整 | 1h |
| 后端 | xlsx 预览功能实现 | 2h |
| 后端 | xlsx 导入功能实现 | 2h |
| 测试 | 功能测试和调试 | 2h |
| **总计** | | **9h** |

---

## 下一步行动

确认计划后，按以下顺序执行：

1. ✅ 用户确认计划
2. 🔄 开始前端修改（QAImport.vue）
3. 🔄 后端 xlsx 预览功能
4. 🔄 后端 xlsx 导入功能
5. 🔄 联调测试

---

*计划创建时间: 2026-03-17*  
*状态: ✅ 已完成*
