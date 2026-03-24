<template>
  <div class="chapter-container" v-loading="novelStore.isLoading">
    <section class="chapter-hero">
      <div>
        <el-page-header @back="goBack" />
        <p class="hero-badge">阅读模式</p>
        <h2 class="page-title">章节阅读</h2>
        <p class="hero-subtitle">支持阅读主题、排版调节、进度记忆与键盘快捷翻页。</p>
      </div>
      <div class="chapter-nav compact-nav">
        <el-button :disabled="!hasPrevChapter" @click="navigateToChapter('prev')" :icon="ArrowLeft" type="primary" plain>
          上一章
        </el-button>
        <el-dropdown @command="handleCommand">
          <el-button type="primary">
            目录
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="chapter-dropdown-menu">
              <el-dropdown-item
                v-for="chapter in nearbyChapters"
                :key="chapter.id"
                :command="chapter.id"
                :class="{ 'current-chapter': chapter.id === chapterId }"
              >
                {{ chapter.title }}
              </el-dropdown-item>
              <el-dropdown-item divided command="all">查看全部章节</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button :disabled="!hasNextChapter" @click="navigateToChapter('next')" :icon="ArrowRight" type="primary" plain>
          下一章
        </el-button>
      </div>
    </section>

    <div class="chapter-content-wrapper" v-if="novelStore.currentChapter">
      <div class="chapter-info">
        <div>
          <h1 class="chapter-title">{{ novelStore.currentChapter.title }}</h1>
          <p class="chapter-subtitle">当前正在阅读本章内容，空格键向下翻页，方向键可切换章节。</p>
          <div class="chapter-meta-tags">
            <el-tag effect="plain" size="small">字号 {{ readerPreferences.fontSize }}px</el-tag>
            <el-tag effect="plain" size="small">{{ activeThemeOption.label }}</el-tag>
            <el-tag effect="plain" size="small">行距 {{ readerPreferences.lineHeight.toFixed(1) }}</el-tag>
          </div>
        </div>

        <div class="reading-settings">
          <el-button-group>
            <el-tooltip content="减小字体" placement="top">
              <el-button @click="decreaseFontSize" :icon="Minus" plain />
            </el-tooltip>
            <el-tooltip content="增大字体" placement="top">
              <el-button @click="increaseFontSize" :icon="Plus" plain />
            </el-tooltip>
          </el-button-group>

          <el-tooltip content="快速切换夜间主题" placement="top">
            <el-button
              @click="toggleNightTheme"
              :icon="readerPreferences.theme === 'dark' || readerPreferences.theme === 'oled' ? Moon : Sunny"
              plain
              type="default"
            />
          </el-tooltip>

          <el-tooltip content="阅读设置" placement="top">
            <el-button @click="settingsDrawerVisible = true" :icon="Setting" plain type="primary" />
          </el-tooltip>
        </div>
      </div>

      <div
        class="chapter-content"
        :class="[`theme-${readerPreferences.theme}`]"
        :style="chapterContentStyle"
        v-html="novelStore.currentChapter.content"
      ></div>

      <div class="chapter-footer">
        <div class="chapter-nav">
          <el-button :disabled="!hasPrevChapter" @click="navigateToChapter('prev')" :icon="ArrowLeft" type="primary" plain>
            上一章
          </el-button>

          <el-button @click="router.push(`/novel/${novelId}`)" type="primary">返回目录</el-button>

          <el-button :disabled="!hasNextChapter" @click="navigateToChapter('next')" :icon="ArrowRight" type="primary" plain>
            下一章
          </el-button>
        </div>
      </div>
    </div>

    <div class="chapter-error" v-else-if="novelStore.error">
      <el-result icon="error" :title="novelStore.error" sub-title="无法加载章节内容">
        <template #extra>
          <el-button type="primary" @click="fetchChapterContent">重试</el-button>
          <el-button @click="router.push(`/novel/${novelId}`)">返回小说页面</el-button>
        </template>
      </el-result>
    </div>

    <el-drawer v-model="settingsDrawerVisible" title="阅读设置" size="360px" destroy-on-close>
      <div class="reader-settings-panel">
        <section class="settings-block">
          <div class="settings-header">
            <h3>字体大小</h3>
            <span>{{ readerPreferences.fontSize }}px</span>
          </div>
          <el-slider v-model="readerPreferences.fontSize" :min="14" :max="30" :step="1" show-input />
        </section>

        <section class="settings-block">
          <div class="settings-header">
            <h3>背景主题</h3>
            <span>{{ activeThemeOption.label }}</span>
          </div>
          <el-radio-group v-model="readerPreferences.theme" class="theme-selector">
            <el-radio-button v-for="option in themeOptions" :key="option.value" :label="option.value">
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
          <p class="settings-description">{{ activeThemeOption.description }}</p>
        </section>

        <section class="settings-block">
          <div class="settings-header">
            <h3>行距</h3>
            <span>{{ readerPreferences.lineHeight.toFixed(1) }}</span>
          </div>
          <el-slider v-model="readerPreferences.lineHeight" :min="1.4" :max="2.6" :step="0.1" show-input />
        </section>

        <section class="settings-block">
          <div class="settings-header">
            <h3>段间距</h3>
            <span>{{ readerPreferences.paragraphSpacing.toFixed(1) }}em</span>
          </div>
          <el-slider v-model="readerPreferences.paragraphSpacing" :min="0.5" :max="2.5" :step="0.1" show-input />
        </section>

        <section class="settings-block keyboard-hints">
          <div class="settings-header">
            <h3>快捷键提示</h3>
          </div>
          <ul>
            <li><kbd>←</kbd> 上一章</li>
            <li><kbd>→</kbd> 下一章</li>
            <li><kbd>Space</kbd> 向下翻页</li>
          </ul>
        </section>

        <div class="settings-footer">
          <el-button @click="resetPreferences">恢复默认</el-button>
          <el-button type="primary" @click="settingsDrawerVisible = false">完成</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, ArrowDown, Minus, Plus, Moon, Sunny, Setting } from '@element-plus/icons-vue'
