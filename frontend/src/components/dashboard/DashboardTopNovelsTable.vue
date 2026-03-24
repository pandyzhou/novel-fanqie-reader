<template>
  <DashboardCard title="热门小说" body-class="table-panel" :loading="loading">
    <div class="top-table-shell page-table-shell">
      <el-table :data="novels" style="width: 100%" @row-click="handleRowClick">
      <el-table-column type="index" width="50" />
      <el-table-column width="80">
        <template #default="{ row }">
          <div class="novel-cover-small">
            <el-image v-if="resolveCoverUrl(row)" :src="resolveCoverUrl(row)" fit="cover">
              <template #error>
                <div class="cover-placeholder">封面</div>
              </template>
            </el-image>
            <div v-else class="cover-placeholder">封面</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200">
        <template #default="{ row }">
          <router-link :to="'/novel/' + String(row.id)" class="novel-title">{{ row.title }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="author" label="作者" min-width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status)">{{ row.status || '未知' }}</el-tag>
        </template>
      </el-table-column>
        <el-table-column label="标签" min-width="150">
          <template #default="{ row }">
            <div class="novel-tags">
              <template v-if="row.tags">
                <el-tag v-for="tag in row.tags.split('|').slice(0, 3)" :key="tag" size="small" effect="plain" class="novel-tag">
                  {{ tag }}
                </el-tag>
              </template>
              <span v-else>-</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </DashboardCard>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { NovelSummary } from '../../api'
import DashboardCard from './DashboardCard.vue'

defineProps<{
  novels: NovelSummary[]
  loading: boolean
}>()

const router = useRouter()

const resolveCoverUrl = (novel: NovelSummary): string => novel.cover_image_url || ''

const getStatusTag = (status: string | null): '' | 'success' | 'warning' | 'info' | 'danger' => {
  if (!status) {
    return ''
  }

  if (status.includes('完结')) {
    return 'success'
  }

  if (status.includes('连载')) {
    return 'warning'
  }

  return 'info'
}

const handleRowClick = (row: NovelSummary) => {
  router.push(`/novel/${String(row.id)}`)
}
</script>

<style scoped>
.table-panel {
  min-height: 180px;
}

.top-table-shell {
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04)),
    var(--panel-subtle-bg);
}

.novel-cover-small {
  width: 40px;
  height: 60px;
  overflow: hidden;
  border-radius: 10px;
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), 0 0 16px rgba(84, 227, 255, 0.08);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-muted);
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
}

.novel-title {
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 700;
}

.novel-title:hover {
  text-decoration: underline;
}

.novel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.novel-tag {
  margin-right: 0;
}
</style>
