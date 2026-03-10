import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
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
      // 代理 API 请求到 Flask 后端（使用 ^ 精确匹配 API 路径）
      '^/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 代理后端 API 路由（排除纯页面路由）
      '^/local_knowledge/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 知识库详情相关 API（排除页面路由 /local_knowledge_detail/:id/:name）
      '^/local_knowledge_detail/sync': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/local_knowledge_detail/question': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/local_knowledge_detail/question_set': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/local_knowledge_detail/task': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/local_knowledge_detail/label_studio': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/local_knowledge_doc': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 环境相关 API
      '^/environment/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/environment_detail_list': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 知识库 API
      '^/knowledge_base/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/label_studio_env': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 标注任务 API
      '^/annotation_tasks': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // QA 相关 API（排除页面路由 /qa/groups, /qa/groups/:id, /qa/groups/:id/import）
      '^/qa/groups$': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/api/qa/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // LLM 相关 API
      '^/llm/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 报告相关 API（注意：排除 /report_list 前端路由）
      '^/report/': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 报告列表数据 API
      '^/report_list/data': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // 静态文件（Flask 后端提供的静态资源）
      '^/static': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      // Flask 后端生成的 CSS/JS 文件路由
      '^/css': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '^/js': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