import { useNovelStore } from '../store'
import api from '../api'
import type { ChapterSummary } from '../api'
import {
  resetReaderPreferences,
  saveReaderPreferences,
  saveReadingProgress,
  loadReadingProgress,
  useReaderPreferences,
  type ReaderTheme,
} from '../composables/useReaderPreferences'

const CHAPTER_WINDOW_SIZE = 20

const themeOptions: Array<{ value: ReaderTheme; label: string; description: string }> = [
  { value: 'light', label: '浅色', description: '保持页面默认浅色背景，适合白天阅读。' },
  { value: 'dark', label: '深色', description: '深色背景配合浅色文字，适合夜间使用。' },
  { value: 'sepia', label: '羊皮纸', description: '偏暖的纸张色调，更接近传统阅读器。' },
  { value: 'eye-care', label: '护眼绿', description: '柔和豆沙绿色，降低长时间阅读疲劳。' },
  { value: 'oled', label: '纯黑', description: '纯黑背景，适合 OLED 屏幕夜间阅读。' },
]

const route = useRoute()
const router = useRouter()
const novelStore = useNovelStore()
const { preferences: readerPreferences } = useReaderPreferences()

const novelId = computed(() => route.params.novelId as string)
const chapterId = computed(() => route.params.chapterId as string)
const nearbyChapters = ref<ChapterSummary[]>([])
const prevChapterId = ref<string | null>(null)
const nextChapterId = ref<string | null>(null)
const settingsDrawerVisible = ref(false)
const hasPrevChapter = computed(() => !!prevChapterId.value)
const hasNextChapter = computed(() => !!nextChapterId.value)
const activeThemeOption = computed(
  () => themeOptions.find((option) => option.value === readerPreferences.theme) || themeOptions[0],
)
const chapterContentStyle = computed(() => ({
  fontSize: `${readerPreferences.fontSize}px`,
  lineHeight: `${readerPreferences.lineHeight}`,
  '--paragraph-spacing': `${readerPreferences.paragraphSpacing}em`,
}))

let scrollPersistTimer: ReturnType<typeof setTimeout> | null = null

const resolveChapterWindowPage = (chapterIndex: number) => {
  const normalizedIndex = Math.max(chapterIndex - 1, 0)
  return Math.floor(normalizedIndex / CHAPTER_WINDOW_SIZE) + 1
}

const persistReadingProgress = () => {
  if (!novelId.value || !chapterId.value || !novelStore.currentChapter) {
    return
  }

  saveReadingProgress(novelId.value, {
    chapterId: chapterId.value,
    chapterTitle: novelStore.currentChapter.title,
    scrollTop: window.scrollY,
    updatedAt: Date.now(),
  })
}

const schedulePersistReadingProgress = () => {
  if (scrollPersistTimer) {
    clearTimeout(scrollPersistTimer)
  }
  scrollPersistTimer = window.setTimeout(() => {
    persistReadingProgress()
    scrollPersistTimer = null
  }, 120)
}

