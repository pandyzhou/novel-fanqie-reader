<template>
  <div class="novels-container">
    <section class="novels-hero">
      <div>
        <p class="hero-badge">书库概览</p>
        <h2 class="page-title">小说列表</h2>
        <p class="hero-subtitle">查看已入库小说，按最近抓取时间持续积累你的本地小说资产。</p>
      </div>
      <el-button type="primary" @click="router.push('/upload')">添加小说</el-button>
    </section>

    <el-card class="glass-card novels-card page-panel-card">
      <div class="novels-header">
        <div class="novels-filters">
          <el-select v-model="perPage" placeholder="每页显示" @change="handlePerPageChange">
            <el-option :value="10" label="10条/页" />
            <el-option :value="20" label="20条/页" />
            <el-option :value="50" label="50条/页" />
          </el-select>
        </div>
        <el-text type="info">当前共 {{ novelStore.pagination.total }} 本小说</el-text>
      </div>

      <div v-if="novelStore.novels.length > 0" class="novels-mobile-list">
        <article
          v-for="novel in novelStore.novels"
          :key="`mobile-${String(novel.id)}`"
          class="novel-mobile-card page-subtle-shell"
          @click="handleRowClick(novel)"
        >
          <div class="novel-mobile-main">
            <div class="novel-cover novel-cover-mobile">
              <el-image v-if="resolveCoverUrl(novel)" :src="resolveCoverUrl(novel)" fit="cover" :preview-src-list="[resolveCoverUrl(novel)]">
                <template #error>
                  <div class="cover-placeholder">封面</div>
                </template>
              </el-image>
              <div v-else class="cover-placeholder">封面</div>
            </div>

            <div class="novel-mobile-body">
              <div class="novel-mobile-header">
                <router-link :to="'/novel/' + String(novel.id)" class="novel-title" @click.stop>
                  {{ novel.title }}
                </router-link>
                <el-tag :type="getStatusTag(novel.status)">
                  {{ novel.status || '未知' }}
                </el-tag>
              </div>

              <p class="novel-mobile-author">{{ novel.author || '未知作者' }}</p>

              <div class="novel-mobile-meta">
                <span>章节 {{ novel.total_chapters || 0 }}</span>
                <span>更新 {{ formatDate(novel.last_crawled_at) }}</span>
              </div>

              <div class="novel-tags novel-tags-mobile">
                <template v-if="novel.tags">
                  <el-tag
                    v-for="tag in novel.tags.split('|')"
                    :key="`${String(novel.id)}-${tag}`"
                    size="small"
                    effect="plain"
                    class="novel-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </template>
                <span v-else class="novel-meta-muted">暂无标签</span>
              </div>
            </div>
          </div>

          <div class="novel-mobile-actions">
            <el-button type="primary" plain @click.stop="handleRowClick(novel)">查看详情</el-button>
            <el-button type="danger" plain @click.stop="deleteNovel(novel)">删除</el-button>
          </div>
        </article>
      </div>

      <el-empty v-else-if="!novelStore.isLoading" class="novels-mobile-empty" description="暂无小说" />

      <el-table
        v-loading="novelStore.isLoading"
        :data="novelStore.novels"
        style="width: 100%"
        @row-click="handleRowClick"
        class="novels-table novels-table-desktop"
      >
        <el-table-column width="88">
          <template #default="{ row }">
            <div class="novel-cover">
              <el-image v-if="resolveCoverUrl(row)" :src="resolveCoverUrl(row)" fit="cover" :preview-src-list="[resolveCoverUrl(row)]">
                <template #error>
                  <div class="cover-placeholder">封面</div>
                </template>
              </el-image>
              <div v-else class="cover-placeholder">封面</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="标题" min-width="220">
          <template #default="{ row }">
            <router-link :to="'/novel/' + String(row.id)" class="novel-title">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>

        <el-table-column prop="author" label="作者" min-width="120" />

        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ row.status || '未知' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="total_chapters" label="章节数" width="100" />

        <el-table-column label="标签" min-width="170">
          <template #default="{ row }">
            <div class="novel-tags">
              <template v-if="row.tags">
                <el-tag
                  v-for="tag in row.tags.split('|')"
                  :key="tag"
                  size="small"
                  effect="plain"
                  class="novel-tag"
                >
                  {{ tag }}
                </el-tag>
              </template>
              <span v-else>-</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最近更新" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_crawled_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" text @click.stop="deleteNovel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="novels-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="perPage"
          layout="total, prev, pager, next, jumper"
          :total="novelStore.pagination.total"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { NovelSummary } from '../api'
