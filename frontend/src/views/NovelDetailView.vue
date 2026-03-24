<template>
  <div class="novel-detail-container">
    <template v-if="showDetailSkeleton">
      <section class="detail-hero detail-skeleton-card">
        <el-skeleton animated>
          <template #template>
            <div class="detail-skeleton-stack">
              <el-skeleton-item variant="text" style="width: 88px; height: 18px" />
              <el-skeleton-item variant="h1" style="width: 52%; height: 34px" />
              <el-skeleton-item variant="text" style="width: 70%" />
              <el-skeleton-item variant="text" style="width: 38%" />
            </div>
          </template>
        </el-skeleton>
      </section>

      <div class="novel-info detail-skeleton-layout">
        <el-card class="glass-card detail-overview detail-skeleton-card page-panel-card">
          <div class="novel-basic-info">
            <el-skeleton-item class="detail-skeleton-cover" variant="image" />
            <div class="novel-meta">
              <div class="meta-grid">
                <el-skeleton-item v-for="index in 4" :key="index" class="detail-skeleton-meta" variant="rect" />
              </div>
              <div class="detail-skeleton-tags">
                <el-skeleton-item v-for="index in 4" :key="`tag-${index}`" variant="button" />
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="glass-card novel-description detail-skeleton-card page-panel-card">
          <el-skeleton animated :rows="4" />
        </el-card>
      </div>

      <el-card class="glass-card chapters-section detail-skeleton-card page-panel-card">
        <el-skeleton animated :rows="6" />
      </el-card>
    </template>

    <template v-else-if="novelStore.currentNovel">
      <section class="detail-hero">
        <div class="detail-hero-left">
          <el-page-header @back="goBack" />
          <p class="hero-badge">小说详情</p>
          <h2 class="page-title">{{ novelStore.currentNovel.title }}</h2>
          <p class="hero-subtitle">已抓取 {{ novelStore.currentNovel.chapters_in_db }} 章，支持继续更新、导出与在线阅读。</p>
          <p v-if="readingProgress" class="reading-progress-hint">
            上次阅读到：{{ readingProgress.chapterTitle || '最近阅读章节' }}
          </p>
        </div>
        <div class="detail-hero-actions">
          <el-button type="primary" @click="handlePrimaryReadAction">
            {{ readingProgress ? '继续阅读' : '开始阅读' }}
          </el-button>
          <el-button v-if="readingProgress" plain @click="scrollToChapters">查看目录</el-button>
          <el-button type="info" :icon="RefreshRight" @click="refreshNovel">更新</el-button>
          <el-button type="success" :icon="Download" @click="downloadNovel" :loading="isDownloading">
            下载
          </el-button>
          <el-button :icon="View" @click="viewWordCloud">查看词云</el-button>
          <el-button type="danger" plain @click="deleteNovel" :loading="isDeleting">
            删除小说
          </el-button>
        </div>
      </section>

      <div class="novel-info">
        <el-card class="glass-card detail-overview page-panel-card">
          <div class="novel-basic-info">
            <div class="novel-cover">
              <el-image v-if="resolveCoverUrl()" :src="resolveCoverUrl()" fit="cover" :preview-src-list="[resolveCoverUrl()]">
                <template #error>
                  <div class="cover-placeholder">封面</div>
                </template>
              </el-image>
              <div v-else class="cover-placeholder">封面</div>
            </div>
            <div class="novel-meta">
              <div class="meta-grid">
                <div class="meta-block">
                  <span class="meta-label">作者</span>
                  <strong>{{ novelStore.currentNovel.author || '未知' }}</strong>
                </div>
                <div class="meta-block">
                  <span class="meta-label">状态</span>
                  <el-tag :type="getStatusTag(novelStore.currentNovel.status)">
                    {{ novelStore.currentNovel.status || '未知' }}
                  </el-tag>
                </div>
                <div class="meta-block">
                  <span class="meta-label">章节</span>
                  <div class="chapter-progress">
                    <el-tooltip
                      v-if="novelStore.currentNovel.chapters_in_db < (novelStore.currentNovel.total_chapters || 0)"
                      effect="dark"
                      content="正在爬取更多章节"
                      placement="top"
                    >
                      <span>
                        {{ novelStore.currentNovel.chapters_in_db }} /
                        {{ novelStore.currentNovel.total_chapters || '?' }}
                      </span>
                    </el-tooltip>
                    <span v-else>{{ novelStore.currentNovel.chapters_in_db }}</span>
                  </div>
                </div>
                <div class="meta-block">
                  <span class="meta-label">最近更新</span>
                  <strong>{{ formatDate(novelStore.currentNovel.last_crawled_at) }}</strong>
                </div>
              </div>

              <div class="novel-tags" v-if="novelStore.currentNovel.tags">
                <span class="meta-label">标签</span>
                <div class="tags-list">
                  <el-tag
                    v-for="tag in novelStore.currentNovel.tags.split('|')"
                    :key="tag"
                    size="small"
                    effect="plain"
                    class="novel-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="glass-card novel-description page-panel-card">
          <template #header>
            <div class="section-header">
              <h3>简介</h3>
            </div>
          </template>
          <p>{{ novelStore.currentNovel.description || '暂无简介' }}</p>
        </el-card>
      </div>

      <el-card id="chapters-section" class="glass-card chapters-section page-panel-card">
        <template #header>
          <div class="section-header">
            <h3>目录与分析</h3>
          </div>
        </template>

        <div v-if="loadingChapters && chapters.length === 0" class="chapters-skeleton">
          <el-skeleton animated :rows="6" />
        </div>
        <div v-else>
          <el-tabs v-model="chaptersTab">
            <el-tab-pane label="章节列表" name="list">
              <div v-if="chapters.length > 0">
                <div class="chapters-mobile-list">
                  <article
                    v-for="chapter in chapters"
                    :key="`mobile-${chapter.id}`"
                    class="chapter-mobile-card page-subtle-shell"
                    @click="openChapter(chapter)"
                  >
                    <div class="chapter-mobile-header">
                      <div>
                        <span class="chapter-mobile-index">第 {{ chapter.index }} 章</span>
                        <h4>{{ chapter.title }}</h4>
                      </div>
                      <el-button type="primary" plain size="small" @click.stop="openChapter(chapter)">
                        阅读
                      </el-button>
                    </div>
                    <p class="chapter-mobile-time">获取时间：{{ formatDate(chapter.fetched_at) }}</p>
                  </article>
                </div>

                <el-table
                  :data="chapters"
                  style="width: 100%"
                  @row-click="openChapter"
                  class="chapters-table-desktop"
                >
                  <el-table-column prop="index" label="章节" width="80" />
                  <el-table-column prop="title" label="标题" min-width="220" />
                  <el-table-column label="获取时间" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.fetched_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column width="100">
                    <template #default="{ row }">
                      <el-button type="primary" size="small" text @click.stop="openChapter(row)">
                        阅读
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <el-empty v-else description="暂无章节" />
              <div class="chapters-pagination" v-if="totalChapters > 0">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="perPage"
                  layout="total, prev, pager, next, jumper"
                  :total="totalChapters"
                  @current-change="handlePageChange"
                />
              </div>
            </el-tab-pane>

            <el-tab-pane label="词云视图" name="wordcloud">
              <div class="wordcloud-container">
                <el-image v-if="wordCloudSrc" :src="wordCloudSrc" fit="contain" class="wordcloud-image" />
                <el-empty v-else description="词云加载中..." />
                <p class="wordcloud-note">词云会根据小说内容自动生成，展示出现频率较高的词语。</p>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>

      <el-dialog v-model="wordCloudDialogVisible" title="词云视图" width="80%" center>
        <div class="wordcloud-dialog-content">
          <el-image v-if="wordCloudSrc" :src="wordCloudSrc" fit="contain" style="width: 100%" />
          <el-empty v-else description="正在加载词云..." />
        </div>
      </el-dialog>

      <el-dialog v-model="downloadOptions.visible" title="下载选项" width="400px">
        <el-form label-position="top">
          <el-form-item label="文件格式">
            <el-select v-model="downloadOptions.format" style="width: 100%">
              <el-option value="epub" label="EPUB文件" />
              <el-option value="txt" label="文本文件 (TXT)" disabled />
              <el-option value="pdf" label="PDF文件" disabled />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="downloadOptions.includeImages">包含封面图片</el-checkbox>
          </el-form-item>
        </el-form>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="downloadOptions.visible = false">取消</el-button>
            <el-button type="primary" @click="downloadNovel">下载</el-button>
          </div>
        </template>
      </el-dialog>
    </template>

    <div v-else-if="novelStore.error" class="novel-error">
      <el-result icon="error" :title="novelStore.error" sub-title="无法加载小说信息">
        <template #extra>
          <el-button type="primary" @click="fetchNovelDetails">重试</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { RefreshRight, View, Download } from '@element-plus/icons-vue'
