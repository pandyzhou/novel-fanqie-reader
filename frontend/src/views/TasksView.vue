<template>
  <div class="tasks-container">
    <section class="tasks-hero">
      <div>
        <p class="hero-badge">任务中心</p>
        <h2 class="page-title">任务管理</h2>
        <p class="hero-subtitle">查看下载进度、失败原因与重试状态，统一管理后台任务。</p>
      </div>
      <div class="hero-actions">
        <el-tag type="success" v-if="socketConnected">实时更新中</el-tag>
        <el-tag type="warning" v-else>实时更新未连接</el-tag>
        <el-button type="primary" @click="refreshTasks" :loading="taskStore.isLoading">
          <el-icon><Refresh /></el-icon>
          刷新任务
        </el-button>
      </div>
    </section>

    <el-card class="glass-card tasks-card page-panel-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div>
            <h3>下载任务列表</h3>
            <p>支持终止、删除与重新下载。</p>
          </div>
        </div>
      </template>

      <div>
        <div v-if="showTaskSkeleton" class="tasks-skeleton">
          <el-skeleton animated :rows="6" />
        </div>

        <template v-else-if="showTaskEmpty">
          <el-empty description="暂无任务">
            <template #description>
              <p>当前还没有下载任务记录。</p>
              <p>你可以先去搜索页或添加页创建一个任务。</p>
            </template>
            <el-button type="primary" @click="navigateToUpload">添加小说</el-button>
          </el-empty>
        </template>

        <el-result v-else-if="showTaskErrorState" icon="error" :title="taskStore.error || '任务列表加载失败'" sub-title="请检查后端服务和任务队列是否可用。">
          <template #extra>
            <el-button type="primary" @click="refreshTasks">重新加载</el-button>
            <el-button @click="navigateToUpload">前往添加页</el-button>
          </template>
        </el-result>

        <div v-else>
          <div class="tasks-mobile-list">
            <article v-for="row in taskStore.tasks" :key="`mobile-${row.id}`" class="task-mobile-card page-subtle-shell">
              <div class="task-mobile-header">
                <div class="novel-info">
                  <template v-if="row.novel">
                    <router-link :to="'/novel/' + String(row.novel_id)" class="novel-title">
                      {{ row.novel.title }}
                    </router-link>
                    <div class="novel-author">{{ row.novel.author || '未知作者' }}</div>
                  </template>
                  <template v-else>
                    <span class="novel-title">小说ID: {{ row.novel_id }}</span>
                  </template>
                </div>
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </div>

              <div class="task-mobile-meta">
                <span>任务 #{{ row.id }}</span>
                <span>阶段 {{ getTaskStageText(row.task_stage) }}</span>
                <span>更新 {{ formatDate(row.updated_at) }}</span>
              </div>

              <div class="task-progress-container task-progress-mobile">
                <div v-if="['DOWNLOADING', 'PROCESSING'].includes(row.status)" class="task-progress-info">
                  <el-progress
                    :percentage="normalizePercentage(row.progress)"
                    :format="percentFormat"
                    :status="getProgressStatus(row.status)"
                  />
                  <div class="task-status-message">
                    {{ row.message || getDefaultProgressMessage(row) }}
                  </div>
                </div>
                <div v-else-if="row.status === 'COMPLETED'" class="task-completed">
                  <el-progress :percentage="100" status="success" />
                  <div class="task-status-message">下载完成</div>
                </div>
                <div v-else-if="row.status === 'FAILED'" class="task-failed">
                  <el-progress :percentage="normalizePercentage(row.progress)" status="exception" />
                  <div class="task-status-message">{{ row.message || '下载失败' }}</div>
                  <div v-if="row.error_code" class="task-status-meta">{{ getTaskErrorText(row.error_code) }}</div>
                </div>
                <div v-else-if="row.status === 'TERMINATED'" class="task-terminated">
                  <el-progress :percentage="normalizePercentage(row.progress)" status="warning" />
                  <div class="task-status-message">{{ row.message || '已终止' }}</div>
                  <div v-if="row.error_code" class="task-status-meta">{{ getTaskErrorText(row.error_code) }}</div>
                </div>
                <div v-else class="task-pending">
                  <el-progress :percentage="0" />
                  <div class="task-status-message">等待中</div>
                </div>
              </div>

              <div class="task-mobile-details">
                <span>创建 {{ formatDate(row.created_at) }}</span>
                <span>错误 {{ getTaskErrorText(row.error_code) }}</span>
                <span>Celery {{ row.celery_task_id || '-' }}</span>
              </div>

              <div v-if="!row.deleted" class="task-mobile-actions">
                <el-button
                  v-if="['PENDING', 'DOWNLOADING', 'PROCESSING'].includes(row.status)"
                  type="warning"
                  plain
                  @click="terminateTask(row.id)"
                  :loading="row.id === activeTaskId && actionType === 'terminate'"
                >
                  终止任务
                </el-button>
                <el-button
                  v-if="['COMPLETED', 'FAILED', 'TERMINATED'].includes(row.status)"
                  type="primary"
                  @click="redownloadTask(row.id)"
                  :loading="row.id === activeTaskId && actionType === 'redownload'"
                >
                  重新下载
                </el-button>
                <el-button
                  type="danger"
                  plain
                  @click="deleteTask(row.id)"
                  :loading="row.id === activeTaskId && actionType === 'delete'"
                >
                  删除任务
                </el-button>
              </div>
            </article>
          </div>

          <el-table :data="taskStore.tasks" style="width: 100%" class="tasks-table tasks-table-desktop">
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="task-details">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="任务ID">{{ row.id }}</el-descriptions-item>
                    <el-descriptions-item label="Celery ID">{{ row.celery_task_id || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ formatDate(row.created_at) }}</el-descriptions-item>
                    <el-descriptions-item label="更新时间">{{ formatDate(row.updated_at) }}</el-descriptions-item>
                    <el-descriptions-item label="任务阶段">{{ getTaskStageText(row.task_stage) }}</el-descriptions-item>
                    <el-descriptions-item label="错误分类">{{ getTaskErrorText(row.error_code) }}</el-descriptions-item>
                    <el-descriptions-item label="状态信息" :span="2">{{ row.message || '-' }}</el-descriptions-item>
                  </el-descriptions>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="小说信息" min-width="250">
              <template #default="{ row }">
                <template v-if="row.novel">
                  <div class="novel-info">
                    <router-link :to="'/novel/' + String(row.novel_id)" class="novel-title">
                      {{ row.novel.title }}
                    </router-link>
                    <div class="novel-author">{{ row.novel.author || '未知作者' }}</div>
                  </div>
                </template>
                <template v-else>
                  <span>小说ID: {{ row.novel_id }}</span>
                </template>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="进度" width="240">
              <template #default="{ row }">
                <div class="task-progress-container">
                  <div
                    v-if="['DOWNLOADING', 'PROCESSING'].includes(row.status)"
                    class="task-progress-info"
                  >
                    <el-progress
                      :percentage="normalizePercentage(row.progress)"
                      :format="percentFormat"
                      :status="getProgressStatus(row.status)"
                    />
                    <div class="task-status-message">
                      {{ row.message || getDefaultProgressMessage(row) }}
                    </div>
                  </div>
                  <div v-else-if="row.status === 'COMPLETED'" class="task-completed">
                    <el-progress :percentage="100" status="success" />
                    <div class="task-status-message">下载完成</div>
                  </div>
                  <div v-else-if="row.status === 'FAILED'" class="task-failed">
                    <el-progress :percentage="normalizePercentage(row.progress)" status="exception" />
                    <div class="task-status-message">{{ row.message || '下载失败' }}</div>
                    <div v-if="row.error_code" class="task-status-meta">{{ getTaskErrorText(row.error_code) }}</div>
                  </div>
                  <div v-else-if="row.status === 'TERMINATED'" class="task-terminated">
                    <el-progress :percentage="normalizePercentage(row.progress)" status="warning" />
                    <div class="task-status-message">{{ row.message || '已终止' }}</div>
                    <div v-if="row.error_code" class="task-status-meta">{{ getTaskErrorText(row.error_code) }}</div>
                  </div>
                  <div v-else class="task-pending">
                    <el-progress :percentage="0" />
                    <div class="task-status-message">等待中</div>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="task-actions">
                  <el-button-group v-if="!row.deleted">
                    <el-button
                      v-if="['PENDING', 'DOWNLOADING', 'PROCESSING'].includes(row.status)"
                      size="small"
                      type="warning"
                      @click="terminateTask(row.id)"
                      :loading="row.id === activeTaskId && actionType === 'terminate'"
                    >
                      终止
                    </el-button>
                    <el-button
                      v-if="['COMPLETED', 'FAILED', 'TERMINATED'].includes(row.status)"
                      size="small"
                      type="primary"
                      @click="redownloadTask(row.id)"
                      :loading="row.id === activeTaskId && actionType === 'redownload'"
                    >
                      重新下载
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      @click="deleteTask(row.id)"
                      :loading="row.id === activeTaskId && actionType === 'delete'"
                    >
                      删除任务
                    </el-button>
                  </el-button-group>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="task-error" v-if="taskStore.error && taskStore.tasks.length > 0 && !taskStore.isLoading">
        <el-alert :title="taskStore.error" type="error" :closable="false" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useTaskStore } from '../store'
