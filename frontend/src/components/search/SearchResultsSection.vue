<template>
  <div class="search-results">
    <div v-if="searching || (storeLoading && searchResults.length === 0)" class="search-loading">
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="searchResults.length === 0" class="no-results">
      <el-empty description="暂无搜索结果">
        <template #description>
          <p>找不到与“{{ lastSearchQuery }}”相关的小说</p>
          <p>请尝试其他关键词，或检查拼写是否正确</p>
        </template>
      </el-empty>
    </div>

    <div v-else class="results-content">
      <div class="results-header">
        <div>
          <h3>搜索结果：已加载 {{ searchResults.length }} 个结果</h3>
          <p class="results-summary">当前筛选后显示 {{ displayedResults.length }} 本，每批自动加载 {{ searchPerPage }} 条。</p>
        </div>
        <el-tag type="info">本地缓存已启用</el-tag>
      </div>

      <SearchToolbar
        :sort-field="sortField"
        :sort-order="sortOrder"
        :show-cached-only="showCachedOnly"
        :show-ready-only="showReadyOnly"
        :batch-downloading="batchDownloading"
        :downloadable-count="downloadableCount"
        @update:sort-field="emit('update:sortField', $event)"
        @update:sort-order="emit('update:sortOrder', $event)"
        @update:show-cached-only="emit('update:showCachedOnly', $event)"
        @update:show-ready-only="emit('update:showReadyOnly', $event)"
        @batch-download="emit('batch-download')"
      />

      <div v-if="displayedResults.length === 0" class="no-results filtered-empty">
        <el-empty description="当前筛选条件下暂无结果">
          <template #description>
            <p>当前已加载结果暂时不满足筛选条件。</p>
            <p>{{ filteredEmptyHint }}</p>
          </template>
        </el-empty>
      </div>

      <div v-else class="results-grid">
        <SearchResultCard
          v-for="novel in displayedResults"
          :key="novel.id"
          :novel="novel"
          :cover-url="resolveCoverUrl(novel.cover)"
          :loading-id="loadingId"
          :is-preview-mode="isPreviewMode"
          :batch-downloading="batchDownloading"
          @download-full="emit('download-full', $event)"
          @download-preview="emit('download-preview', $event)"
        />
      </div>

      <SearchLoadMore
        :has-more="loadMoreHasMore"
        :loading="loadMoreLoading"
        @update:trigger="emit('update:loadMoreTrigger', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NovelSearchResult } from '../../api'
import SearchLoadMore from './SearchLoadMore.vue'
import SearchResultCard from './SearchResultCard.vue'
import SearchToolbar from './SearchToolbar.vue'
import type { SearchSortField, SearchSortOrder } from './search.types'

const props = defineProps<{
  searching: boolean
  storeLoading: boolean
  searchResults: NovelSearchResult[]
  displayedResults: NovelSearchResult[]
  lastSearchQuery: string
  searchPerPage: number
  sortField: SearchSortField
  sortOrder: SearchSortOrder
  showCachedOnly: boolean
  showReadyOnly: boolean
  batchDownloading: boolean
  downloadableCount: number
  loadingId: string | null
  isPreviewMode: boolean
  loadMoreHasMore: boolean
  loadMoreLoading: boolean
}>()

const emit = defineEmits<{
  'update:sortField': [value: SearchSortField]
  'update:sortOrder': [value: SearchSortOrder]
  'update:showCachedOnly': [value: boolean]
  'update:showReadyOnly': [value: boolean]
  'batch-download': []
  'download-full': [novelId: string]
  'download-preview': [novelId: string]
  'update:loadMoreTrigger': [element: HTMLElement | null]
}>()

const filteredEmptyHint = computed(() =>
  props.loadMoreHasMore ? '继续下滑到底部，系统仍会尝试自动加载更多结果。' : '请调整筛选条件后重试。',
)

const resolveCoverUrl = (coverUrl: string | null | undefined) => coverUrl || ''
</script>

<style scoped>
.search-results,
.results-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.search-loading {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.04) 26px, rgba(84, 227, 255, 0.04) 27px),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.no-results,
.filtered-empty {
  padding: 8px 0;
}

.results-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.results-header h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.results-summary {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 14px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .search-results,
  .results-content {
    gap: 18px;
  }

  .results-header h3 {
    font-size: 18px;
  }

  .results-summary {
    font-size: 13px;
  }

  .results-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
