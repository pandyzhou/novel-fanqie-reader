<template>
  <div class="load-more-section">
    <div :ref="setTriggerRef" class="load-more-trigger">
      <el-text v-if="hasMore" type="info">
        <el-icon class="loading-icon" v-if="loading"><Loading /></el-icon>
        {{ loading ? '正在自动加载更多结果…' : '下滑到底部将自动加载更多结果' }}
      </el-text>
      <el-text v-else type="info">已显示全部已获取的搜索结果</el-text>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  hasMore: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  'update:trigger': [element: HTMLElement | null]
}>()

const setTriggerRef = (el: Element | ComponentPublicInstance | null) => {
  emit('update:trigger', el instanceof HTMLElement ? el : null)
}
</script>

<style scoped>
.load-more-section {
  margin-top: 8px;
  display: flex;
  justify-content: center;
}

.load-more-trigger {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border-radius: 999px;
  background: var(--surface-muted);
  border: 1px solid var(--border-color);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.loading-icon {
  margin-right: 6px;
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