import { useNovelStore } from '../store'
import { showConfirmDialog } from '../utils/confirmDialog'

const router = useRouter()
const novelStore = useNovelStore()

const currentPage = ref(1)
const perPage = ref(10)

const fetchNovels = async () => {
  await novelStore.fetchNovels(currentPage.value, perPage.value)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchNovels()
}

const handlePerPageChange = () => {
  currentPage.value = 1
  fetchNovels()
}

const handleRowClick = (row: NovelSummary) => {
  router.push(`/novel/${String(row.id)}`)
}

const resolveCoverUrl = (row: NovelSummary): string => row.cover_image_url || ''

const deleteNovel = async (row: NovelSummary) => {
  try {
    await showConfirmDialog(
      `确定要删除《${row.title}》吗？已抓取章节、词云和导出文件会一起清理。若存在进行中的任务将无法删除。`,
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

  const success = await novelStore.deleteNovel(row.id)
  if (success) {
    ElMessage.success('小说已删除')
    await fetchNovels()
  } else {
    ElMessage.error(novelStore.error || '删除小说失败')
  }
}

const getStatusTag = (status: string | null): '' | 'success' | 'warning' | 'info' | 'danger' => {
  if (!status) return ''

  if (status.includes('完结')) return 'success'
  if (status.includes('连载')) return 'warning'
  return 'info'
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

watch([currentPage, perPage], () => {
  fetchNovels()
})

onMounted(() => {
  fetchNovels()
})
</script>

<style scoped>
.novels-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 32px;
}

.novels-hero {
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

.novels-card {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.novels-card .el-card__body) {
  padding: 24px;
}

.novels-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
  flex-wrap: wrap;
}

.novels-filters {
  display: flex;
  gap: 10px;
}

.novels-mobile-list,
.novels-mobile-empty {
  display: none;
}

.novel-mobile-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 14px 14px;
  cursor: pointer;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.04) 26px, rgba(84, 227, 255, 0.04) 27px),
    var(--panel-subtle-bg);
}

.novel-mobile-card::before {
  content: 'ARCHIVE NODE';
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: var(--accent-strong);
  opacity: 0.82;
}

.novel-mobile-card::after {
  content: '';
  position: absolute;
  top: 12px;
  right: 12px;
  width: 44px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet));
  opacity: 0.9;
}

.novel-mobile-main {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.novel-mobile-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.novel-mobile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.novel-mobile-author,
.novel-meta-muted {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.novel-mobile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.novel-mobile-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.14);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.1), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.novel-tags-mobile {
  min-height: 24px;
}

.novel-mobile-actions {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
}

.novel-mobile-actions .el-button {
  flex: 1;
}

:deep(.novels-table) {
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.32), rgba(255, 255, 255, 0.08));
  overflow: hidden;
}

html[data-theme='dark'] :deep(.novels-table) {
  background: linear-gradient(180deg, rgba(30, 45, 68, 0.42), rgba(17, 25, 39, 0.16));
}

.novels-pagination {
  margin-top: 22px;
  display: flex;
  justify-content: center;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.novel-cover {
  width: 60px;
  height: 80px;
  overflow: hidden;
  border-radius: 10px;
  background: var(--surface-muted);
  box-shadow: inset 0 0 0 1px var(--border-color-light);
}

.novel-cover-mobile {
  width: 78px;
  height: 104px;
  flex-shrink: 0;
  position: relative;
  border: 1px solid rgba(84, 227, 255, 0.18);
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.novel-cover-mobile::after {
  content: 'LIB';
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(9, 17, 38, 0.58);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
}

.novel-title {
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 700;
  text-shadow: 0 0 16px rgba(84, 227, 255, 0.08);
}

.novel-title:hover {
  text-decoration: underline;
}

.novel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.novel-tag {
  margin-right: 0;
}

@media (max-width: 768px) {
  .novels-hero {
    padding: 20px;
  }

  :deep(.novels-card .el-card__body) {
    padding: 18px;
  }

  .novels-header {
    padding: 12px;
    margin-bottom: 16px;
  }

  .novels-filters {
    width: 100%;
  }

  :deep(.novels-filters .el-select) {
    width: 100%;
  }

  .novels-mobile-list {
    display: grid;
    gap: 14px;
  }

  .novels-mobile-empty {
    display: block;
  }

  .novels-table-desktop {
    display: none;
  }

  .novels-pagination {
    margin-top: 18px;
    padding: 12px;
  }
}

@media (max-width: 520px) {
  .novel-mobile-main {
    gap: 12px;
  }

  .novel-mobile-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .novel-mobile-actions {
    flex-direction: column;
  }
}
</style>
