<template>
  <div class="search-toolbar">
    <div class="toolbar-group">
      <el-select
        :model-value="sortField"
        class="toolbar-select"
        size="large"
        @update:model-value="emit('update:sortField', $event)"
      >
        <el-option v-for="option in SEARCH_SORT_OPTIONS" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
      <el-select
        :model-value="sortOrder"
        class="toolbar-select toolbar-order"
        size="large"
        @update:model-value="emit('update:sortOrder', $event)"
      >
        <el-option v-for="option in orderOptions" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
    </div>

    <div class="toolbar-group toolbar-switches">
      <el-switch
        :model-value="showCachedOnly"
        active-text="只看已缓存"
        @update:model-value="emit('update:showCachedOnly', $event)"
      />
      <el-switch
        :model-value="showReadyOnly"
        active-text="只看可读"
        @update:model-value="emit('update:showReadyOnly', $event)"
      />
    </div>

    <el-button
      type="primary"
      class="batch-download-button"
      :loading="batchDownloading"
      :disabled="downloadableCount === 0"
      @click="emit('batch-download')"
    >
      <el-icon><Download /></el-icon>
      一键下载当前结果（{{ downloadableCount }} 本）
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { SEARCH_ORDER_OPTIONS, SEARCH_SORT_OPTIONS } from './search.constants'
import type { SearchSortField, SearchSortOrder } from './search.types'

const props = defineProps<{
  sortField: SearchSortField
  sortOrder: SearchSortOrder
  showCachedOnly: boolean
  showReadyOnly: boolean
  batchDownloading: boolean
  downloadableCount: number
}>()

const emit = defineEmits<{
  'update:sortField': [value: SearchSortField]
  'update:sortOrder': [value: SearchSortOrder]
  'update:showCachedOnly': [value: boolean]
  'update:showReadyOnly': [value: boolean]
  'batch-download': []
}>()

const orderOptions = computed(() =>
  props.sortField === 'relevance'
    ? SEARCH_ORDER_OPTIONS.filter((option) => option.value === 'desc')
    : SEARCH_ORDER_OPTIONS,
)

watch(
  () => props.sortField,
  (value) => {
    if (value === 'relevance' && props.sortOrder !== 'desc') {
      emit('update:sortOrder', 'desc')
    }
  },
)
</script>

<style scoped>
.search-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, auto);
  gap: 16px;
  padding: 16px;
  border-radius: 14px;
  background: var(--surface-muted);
  border: 1px solid var(--border-color-light);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-switches {
  justify-content: flex-start;
}

.toolbar-select {
  min-width: 170px;
}

.toolbar-order {
  min-width: 120px;
}

.batch-download-button {
  justify-self: flex-end;
  min-height: 46px;
  padding-inline: 18px;
  border-radius: 12px;
}

@media (max-width: 1024px) {
  .search-toolbar {
    grid-template-columns: 1fr;
  }

  .batch-download-button {
    justify-self: stretch;
  }
}

@media (max-width: 768px) {
  .search-toolbar {
    gap: 14px;
    padding: 14px;
  }

  .toolbar-group {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-select,
  .toolbar-order,
  .batch-download-button {
    width: 100%;
  }

  .toolbar-switches {
    gap: 10px;
  }

  .toolbar-switches :deep(.el-switch) {
    justify-content: space-between;
    width: 100%;
    margin: 0;
  }
}
</style>
