import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: {
        title: '问答系统召回质量评估报告服务'
      }
    },
    {
      path: '/qa/groups',
      alias: '/qa/groups/',
      name: 'qa-groups',
      component: () => import('@/views/qa/QAGroupList.vue'),
      meta: {
        title: '问答对组管理'
      }
    },
    {
      path: '/qa/groups/:id',
      name: 'qa-group-detail',
      component: () => import('@/views/qa/QAGroupDetail.vue'),
      meta: {
        title: '问答对组详情'
      }
    },
    {
      path: '/qa/groups/:id/import',
      name: 'qa-import',
      component: () => import('@/views/qa/QAImport.vue'),
      meta: {
        title: '导入问答对'
      }
    },
    {
      path: '/llm/models',
      alias: '/llm/models/',
      name: 'llm-models',
      component: () => import('@/views/llm/ModelList.vue'),
      meta: {
        title: 'LLM模型管理'
      }
    },
    {
      path: '/llm/models/:name',
      name: 'llm-model-detail',
      component: () => import('@/views/llm/ModelDetail.vue'),
      meta: {
        title: '模型详情'
      }
    },
    {
      path: '/llm/reports/:id',
      name: 'llm-evaluation-report',
      component: () => import('@/views/llm/EvaluationReport.vue'),
      meta: {
        title: '评估报告'
      }
    },
    {
      path: '/local_knowledge',
      alias: ['/local_knowledge/', '/localKnowledge'],
      name: 'local-knowledge',
      component: () => import('@/views/knowledge/KnowledgeList.vue'),
      meta: {
        title: '知识库管理'
      }
    },
    {
      path: '/local_knowledge_detail/:kno_id/:kno_name',
      name: 'knowledge-detail',
      component: () => import('@/views/knowledge/KnowledgeDetail.vue'),
      meta: {
        title: '知识库详情'
      }
    },
    {
      path: '/environment',
      alias: '/environment/',
      name: 'environment',
      component: () => import('@/views/environment/EnvironmentList.vue'),
      meta: {
        title: '环境管理'
      }
    },
    {
      path: '/environment_detail',
      alias: '/environment_detail/',
      name: 'environment-detail',
      component: () => import('@/views/environment/EnvironmentDetail.vue'),
      meta: {
        title: '环境详情'
      }
    },
    {
      path: '/label_studio_env',
      alias: '/label_studio_env/',
      name: 'label-studio-env',
      component: () => import('@/views/environment/LabelStudioEnv.vue'),
      meta: {
        title: 'Label-Studio环境'
      }
    },
    {
      path: '/annotation_tasks',
      alias: '/annotation_tasks/',
      name: 'annotation-tasks',
      component: () => import('@/views/annotation/TaskList.vue'),
      meta: {
        title: '标注任务管理'
      }
    },
    {
      path: '/report_list',
      alias: '/report_list/',
      name: 'report-list',
      component: () => import('@/views/report/ReportList.vue'),
      meta: {
        title: '评估报告列表'
      }
    },
    // 开发测试页面（仅开发环境使用）
    {
      path: '/components-test',
      name: 'components-test',
      component: () => import('@/views/ComponentsTestView.vue'),
      meta: {
        title: '组件测试',
        hidden: true
      }
    },
    // 404 页面
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: {
        title: '页面不存在'
      }
    }
  ],
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = title + ' - AI-KEN'
  }
  next()
})

export default router
