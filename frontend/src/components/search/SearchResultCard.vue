<template>
  <el-card class="novel-card" shadow="hover">
    <div class="novel-content">
      <div class="novel-cover">
        <el-image v-if="coverUrl" :src="coverUrl" fit="cover" class="cover-image" lazy>
          <template #error>
            <div class="cover-placeholder">
              <el-icon :size="40"><Picture /></el-icon>
            </div>
          </template>
        </el-image>
        <div v-else class="cover-placeholder">
          <el-icon :size="40"><Picture /></el-icon>
        </div>
      </div>

      <div class="novel-info">
        <div class="novel-header">
          <h3 class="novel-title">{{ novel.title }}</h3>
          <div class="novel-badges">
            <el-tag v-if="novel.is_ready" type="success" effect="dark">可读</el-tag>
            <el-tag v-if="novel.is_cached" type="info" effect="dark">已缓存</el-tag>
          </div>
        </div>

        <div class="novel-meta">
          <span class="meta-item">
            <el-icon><User /></el-icon>
            {{ novel.author || '未知' }}
          </span>
          <span v-if="novel.category" class="meta-item">
            <el-icon><FolderOpened /></el-icon>
            {{ novel.category }}
          </span>
          <span class="meta-item">
            <el-icon><Download /></el-icon>
            已抓取 {{ novel.chapters_in_db || 0 }} 章
          </span>
          <span class="meta-item heat-item"> 综合热度 {{ formatCount(novel.local_heat_score) }} </span>
        </div>

        <div v-if="novel.description" class="novel-description">
          <el-text line-clamp="3" :title="novel.description">
            {{ novel.description }}
          </el-text>
        </div>

        <div class="novel-actions">
          <el-button
            type="primary"
            size="default"
            @click="emit('download-full', novel.id)"
            :loading="loadingId === novel.id && !isPreviewMode"
            :disabled="loadingId === novel.id || batchDownloading"
          >
            <el-icon><Download /></el-icon>
            下载全本
          </el-button>
          <el-button
            type="success"
            size="default"
            @click="emit('download-preview', novel.id)"
            :loading="loadingId === novel.id && isPreviewMode"
            :disabled="loadingId === novel.id || batchDownloading"
          >
            <el-icon><View /></el-icon>
            前十章预览
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { FolderOpened, Picture, Download, User, View } from '@element-plus/icons-vue'
import type { NovelSearchResult } from '../../api'

defineProps<{
  novel: NovelSearchResult
  coverUrl: string
  loadingId: string | null
  isPreviewMode: boolean
  batchDownloading: boolean
}>()

const emit = defineEmits<{
  'download-full': [novelId: string]
  'download-preview': [novelId: string]
}>()

const formatCount = (value?: number | null): string => {
  const numericValue = Math.round(value || 0)
  return new Intl.NumberFormat('zh-CN').format(numericValue)
}
</script>

<style scoped>
.novel-card {
  position: relative;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(84, 227, 255, 0.04) 28px, rgba(84, 227, 255, 0.04) 29px),
    var(--surface-solid);
  box-shadow: var(--shadow-card);
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.novel-card::before {
  content: 'SEARCH NODE';
  position: absolute;
  top: 12px;
  left: 16px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: var(--accent-strong);
  opacity: 0.84;
}

.novel-card::after {
  content: '';
  position: absolute;
  top: 14px;
  right: 16px;
  width: 48px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet), var(--neon-pink));
  opacity: 0.92;
}

.novel-card:hover {
  border-color: rgba(84, 227, 255, 0.18);
  box-shadow: var(--shadow-soft), 0 0 26px rgba(84, 227, 255, 0.08);
  transform: translateY(-2px);
}

:deep(.novel-card .el-card__body) {
  height: 100%;
  padding: 22px 18px 18px;
}

.novel-content {
  display: flex;
  gap: 18px;
  height: 100%;
}

.novel-cover {
  position: relative;
  flex-shrink: 0;
  width: 126px;
  height: 172px;
  border-radius: 14px;
  overflow: hidden;
  background: var(--surface-muted);
  border: 1px solid rgba(84, 227, 255, 0.16);
  box-shadow: inset 0 0 0 1px var(--border-color-light), 0 0 18px rgba(84, 227, 255, 0.08);
}

.cover-image {
  width: 100%;
  height: 100%;
}

.novel-cover::after {
  content: 'LIVE';
  position: absolute;
  left: 10px;
  bottom: 10px;
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(9, 17, 38, 0.64);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-muted);
  color: var(--text-tertiary);
}

.novel-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.novel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.novel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.novel-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

:deep(.novel-badges .el-tag) {
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.08);
}

.novel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.08), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.heat-item {
  color: var(--accent-strong);
  font-weight: 700;
}

.novel-description {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  flex: 1;
}

.novel-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
}

.novel-actions .el-button {
  flex: 1;
  min-height: 42px;
  border-radius: 14px;
}

@media (max-width: 768px) {
  .novel-content {
    flex-direction: column;
    gap: 14px;
  }

  .novel-cover {
    width: 100%;
    height: 220px;
  }

  .novel-header {
    flex-direction: column;
  }

  .novel-badges {
    justify-content: flex-start;
  }

  .novel-actions {
    flex-direction: column;
  }

  .novel-actions .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .novel-card {
    border-radius: 16px;
  }

  .novel-cover {
    height: 200px;
  }

  .novel-title {
    font-size: 17px;
  }
}
</style>
