<template>
  <DashboardCard title="热门小说词云" body-class="wordcloud-panel" :loading="loading">
    <div v-if="items.length > 0" class="wordcloud-grid">
      <div v-for="cloud in items" :key="cloud.novelId" class="wordcloud-item page-subtle-shell">
        <h4>{{ cloud.novelTitle }}</h4>
        <el-image
          :src="cloud.wordCloudUrl"
          fit="contain"
          class="wordcloud-image"
          :preview-src-list="[cloud.wordCloudUrl]"
        />
      </div>
    </div>
    <el-empty v-else description="暂无词云数据" />
  </DashboardCard>
</template>

<script setup lang="ts">
import type { DashboardWordCloudItem } from './dashboard.types'
import DashboardCard from './DashboardCard.vue'

defineProps<{
  items: DashboardWordCloudItem[]
  loading: boolean
}>()
</script>

<style scoped>
.wordcloud-panel {
  padding: 4px;
  min-height: 300px;
}

.wordcloud-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.wordcloud-item {
  padding: 18px;
  text-align: center;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    var(--panel-subtle-bg);
}

.wordcloud-item h4 {
  margin: 0 0 14px;
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 800;
  text-shadow: 0 0 16px rgba(84, 227, 255, 0.1);
}

.wordcloud-image {
  width: 100%;
  height: 250px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0.22)),
    radial-gradient(circle at 18% 18%, rgba(84, 227, 255, 0.08), transparent 24%);
  box-shadow: var(--panel-subtle-shadow), 0 0 22px rgba(84, 227, 255, 0.08);
}

html[data-theme='dark'] .wordcloud-image {
  background:
    linear-gradient(180deg, rgba(24, 38, 76, 0.42), rgba(13, 21, 43, 0.22)),
    radial-gradient(circle at 18% 18%, rgba(84, 227, 255, 0.08), transparent 24%);
}
</style>
