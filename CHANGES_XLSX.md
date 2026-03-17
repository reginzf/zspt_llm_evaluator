# XLSX 导入功能 - 代码变更汇总

> 变更时间: 2026-03-17  
> 功能: 支持从 Excel (.xlsx) 文件导入问答对数据

---

## 变更文件列表

### 1. 前端修改

#### `frontend/src/views/qa/QAImport.vue`
**修改内容**:
1. ✅ 修改提示文本（第52行）
   - 从: "请选择 HuggingFace 数据集文件夹或单个数据文件"
   - 到: "请选择 HuggingFace 数据集文件夹或单个数据文件或xlsx文件"

2. ✅ 新增 xlsx 上传模式（第55-59行）
   - 添加 `el-radio-button label="xlsx"` 选项

3. ✅ 修改上传区域图标和文本（第70-80行）
   - 根据 uploadMode 动态显示不同图标和提示文本

4. ✅ 修改文件输入框 accept 属性（第84-92行）
   - xlsx 模式下限制只选择 .xlsx 文件

5. ✅ 修改 uploadMode 类型定义（第282行）
   - 从: `ref<'folder' | 'file'>`
   - 到: `ref<'folder' | 'file' | 'xlsx'>`

6. ✅ 修改 handleFileSelect 方法（第401-416行）
   - 添加 xlsx 文件类型校验

7. ✅ 修改 handleDrop 方法（第418-443行）
   - 添加拖拽时的 xlsx 文件类型校验

---

### 2. 后端修改

#### `src/sql_funs/ai_qa_data_crud_enhanced.py`
**修改内容**:
1. ✅ 修改 `preview_huggingface_dataset` 方法（第138-155行）
   - 添加 xlsx 文件类型检测
   - 检测到 .xlsx 扩展名时调用 `_preview_xlsx_file`

2. ✅ 新增 `_preview_xlsx_file` 方法（第341-390行）
   - 使用 pandas 读取 xlsx 文件第一个 sheet
   - 处理 NaN 值和数据类型转换
   - 返回 DatasetPreview 对象

3. ✅ 修改 `import_with_mapping` 方法（第616-628行）
   - 添加 xlsx 文件类型检测
   - 检测到 .xlsx 扩展名时调用 `_import_xlsx_file`

4. ✅ 新增 `_import_xlsx_file` 方法（第779-860行）
   - 使用 pandas 读取完整 xlsx 文件
   - 逐行转换为 QA 数据格式
   - 批量插入到数据库

---

### 3. 测试文件

#### `test_xlsx_simple.py` (新增)
- 独立的 xlsx 功能测试脚本
- 测试预览和数据转换逻辑
- 不依赖 PostgreSQL

#### `test_xlsx_import.py` (新增)
- 完整的集成测试脚本
- 依赖项目模块和数据库

#### `TEST_CASES_XLSX.md` (新增)
- 完整的测试用例文档
- 包含前端、后端、回归、边界测试

---

## 依赖确认

### requirements.txt 中已存在:
- ✅ `pandas==2.3.3`
- ✅ `openpyxl==3.1.5`

无需额外安装依赖。

---

## API 变更

### 已有 API 支持 xlsx (无需修改)
以下 API 自动支持 xlsx 文件，无需修改：

| API | 路径 | 说明 |
|-----|------|------|
| 上传 | `POST /api/qa/groups/{id}/items/import/upload` | 上传文件到 MinIO |
| 预览 | `POST /api/qa/groups/{id}/items/import/preview` | 预览数据（新增 xlsx 支持）|
| 导入 | `POST /api/qa/groups/{id}/items/import/execute` | 执行导入（新增 xlsx 支持）|

### 前端 API 调用
前端 `uploadQAFile` 和 `previewDataset` 函数无需修改即可支持 xlsx 文件。

---

## 测试验证

### 单元测试
```bash
cd /root/.openclaw/workspace/zspt_llm_evaluator
python3 test_xlsx_simple.py
```

**结果**: ✅ 全部通过
- 预览功能: ✅
- 数据转换: ✅

### 功能测试
需要完整环境进行：
1. 启动后端: `python app.py --debug`
2. 启动前端: `cd frontend && npm run dev`
3. 访问 http://localhost:5173/qa/groups/1/import

---

## 部署说明

### 无需额外配置
- 代码已兼容现有架构
- 依赖已存在于 requirements.txt

### 运行环境要求
- Python >= 3.8
- pandas >= 2.0
- openpyxl >= 3.0

---

## 回滚方案

如需回滚，只需还原以下文件：
```bash
git checkout frontend/src/views/qa/QAImport.vue
git checkout src/sql_funs/ai_qa_data_crud_enhanced.py
```

---

## 后续优化建议

1. **多 Sheet 支持**: 允许用户选择要导入的 sheet
2. **数据验证**: 在预览阶段验证数据格式（如难度等级是否为整数）
3. **进度优化**: 大文件导入时提供更细粒度的进度反馈
4. **模板下载**: 提供标准 xlsx 模板供用户下载

---

*文档版本: 1.0*  
*最后更新: 2026-03-17*
