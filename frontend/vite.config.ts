import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量（支持 .env.development.local 覆盖）
  const env = loadEnv(mode, process.cwd())
  
  // 自动检测后端地址：优先使用环境变量，其次检测服务器 IP
  const detectBackendUrl = () => {
    if (env.VITE_BACKEND_URL) return env.VITE_BACKEND_URL
    
    // 尝试获取本机 IP（用于服务器部署）
    // 生产环境应该明确设置 VITE_BACKEND_URL
    return 'http://127.0.0.1:5001'
  }
  
  const backendUrl = detectBackendUrl()
  console.log(`[Vite Proxy] Backend URL: ${backendUrl}`)

  return {
    plugins: [
      vue(),
      vueDevTools(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    server: {
      port: 5173,
      host: '0.0.0.0',  // 允许从任意 IP 访问
      proxy: {
        // 代理 API 请求到 Flask 后端
        '^/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 代理后端 API 路由（排除纯页面路由）
        '^/local_knowledge/': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 知识库详情相关 API（排除页面路由 /local_knowledge_detail/:id/:name）
        '^/local_knowledge_detail/sync': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/local_knowledge_detail/question': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/local_knowledge_detail/question_set': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/local_knowledge_detail/task': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/local_knowledge_detail/label_studio': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/local_knowledge_doc': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 环境相关 API
        '^/environment/': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/environment_detail_list': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 知识库 API
        '^/knowledge_base/': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/label_studio_env': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 标注任务 API
        '^/annotation_tasks': {
          target: backendUrl,
          changeOrigin: true,
        },
        // QA 相关 API（排除页面路由 /qa/groups, /qa/groups/:id, /qa/groups/:id/import）
        '^/qa/groups$': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/api/qa/': {
          target: backendUrl,
          changeOrigin: true,
        },
        // LLM 相关 API
        '^/llm/': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 报告相关 API（注意：排除 /report_list 前端路由）
        '^/report/': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 报告列表数据 API
        '^/report_list/data': {
          target: backendUrl,
          changeOrigin: true,
        },
        // 静态文件（Flask 后端提供的静态资源）
        '^/static': {
          target: backendUrl,
          changeOrigin: true,
        },
        // Flask 后端生成的 CSS/JS 文件路由
        '^/css': {
          target: backendUrl,
          changeOrigin: true,
        },
        '^/js': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
    },
  }
})
