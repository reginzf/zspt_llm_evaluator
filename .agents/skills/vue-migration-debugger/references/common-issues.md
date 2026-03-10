# 常见问题及解决方案

## 1. API 路由问题

### 1.1 404 Not Found
**现象**：请求返回 404
**排查**：
1. 检查前端调用的 URL 是否与后端 `@route` 定义匹配
2. 检查是否有 `/api` 前缀遗漏
3. 检查 URL 参数是否正确传递

**案例**：
```typescript
// ❌ 前端
await legacyPost('/local_knowledge_detail', { kno_id, kno_name })
// 后端
@local_knowledge_detail_bp.route('/api/local_knowledge_detail', methods=['POST'])

// ✅ 修复
await legacyPost('/api/local_knowledge_detail', { kno_id, kno_name })
```

### 1.2 405 Method Not Allowed
**现象**：PUT/DELETE 请求返回 405
**原因**：
1. Flask CORS 配置未包含该路由
2. 前端使用的 HTTP 方法与后端不匹配

**解决**：
```python
# app.py 添加 CORS 配置
CORS(app, resources={
    r"/local_knowledge_detail/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})
```

### 1.3 前端代理问题（开发模式）
**现象**：访问 `http://localhost:5173/xxx` 跳转到 `http://127.0.0.1:5001/xxx`
**原因**：`vite.config.ts` 中代理配置匹配了页面路由

**解决**：
```typescript
// vite.config.ts
proxy: {
  // ❌ 错误：匹配了页面路由
  '/local_knowledge': { target: 'http://127.0.0.1:5001' },
  
  // ✅ 正确：只匹配 API 路由
  '^/local_knowledge/': { target: 'http://127.0.0.1:5001' },
}
```

## 2. 数据格式问题

### 2.1 后端期望表单，前端发送 JSON
**现象**：500 错误，后端获取不到参数
**案例**：
```python
# ❌ 后端
knol_describe = request.form.get('knol_describe')  # None

# ✅ 修复后端支持两种格式
if request.is_json:
    data = request.get_json()
    knol_describe = data.get('kno_describe')
else:
    knol_describe = request.form.get('knol_describe')
```

### 2.2 响应格式不匹配
**现象**：列表显示 "No Data"，但 API 返回了数据
**案例**：
```python
# ❌ 后端直接返回数组
return jsonify(file_list)

# ✅ 应该返回标准格式
return jsonify({
    'success': True,
    'data': file_list
})
```

### 2.3 字段名不一致
**现象**：数据保存成功但字段为空
**案例**：
```typescript
// 前端发送
{ "kno_describe": "描述" }

// 后端接收
request.form.get('knol_describe')  // 字段名不一致！
```

## 3. 数据库字段索引错误

**现象**：500 错误，提示 `'list' object has no attribute 'isoformat'`
**原因**：数据库查询结果的字段索引错误

**案例**：
```python
# ❌ 错误索引
'created_at': item[10].isoformat()  # 实际是第6列

# ✅ 正确索引（根据表结构）
# ai_local_knowledge 表结构:
# 0: id, 1: kno_id, 2: kno_name, 3: kno_describe, 4: kno_path, 5: ls_status
# 6: created_at, 7: updated_at, 8: knowledge_domain, 9: domain_description
# 10: required_background, 11: required_skills
'created_at': item[6].isoformat() if item[6] else None
```

## 4. HTTP 客户端选择

**现象**：404/405 错误，路由正确但无法访问
**原因**：使用了错误的 HTTP 客户端

```typescript
// api/index.ts 定义了两个客户端
const apiClient = axios.create({ baseURL: '/api' })      // 带 /api 前缀
const legacyClient = axios.create({ baseURL: '/' })      // 不带前缀

// ❌ 错误：使用 apiClient 访问非 /api 路由
await apiClient.post('/local_knowledge/upload', formData)
// 实际请求：POST /api/local_knowledge/upload （404）

// ✅ 正确：使用 legacyClient
await legacyPost('/local_knowledge/upload', formData)
// 实际请求：POST /local_knowledge/upload （200）
```

## 5. CORS 配置遗漏

**常见遗漏路由：**
```python
# app.py 中需要配置的路由
CORS(app, resources={
    r"/api/*": { ... },                    # API 路由
    r"/local_knowledge/*": { ... },        # 知识库路由
    r"/local_knowledge_detail/*": { ... }, # 知识库详情路由
    r"/local_knowledge_doc/*": { ... },    # 知识库文件路由（容易遗漏！）
    r"/local_knowledge/upload": { ... },   # 上传路由（具体路径）
})
```

## 6. 字段缺失问题

**现象**：编辑表单缺少某些字段
**原因**：Vue 代码未从老代码中完整迁移字段

**检查清单：**
- [ ] 表单 `reactive` 对象定义了所有字段
- [ ] `showEditDialog` 函数填充了所有字段
- [ ] `handleEditSubmit` 函数提交了所有字段
- [ ] 后端 API 接收并保存了所有字段

## 7. 重复请求问题

**现象**：同一个接口被调用多次
**原因**：多个 `onMounted` 或 `watch` 触发

**解决**：
```typescript
// ❌ 错误：两个独立的加载函数调用同一个 API
onMounted(() => {
  loadKnowledgeDetail()  // GET /api/xxx
  loadFileList()         // GET /api/xxx （重复！）
})

// ✅ 正确：合并为一个请求
async function loadFileList() {
  const res = await getKnowledgeFiles(...)
  fileList.value = res.data || []
  // 同时提取知识库信息
  setKnowledgeFromFiles(fileList.value)
}
```