import api from '../api'

const router = useRouter()
const taskStore = useTaskStore()
const activeTaskId = ref<number | null>(null)
const actionType = ref<'terminate' | 'delete' | 'redownload' | null>(null)
const socketConnected = ref(false)
let socketStatusTimer: ReturnType<typeof setInterval> | null = null

const showTaskSkeleton = computed(() => taskStore.isLoading && taskStore.tasks.length === 0 && !taskStore.error)
const showTaskEmpty = computed(() => !taskStore.isLoading && taskStore.tasks.length === 0 && !taskStore.error)
const showTaskErrorState = computed(() => !taskStore.isLoading && taskStore.tasks.length === 0 && !!taskStore.error)

const checkSocketConnection = () => {
  socketConnected.value = api.WebSocketAPI.isConnected()
}

const normalizePercentage = (value: number | null | undefined) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round(value)))
}

const percentFormat = (percentage: number) => `${percentage}%`

const setupWebSocketConnection = async () => {
  const connected = await taskStore.setupWebSocketListener()
  socketConnected.value = connected
}

const refreshTasks = async () => {
  await taskStore.fetchTasks()
  checkSocketConnection()
  if (!socketConnected.value) {
    await setupWebSocketConnection()
  }
}

const navigateToUpload = () => {
  router.push('/upload')
}

