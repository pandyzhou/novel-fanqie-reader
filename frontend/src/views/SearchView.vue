<template>
  <div class="search-container">
    <SearchHero :loaded-count="novelStore.searchResults.length" :visible-count="displayedResults.length" />

    <el-card class="search-panel page-panel-card">
      <div class="search-form">
        <el-input
          v-model="searchQuery"
          placeholder="输入小说名称或作者进行搜索"
          class="search-input"
          clearable
          :prefix-icon="Search"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch" :loading="searching">搜索</el-button>
      </div>

      <div class="search-tips" v-if="!hasSearched">
        <el-empty description="输入关键词开始搜索">
          <template #description>
            <p>你可以搜索小说名称或作者，找到你想看的小说。</p>
            <p>搜索结果支持自动加载、排序筛选，并可以一键下载当前结果。</p>
          </template>
        </el-empty>
      </div>

      <SearchResultsSection
        v-else
        :searching="searching"
        :store-loading="novelStore.isLoading"
        :search-results="novelStore.searchResults"
        :displayed-results="displayedResults"
        :last-search-query="lastSearchQuery"
        :search-per-page="novelStore.searchPerPage"
        :sort-field="sortField"
        :sort-order="sortOrder"
        :show-cached-only="showCachedOnly"
        :show-ready-only="showReadyOnly"
        :batch-downloading="batchDownloading"
        :downloadable-count="downloadableResults.length"
        :loading-id="addingNovelId"
        :is-preview-mode="isPreviewMode"
        :load-more-has-more="novelStore.searchHasMore"
        :load-more-loading="novelStore.searchLoadingMore"
        @update:sort-field="sortField = $event"
        @update:sort-order="sortOrder = $event"
        @update:show-cached-only="showCachedOnly = $event"
        @update:show-ready-only="showReadyOnly = $event"
        @batch-download="handleBatchDownload"
        @download-full="addNovel($event, false)"
        @download-preview="addNovel($event, true)"
        @update:load-more-trigger="setTriggerRef"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import SearchHero from '../components/search/SearchHero.vue'
import SearchResultsSection from '../components/search/SearchResultsSection.vue'
import {
  SEARCH_DEFAULT_SORT_FIELD,
  SEARCH_DEFAULT_SORT_ORDER,
} from '../components/search/search.constants'
import type { SearchSortField, SearchSortOrder } from '../components/search/search.types'
import { useSearchFilters } from '../composables/useSearchFilters'
import { useSearchLoadMore } from '../composables/useSearchLoadMore'
import {
  isAlreadyActiveTaskError,
  resolveQueuedNovelErrorPresentation,
  resolveQueuedNovelSuccessMessage,
} from '../composables/useNovelTaskFeedback'
import { useNovelStore } from '../store'

const novelStore = useNovelStore()

const searchQuery = ref('')
const lastSearchQuery = ref('')
const hasSearched = ref(false)
const searching = ref(false)
const addingNovelId = ref<string | null>(null)
const isPreviewMode = ref(false)
const batchDownloading = ref(false)

const sortField = ref<SearchSortField>(SEARCH_DEFAULT_SORT_FIELD)
const sortOrder = ref<SearchSortOrder>(SEARCH_DEFAULT_SORT_ORDER)
const showCachedOnly = ref(false)
const showReadyOnly = ref(false)

const effectiveSortOrder = computed<SearchSortOrder>(() =>
  sortField.value === 'relevance' ? 'desc' : sortOrder.value,
)

const { displayedResults, downloadableResults } = useSearchFilters(
  computed(() => novelStore.searchResults),
  sortField,
  effectiveSortOrder,
  showCachedOnly,
  showReadyOnly,
)

const canAutoLoadMore = computed(
  () =>
    hasSearched.value &&
    novelStore.searchHasMore &&
    !novelStore.searchLoadingMore &&
    !novelStore.isLoading &&
    !batchDownloading.value,
)