import { useNovelStore } from '../store'
import { showConfirmDialog } from '../utils/confirmDialog'
import api from '../api'
import type { ChapterSummary } from '../api'
import {
  resolveQueuedNovelErrorPresentation,
  resolveQueuedNovelSuccessMessage,
} from '../composables/useNovelTaskFeedback'
import { loadReadingProgress, type ReadingProgress } from '../composables/useReaderPreferences'

const route = useRoute()
const router = useRouter()
const novelStore = useNovelStore()

const novelId = computed(() => route.params.novelId as string)
const loadingChapters = ref(false)
const chapters = ref<ChapterSummary[]>([])
const totalChapters = ref(0)
const currentPage = ref(1)
const perPage = ref(50)
const chaptersTab = ref<'list' | 'wordcloud'>('list')
const wordCloudSrc = ref<string>('')
const wordCloudDialogVisible = ref(false)
const isDownloading = ref(false)
const isDeleting = ref(false)
const readingProgress = ref<ReadingProgress | null>(null)
const showDetailSkeleton = computed(
  () => novelStore.isLoading && !novelStore.currentNovel && !novelStore.error,
)
const downloadOptions = ref({
  visible: false,
  format: 'epub',
  includeImages: true,
})

const refreshReadingProgress = () => {
  readingProgress.value = novelId.value ? loadReadingProgress(novelId.value) : null
}