const terminateTask = async (taskId: number) => {
  activeTaskId.value = taskId
  actionType.value = 'terminate'

  try {
    await ElMessageBox.confirm('确定要终止此任务吗？该操作不可逆。', '终止任务', {
      confirmButtonText: '终止',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })

    const result = await taskStore.terminateTask(taskId)
    if (result) {
      ElMessage.success('任务已终止')
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(taskStore.error || '终止任务失败')
    }
  } finally {
    activeTaskId.value = null
    actionType.value = null
  }
}

const deleteTask = async (taskId: number) => {
  activeTaskId.value = taskId
  actionType.value = 'delete'

  try {
    await ElMessageBox.confirm('确定要删除此任务记录吗？该操作不会删除已经下载好的小说内容。', '删除任务', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })

    const result = await taskStore.deleteTask(taskId)
    if (result) {
      ElMessage.success('任务已删除')
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(taskStore.error || '删除任务失败')
    }
  } finally {
    activeTaskId.value = null
    actionType.value = null
  }
}

const redownloadTask = async (taskId: number) => {
  activeTaskId.value = taskId
  actionType.value = 'redownload'

  try {
    const result = await taskStore.redownloadTask(taskId)
    if (result) {
      ElMessage.success('任务已重新添加到下载队列')
    }
  } catch {
    ElMessage.error(taskStore.error || '重新下载失败')
  } finally {
    activeTaskId.value = null
    actionType.value = null
  }
}

const getStatusType = (status: string): 'success' | 'warning' | 'danger' | 'info' => {
  switch (status) {
    case 'COMPLETED':
      return 'success'
    case 'FAILED':
      return 'danger'
    case 'TERMINATED':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'PENDING':
      return '等待中'
    case 'DOWNLOADING':
      return '下载中'
    case 'PROCESSING':
      return '处理中'
    case 'COMPLETED':
      return '已完成'
    case 'FAILED':
      return '失败'
    case 'TERMINATED':
      return '已终止'
    default:
      return status
  }
}

const TASK_STAGE_LABELS: Record<string, string> = {
  setup: '初始化',
  metadata: '元数据',
  chapter_list: '章节目录',
  download: '章节下载',
  persist: '数据写入',
  analysis: '内容分析',
  finalize: '收尾导出',
}

const TASK_ERROR_LABELS: Record<string, string> = {
  terminated_before_start: '开始前终止',
  downloader_components_missing: '下载器组件缺失',
  downloader_context_init_failed: '下载器初始化失败',
  terminated_metadata_fetch: '元数据阶段终止',
  novel_db_update_failed: '元数据写库失败',
  terminated_chapter_list_fetch: '章节目录阶段终止',
  source_chapter_list_empty: '源站无章节',
  terminated_after_download: '下载完成后终止',
  terminated_during_persist: '写库阶段终止',
  chapter_db_transaction_failed: '章节写库失败',
  export_incomplete: '导出未生成',
  task_terminated: '任务已终止',
  unexpected_exception: '未分类异常',
  book_info_fetch_failed: '小说元数据获取失败',
  chapter_list_fetch_failed: '章节目录获取失败',
  export_finalize_failed: '导出收尾失败',
  analysis_failed: '文本分析失败',
}

const getProgressStatus = (status: string): '' | 'success' | 'exception' | 'warning' => {
  switch (status) {
    case 'DOWNLOADING':
      return 'success'
    case 'FAILED':
      return 'exception'
    case 'TERMINATED':
      return 'warning'
    default:
      return ''
  }
}

const getTaskStageText = (stage?: string | null) => {
  if (!stage) {
    return '-'
  }
  return TASK_STAGE_LABELS[stage] || stage
}

