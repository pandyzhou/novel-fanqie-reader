<template>
  <div class="dashboard-container">
    <section class="dashboard-hero">
      <div>
        <p class="hero-badge">数据总览</p>
        <h2 class="page-title">数据大屏</h2>
        <p class="hero-subtitle">查看小说增长、任务状态、标签分布与词云概览，快速掌握书库全局情况。</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="refreshData" :loading="refreshing">
        刷新数据
      </el-button>
    </section>

    <template v-if="showDashboardSkeleton">
      <section class="dashboard-skeleton-grid">
        <el-card v-for="index in 4" :key="index" class="dashboard-skeleton-card page-panel-card">
          <el-skeleton animated :rows="index === 1 ? 2 : 5" />
        </el-card>
      </section>
    </template>

    <template v-else-if="showDashboardEmpty">
      <el-card class="dashboard-empty-card page-panel-card">
        <el-empty description="当前暂无可展示的数据大屏内容">
          <template #description>
            <p>可能是书库仍为空，或统计数据尚未生成。</p>
            <p>可以先去搜索小说并加入下载任务，稍后再回来查看。</p>
          </template>
          <el-button type="primary" @click="refreshData">重新加载</el-button>
        </el-empty>
      </el-card>
    </template>

    <template v-else>
      <el-row :gutter="20">
        <el-col :span="24">
          <DashboardOverviewSection :stats="stats" :loading="overviewLoading" />
        </el-col>
      </el-row>

      <el-row v-for="(row, rowIndex) in dashboardChartRows" :key="rowIndex" :gutter="20" class="chart-row">
        <el-col v-for="chart in row" :key="chart.key" :span="24" :lg="chart.lg ?? 12">
          <DashboardCard :title="chart.title" body-class="chart-container" :loading="getChartLoading(chart.key)">
            <template v-if="chart.actions === 'timeRange'" #actions>
              <div class="chart-actions">
                <el-radio-group v-model="timeRange" size="small" @change="renderTrendChart(dashboardNovelsCache)">
                  <el-radio-button value="week">最近一周</el-radio-button>
                  <el-radio-button value="month">最近一月</el-radio-button>
                  <el-radio-button value="year">最近一年</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div :ref="getChartRefBinder(chart.key)" class="echarts-container"></div>
          </DashboardCard>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="chart-row">
        <el-col :span="24">
          <DashboardWordCloudPanel :items="wordClouds" :loading="wordCloudPanelLoading" />
        </el-col>
      </el-row>

      <el-row :gutter="20" class="chart-row">
        <el-col :span="24">
          <DashboardTopNovelsTable :novels="topNovels" :loading="topNovelsLoading" />
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { LineChart, PieChart, BarChart, GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import DashboardCard from '../components/dashboard/DashboardCard.vue'
import DashboardOverviewSection from '../components/dashboard/DashboardOverviewSection.vue'
import DashboardTopNovelsTable from '../components/dashboard/DashboardTopNovelsTable.vue'
import DashboardWordCloudPanel from '../components/dashboard/DashboardWordCloudPanel.vue'
import { DASHBOARD_CHART_ROWS } from '../components/dashboard/dashboardChartMeta'
import { useDashboardChartRegistry } from '../composables/useDashboardChartRegistry'
import { useDashboardCharts } from '../composables/useDashboardCharts'
import { useDashboardData } from '../composables/useDashboardData'
import { useDashboardPageShell } from '../composables/useDashboardPageShell'
import { type DashboardTimeRange } from '../utils/dashboardChartOptions'

echarts.use([TooltipComponent, LegendComponent, GridComponent, LineChart, PieChart, BarChart, GraphChart, CanvasRenderer])

const dashboardChartRows = DASHBOARD_CHART_ROWS
const timeRange = ref<DashboardTimeRange>('month')

const {
  refreshing,
  overviewLoading,
  topNovelsLoading,
  wordCloudPanelLoading,
  stats,
  topNovels,
  dashboardNovelsCache,
  wordClouds,
  getCurrentUploadStats,
  initializeDashboard,
  refreshDashboard,
} = useDashboardData()

const { setChartRef, renderChart, resizeAllCharts, disposeAllCharts } = useDashboardCharts()

const { getChartLoading, renderTrendChart, renderAllCharts } = useDashboardChartRegistry({
  timeRange,
  getCurrentUploadStats,
  renderChart,
})

const { getChartRefBinder } = useDashboardPageShell({
  initializeDashboard,
  renderAllCharts,
  resizeAllCharts,
  disposeAllCharts,
  setChartRef,
  getNovels: () => dashboardNovelsCache.value,
})

const hasDashboardData = computed(
  () => stats.value.totalNovels > 0 || topNovels.value.length > 0 || wordClouds.value.length > 0,
)
const showDashboardSkeleton = computed(
  () => (overviewLoading.value || topNovelsLoading.value || wordCloudPanelLoading.value) && !hasDashboardData.value,
)
const showDashboardEmpty = computed(
  () => !showDashboardSkeleton.value && !refreshing.value && !hasDashboardData.value,
)

const refreshData = async () => {
  await refreshDashboard(renderAllCharts)
}
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 40px;
}

.dashboard-hero {
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

.dashboard-skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.dashboard-skeleton-card,
.dashboard-empty-card {
  border-radius: 20px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.04) 26px, rgba(84, 227, 255, 0.04) 27px),
    var(--panel-raised-bg);
}

:deep(.dashboard-skeleton-card .el-card__body),
:deep(.dashboard-empty-card .el-card__body) {
  padding: 24px;
}

.chart-row {
  margin-top: 20px;
}

.chart-actions {
  display: flex;
  align-items: center;
}

.echarts-container {
  height: 100%;
  width: 100%;
}

@media (max-width: 768px) {
  .dashboard-hero {
    padding: 20px;
  }

  .dashboard-skeleton-grid {
    grid-template-columns: 1fr;
  }
}
</style>