const restoreReadingProgress = async () => {
  await nextTick()
  const savedProgress = loadReadingProgress(novelId.value)
  const targetScrollTop = savedProgress?.chapterId === chapterId.value ? savedProgress.scrollTop : 0
  window.scrollTo({ top: targetScrollTop, behavior: 'auto' })
}

const fetchNearbyChapters = async (chapterIndex: number) => {
  if (!novelId.value) return

  try {
    const response = await api.Novels.listChapters(
      novelId.value,
      resolveChapterWindowPage(chapterIndex),
      CHAPTER_WINDOW_SIZE,
    )
    if ('error' in response) {
      ElMessage.error(response.error)
      return
    }
    nearbyChapters.value = response.items
  } catch {
    ElMessage.error('获取章节列表失败')
  }
}

const fetchChapterContent = async () => {
  if (!novelId.value || !chapterId.value) return

  await novelStore.fetchChapterContent(novelId.value, chapterId.value)
  const currentChapter = novelStore.currentChapter
  if (!currentChapter) {
    return
  }

  prevChapterId.value = currentChapter.prev_chapter_id || null
  nextChapterId.value = currentChapter.next_chapter_id || null
  await fetchNearbyChapters(currentChapter.index)
  await restoreReadingProgress()
  persistReadingProgress()
}

const navigateToChapter = (direction: 'prev' | 'next') => {
  if (!novelId.value) return

  const targetChapterId = direction === 'prev' ? prevChapterId.value : nextChapterId.value
  if (!targetChapterId) return

  persistReadingProgress()
  router.push(`/novel/${novelId.value}/chapter/${targetChapterId}`)
}

const handleCommand = (command: string | number) => {
  persistReadingProgress()
  if (command === 'all') {
    router.push(`/novel/${novelId.value}`)
  } else {
    router.push(`/novel/${novelId.value}/chapter/${command}`)
  }
}

const goBack = () => {
  persistReadingProgress()
  router.push(`/novel/${novelId.value}`)
}

const increaseFontSize = () => {
  readerPreferences.fontSize = Math.min(readerPreferences.fontSize + 2, 30)
}

const decreaseFontSize = () => {
  readerPreferences.fontSize = Math.max(readerPreferences.fontSize - 2, 14)
}

const toggleNightTheme = () => {
  readerPreferences.theme =
    readerPreferences.theme === 'dark' || readerPreferences.theme === 'oled' ? 'light' : 'dark'
}

const resetPreferences = () => {
  Object.assign(readerPreferences, resetReaderPreferences())
}

const shouldIgnoreKeyboardShortcut = (event: KeyboardEvent) => {
  const target = event.target as HTMLElement | null
  if (!target) {
    return false
  }

  return (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.tagName === 'SELECT' ||
    target.isContentEditable
  )
}

const handleKeydown = (event: KeyboardEvent) => {
  if (settingsDrawerVisible.value || shouldIgnoreKeyboardShortcut(event)) {
    return
  }

  if (event.key === 'ArrowLeft' && hasPrevChapter.value) {
    event.preventDefault()
    navigateToChapter('prev')
    return
  }

  if (event.key === 'ArrowRight' && hasNextChapter.value) {
    event.preventDefault()
    navigateToChapter('next')
    return
  }

  if (event.code === 'Space') {
    event.preventDefault()
    window.scrollBy({ top: window.innerHeight * 0.85, behavior: 'smooth' })
  }
}

watch(
  () => ({
    fontSize: readerPreferences.fontSize,
    theme: readerPreferences.theme,
    lineHeight: readerPreferences.lineHeight,
    paragraphSpacing: readerPreferences.paragraphSpacing,
  }),
  (nextPreferences) => {
    saveReaderPreferences(nextPreferences)
  },
  { deep: true },
)

watch(
  () => [route.params.novelId, route.params.chapterId],
  ([newNovelId, newChapterId]) => {
    if (newNovelId && newChapterId) {
      fetchChapterContent()
    }
  },
)

onMounted(() => {
  fetchChapterContent()
  window.addEventListener('scroll', schedulePersistReadingProgress, { passive: true })
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  persistReadingProgress()
  window.removeEventListener('scroll', schedulePersistReadingProgress)
  window.removeEventListener('keydown', handleKeydown)
  if (scrollPersistTimer) {
    clearTimeout(scrollPersistTimer)
  }
})
</script>

<style scoped>
.chapter-container {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 60px;
}

