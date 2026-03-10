# 页面路由映射表

## 完整路由 → 代码文件对照

### 首页
| 类型 | 路径 |
|-----|------|
| 路由 | `/` |
| Vue 组件 | `frontend/src/views/Home.vue` |
| 后端路由 | `src/flask_funcs/home.py` |
| 老模板 | `src/flask_funcs/reports/templates/home.html` |

### QA 数据管理
| 类型 | 路径 |
|-----|------|
| 路由 | `/qa` |
| Vue 组件 | `frontend/src/views/qa/QAGroupList.vue` |
| 后端路由 | `src/flask_funcs/qa_data_group.py` |
| 老模板 | `src/flask_funcs/reports/templates/qa_groups.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/qa_groups.js`, `qa_groups_optimized.js` |

### QA 分组详情
| 类型 | 路径 |
|-----|------|
| 路由 | `/qa/:groupId` |
| Vue 组件 | `frontend/src/views/qa/QAGroupDetail.vue` |
| 后端路由 | `src/flask_funcs/qa_data.py` |
| 老模板 | `src/flask_funcs/reports/templates/qa_group_detail.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/qa_group_detail.js` |

### LLM 模型列表
| 类型 | 路径 |
|-----|------|
| 路由 | `/llm` |
| Vue 组件 | `frontend/src/views/llm/LLMModelList.vue` |
| 后端路由 | `src/flask_funcs/llm_model_routes.py` |
| 老模板 | `src/flask_funcs/reports/templates/llm_models.html` |

### LLM 模型详情
| 类型 | 路径 |
|-----|------|
| 路由 | `/llm/:id` |
| Vue 组件 | `frontend/src/views/llm/LLMModelDetail.vue` |
| 后端路由 | `src/flask_funcs/llm_model_routes.py` |
| 老模板 | `src/flask_funcs/reports/templates/llm_model_detail.html` |

### 知识库列表
| 类型 | 路径 |
|-----|------|
| 路由 | `/knowledge` |
| Vue 组件 | `frontend/src/views/knowledge/KnowledgeList.vue` |
| 后端路由 | `src/flask_funcs/local_knowledge.py` |
| 老模板 | `src/flask_funcs/reports/templates/local_knowledge.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/local_knowledge.js` |

### 知识库详情
| 类型 | 路径 |
|-----|------|
| 路由 | `/knowledge/:id` |
| Vue 组件 | `frontend/src/views/knowledge/KnowledgeDetail.vue` |
| 后端路由 | `src/flask_funcs/local_knowledge_detail.py`, `local_knowledge_detail_*.py` |
| 老模板 | `src/flask_funcs/reports/templates/local_knowledge_detail*.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/local_knowledge_detail*.js` |

### 环境管理
| 类型 | 路径 |
|-----|------|
| 路由 | `/environment` |
| Vue 组件 | `frontend/src/views/environment/EnvironmentList.vue` |
| 后端路由 | `src/flask_funcs/environment.py` |
| 老模板 | `src/flask_funcs/reports/templates/environment.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/environment.js` |
| 老详情模板 | `src/flask_funcs/reports/templates/environment_detail.html` |

### Label Studio 环境
| 类型 | 路径 |
|-----|------|
| 路由 | `/label-studio` |
| Vue 组件 | `frontend/src/views/environment/LabelStudioEnv.vue` |
| 后端路由 | `src/flask_funcs/label_studio_env.py` |
| 老模板 | `src/flask_funcs/reports/templates/label_studio_env.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/label_studio_env.js` |

### 标注任务
| 类型 | 路径 |
|-----|------|
| 路由 | `/tasks` |
| Vue 组件 | `frontend/src/views/tasks/AnnotationTaskList.vue` |
| 后端路由 | `src/flask_funcs/annotation_tasks.py` |
| 老模板 | `src/flask_funcs/reports/templates/annotation_tasks.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/annotation_tasks.js` |

### 报告列表
| 类型 | 路径 |
|-----|------|
| 路由 | `/reports` |
| Vue 组件 | `frontend/src/views/reports/ReportList.vue` |
| 后端路由 | `src/flask_funcs/report_list.py` |
| 老模板 | `src/flask_funcs/reports/templates/report_list.html` |
| 老 JS | `src/flask_funcs/reports/statics/js/report_list.js` |

## 后端 API 路由文件映射

| API 前缀 | 处理文件 |
|---------|---------|
| `/api/environment/*` | `src/flask_funcs/environment.py` |
| `/api/qa/*` | `src/flask_funcs/qa_data.py`, `qa_data_group.py` |
| `/api/llm/*` | `src/flask_funcs/llm_model_routes.py` |
| `/api/knowledge/*` | `src/flask_funcs/local_knowledge.py` |
| `/local_knowledge/*` | `src/flask_funcs/local_knowledge.py` |
| `/local_knowledge_detail/*` | `src/flask_funcs/local_knowledge_detail.py` |
| `/api/label_studio/*` | `src/flask_funcs/label_studio_env.py` |
| `/api/tasks/*` | `src/flask_funcs/annotation_tasks.py` |
| `/api/reports/*` | `src/flask_funcs/report_list.py` |
| `/api/knowledge_doc/*` | `src/flask_funcs/knowledge_doc.py` |
