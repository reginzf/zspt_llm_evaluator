# 前后端路由检查报告

## 生成时间
2026-03-06

## 1. CORS 配置缺失的路由

以下路由在 Flask 中注册，但 CORS 配置中未包含：

| 路由前缀 | 涉及的蓝图 | 风险等级 |
|---------|-----------|---------|
| `/report_list/*` | report_list_bp | 🟡 中 |
| `/knowledge_base/*` | knowledge_base_bp | 🟡 中 |
| `/local_knowledge_doc/*` | local_knowledge_detail_bp | 🔴 高 |
| `/annotation_tasks/*` | annotation_tasks_bp | 🟡 中 |
| `/llm/*` (页面路由) | llm_model_bp | 🟢 低 |
| `/qa/*` (页面路由) | qa_data_bp | 🟢 低 |
| `/local_knowledge_detail/task/*` | local_knowledge_detail_task_bp | 🟡 中 |
| `/local_knowledge_detail/label_studio/*` | local_knowledge_label_studio_bp | 🟡 中 |
| `/environment_detail/*` | environment_bp | 🟡 中 |

## 2. 前端 API 调用检查

### 2.1 已验证匹配的调用
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /local_knowledge/list` | `@route('/local_knowledge/list')` | ✅ |
| `POST /local_knowledge/create` | `@route('/local_knowledge/create')` | ✅ |
| `POST /local_knowledge/edit` | `@route('/local_knowledge/edit')` | ✅ |
| `DELETE /local_knowledge/delete/${knoId}` | `@route('/local_knowledge/delete/<kno_id>')` | ✅ |
| `POST /api/local_knowledge_detail` | `@route('/api/local_knowledge_detail')` | ✅ |
| `GET /local_knowledge/bindings/${knoId}` | `@route('/local_knowledge/bindings/<kno_id>')` | ✅ |
| `POST /local_knowledge/bind` | `@route('/local_knowledge/bind')` | ✅ |
| `POST /local_knowledge_detail/sync` | `@route('/local_knowledge_detail/sync')` | ✅ |
| `PUT /local_knowledge_doc/edit/${knolId}` | `@route('/local_knowledge_doc/edit/<knol_id>')` | ⚠️ 需CORS |
| `DELETE /local_knowledge_doc/delete/${knolId}` | `@route('/local_knowledge_doc/delete/<knol_id>')` | ⚠️ 需CORS |
| `GET /label_studio_env/list/` | `@route('/label_studio_env/list/')` | ✅ |
| `POST /label_studio_env/create/` | `@route('/label_studio_env/create/')` | ✅ |
| `PUT /label_studio_env/update/` | `@route('/label_studio_env/update/')` | ✅ |
| `DELETE /label_studio_env/delete/` | `@route('/label_studio_env/delete/')` | ✅ |
| `GET /environment/list/` | `@route('/environment/list/')` | ✅ |
| `POST /environment/create/` | `@route('/environment/create/')` | ✅ |
| `PUT /environment/update/` | `@route('/environment/update/')` | ✅ |
| `DELETE /environment/delete/` | `@route('/environment/delete/')` | ✅ |

### 2.2 疑似问题调用

| 前端调用 | 问题描述 |
|---------|---------|
| `legacyDel('/local_knowledge_doc/delete/', { data: {...} })` | DELETE 请求带 body，部分服务器不支持 |
| `legacyDel('/label_studio_env/delete/', { data: {...} })` | DELETE 请求带 body |
| `legacyDel('/annotation/tasks/delete', { data: {...} })` | DELETE 请求带 body |

## 3. 推荐的 CORS 配置更新

```python
CORS(app, resources={
    # 已配置的路由...
    
    # 新增：知识库文件操作
    r"/local_knowledge_doc/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    },
    
    # 新增：知识库任务
    r"/local_knowledge_detail/task/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    },
    
    # 新增：知识库 Label Studio
    r"/local_knowledge_detail/label_studio/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    },
    
    # 新增：报告列表
    r"/report_list/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"]
    },
    
    # 新增：知识库管理
    r"/knowledge_base/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    },
    
    # 新增：标注任务
    r"/annotation_tasks/*": {
        "origins": ["http://localhost:5001", "http://127.0.0.1:5001", "http://localhost:5173"],
        "methods": ["GET", "OPTIONS"]
    },
})
```

## 4. 数据格式潜在问题

### 4.1 已修复的问题
- [x] `local_knowledge/list` 返回格式改为 `{success, data}`
- [x] `local_knowledge_doc/edit` 支持 JSON 和表单格式
- [x] 数据库字段索引修正

### 4.2 需要检查的后端 API

| API | 检查项 |
|-----|-------|
| `/local_knowledge_detail/question/*` | 是否返回标准 `{success, data}` 格式 |
| `/local_knowledge_detail/task/*` | 是否返回标准 `{success, data}` 格式 |
| `/local_knowledge_detail/label_studio/*` | 是否返回标准 `{success, data}` 格式 |

## 5. 建议的修复步骤

1. **高优先级**：添加 `/local_knowledge_doc/*` 到 CORS 配置
2. **中优先级**：添加其他缺失的路由到 CORS 配置
3. **低优先级**：统一所有后端 API 返回格式为 `{success, data}`
