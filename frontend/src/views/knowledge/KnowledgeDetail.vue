<template>
  <div class="page-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><Back /></el-icon>
            </el-button>
            <h2>{{ knowledge?.kno_name }}</h2>
          </div>
          <el-tag :type="getStatusType(knowledge?.ls_status)">{{ getStatusLabel(knowledge?.ls_status) }}</el-tag>
        </div>
      </template>

      <!-- 知识库基本信息 -->
      <el-descriptions :column="3" border class="knowledge-info">
        <el-descriptions-item label="知识库ID">{{ knowledge?.kno_id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ knowledge?.kno_name }}</el-descriptions-item>
        <el-descriptions-item label="路径">{{ knowledge?.kno_path }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">{{ knowledge?.kno_describe || '暂无描述' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" class="detail-tabs" type="border-card">
        <!-- 1. 知识库文件 -->
        <el-tab-pane label="知识库文件" name="files" lazy>
          <div class="tab-actions">
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon><Upload /></el-icon>上传文件
            </el-button>
          </div>
          <el-table :data="fileList || []" stripe border v-loading="loadingFiles">
            <el-table-column prop="kno_name" label="文件名称" min-width="150" />
            <el-table-column prop="kno_describe" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="ls_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getFileStatusType(row.ls_status)">{{ getFileStatusLabel(row.ls_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="knol_path" label="路径" min-width="200" show-overflow-tooltip />
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="editFile(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteFile(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 2. 知识库绑定 -->
        <el-tab-pane label="知识库绑定" name="bindings" lazy>
          <div class="tab-actions">
            <el-button type="primary" @click="showBindDialog = true">绑定知识库</el-button>
          </div>
          <el-empty v-if="bindings.length === 0" description="暂无绑定知识库" />
          <div v-else class="binding-list">
            <el-card v-for="binding in bindings" :key="binding.knowledge_id" class="binding-item" shadow="hover">
              <div class="binding-content">
                <div class="binding-info">
                  <div><strong>知识库:</strong> {{ binding.knowledge_name || binding.knowledge_id }}</div>
                  <div><strong>ID:</strong> {{ binding.knowledge_id }}</div>
                  <div>
                    <strong>状态:</strong>
                    <el-tag :type="getBindStatusType(binding.bind_status)" size="small">
                      {{ getBindStatusLabel(binding.bind_status) }}
                    </el-tag>
                  </div>
                </div>
                <div class="binding-actions">
                  <el-button v-if="binding.bind_status === 2" type="primary" size="small" @click="syncKnowledge(binding)">同步</el-button>
                  <el-button type="danger" size="small" @click="unbindKnowledge(binding)">解绑</el-button>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 3. 问题集 -->
        <el-tab-pane label="问题集" name="questions" lazy>
          <div class="tab-actions">
            <el-button type="primary" @click="showCreateQuestionSetDialog = true">创建问题集</el-button>
          </div>
          <el-empty v-if="questionSets.length === 0" description="暂没问题集" />
          <div v-else class="question-set-list">
            <el-collapse v-model="expandedQuestionSets">
              <el-collapse-item v-for="set in questionSets" :key="set.question_id" :name="set.question_id">
                <template #title>
                  <div class="question-set-header">
                    <span class="question-set-name">{{ set.question_name }}</span>
                    <span class="question-set-meta">ID: {{ set.question_id }} | 类型: {{ set.question_set_type || 'N/A' }}</span>
                    <div class="question-set-actions" @click.stop>
                      <el-button link type="primary" size="small" @click="openCreateQuestionDialog(set)">创建问题</el-button>
                      <el-button link type="primary" size="small" @click="editQuestionSet(set)">编辑</el-button>
                      <el-button link type="danger" size="small" @click="deleteQuestionSet(set)">删除</el-button>
                    </div>
                  </div>
                </template>
                <div class="question-list">
                  <!-- 搜索和筛选工具栏 -->
                  <div class="question-toolbar">
                    <el-input
                      v-model="set.searchQuery"
                      placeholder="搜索问题内容"
                      clearable
                      size="small"
                      style="width: 220px"
                      @input="handleSearch(set)"
                    >
                      <template #prefix>
                        <el-icon><Search /></el-icon>
                      </template>
                    </el-input>
                    <el-select
                      v-model="set.filterType"
                      placeholder="问题类型"
                      clearable
                      size="small"
                      style="width: 120px; margin-left: 10px"
                      @change="handleSearch(set)"
                    >
                      <el-option label="事实型" value="factual" />
                      <el-option label="上下文型" value="contextual" />
                      <el-option label="概念型" value="conceptual" />
                      <el-option label="推理型" value="reasoning" />
                      <el-option label="应用型" value="application" />
                    </el-select>
                    <el-button 
                      link 
                      type="primary" 
                      size="small" 
                      style="margin-left: auto"
                      @click="refreshQuestionSet(set)"
                    >
                      <el-icon><Refresh /></el-icon>刷新
                    </el-button>
                  </div>
                  
                  <!-- 问题表格 -->
                  <el-table :data="getPagedQuestions(set)" stripe size="small" v-loading="set.loading">
                    <el-table-column prop="question_type" label="类型" width="100">
                      <template #default="{ row }">
                        <el-tag size="small" :type="getQuestionTypeTag(row.question_type)">
                          {{ row.question_type }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="question_id" label="问题ID" width="150" show-overflow-tooltip />
                    <el-table-column prop="question_content" label="问题正文" min-width="250" show-overflow-tooltip />
                    <el-table-column prop="chunk_ids" label="问题切片" min-width="150" show-overflow-tooltip />
                    <el-table-column label="操作" width="180" fixed="right">
                      <template #default="{ row }">
                        <el-button link type="primary" size="small" @click="showQuestionDetail(row, set.question_set_type)">详情</el-button>
                        <el-button link type="primary" size="small" @click="editQuestion(row, set.question_set_type)">编辑</el-button>
                        <el-button link type="danger" size="small" @click="deleteQuestion(row, set.question_set_type)">删除</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                  
                  <!-- 分页组件 -->
                  <div class="question-pagination" v-if="getFilteredQuestions(set).length > 0">
                    <el-pagination
                      v-model:current-page="set.currentPage"
                      v-model:page-size="set.pageSize"
                      :page-sizes="[5, 10, 20, 50]"
                      :total="getFilteredQuestions(set).length"
                      layout="total, sizes, prev, pager, next"
                      size="small"
                      @size-change="handleSizeChange(set)"
                      @current-change="handleCurrentChange(set)"
                    />
                  </div>
                  
                  <el-empty v-if="!set.questions || set.questions.length === 0" description="暂无问题" />
                  <el-empty v-else-if="getFilteredQuestions(set).length === 0" description="没有匹配的问题" />
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>

        <!-- 4. 标注 -->
        <el-tab-pane label="标注" name="annotations" lazy>
          <div class="tab-actions">
            <el-button type="primary" @click="showBindEnvironmentDialog = true">绑定Label-Studio环境</el-button>
          </div>
          <el-empty v-if="environments.length === 0" description="暂无绑定环境" />
          <div v-else class="environment-list">
            <div v-for="env in environments" :key="env.label_studio_id" class="environment-item">
              <!-- 环境头部 -->
              <div class="environment-header">
                <div class="environment-info">
                  <el-button 
                    link 
                    class="expand-btn" 
                    @click="toggleEnvironment(env)"
                  >
                    <el-icon>
                      <arrow-down v-if="expandedEnvironments.includes(env.label_studio_id)" />
                      <arrow-right v-else />
                    </el-icon>
                    <span class="expand-text">
                      {{ expandedEnvironments.includes(env.label_studio_id) ? '折叠' : '展开' }}
                    </span>
                  </el-button>
                  <span class="env-id">环境ID: {{ env.label_studio_id }}</span>
                  <span class="env-url">{{ env.label_studio_url }}</span>
                  <el-tag size="small" type="info">任务数: {{ env.task_count || 0 }}</el-tag>
                </div>
                <div class="environment-actions">
                  <el-button type="primary" size="small" @click="openCreateTaskDialog(env)">创建任务</el-button>
                  <el-button type="danger" size="small" @click="unbindEnvironment(env)">解绑</el-button>
                </div>
              </div>
              
              <!-- 展开的任务列表 -->
              <div v-if="expandedEnvironments.includes(env.label_studio_id)" class="environment-tasks">
                <el-table 
                  :data="environmentTasks[env.label_studio_id] || []" 
                  stripe 
                  border 
                  size="small"
                  v-loading="loadingEnvironmentTasks[env.label_studio_id]"
                  empty-text="暂无标注任务"
                >
                  <el-table-column prop="task_name" label="任务名称" min-width="150" />
                  <el-table-column prop="knowledge_base_name" label="知识库" width="150" />
                  <el-table-column prop="question_set_name" label="问题集" width="150" />
                  <el-table-column label="进度" width="150">
                    <template #default="{ row }">
                      <el-progress :percentage="getProgress(row)" :format="() => `${row.annotated_chunks || 0}/${row.total_chunks || 0}`" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="task_status" label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="getTaskStatusType(row.task_status)" size="small">{{ row.task_status }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="250" fixed="right">
                    <template #default="{ row }">
                      <el-button link type="primary" size="small" @click="annotateTask(row)">标注</el-button>
                      <el-button link type="primary" size="small" @click="showAnnotationDialog(row)">修改标注方式</el-button>
                      <el-button link type="primary" size="small" @click="syncTask(row)">同步</el-button>
                      <el-button link type="danger" size="small" @click="deleteTask(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 5. 任务 -->
        <el-tab-pane label="任务" name="tasks" lazy>
          <div class="tab-actions">
            <el-button type="primary" @click="openCreateMetricTaskDialog()">创建任务</el-button>
          </div>
          <el-table :data="tasks || []" stripe border v-loading="loadingTasks">
            <el-table-column prop="task_name" label="任务名称" min-width="180" />
            <el-table-column prop="match_type" label="匹配方式" width="150">
              <template #default="{ row }">
                <span>{{ row.match_type === 'chunkTextMatch' ? '切片语义匹配' : (row.match_type === 'chunkIdMatch' ? '切片ID匹配' : row.match_type) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="annotation_type" label="标注类型" width="120" />
            <el-table-column prop="task_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getTaskStatusType(row.task_status)">{{ row.task_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="showCalculationDialog(row)">计算</el-button>
                <el-button link type="primary" size="small" @click="showReportDialog(row)">报告</el-button>
                <el-button link type="danger" size="small" @click="deleteMetricTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 上传文件对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文件" width="500px" @closed="uploadFileList = []">
      <el-upload 
        drag 
        multiple 
        :auto-upload="false" 
        :on-change="handleFileChange" 
        v-model:file-list="uploadFileList"
        ref="uploadRef"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false; uploadFileList = []">取消</el-button>
        <el-button type="primary" @click="uploadFiles" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑文件对话框 -->
    <el-dialog v-model="showEditFileDialog" title="编辑文件描述" width="500px">
      <el-form :model="editFileForm" label-width="80px">
        <el-form-item label="描述">
          <el-input v-model="editFileForm.kno_describe" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditFileDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFileEdit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 绑定知识库对话框 -->
    <el-dialog v-model="showBindDialog" title="绑定知识库" width="500px">
      <el-form :model="bindForm" label-width="100px">
        <el-form-item label="选择环境">
          <el-select v-model="bindForm.envId" @change="loadEnvKnowledgeBases" style="width: 100%">
            <el-option v-for="env in allEnvironments" :key="env.zlpt_base_id" :label="env.zlpt_name" :value="env.zlpt_base_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择知识库">
          <el-select v-model="bindForm.kbId" style="width: 100%" :disabled="!bindForm.envId">
            <el-option v-for="kb in envKnowledgeBases" :key="kb.knowledge_id" :label="kb.knowledge_name" :value="kb.knowledge_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" @click="bindKnowledge" :loading="submitting">绑定</el-button>
      </template>
    </el-dialog>

    <!-- 创建问题集对话框 -->
    <el-dialog v-model="showCreateQuestionSetDialog" title="创建问题集" width="500px">
      <el-form :model="questionSetForm" :rules="questionSetRules" ref="questionSetFormRef" label-width="100px">
        <el-form-item label="名称" prop="question_name">
          <el-input v-model="questionSetForm.question_name" />
        </el-form-item>
        <el-form-item label="类型" prop="question_set_type">
          <el-select v-model="questionSetForm.question_set_type" style="width: 100%">
            <el-option label="基础问题" value="basic" />
            <el-option label="详细问题" value="detailed" />
            <el-option label="机制问题" value="mechanism" />
            <el-option label="主题问题" value="thematic" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateQuestionSetDialog = false">取消</el-button>
        <el-button type="primary" @click="createQuestionSet" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 创建问题对话框 -->
    <el-dialog v-model="showCreateQuestionDialog" title="创建问题" width="600px">
      <el-form :model="questionForm" :rules="questionRules" ref="questionFormRef" label-width="100px">
        <el-form-item label="问题类型" prop="question_type">
          <el-select v-model="questionForm.question_type" style="width: 100%">
            <el-option label="事实型" value="factual" />
            <el-option label="上下文型" value="contextual" />
            <el-option label="概念型" value="conceptual" />
            <el-option label="推理型" value="reasoning" />
            <el-option label="应用型" value="application" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题内容" prop="question_content">
          <el-input v-model="questionForm.question_content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="关联切片">
          <el-input v-model="questionForm.chunk_ids" placeholder="用逗号分隔切片ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateQuestionDialog = false">取消</el-button>
        <el-button type="primary" @click="saveQuestion" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 问题详情对话框 -->
    <el-dialog v-model="showQuestionDetailDialog" title="问题详情" width="600px">
      <el-descriptions :column="1" border v-if="currentQuestion">
        <el-descriptions-item label="问题ID">{{ currentQuestion.question_id }}</el-descriptions-item>
        <el-descriptions-item label="问题类型">{{ currentQuestion.question_type }}</el-descriptions-item>
        <el-descriptions-item label="问题内容">{{ currentQuestion.question_content }}</el-descriptions-item>
        <el-descriptions-item label="关联切片">{{ currentQuestion.chunk_ids || '无' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentQuestion.created_at }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showQuestionDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 编辑问题对话框 -->
    <el-dialog v-model="showEditQuestionDialog" title="编辑问题" width="600px">
      <el-form :model="editQuestionForm" label-width="100px">
        <el-form-item label="问题类型">
          <el-select v-model="editQuestionForm.question_type" style="width: 100%">
            <el-option label="事实型" value="factual" />
            <el-option label="上下文型" value="contextual" />
            <el-option label="概念型" value="conceptual" />
            <el-option label="推理型" value="reasoning" />
            <el-option label="应用型" value="application" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题内容">
          <el-input v-model="editQuestionForm.question_content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="关联切片">
          <el-input v-model="editQuestionForm.chunk_ids" placeholder="用逗号分隔切片ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditQuestionDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEditQuestion" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 绑定Label-Studio环境对话框 -->
    <el-dialog v-model="showBindEnvironmentDialog" title="绑定Label-Studio环境" width="500px">
      <el-form :model="bindEnvForm" label-width="100px">
        <el-form-item label="选择环境">
          <el-select v-model="bindEnvForm.envId" style="width: 100%">
            <el-option v-for="env in availableLabelStudioEnvs" :key="env.label_studio_id" :label="env.label_studio_url" :value="env.label_studio_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindEnvironmentDialog = false">取消</el-button>
        <el-button type="primary" @click="bindEnvironment" :loading="submitting">绑定</el-button>
      </template>
    </el-dialog>

    <!-- 创建标注任务对话框 -->
    <el-dialog v-model="showCreateTaskDialog" title="创建标注任务" width="500px">
      <el-form :model="taskForm" :rules="taskRules" ref="taskFormRef" label-width="100px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="taskForm.task_name" />
        </el-form-item>
        <el-form-item label="Label-Studio环境">
          <el-input v-model="taskForm.env_name" disabled />
        </el-form-item>
        <el-form-item label="问题集" prop="question_set_id">
          <el-select v-model="taskForm.question_set_id" style="width: 100%">
            <el-option v-for="set in questionSets" :key="set.question_id" :label="set.question_name" :value="set.question_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标注类型" prop="annotation_type">
          <el-select v-model="taskForm.annotation_type" style="width: 100%">
            <el-option label="LLM标注" value="llm" />
            <el-option label="人工标注" value="manual" />
            <el-option label="MLB标注" value="mlb" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTask" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 创建指标任务对话框 -->
    <el-dialog v-model="showCreateMetricTaskDialog" title="创建指标任务" width="600px">
      <el-form :model="metricTaskForm" :rules="metricTaskRules" ref="metricTaskFormRef" label-width="100px">
        <el-form-item label="匹配方式" prop="match_type">
          <el-select v-model="metricTaskForm.match_type" style="width: 100%" @change="handleMatchTypeChange">
            <el-option label="切片ID匹配" value="chunkIdMatch" />
            <el-option label="切片语义匹配" value="chunkTextMatch" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识库" prop="knowledge_base_id" v-if="metricTaskForm.match_type === 'chunkTextMatch'">
          <el-select v-model="metricTaskForm.knowledge_base_id" style="width: 100%">
            <el-option v-for="kb in bindings" :key="kb.knowledge_id" :label="kb.knowledge_name || kb.knowledge_id" :value="kb.knowledge_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标注任务" prop="task_id">
          <el-select v-model="metricTaskForm.task_id" style="width: 100%">
            <el-option v-for="task in completedAnnotationTasks" :key="task.task_id" :label="`${task.task_name} (${task.task_id})`" :value="task.task_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateMetricTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMetricTask" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 标注方式选择模态框 -->
    <el-dialog v-model="showAnnotationModal" title="选择标注方式" width="400px">
      <el-form label-width="100px">
        <el-form-item label="标注类型">
          <el-select v-model="annotationType" style="width: 100%">
            <el-option label="LLM标注" value="llm" />
            <el-option label="人工标注" value="manual" />
            <el-option label="MLB标注" value="mlb" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAnnotationModal = false">取消</el-button>
        <el-button type="primary" @click="confirmAnnotationType">确定</el-button>
      </template>
    </el-dialog>

    <!-- 质量计算方式选择模态框 -->
    <el-dialog v-model="showCalculationModal" title="选择召回方式" width="400px">
      <el-form label-width="100px">
        <el-form-item label="召回方式">
          <el-select v-model="calculationForm.search_type" style="width: 100%">
            <el-option label="向量检索" value="vectorSearch" />
            <el-option label="混合检索" value="hybridSearch" />
            <el-option label="增强检索" value="augmentedSearch" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCalculationModal = false">取消</el-button>
        <el-button type="primary" @click="confirmCalculation" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 报告查看对话框 -->
    <el-dialog v-model="showReportModal" title="查看报告" width="800px">
      <div v-if="reports.length > 0">
        <el-table :data="reports" stripe border size="small">
          <el-table-column label="报告名称" min-width="200">
            <template #default="{ row }">
              <el-link type="primary" @click="openReport(row)">{{ row.filepath || 'N/A' }}</el-link>
              <div class="report-id">ID: {{ row.report_id || 'N/A' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="召回方式" width="120">
            <template #default="{ row }">
              {{ searchTypeMap[row.search_type] || row.search_type || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column label="匹配方式" width="120">
            <template #default="{ row }">
              {{ matchTypeMap[row.match_type] || row.match_type || 'N/A' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="error_msg" label="错误信息" min-width="150" show-overflow-tooltip />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="deleteReport(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无报告数据" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Upload, UploadFilled, Search, Refresh, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import {
  getKnowledgeFiles,
  getKnowledgeBindings,
  bindKnowledge as bindKnowledgeApi,
  syncKnowledge as syncKnowledgeApi,
  editFile as editFileApi,
  deleteFile as deleteFileApi,
  getQuestionSets,
  createQuestionSet as createQuestionSetApi,
  deleteQuestionSet as deleteQuestionSetApi,
  getQuestions,
  getQuestionDetail,
  createQuestion as createQuestionApi,
  updateQuestion,
  deleteQuestion as deleteQuestionApi,
  getLabelStudioEnvs,
  getLabelStudioEnvironments,
  bindLabelStudioEnvironment,
  unbindLabelStudioEnvironment,
  getTasksByEnvironment,
  createAnnotationTask,
  deleteAnnotationTask,
  updateAnnotationType,
  syncAnnotationTask,
  getCompletedAnnotationTasks,
  createMetricTask,
  getMetricTaskInfo,
  startCalculation,
  getMetricReports,
  deleteMetricReport,
  deleteMetricTaskApi
} from '@/api/knowledge'
import {
  getEnvironmentList,
  getEnvironmentKnowledgeBases
} from '@/api/environment'
import apiClient, { legacyGet, legacyPost } from '@/api/index'

const route = useRoute()
const router = useRouter()
const knoId = route.params.kno_id as string
const knoName = route.params.kno_name as string

// 加载状态
const loading = ref(false)
const loadingFiles = ref(false)
const loadingTasks = ref(false)
const submitting = ref(false)
const uploading = ref(false)

// 标签页
const activeTab = ref('files')

// 知识库信息
const knowledge = ref<any>(null)

// 文件列表
const fileList = ref<any[]>([])
const showUploadDialog = ref(false)
const uploadFileList = ref<UploadFile[]>([])
const uploadRef = ref()

// 编辑文件
const showEditFileDialog = ref(false)
const editFileForm = reactive({ knol_id: '', kno_describe: '' })

// 绑定知识库
const showBindDialog = ref(false)
const bindings = ref<any[]>([])
const allEnvironments = ref<any[]>([])
const envKnowledgeBases = ref<any[]>([])
const bindForm = reactive({ envId: '', kbId: '' })

// 问题集
const questionSets = ref<any[]>([])
const expandedQuestionSets = ref<string[]>([])
const questionSetsLoaded = ref(false)
const showCreateQuestionSetDialog = ref(false)
const questionSetFormRef = ref<FormInstance>()
const questionSetForm = reactive({ question_name: '', question_set_type: 'basic' })
const questionSetRules: FormRules = {
  question_name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  question_set_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

// 问题
const showCreateQuestionDialog = ref(false)
const currentQuestionSet = ref<any>(null)
const questionFormRef = ref<FormInstance>()
const questionForm = reactive({ question_type: 'factual', question_content: '', chunk_ids: '' })
const questionRules: FormRules = {
  question_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  question_content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

// Label-Studio环境
const environments = ref<any[]>([])
const availableLabelStudioEnvs = ref<any[]>([])
const showBindEnvironmentDialog = ref(false)
const bindEnvForm = reactive({ envId: '' })
const expandedEnvironments = ref<string[]>([])
const environmentTasks = reactive<Record<string, any[]>>({})
const loadingEnvironmentTasks = reactive<Record<string, boolean>>({})

// 标注任务
const showAnnotationModal = ref(false)
const currentAnnotationTask = ref<any>(null)
const annotationType = ref('llm')

// 任务
const tasks = ref<any[]>([])
const showCreateTaskDialog = ref(false)
const taskFormRef = ref<FormInstance>()
const taskForm = reactive({ task_name: '', env_name: '', question_set_id: '', annotation_type: 'llm' })
const taskRules: FormRules = {
  task_name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  question_set_id: [{ required: true, message: '请选择问题集', trigger: 'change' }],
  annotation_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

// 指标任务
const showCreateMetricTaskDialog = ref(false)
const metricTaskFormRef = ref<FormInstance>()
const metricTaskForm = reactive({ match_type: '', task_id: '', knowledge_base_id: '' })
const metricTaskRules: FormRules = {
  match_type: [{ required: true, message: '请选择匹配方式', trigger: 'change' }],
  task_id: [{ required: true, message: '请选择标注任务', trigger: 'change' }],
  knowledge_base_id: [{ required: false }]
}
const completedAnnotationTasks = ref<any[]>([])

// 质量计算相关
const showCalculationModal = ref(false)
const currentCalculationTask = ref<any>(null)
const calculationForm = reactive({ search_type: '' })

// 报告相关
const showReportModal = ref(false)
const currentMetricTask = ref<any>(null)
const reports = ref<any[]>([])

// 映射关系
const searchTypeMap: Record<string, string> = {
  'vectorSearch': '向量检索',
  'hybridSearch': '混合检索',
  'augmentedSearch': '增强检索'
}

const matchTypeMap: Record<string, string> = {
  'chunkTextMatch': '切片语义匹配',
  'chunkIdMatch': '切片ID匹配'
}

// 状态映射
function getStatusType(status: number) {
  const map: Record<number, string> = { 0: 'success', 1: 'info', 2: 'warning', 3: 'danger' }
  return map[status] || 'info'
}
function getStatusLabel(status: number) {
  const map: Record<number, string> = { 0: '已完成', 1: '未开始', 2: '进行中', 3: '失败' }
  return map[status] || '未知'
}
function getFileStatusType(status: number) {
  const map: Record<number, string> = { 0: 'success', 1: 'info', 2: 'warning' }
  return map[status] || 'info'
}
function getFileStatusLabel(status: number) {
  const map: Record<number, string> = { 0: '已同步', 1: '未开始', 2: '同步中' }
  return map[status] || '未知'
}
function getBindStatusType(status: number) {
  const map: Record<number, string> = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger', 4: 'info' }
  return map[status] || 'info'
}
function getBindStatusLabel(status: number) {
  const map: Record<number, string> = { 0: '未绑定', 1: '绑定中', 2: '已绑定', 3: '解绑中', 4: '已解绑' }
  return map[status] || '未知'
}
function getTaskStatusType(status: string) {
  const map: Record<string, string> = { '未开始': 'info', '标注中': 'warning', '进行中': 'warning', '已完成': 'success' }
  return map[status] || 'info'
}
function getProgress(row: any) {
  const total = row.total_chunks || 0
  const annotated = row.annotated_chunks || 0
  return total ? Math.round((annotated / total) * 100) : 0
}

// 问题类型标签样式
function getQuestionTypeTag(type: string) {
  const map: Record<string, string> = {
    'factual': 'primary',
    'contextual': 'success',
    'conceptual': 'warning',
    'reasoning': 'danger',
    'application': 'info'
  }
  return map[type] || 'info'
}

// 搜索和分页相关函数
function getFilteredQuestions(set: any) {
  if (!set.questions) return []
  let result = [...set.questions]
  
  // 按问题类型筛选
  if (set.filterType) {
    result = result.filter((q: any) => q.question_type === set.filterType)
  }
  
  // 按搜索关键词筛选
  if (set.searchQuery) {
    const query = set.searchQuery.toLowerCase()
    result = result.filter((q: any) => 
      (q.question_content && q.question_content.toLowerCase().includes(query)) ||
      (q.question_id && q.question_id.toLowerCase().includes(query))
    )
  }
  
  return result
}

function getPagedQuestions(set: any) {
  const filtered = getFilteredQuestions(set)
  const start = (set.currentPage - 1) * set.pageSize
  const end = start + set.pageSize
  return filtered.slice(start, end)
}

function handleSearch(set: any) {
  set.currentPage = 1
}

function handleSizeChange(set: any) {
  set.currentPage = 1
}

function handleCurrentChange(set: any) {
  // 分页切换时无需额外操作
}

async function refreshQuestionSet(set: any) {
  set.loading = true
  try {
    const res = await getQuestions(set.question_id, set.question_set_type || 'basic')
    set.questions = (res.data as any) || []
    ElMessage.success('刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    set.loading = false
  }
}

// 设置知识库基本信息（从文件列表中提取）
function setKnowledgeFromFiles(files: any[]) {
  if (files && files.length > 0) {
    const firstFile = files[0]
    knowledge.value = {
      kno_id: knoId,
      kno_name: knoName,
      kno_describe: firstFile.kno_describe || '',
      kno_path: firstFile.knol_path || '',
      ls_status: firstFile.ls_status || 1
    }
  } else {
    knowledge.value = { kno_id: knoId, kno_name: knoName, kno_describe: '', kno_path: '', ls_status: 1 }
  }
}

async function loadFileList() {
  loading.value = true
  loadingFiles.value = true
  try {
    const res = await getKnowledgeFiles(knoId, knoName)
    if (res.success) {
      fileList.value = res.data || []
      // 同时更新知识库基本信息
      setKnowledgeFromFiles(fileList.value)
    } else {
      ElMessage.error(res.message || '加载文件列表失败')
      fileList.value = []
      knowledge.value = { kno_id: knoId, kno_name: knoName, kno_describe: '', kno_path: '', ls_status: 1 }
    }
  } catch (error) {
    ElMessage.error('加载文件列表失败')
    fileList.value = []
    knowledge.value = { kno_id: knoId, kno_name: knoName, kno_describe: '', kno_path: '', ls_status: 1 }
  } finally {
    loading.value = false
    loadingFiles.value = false
  }
}

async function loadBindings() {
  try {
    const res = await getKnowledgeBindings(knoId)
    if (res.success) {
      bindings.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载绑定列表失败')
      bindings.value = []
    }
  } catch (error) {
    ElMessage.error('加载绑定列表失败')
    bindings.value = []
  }
}

async function loadQuestionSets(forceReload = false) {
  // 如果已经加载过且不强制刷新，则跳过
  if (questionSetsLoaded.value && !forceReload) {
    return
  }
  
  try {
    const res = await getQuestionSets(knoId)
    if (res.success) {
      const sets = (res.data || []).map((set: any) => ({
        ...set,
        loading: false,
        questions: [],
        // 搜索和分页相关数据
        searchQuery: '',
        filterType: '',
        currentPage: 1,
        pageSize: 10
      }))
      questionSets.value = sets
      questionSetsLoaded.value = true
      
      // 并行加载每个问题集的问题列表
      await Promise.all(sets.map(async (set: any) => {
        set.loading = true
        try {
          const questionRes = await getQuestions(set.question_id, set.question_set_type || 'basic')
          set.questions = (questionRes.data as any) || []
        } catch (error) {
          set.questions = []
        } finally {
          set.loading = false
        }
      }))
    } else {
      ElMessage.error(res.message || '加载问题集失败')
      questionSets.value = []
    }
  } catch (error) {
    ElMessage.error('加载问题集失败')
    questionSets.value = []
  }
}

async function loadEnvironments() {
  try {
    // 使用正确的 API 获取当前知识库绑定的环境
    const res = await getLabelStudioEnvironments(knoId)
    if (res.success) {
      // 从响应中提取绑定的环境
      const boundEnvs = res.data?.bound_environments || []
      const allEnvs = res.data?.environments || []
      
      // 只显示已绑定的环境，并添加任务数量
      environments.value = allEnvs.filter((env: any) => 
        boundEnvs.some((bound: any) => bound.label_studio_id === env.label_studio_id && bound.bind_status === 2)
      ).map((env: any) => ({
        ...env,
        task_count: env.task_count || 0
      }))
    } else {
      ElMessage.error(res.message || '加载环境列表失败')
      environments.value = []
    }
  } catch (error) {
    ElMessage.error('加载环境列表失败')
    environments.value = []
  }
}

// 刷新指定环境的任务列表
async function refreshEnvironmentTasks(envId: string) {
  loadingEnvironmentTasks[envId] = true
  try {
    const res = await getTasksByEnvironment(envId, knoId)
    if (res.success) {
      environmentTasks[envId] = res.data || []
    } else {
      environmentTasks[envId] = []
    }
  } catch (error) {
    environmentTasks[envId] = []
  } finally {
    loadingEnvironmentTasks[envId] = false
  }
}

// 切换环境展开/折叠
async function toggleEnvironment(env: any) {
  const envId = env.label_studio_id
  const index = expandedEnvironments.value.indexOf(envId)
  if (index > -1) {
    expandedEnvironments.value.splice(index, 1)
  } else {
    expandedEnvironments.value.push(envId)
    // 加载该环境的任务
    if (!(envId in environmentTasks)) {
      await refreshEnvironmentTasks(envId)
    }
  }
}

async function loadTasks() {
  loadingTasks.value = true
  try {
    // 使用指标任务API作为任务列表
    const res: any = await legacyGet(`/local_knowledge_detail/task/metric/list?knowledge_id=${knoId}`)
    // 注意：legacyGet直接返回响应数据，不是res.data
    if (res.success) {
      tasks.value = (res.data || []).map((task: any) => ({
        ...task,
        task_type: task.task_type || '指标任务',
        task_status: task.status || '未开始',
        created_at: task.created_at || new Date().toISOString()
      }))
    } else {
      // 如果没有指标任务，显示空列表
      tasks.value = []
    }
  } catch (error) {
    // 指标任务API可能不存在，显示空列表
    tasks.value = []
  } finally {
    loadingTasks.value = false
  }
}

async function loadAllEnvironments() {
  try {
    const res = await getEnvironmentList()
    if (res.success) {
      allEnvironments.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载环境列表失败')
      allEnvironments.value = []
    }
  } catch (error) {
    ElMessage.error('加载环境列表失败')
    allEnvironments.value = []
  }
}

async function loadLabelStudioEnvs() {
  try {
    const res = await getLabelStudioEnvs()
    if (res.success) {
      availableLabelStudioEnvs.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载Label-Studio环境失败')
      availableLabelStudioEnvs.value = []
    }
  } catch (error) {
    ElMessage.error('加载Label-Studio环境失败')
    availableLabelStudioEnvs.value = []
  }
}

async function loadEnvKnowledgeBases() {
  if (!bindForm.envId) return
  try {
    const res = await getEnvironmentKnowledgeBases(bindForm.envId)
    if (res.success) {
      envKnowledgeBases.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载知识库列表失败')
      envKnowledgeBases.value = []
    }
  } catch (error) {
    ElMessage.error('加载知识库列表失败')
    envKnowledgeBases.value = []
  }
}

// 文件操作
function handleFileChange() {
  // v-model:file-list 会自动更新 uploadFileList，无需手动处理
}

async function uploadFiles() {
  if (uploadFileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    uploadFileList.value.forEach((file: UploadFile) => {
      if (file.raw) {
        formData.append('files', file.raw)
      }
    })
    formData.append('kno_id', knoId)
    
    const res: any = await legacyPost('/api/local_knowledge/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.success || res.status === 'success') {
      ElMessage.success(res.message || '上传成功')
      showUploadDialog.value = false
      uploadFileList.value = []
      loadFileList()
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

function editFile(row: any) {
  editFileForm.knol_id = row.knol_id
  editFileForm.kno_describe = row.kno_describe || ''
  showEditFileDialog.value = true
}

async function saveFileEdit() {
  submitting.value = true
  try {
    const res = await editFileApi(editFileForm.knol_id, { kno_describe: editFileForm.kno_describe })
    if (res.success) {
      ElMessage.success('保存成功')
      showEditFileDialog.value = false
      loadFileList()
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

async function deleteFile(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除文件 ${row.kno_name} 吗？`, '确认删除', { type: 'warning' })
    const res = await deleteFileApi(row.knol_id)
    if (res.success || res.status === 'success') {
      ElMessage.success(res.message || '删除成功')
      loadFileList()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 绑定操作
async function bindKnowledge() {
  if (!bindForm.envId || !bindForm.kbId) {
    ElMessage.warning('请选择环境和知识库')
    return
  }
  submitting.value = true
  try {
    const selectedEnv = allEnvironments.value.find(e => e.zlpt_base_id === bindForm.envId)
    const selectedKb = envKnowledgeBases.value.find(k => k.knowledge_id === bindForm.kbId)
    const res = await bindKnowledgeApi({
      kno_id: knoId,
      knowledge_id: bindForm.kbId,
      operation: 'bind'
    })
    if (res.success) {
      ElMessage.success('绑定成功')
      showBindDialog.value = false
      bindForm.envId = ''
      bindForm.kbId = ''
      loadBindings()
    } else {
      ElMessage.error(res.message || '绑定失败')
    }
  } catch (error) {
    ElMessage.error('绑定失败')
  } finally {
    submitting.value = false
  }
}

async function unbindKnowledge(binding: any) {
  try {
    await ElMessageBox.confirm('确定解绑此知识库吗？', '确认解绑', { type: 'warning' })
    const res = await bindKnowledgeApi({
      kno_id: knoId,
      knowledge_id: binding.knowledge_id,
      operation: 'unbind'
    })
    if (res.success) {
      ElMessage.success('解绑成功')
      loadBindings()
    } else {
      ElMessage.error(res.message || '解绑失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('解绑失败')
    }
  }
}

async function syncKnowledge(binding: any) {
  try {
    const res = await syncKnowledgeApi(knoId, binding.knowledge_id)
    if (res.success) {
      ElMessage.success('同步成功')
      loadBindings()
    } else {
      ElMessage.error(res.message || '同步失败')
    }
  } catch (error) {
    ElMessage.error('同步失败')
  }
}

// 问题集操作
async function createQuestionSet() {
  const valid = await questionSetFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await createQuestionSetApi({
      question_name: questionSetForm.question_name,
      question_set_type: questionSetForm.question_set_type,
      knowledge_id: knoId
    })
    if (res.success) {
      ElMessage.success('创建成功')
      showCreateQuestionSetDialog.value = false
      loadQuestionSets()
      questionSetForm.question_name = ''
      questionSetForm.question_set_type = 'basic'
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

function editQuestionSet(set: any) {
  // TODO: 编辑问题集 - 需要后端支持更新API
  ElMessage.info('编辑功能开发中')
}

async function deleteQuestionSet(set: any) {
  try {
    await ElMessageBox.confirm(`确定删除问题集 ${set.question_name} 吗？`, '确认删除', { type: 'warning' })
    const res = await deleteQuestionSetApi(set.question_id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadQuestionSets()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 问题操作
function openCreateQuestionDialog(set: any) {
  currentQuestionSet.value = set
  questionForm.question_type = 'factual'
  questionForm.question_content = ''
  questionForm.chunk_ids = ''
  showCreateQuestionDialog.value = true
}

async function saveQuestion() {
  const valid = await questionFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    // 将逗号分隔的字符串转换为数组
    const chunkIdsStr = questionForm.chunk_ids
      ? questionForm.chunk_ids.split(',').map(id => id.trim()).filter(id => id).join(',')
      : ''
    const res = await createQuestionApi({
      question_type: questionForm.question_type,
      question_content: questionForm.question_content,
      chunk_ids: chunkIdsStr,
      set_id: currentQuestionSet.value?.question_id
    })
    if (res.success) {
      ElMessage.success('创建成功')
      showCreateQuestionDialog.value = false
      // 只刷新当前问题集的问题列表，保持搜索状态
      if (currentQuestionSet.value) {
        await refreshQuestionSet(currentQuestionSet.value)
      }
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

// 问题详情和编辑
const showQuestionDetailDialog = ref(false)
const showEditQuestionDialog = ref(false)
const currentQuestion = ref<any>(null)
const editQuestionForm = reactive({
  question_id: '',
  question_type: 'factual',
  question_content: '',
  chunk_ids: '',
  question_set_type: 'basic'  // 用于后端API，实际是问题集类型
})

async function showQuestionDetail(question: any, questionSetType: string) {
  try {
    const res = await getQuestionDetail(question.question_id, questionSetType)
    if (res.success) {
      currentQuestion.value = res.data
      showQuestionDetailDialog.value = true
    } else {
      ElMessage.error(res.message || '获取问题详情失败')
    }
  } catch (error) {
    ElMessage.error('获取问题详情失败')
  }
}

async function editQuestion(question: any, questionSetType: string) {
  try {
    const res = await getQuestionDetail(question.question_id, questionSetType)
    if (res.success && res.data) {
      const q = res.data
      editQuestionForm.question_id = q.question_id || ''
      editQuestionForm.question_type = q.question_type || 'factual'
      editQuestionForm.question_content = q.question_content || ''
      // 将数组转换为逗号分隔的字符串
      editQuestionForm.chunk_ids = Array.isArray(q.chunk_ids) ? q.chunk_ids.join(',') : (q.chunk_ids || '')
      // 保存问题集类型，后端API需要这个来定位表
      editQuestionForm.question_set_type = questionSetType
      showEditQuestionDialog.value = true
    } else {
      ElMessage.error(res.message || '获取问题信息失败')
    }
  } catch (error) {
    ElMessage.error('获取问题信息失败')
  }
}

async function saveEditQuestion() {
  submitting.value = true
  try {
    // 将逗号分隔的字符串转换为数组
    const chunkIdsStr = editQuestionForm.chunk_ids
      ? editQuestionForm.chunk_ids.split(',').map(id => id.trim()).filter(id => id).join(',')
      : ''
    // 注意：后端API的question_type字段实际上是问题集类型（basic/detailed等）
    const res = await updateQuestion(editQuestionForm.question_id, {
      question_type: editQuestionForm.question_set_type,
      question_content: editQuestionForm.question_content,
      chunk_ids: chunkIdsStr
    })
    if (res.success) {
      ElMessage.success('更新成功')
      showEditQuestionDialog.value = false
      // 找到对应的问题集并刷新，保持搜索状态
      const targetSet = questionSets.value.find(
        (s: any) => s.question_set_type === editQuestionForm.question_set_type
      )
      if (targetSet) {
        await refreshQuestionSet(targetSet)
      }
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    submitting.value = false
  }
}

async function deleteQuestion(question: any, questionSetType: string) {
  try {
    await ElMessageBox.confirm('确定删除此问题吗？', '确认删除', { type: 'warning' })
    const res = await deleteQuestionApi(question.question_id, questionSetType)
    if (res.success) {
      ElMessage.success('删除成功')
      // 找到对应的问题集并刷新，保持搜索状态
      const targetSet = questionSets.value.find(
        (s: any) => s.question_set_type === questionSetType
      )
      if (targetSet) {
        await refreshQuestionSet(targetSet)
      }
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 环境操作
async function bindEnvironment() {
  if (!bindEnvForm.envId) {
    ElMessage.warning('请选择环境')
    return
  }
  submitting.value = true
  try {
    // 调用绑定Label-Studio环境的API
    const res = await bindLabelStudioEnvironment(knoId, bindEnvForm.envId)
    if (res.success) {
      ElMessage.success('绑定成功')
      showBindEnvironmentDialog.value = false
      bindEnvForm.envId = ''
      loadEnvironments()
    } else {
      ElMessage.error(res.message || '绑定失败')
    }
  } catch (error) {
    ElMessage.error('绑定失败')
  } finally {
    submitting.value = false
  }
}

// 解绑环境
async function unbindEnvironment(row: any) {
  try {
    await ElMessageBox.confirm('确定要解绑此Label-Studio环境吗？', '确认解绑', { type: 'warning' })
    const res = await unbindLabelStudioEnvironment(knoId, row.label_studio_id)
    if (res.success) {
      ElMessage.success('解绑成功')
      loadEnvironments()
    } else {
      ElMessage.error(res.message || '解绑失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('解绑失败')
    }
  }
}

// 当前选中的环境（用于创建任务）
const currentTaskEnv = ref<any>(null)

// 标注任务操作
async function openCreateTaskDialog(row?: any) {
  currentTaskEnv.value = row || null
  taskForm.task_name = ''
  taskForm.env_name = row?.label_studio_url || ''
  taskForm.question_set_id = ''
  taskForm.annotation_type = 'llm'
  
  // 确保问题集已加载
  if (!questionSetsLoaded.value || questionSets.value.length === 0) {
    await loadQuestionSets()
  }
  
  showCreateTaskDialog.value = true
}

// 打开创建指标任务对话框（用于任务标签页）
async function openCreateMetricTaskDialog() {
  metricTaskForm.match_type = ''
  metricTaskForm.task_id = ''
  metricTaskForm.knowledge_base_id = ''
  completedAnnotationTasks.value = []
  
  // 确保知识库绑定列表已加载
  if (bindings.value.length === 0) {
    await loadBindings()
  }
  
  // 加载已完成的标注任务
  try {
    const res = await getCompletedAnnotationTasks(knoId)
    if (res.success) {
      completedAnnotationTasks.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载已完成任务失败')
    }
  } catch (error) {
    ElMessage.error('加载已完成任务失败')
  }
  
  showCreateMetricTaskDialog.value = true
}

// 处理匹配方式变化
function handleMatchTypeChange() {
  // 当匹配方式改变时，重置知识库选择
  if (metricTaskForm.match_type !== 'chunkTextMatch') {
    metricTaskForm.knowledge_base_id = ''
  }
}

// 保存指标任务
async function saveMetricTask() {
  const valid = await metricTaskFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  // 如果是切片语义匹配，需要验证知识库
  if (metricTaskForm.match_type === 'chunkTextMatch' && !metricTaskForm.knowledge_base_id) {
    ElMessage.warning('切片语义匹配需要选择知识库')
    return
  }
  
  submitting.value = true
  try {
    const requestData: any = {
      task_id: metricTaskForm.task_id,
      match_type: metricTaskForm.match_type
    }
    
    // 如果是切片语义匹配，添加知识库ID
    if (metricTaskForm.match_type === 'chunkTextMatch') {
      requestData.knowledge_base_id = metricTaskForm.knowledge_base_id
    }
    
    const res = await createMetricTask(requestData)
    if (res.success) {
      ElMessage.success('指标任务创建成功')
      showCreateMetricTaskDialog.value = false
      loadTasks()
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

// 显示质量计算对话框
function showCalculationDialog(row: any) {
  currentCalculationTask.value = row
  calculationForm.search_type = ''
  showCalculationModal.value = true
}

// 确认计算
async function confirmCalculation() {
  if (!calculationForm.search_type) {
    ElMessage.warning('请选择召回方式')
    return
  }
  
  if (!currentCalculationTask.value) {
    ElMessage.warning('任务信息不能为空')
    return
  }
  
  submitting.value = true
  try {
    // 获取任务信息
    const taskRes = await getMetricTaskInfo(currentCalculationTask.value.task_id)
    if (!taskRes.success || !taskRes.data) {
      ElMessage.error(taskRes.message || '无法获取任务信息')
      return
    }
    
    const taskInfo = taskRes.data
    const matchType = taskInfo.match_type
    const metricTaskId = taskInfo.metric_task_id
    
    if (!matchType) {
      ElMessage.error('任务缺少匹配方式信息')
      return
    }
    
    // 启动计算
    const res = await startCalculation({
      task_id: currentCalculationTask.value.task_id,
      search_type: calculationForm.search_type,
      match_type: matchType,
      metric_task_id: metricTaskId
    })
    
    if (res.success) {
      ElMessage.success('质量计算已启动')
      showCalculationModal.value = false
      loadTasks()
    } else {
      ElMessage.error(res.message || '启动计算失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 显示报告对话框
async function showReportDialog(row: any) {
  currentMetricTask.value = row
  reports.value = []
  showReportModal.value = true
  
  // 加载报告列表
  try {
    const res = await getMetricReports(row.metric_task_id)
    if (res.success) {
      reports.value = res.data || []
    } else {
      ElMessage.error(res.message || '加载报告失败')
    }
  } catch (error) {
    ElMessage.error('加载报告失败')
  }
}

// 打开报告
function openReport(report: any) {
  if (!report.filepath) {
    ElMessage.warning('报告文件路径为空')
    return
  }
  // 在新窗口打开报告
  window.open(`/report/${report.filepath}`, '_blank')
}

// 删除报告
async function deleteReport(report: any) {
  try {
    await ElMessageBox.confirm('确定要删除这个报告吗？此操作不可撤销。', '确认删除', { type: 'warning' })
    const res = await deleteMetricReport(report.report_id)
    if (res.success) {
      ElMessage.success('报告删除成功')
      // 刷新报告列表
      if (currentMetricTask.value) {
        const refreshRes = await getMetricReports(currentMetricTask.value.metric_task_id)
        if (refreshRes.success) {
          reports.value = refreshRes.data || []
        }
      }
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除报告失败')
    }
  }
}

// 删除指标任务
async function deleteMetricTask(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？将同时删除相关的报告文件和数据库记录。', '确认删除', { type: 'warning' })
    const res = await deleteMetricTaskApi(row.metric_task_id)
    if (res.success) {
      ElMessage.success('任务删除成功')
      loadTasks()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

function showAnnotationDialog(row: any) {
  // 打开标注方式选择模态框
  currentAnnotationTask.value = row
  annotationType.value = row.annotation_type || 'llm'
  showAnnotationModal.value = true
}

async function confirmAnnotationType() {
  if (!currentAnnotationTask.value) return
  
  try {
    const res = await updateAnnotationType(
      currentAnnotationTask.value.task_id,
      annotationType.value
    )
    if (res.success) {
      ElMessage.success('标注方式更新成功')
      showAnnotationModal.value = false
      // 刷新该任务所属环境的任务列表
      const envId = currentAnnotationTask.value.label_studio_env_id
      if (envId) {
        await refreshEnvironmentTasks(envId)
      }
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新标注方式失败')
  }
}

function annotateTask(row: any) {
  // 打开标注方式选择模态框，与老代码逻辑一致
  currentAnnotationTask.value = row
  annotationType.value = row.annotation_type || 'llm'
  showAnnotationModal.value = true
}

async function syncTask(row: any) {
  try {
    const res = await syncAnnotationTask(row.task_id)
    if (res.success) {
      ElMessage.success('任务同步成功')
      // 刷新该任务所属环境的任务列表
      const envId = row.label_studio_env_id
      if (envId) {
        await refreshEnvironmentTasks(envId)
      }
    } else {
      ElMessage.error(res.message || '同步失败')
    }
  } catch (error) {
    ElMessage.error('同步任务失败')
  }
}

async function saveTask() {
  const valid = await taskFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    // 从taskForm.env_name找到对应的环境ID
    const targetEnv = environments.value.find((env: any) => env.label_studio_url === taskForm.env_name)
    const labelStudioEnvId = targetEnv?.label_studio_id
    
    const res = await createAnnotationTask({
      task_name: taskForm.task_name,
      question_set_id: taskForm.question_set_id,
      annotation_type: taskForm.annotation_type,
      local_knowledge_id: knoId,
      label_studio_env_id: labelStudioEnvId
    })
    if (res.success) {
      ElMessage.success('创建成功')
      showCreateTaskDialog.value = false
      // 刷新对应环境的任务列表
      if (labelStudioEnvId) {
        await refreshEnvironmentTasks(labelStudioEnvId)
      }
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

function editTask(row: any) {
  // TODO: 编辑任务 - 需要后端支持更新API
  ElMessage.info('编辑功能开发中')
}

async function deleteTask(row: any) {
  try {
    await ElMessageBox.confirm('确定删除此任务吗？', '确认删除', { type: 'warning' })
    const res = await deleteAnnotationTask(row.task_id)
    if (res.success) {
      ElMessage.success('删除成功')
      // 刷新该任务所属环境的任务列表
      const envId = row.label_studio_env_id
      if (envId) {
        await refreshEnvironmentTasks(envId)
      }
      loadTasks()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function goBack() {
  router.back()
}

// 监听标签页切换
watch(activeTab, (tab) => {
  // 切换标签页时重置展开状态，避免渲染问题
  if (tab !== 'questions') {
    expandedQuestionSets.value = []
  }
  
  if (tab === 'files') loadFileList()
  else if (tab === 'bindings') loadBindings()
  else if (tab === 'questions') loadQuestionSets()  // 使用缓存，不强制刷新
  else if (tab === 'annotations') { 
    // 标注标签页：加载绑定的环境（任务在展开环境时按需加载）
    loadEnvironments()
  }
  else if (tab === 'tasks') loadTasks()
})

onMounted(() => {
  loadFileList()  // 加载文件列表的同时会设置知识库信息
  loadAllEnvironments()
  loadLabelStudioEnvs()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h2 {
      margin: 0;
    }
  }
}

.knowledge-info {
  margin-bottom: 20px;
}

.detail-tabs {
  margin-top: 20px;
}

.tab-actions {
  margin-bottom: 16px;
}

.binding-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.binding-item {
  .binding-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .binding-info {
    div {
      margin-bottom: 4px;
    }
  }

  .binding-actions {
    display: flex;
    gap: 8px;
  }
}

.question-set-list {
  .question-set-header {
    display: flex;
    align-items: center;
    width: 100%;
    padding-right: 20px;

    .question-set-name {
      font-weight: bold;
      margin-right: 16px;
    }

    .question-set-meta {
      color: #909399;
      font-size: 12px;
      flex: 1;
    }

    .question-set-actions {
      margin-left: auto;
    }
  }
}

.question-list {
  padding: 12px;

  .question-toolbar {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    padding: 8px;
    background-color: #f5f7fa;
    border-radius: 4px;
  }

  .question-pagination {
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
  }
}

.section-title {
  margin: 24px 0 16px;
  color: #303133;
  font-size: 16px;
  font-weight: bold;
}

.environment-table {
  margin-bottom: 20px;
}

.environment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .environment-item {
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    overflow: hidden;

    .environment-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background-color: #f5f7fa;
      border-bottom: 1px solid #e4e7ed;

      .environment-info {
        display: flex;
        align-items: center;
        gap: 16px;
        flex: 1;

        .expand-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;

          .expand-text {
            font-size: 13px;
          }
        }

        .env-id {
          font-weight: 500;
          color: #303133;
          min-width: 120px;
        }

        .env-url {
          color: #606266;
          font-size: 13px;
          flex: 1;
        }
      }

      .environment-actions {
        display: flex;
        gap: 8px;
      }
    }

    .environment-tasks {
      padding: 16px;
      background-color: #fff;
    }
  }
}
</style>