const fetchNovelDetails = async () => {
  if (!novelId.value) return
  await novelStore.fetchNovelDetails(novelId.value)
  refreshReadingProgress()
  fetchChapters()
}

const fetchChapters = async () => {
  if (!novelId.value) return
  loadingChapters.value = true
  try {
    const response = await api.Novels.listChapters(novelId.value, currentPage.value, perPage.value)
    if ('error' in response) {
      ElMessage.error(response.error)
      return
    }
    chapters.value = response.items
    totalChapters.value = response.total
  } catch {
    ElMessage.error('获取章节列表失败')
  } finally {
    loadingChapters.value = false
  }
}

const handlePageChange = () => {
  fetchChapters()
}

const openChapter = (chapter: ChapterSummary) => {
  router.push(`/novel/${novelId.value}/chapter/${chapter.id}`)
}

const goBack = () => router.back()

const scrollToChapters = () => {
  document.getElementById('chapters-section')?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

const continueReading = () => {
  if (!novelId.value || !readingProgress.value?.chapterId) {
    scrollToChapters()
    return
  }
  router.push(`/novel/${novelId.value}/chapter/${readingProgress.value.chapterId}`)
}

const handlePrimaryReadAction = () => {
  if (readingProgress.value?.chapterId) {
    continueReading()
    return
  }
  scrollToChapters()
}

const refreshNovel = async () => {
  if (!novelId.value) return
  try {
    const response = await novelStore.addNovel(novelId.value)
    if (response) {
      ElMessage.success(resolveQueuedNovelSuccessMessage('refresh'))
      return
    }

    const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '更新失败')
    ElMessage[presentation.type](presentation.message)
  } catch {
    const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '更新失败')
    ElMessage[presentation.type](presentation.message)
  }
}

