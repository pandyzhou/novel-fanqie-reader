<template>
  <div class="settings-container">
    <section class="settings-hero">
      <div>
        <p class="hero-badge">系统设置</p>
        <h2 class="page-title">设置中心</h2>
        <p class="hero-subtitle">统一查看主题、缓存与本地数据目录信息，避免“设置不见了”的情况。</p>
      </div>
      <div class="settings-actions">
        <el-button @click="refreshSystemInfo" :loading="loadingInfo">刷新信息</el-button>
      </div>
    </section>

    <el-row :gutter="20">
      <el-col :span="24" :lg="12">
        <el-card class="settings-card page-panel-card">
          <template #header>
            <div class="card-header">
              <h3>外观设置</h3>
              <p>使用统一主题状态，首页与设置页的切换会实时同步。</p>
            </div>
          </template>

          <div class="setting-block">
            <div class="setting-row">
              <div>
                <strong>主题模式</strong>
                <p>当前主题会写入 localStorage，并自动应用到所有页面。</p>
              </div>
              <el-switch v-model="isDarkMode" active-text="深色" inactive-text="浅色" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="24" :lg="12">
        <el-card class="settings-card page-panel-card">
          <template #header>
            <div class="card-header">
              <h3>缓存说明</h3>
              <p>说明当前搜索缓存与封面缓存策略。</p>
            </div>
          </template>

          <div class="setting-list">
            <el-alert :title="databaseRuntimeMessage" :type="databaseRuntimeType" :closable="false" show-icon />
            <el-alert v-if="databaseFallbackMessage" :title="databaseFallbackMessage" type="warning" :closable="false" show-icon />
            <el-alert :title="cacheDatabaseMessage" type="success" :closable="false" show-icon />
            <el-alert title="搜索封面已缓存到本地目录，后续访问会更快" type="info" :closable="false" show-icon />
            <el-alert :title="accessModeMessage" type="warning" :closable="false" show-icon />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="settings-card info-card page-panel-card" v-loading="loadingInfo">
      <template #header>
        <div class="card-header">
          <h3>系统路径信息</h3>
          <p>当前项目运行时本地目录与缓存目录。</p>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="项目根目录">{{ systemInfo?.project_root || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数据根目录">{{ systemInfo?.data_base_path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="小说导出目录">{{ systemInfo?.novel_save_path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="小说状态目录">{{ systemInfo?.novel_status_path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="词云目录">{{ systemInfo?.wordcloud_save_path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="搜索封面缓存目录">{{ systemInfo?.search_cover_cache_path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数据库类型">{{ databaseLabel }}</el-descriptions-item>
        <el-descriptions-item label="数据库回退状态">{{ systemInfo?.database_fallback_active ? '已启用回退' : '主数据库直连中' }}</el-descriptions-item>
        <el-descriptions-item v-if="systemInfo?.database_fallback_reason" label="回退原因">{{ systemInfo.database_fallback_reason }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import type { SystemInfoResponse } from '../api'
import { useTheme } from '../composables/useTheme'

const { isDarkMode, initTheme } = useTheme()
const loadingInfo = ref(false)
const systemInfo = ref<SystemInfoResponse | null>(null)

initTheme()

const databaseLabel = computed(() => {
  const backend = systemInfo.value?.database_backend
  if (backend === 'sqlite') return 'SQLite'
  if (backend === 'postgresql') return 'PostgreSQL'
  if (backend === 'mysql') return 'MySQL'
  return '当前数据库'
})

const databaseRuntimeType = computed<'success' | 'warning'>(() =>
  systemInfo.value?.database_fallback_active ? 'warning' : 'success',
)

const databaseRuntimeMessage = computed(() =>
  systemInfo.value?.database_fallback_active
    ? `当前主数据库不可用，系统已自动回退到 ${databaseLabel.value}`
    : `当前运行数据库为 ${databaseLabel.value}`,
)

const databaseFallbackMessage = computed(() => systemInfo.value?.database_fallback_reason || '')
const cacheDatabaseMessage = computed(() => `搜索元数据已缓存到 ${databaseLabel.value}`)
const accessModeMessage = computed(() =>
  systemInfo.value?.internal_api_mode
    ? '当前为内部 API 模式：主要界面无需登录即可使用，任务页会直接订阅实时更新'
    : '当前为认证模式：需要登录后才能订阅实时任务更新'
)

const refreshSystemInfo = async () => {
  loadingInfo.value = true
  try {
    const response = await api.System.info()
    if ('error' in response) {
      ElMessage.error(response.error)
      return
    }
    systemInfo.value = response
  } catch {
    ElMessage.error('获取系统信息失败')
  } finally {
    loadingInfo.value = false
  }
}

onMounted(() => {
  refreshSystemInfo()
})
</script>

<style scoped>
.settings-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 32px;
}

.settings-hero {
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

.settings-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.settings-card {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.settings-card .el-card__body) {
  padding: 24px;
}

.card-header h3 {
  margin: 0;
}

.card-header p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.setting-block {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.setting-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.setting-row p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.setting-list {
  display: grid;
  gap: 12px;
}

:deep(.setting-list .el-alert),
:deep(.info-card .el-descriptions) {
  border-radius: 16px;
}

:deep(.info-card .el-descriptions__content) {
  word-break: break-all;
}

.info-card {
  border-radius: 20px;
}

@media (max-width: 768px) {
  .settings-hero {
    padding: 20px;
  }

  .settings-actions,
  .settings-actions .el-button {
    width: 100%;
  }

  :deep(.settings-card .el-card__body) {
    padding: 18px;
  }

  .setting-block {
    padding: 14px;
  }

  .setting-row {
    flex-direction: column;
    align-items: flex-start;
  }

  :deep(.setting-row .el-switch) {
    align-self: stretch;
    justify-content: space-between;
    width: 100%;
  }
}
</style>
