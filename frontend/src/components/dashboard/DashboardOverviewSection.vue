<template>
  <DashboardCard title="概览" card-class="overview-card" body-class="overview-body" :loading="loading">
    <el-row :gutter="20">
      <el-col :span="24" :md="8">
        <div class="stat-card page-subtle-shell">
          <div class="stat-card__icon stat-card__icon-reading"><el-icon><Reading /></el-icon></div>
          <el-statistic title="小说总数" :value="stats.totalNovels" />
        </div>
      </el-col>
      <el-col :span="24" :md="8">
        <div class="stat-card page-subtle-shell">
          <div class="stat-card__icon stat-card__icon-plus"><el-icon><Plus /></el-icon></div>
          <el-statistic title="本月新增" :value="stats.monthlyNovels" />
        </div>
      </el-col>
      <el-col :span="24" :md="8">
        <div class="stat-card page-subtle-shell">
          <div class="stat-card__icon stat-card__icon-calendar"><el-icon><Calendar /></el-icon></div>
          <el-statistic title="今日新增" :value="stats.todayNovels" />
        </div>
      </el-col>
    </el-row>
  </DashboardCard>
</template>

<script setup lang="ts">
import { Calendar, Plus, Reading } from '@element-plus/icons-vue'
import type { DashboardOverviewStats } from './dashboard.types'
import DashboardCard from './DashboardCard.vue'

defineProps<{
  stats: DashboardOverviewStats
  loading: boolean
}>()
</script>

<style scoped>
.overview-body {
  min-height: 180px;
}

.stat-card {
  text-align: center;
  padding: 22px;
  min-height: 156px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(84, 227, 255, 0.04) 28px, rgba(84, 227, 255, 0.04) 29px),
    var(--panel-subtle-bg);
}

.stat-card__icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  font-size: 22px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32), 0 0 20px rgba(84, 227, 255, 0.1);
}

.stat-card__icon-reading {
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.2), rgba(89, 108, 255, 0.12));
  color: var(--accent-strong);
}

.stat-card__icon-plus {
  background: linear-gradient(135deg, rgba(45, 212, 191, 0.2), rgba(84, 227, 255, 0.12));
  color: var(--el-color-success);
}

.stat-card__icon-calendar {
  background: linear-gradient(135deg, rgba(255, 111, 207, 0.18), rgba(251, 191, 36, 0.14));
  color: var(--neon-pink);
}

:deep(.stat-card .el-statistic) {
  width: 100%;
}

:deep(.stat-card .el-statistic__head) {
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-weight: 700;
}

:deep(.stat-card .el-statistic__content) {
  justify-content: center;
}

:deep(.stat-card .el-statistic__number) {
  font-size: clamp(30px, 4vw, 38px);
  font-weight: 800;
  letter-spacing: -0.03em;
  text-shadow: 0 0 20px rgba(84, 227, 255, 0.12);
}
</style>