const { setTriggerRef } = useSearchLoadMore({
  enabled: computed(() => hasSearched.value && novelStore.searchResults.length > 0),
  canLoadMore: canAutoLoadMore,
  onLoadMore: () => novelStore.loadMoreSearchResults(),
})

const executeSearch = async (query: string) => {
  await novelStore.searchNovels(query, {
    sortField: sortField.value,
    sortOrder: effectiveSortOrder.value,
  })
}

const handleSearch = async () => {
  const trimmedQuery = searchQuery.value.trim()
  if (!trimmedQuery) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  lastSearchQuery.value = trimmedQuery

  try {
    await executeSearch(trimmedQuery)
    hasSearched.value = true
  } finally {
    searching.value = false
  }
}

watch(
  () => [sortField.value, effectiveSortOrder.value] as const,
  async ([nextSortField, nextSortOrder], [prevSortField, prevSortOrder]) => {
    if (!hasSearched.value || !lastSearchQuery.value) {
      return
    }

    if (nextSortField === prevSortField && nextSortOrder === prevSortOrder) {
      return
    }

    searching.value = true
    try {
      await novelStore.searchNovels(lastSearchQuery.value, {
        sortField: nextSortField,
        sortOrder: nextSortOrder,
      })
    } finally {
      searching.value = false
    }
  },
)

const handleBatchDownload = async () => {
  if (downloadableResults.value.length === 0) {
    ElMessage.warning('当前结果里没有需要加入队列的小说')
    return
  }

  const alreadyReadyCount = displayedResults.value.length - downloadableResults.value.length

  try {
    await ElMessageBox.confirm(
      `确认将当前结果中的 ${downloadableResults.value.length} 本小说加入下载队列吗？${alreadyReadyCount > 0 ? `\n其中 ${alreadyReadyCount} 本已可读，将自动跳过。` : ''}`,
      '批量下载确认',
      {
        type: 'info',
        confirmButtonText: '开始下载',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  batchDownloading.value = true
  let successCount = 0
  let skippedCount = alreadyReadyCount
  let failedCount = 0

  for (const novel of downloadableResults.value) {
    const response = await novelStore.addNovel(novel.id)
    if (response) {
      successCount += 1
      continue
    }

    const errorMessage = novelStore.error || ''
    if (isAlreadyActiveTaskError(errorMessage)) {
      skippedCount += 1
    } else {
      failedCount += 1
    }
  }

  batchDownloading.value = false

  if (failedCount === 0) {
    ElMessage.success(`批量下载完成：成功 ${successCount} 本，已跳过 ${skippedCount} 本。`)
  } else {
    ElMessage.warning(`批量下载完成：成功 ${successCount} 本，已跳过 ${skippedCount} 本，失败 ${failedCount} 本。`)
  }
}

const addNovel = async (novelId: string, isPreview: boolean) => {
  addingNovelId.value = novelId
  isPreviewMode.value = isPreview

  try {
    const maxChapters = isPreview ? 10 : undefined
    const response = await novelStore.addNovel(novelId, maxChapters)

    if (response) {
      ElMessage.success(resolveQueuedNovelSuccessMessage(isPreview ? 'preview' : 'full'))
      return
    }

    const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '添加小说失败')
    ElMessage[presentation.type](presentation.message)
  } catch {
    const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '添加小说失败')
    ElMessage[presentation.type](presentation.message)
  } finally {
    addingNovelId.value = null
    isPreviewMode.value = false
  }
}
</script>

<style scoped>
.search-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 32px;
}

.search-panel {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.search-panel .el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
}

.search-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

:deep(.search-input .el-input__wrapper) {
  min-height: 54px;
  border-radius: 18px;
}

:deep(.search-form .el-button) {
  min-height: 54px;
  padding-inline: 24px;
}

.search-tips {
  padding: 24px;
  border-radius: 18px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

@media (max-width: 768px) {
  :deep(.search-panel .el-card__body) {
    gap: 18px;
    padding: 18px;
  }

  .search-form {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 14px;
  }

  :deep(.search-form .el-button) {
    width: 100%;
  }

  .search-tips {
    padding: 18px 16px;
  }
}
</style>