const getTaskErrorText = (errorCode?: string | null) => {
  if (!errorCode) {
    return '-'
  }
  return TASK_ERROR_LABELS[errorCode] || errorCode
}

const getDefaultProgressMessage = (task: { status: string; message?: string | null }) => {
  if (task.status === 'DOWNLOADING') {
    const downloadMatch = task.message?.match(/Downloading (\d+)\/(\d+) chapters/)
    if (downloadMatch && downloadMatch.length >= 3) {
      const current = parseInt(downloadMatch[1])
      const total = parseInt(downloadMatch[2])
      return `下载章节: ${current}/${total}`
    }
    return '正在下载章节...'
  }
  if (task.status === 'PROCESSING') {
    return '正在处理小说数据...'
  }
  return '处理中...'
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-'

  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

watch(
  () => taskStore.tasks,
  () => {
    checkSocketConnection()
  },
  { deep: true },
)

onMounted(async () => {
  await taskStore.fetchTasks()
  await setupWebSocketConnection()
  checkSocketConnection()

  socketStatusTimer = setInterval(() => {
    checkSocketConnection()
  }, 3000)
})

onUnmounted(() => {
  if (socketStatusTimer) {
    clearInterval(socketStatusTimer)
    socketStatusTimer = null
  }
  taskStore.teardownWebSocketListener()
})
</script>

<style scoped>
.tasks-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 32px;
}

.tasks-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 22px 24px;
  border-radius: 18px;
  background: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow: var(--shell-glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.34);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(155%);
}

.hero-badge {
  margin: 0 0 10px;
  color: var(--text-tertiary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 8px;
  color: var(--text-secondary);
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tasks-card {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.tasks-card .el-card__body) {
  padding: 24px;
}

.tasks-skeleton {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.04) 26px, rgba(84, 227, 255, 0.04) 27px),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.card-header h3 {
  margin: 0;
  font-size: 20px;
}

.card-header p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.tasks-mobile-list {
  display: none;
}

.task-mobile-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 14px 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.04) 26px, rgba(84, 227, 255, 0.04) 27px),
    var(--panel-subtle-bg);
}

.task-mobile-card::before {
  content: 'TASK NODE';
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: var(--accent-strong);
  opacity: 0.82;
}

.task-mobile-card::after {
  content: '';
  position: absolute;
  top: 12px;
  right: 12px;
  width: 44px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-pink));
  opacity: 0.9;
}

.task-mobile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.task-mobile-meta,
.task-mobile-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.task-mobile-meta span,
.task-mobile-details span {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.08), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.task-mobile-details {
  color: var(--text-tertiary);
}

.task-mobile-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
}

.task-mobile-actions .el-button {
  flex: 1 1 140px;
}

.task-details {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.novel-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.novel-title {
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 700;
}

.novel-title:hover {
  text-decoration: underline;
}

.novel-author {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 5px;
}

.task-actions {
  display: flex;
  justify-content: center;
}

.task-error {
  margin-top: 15px;
}

:deep(.tasks-table) {
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.08));
  overflow: hidden;
}

html[data-theme='dark'] :deep(.tasks-table) {
  background: linear-gradient(180deg, rgba(30, 45, 68, 0.42), rgba(17, 25, 39, 0.16));
}

.task-progress-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.task-progress-mobile {
  position: relative;
  padding: 14px 12px 12px;
  border-radius: 14px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16), 0 0 18px rgba(84, 227, 255, 0.06);
}

.task-progress-mobile::before {
  content: 'PROCESS';
  position: absolute;
  top: 8px;
  right: 10px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: var(--text-tertiary);
}

html[data-theme='dark'] .task-progress-mobile {
  background:
    linear-gradient(180deg, rgba(24, 38, 76, 0.18), rgba(13, 21, 43, 0.08)),
    rgba(15, 23, 42, 0.16);
}

.task-progress-mobile .task-status-message {
  white-space: normal;
  overflow: visible;
  text-overflow: initial;
  line-height: 1.6;
}

.task-mobile-details span {
  word-break: break-all;
}

.task-status-message {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-status-meta {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.task-progress-info,
.task-completed,
.task-failed,
.task-terminated,
.task-pending {
  width: 100%;
}

@media (max-width: 768px) {
  .tasks-hero {
    padding: 20px;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions .el-button {
    width: 100%;
  }

  :deep(.tasks-card .el-card__body) {
    padding: 18px;
  }

  .tasks-mobile-list {
    display: grid;
    gap: 14px;
  }

  .tasks-table-desktop {
    display: none;
  }
}

@media (max-width: 520px) {
  .task-mobile-header,
  .task-mobile-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .task-mobile-actions .el-button {
    width: 100%;
  }
}
</style>