.chapter-hero {
  display: flex;
  justify-content: space-between;
  gap: 18px;
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

.hero-subtitle,
.chapter-subtitle {
  margin-top: 8px;
  color: var(--text-secondary);
}

.compact-nav {
  align-self: center;
}

.chapter-content-wrapper {
  position: relative;
  border-radius: 20px;
  border: 1px solid var(--panel-raised-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(84, 227, 255, 0.04) 28px, rgba(84, 227, 255, 0.04) 29px),
    var(--panel-raised-bg);
  box-shadow: var(--panel-raised-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.24);
  padding: 34px 30px 30px;
}

.chapter-content-wrapper::before {
  content: 'READER CORE';
  position: absolute;
  top: 12px;
  left: 18px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: var(--accent-strong);
  opacity: 0.82;
}

.chapter-content-wrapper::after {
  content: '';
  position: absolute;
  top: 14px;
  right: 18px;
  width: 56px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet), var(--neon-pink));
}

.chapter-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
}

.chapter-title {
  margin: 0;
  font-size: clamp(26px, 3vw, 34px);
}

.chapter-meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

:deep(.chapter-meta-tags .el-tag) {
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.12), rgba(157, 123, 255, 0.08));
  border-color: rgba(84, 227, 255, 0.16);
  box-shadow: var(--panel-subtle-shadow), 0 0 16px rgba(84, 227, 255, 0.06);
}

.chapter-nav {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.compact-nav,
.chapter-footer .chapter-nav,
.reading-settings {
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
}

.reading-settings {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-content {
  --paragraph-spacing: 1em;
  --reader-frame: rgba(84, 227, 255, 0.12);
  --reader-scanline: rgba(84, 227, 255, 0.03);
  --reader-sheen: rgba(255, 255, 255, 0.08);
  --reader-glow: rgba(84, 227, 255, 0.06);
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 28px 24px;
  border-radius: 16px;
  border: 1px solid var(--reader-frame);
  font-family: 'Noto Serif SC', serif, 'Microsoft YaHei', '微软雅黑';
  text-align: justify;
  color: var(--reader-color, var(--text-primary));
  background: var(--reader-background, transparent);
  box-shadow: var(--reader-shadow, none), 0 0 22px var(--reader-glow);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.chapter-content::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, var(--reader-sheen), transparent 18%),
    repeating-linear-gradient(180deg, transparent, transparent 18px, var(--reader-scanline) 18px, var(--reader-scanline) 19px);
  opacity: 0.72;
}

.chapter-content::after {
  content: '';
  position: absolute;
  top: 12px;
  right: 12px;
  width: 58px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet), var(--neon-pink));
  opacity: 0.46;
}

.chapter-content.theme-light {
  --reader-color: var(--text-primary);
  --reader-frame: rgba(84, 227, 255, 0.16);
  --reader-scanline: rgba(84, 227, 255, 0.03);
  --reader-sheen: rgba(255, 255, 255, 0.12);
  --reader-glow: rgba(84, 227, 255, 0.06);
  --reader-background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(244, 247, 255, 0.48)),
    radial-gradient(circle at 12% 12%, rgba(84, 227, 255, 0.06), transparent 22%);
  --reader-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12), 0 18px 34px rgba(67, 60, 135, 0.08);
}

.chapter-content.theme-dark {
  --reader-color: #e5edf7;
  --reader-frame: rgba(84, 227, 255, 0.14);
  --reader-scanline: rgba(84, 227, 255, 0.028);
  --reader-sheen: rgba(255, 255, 255, 0.05);
  --reader-glow: rgba(84, 227, 255, 0.08);
  --reader-background:
    linear-gradient(180deg, rgba(17, 24, 39, 0.985), rgba(8, 15, 28, 0.95)),
    radial-gradient(circle at 14% 14%, rgba(84, 227, 255, 0.04), transparent 24%);
  --reader-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12), 0 18px 34px rgba(2, 6, 23, 0.26);
}

.chapter-content.theme-sepia {
  --reader-color: #5b4636;
  --reader-frame: rgba(139, 92, 59, 0.16);
  --reader-scanline: rgba(139, 92, 59, 0.024);
  --reader-sheen: rgba(255, 248, 232, 0.14);
  --reader-glow: rgba(139, 92, 59, 0.05);
  --reader-background:
    linear-gradient(180deg, rgba(244, 234, 214, 0.985), rgba(237, 224, 198, 0.95)),
    radial-gradient(circle at 14% 14%, rgba(139, 92, 59, 0.05), transparent 22%);
  --reader-shadow: inset 0 0 0 1px rgba(139, 92, 59, 0.1), 0 18px 34px rgba(91, 70, 54, 0.08);
}