const deleteNovel = async () => {
  if (!novelId.value || !novelStore.currentNovel) return

  try {
    await showConfirmDialog(
      '确定要删除这本小说吗？已抓取章节、词云和导出文件会一起清理。若仍有进行中的任务将无法删除。',
      '删除小说',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }

  isDeleting.value = true
  try {
    const success = await novelStore.deleteNovel(novelId.value)
    if (success) {
      ElMessage.success('小说已删除')
      router.push('/novels')
    } else {
      ElMessage.error(novelStore.error || '删除小说失败')
    }
  } finally {
    isDeleting.value = false
  }
}

const downloadNovel = async () => {
  if (!novelId.value) return

  isDownloading.value = true

  try {
    const response = await api.Novels.fetchNovelBlob(novelId.value)

    if ('error' in response) {
      ElMessage.error(response.error)
      return
    }

    const blob = response as Blob
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `${novelStore.currentNovel?.title || 'novel'}.epub`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('下载开始')
    downloadOptions.value.visible = false
  } catch {
    ElMessage.error('下载失败，请重试')
  } finally {
    isDownloading.value = false
  }
}

async function loadWordCloud() {
  if (!novelId.value) return
  wordCloudSrc.value = ''
  try {
    const response = await api.Stats.fetchWordCloudBlob(novelId.value)
    if (typeof response === 'string') {
      wordCloudSrc.value = response
    } else if ('error' in response) {
      ElMessage.error(response.error)
    }
  } catch {
    ElMessage.error('词云加载失败')
  }
}

watch(chaptersTab, async (tab) => {
  if (tab === 'wordcloud' && !wordCloudSrc.value) {
    await loadWordCloud()
  }
})

function viewWordCloud() {
  wordCloudDialogVisible.value = true
  if (!wordCloudSrc.value) loadWordCloud()
}

function resolveCoverUrl(): string {
  return novelStore.currentNovel?.cover_image_url || ''
}

function getStatusTag(status: string | null): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (!status) return ''
  if (status.includes('完结')) return 'success'
  if (status.includes('连载')) return 'warning'
  return 'info'
}

function formatDate(dateStr: string | null): string {
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
  () => route.params.novelId,
  (newNovelId) => {
    if (newNovelId) {
      currentPage.value = 1
      refreshReadingProgress()
      fetchNovelDetails()
    }
  },
)

onMounted(() => {
  refreshReadingProgress()
  fetchNovelDetails()
})
</script>

<style scoped>
.novel-detail-container {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-bottom: 40px;
}

.detail-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
  padding: 22px 24px;
  border-radius: 18px;
  background: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow: var(--shell-glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.34);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(155%);
}

.hero-badge {
  margin: 10px 0 8px;
  color: var(--text-tertiary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 8px;
  color: var(--text-secondary);
  max-width: 720px;
}

.reading-progress-hint {
  margin: 10px 0 0;
  color: var(--accent-strong);
  font-size: 14px;
  font-weight: 600;
}

.detail-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-start;
}

.chapters-mobile-list {
  display: none;
}

.chapter-mobile-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 14px 14px;
  cursor: pointer;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 24px, rgba(84, 227, 255, 0.04) 24px, rgba(84, 227, 255, 0.04) 25px),
    var(--panel-subtle-bg);
}

.chapter-mobile-card::before {
  content: 'CHAPTER NODE';
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: var(--accent-strong);
  opacity: 0.82;
}

.chapter-mobile-card::after {
  content: '';
  position: absolute;
  top: 12px;
  right: 12px;
  width: 44px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet));
}