.chapter-content.theme-eye-care {
  --reader-color: #244236;
  --reader-frame: rgba(36, 66, 54, 0.14);
  --reader-scanline: rgba(36, 66, 54, 0.022);
  --reader-sheen: rgba(236, 248, 234, 0.12);
  --reader-glow: rgba(36, 66, 54, 0.05);
  --reader-background:
    linear-gradient(180deg, rgba(220, 235, 216, 0.985), rgba(207, 228, 202, 0.95)),
    radial-gradient(circle at 14% 14%, rgba(36, 66, 54, 0.04), transparent 24%);
  --reader-shadow: inset 0 0 0 1px rgba(36, 66, 54, 0.08), 0 18px 34px rgba(36, 66, 54, 0.08);
}

.chapter-content.theme-oled {
  --reader-color: #f8fafc;
  --reader-frame: rgba(84, 227, 255, 0.18);
  --reader-scanline: rgba(84, 227, 255, 0.026);
  --reader-sheen: rgba(84, 227, 255, 0.03);
  --reader-glow: rgba(84, 227, 255, 0.1);
  --reader-background:
    linear-gradient(180deg, rgba(2, 6, 23, 0.995), rgba(1, 4, 12, 0.985)),
    radial-gradient(circle at 14% 14%, rgba(84, 227, 255, 0.04), transparent 22%);
  --reader-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18), 0 18px 34px rgba(2, 6, 23, 0.32);
}

.chapter-content :deep(*) {
  position: relative;
  z-index: 1;
}

.chapter-content :deep(p) {
  margin: 0 0 var(--paragraph-spacing);
  text-indent: 2em;
}

.chapter-content :deep(h1),
.chapter-content :deep(h2),
.chapter-content :deep(h3),
.chapter-content :deep(h4),
.chapter-content :deep(h5),
.chapter-content :deep(h6) {
  margin-top: calc(var(--paragraph-spacing) * 1.2);
  margin-bottom: calc(var(--paragraph-spacing) * 0.8);
}

.chapter-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
}

.chapter-footer {
  margin-top: 50px;
}

.chapter-dropdown-menu {
  min-width: 240px;
  max-height: 420px;
  overflow-y: auto;
}

.current-chapter {
  color: var(--accent-strong);
  font-weight: 700;
}

.chapter-error {
  margin-top: 10px;
}

.reader-settings-panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.settings-block {
  position: relative;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04)),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.settings-block::before {
  content: '';
  position: absolute;
  top: 0;
  left: 14px;
  right: 14px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-violet), transparent);
  opacity: 0.8;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.settings-header h3 {
  margin: 0;
  font-size: 16px;
}

.settings-header span,
.settings-description {
  color: var(--text-secondary);
  font-size: 13px;
}

.theme-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyboard-hints ul {
  margin: 12px 0 0;
  padding-left: 18px;
  color: var(--text-secondary);
}

.keyboard-hints li + li {
  margin-top: 8px;
}

kbd {
  display: inline-flex;
  min-width: 30px;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  color: var(--text-primary);
  box-shadow: var(--panel-subtle-shadow);
  font-family: inherit;
  font-size: 12px;
}

.settings-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .chapter-hero,
  .chapter-content-wrapper {
    padding: 20px;
  }

  .compact-nav {
    width: 100%;
  }

  .compact-nav.chapter-nav {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-items: stretch;
  }

  .compact-nav :deep(.el-dropdown),
  .compact-nav .el-button {
    width: 100%;
  }

  .compact-nav :deep(.el-dropdown > .el-button) {
    width: 100%;
  }

  .chapter-info {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 22px;
  }

  .reading-settings {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .chapter-nav {
    width: 100%;
  }

  .chapter-footer .chapter-nav {
    flex-direction: column;
  }

  .chapter-footer .chapter-nav .el-button {
    width: 100%;
  }

  .chapter-content {
    padding: 22px 18px;
  }

  .settings-block {
    padding: 14px;
  }

  .settings-footer {
    flex-direction: column-reverse;
  }

  .settings-footer .el-button {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .compact-nav.chapter-nav {
    grid-template-columns: 1fr;
  }

  .chapter-content-wrapper {
    padding: 16px;
  }

  .chapter-content {
    padding: 18px 14px;
  }
}
</style>