.chapter-mobile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.chapter-mobile-index {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  margin-bottom: 8px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.14);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.1), rgba(157, 123, 255, 0.08));
  color: var(--accent-strong);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.chapter-mobile-header h4 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
  text-shadow: 0 0 16px rgba(84, 227, 255, 0.06);
}

.chapter-mobile-time {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin: 0;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
  color: var(--text-secondary);
  font-size: 12px;
}

.chapter-mobile-header :deep(.el-button) {
  min-width: 88px;
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.08);
}

.detail-overview,
.novel-description,
.chapters-section {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.detail-overview .el-card__body),
:deep(.novel-description .el-card__body),
:deep(.chapters-section .el-card__body) {
  padding: 24px;
}

.detail-skeleton-layout {
  align-items: stretch;
}

.detail-skeleton-card {
  overflow: hidden;
}

.detail-skeleton-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-skeleton-cover {
  flex-shrink: 0;
  width: 240px;
  height: 320px;
  border-radius: 14px;
}

.detail-skeleton-meta {
  height: 92px;
  border-radius: 14px;
}

.detail-skeleton-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chapters-skeleton {
  padding: 12px 4px;
}

.novel-basic-info {
  display: flex;
  gap: 28px;
}

.novel-cover {
  position: relative;
  flex-shrink: 0;
  width: 240px;
  height: 320px;
  overflow: hidden;
  border-radius: 14px;
  background: var(--surface-muted);
  border: 1px solid rgba(84, 227, 255, 0.16);
  box-shadow: inset 0 0 0 1px var(--border-color-light), 0 0 22px rgba(84, 227, 255, 0.08);
}

.novel-cover::after {
  content: 'ARCHIVE';
  position: absolute;
  left: 12px;
  bottom: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(9, 17, 38, 0.62);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.novel-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.meta-block {
  position: relative;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.meta-block::before {
  content: '';
  position: absolute;
  top: 0;
  left: 14px;
  right: 14px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-violet), transparent);
  opacity: 0.7;
}

.meta-label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chapter-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-weight: 600;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.section-header h3 {
  margin: 0;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.novel-description p {
  margin: 0;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid rgba(84, 227, 255, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
  line-height: 1.8;
  white-space: pre-line;
  color: var(--text-secondary);
}

.chapters-table-desktop {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.chapters-table-desktop .el-table__row .el-button) {
  box-shadow: 0 0 14px rgba(84, 227, 255, 0.06);
}

.chapters-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.wordcloud-container {
  text-align: center;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.wordcloud-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.1));
}

html[data-theme='dark'] .wordcloud-image {
  background: linear-gradient(180deg, rgba(30, 45, 68, 0.4), rgba(17, 25, 39, 0.18));
}

.wordcloud-note {
  margin-top: 20px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.wordcloud-dialog-content {
  display: flex;
  justify-content: center;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  font-size: 14px;
  font-weight: 700;
}

.novel-error {
  margin-top: 20px;
}

@media (max-width: 900px) {
  .novel-basic-info {
    flex-direction: column;
  }

  .novel-cover {
    width: 100%;
    height: 380px;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .detail-hero {
    padding: 20px;
  }

  .detail-hero-actions {
    width: 100%;
    gap: 8px;
  }

  .detail-hero-actions .el-button {
    flex: 1 1 calc(50% - 8px);
    margin-left: 0;
  }

  :deep(.detail-overview .el-card__body),
  :deep(.novel-description .el-card__body),
  :deep(.chapters-section .el-card__body) {
    padding: 18px;
  }

  .novel-basic-info {
    gap: 18px;
  }

  .novel-cover {
    height: 300px;
  }

  .meta-block {
    padding: 14px;
  }

  .chapters-mobile-list {
    display: grid;
    gap: 12px;
  }

  .chapters-table-desktop {
    display: none;
  }

  .chapters-pagination {
    margin-top: 18px;
    padding: 12px;
  }

  :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
  }
}

@media (max-width: 520px) {
  .detail-hero-actions .el-button {
    flex-basis: 100%;
    width: 100%;
  }

  .chapter-mobile-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
