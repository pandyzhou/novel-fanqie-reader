import { ElMessage } from 'element-plus'
import { ref, type Ref } from 'vue'
import type { NovelSummary, UploadStat } from '../api'
import { DASHBOARD_RENDER_ORDER } from '../components/dashboard/dashboardChartMeta'
import type { DashboardChartKey, DashboardChartOption } from './useDashboardCharts'
import type { DashboardChartRenderOptions } from './useDashboardCharts'
import {
  buildAuthorsChartOption,
  buildChaptersChartOption,
  buildStatusChartOption,
  buildTagRelationChartOption,
  buildTagsChartOption,
  buildTrendChartOption,
  buildUpdateFrequencyChartOption,
  type DashboardTimeRange,
} from '../utils/dashboardChartOptions'

interface DashboardChartDefinition {
  loadingState: Ref<boolean>
  optionFactory: () => DashboardChartOption
  errorMessage: string
}

interface UseDashboardChartRegistryOptions {
  timeRange: Ref<DashboardTimeRange>
  getCurrentUploadStats: () => UploadStat[]
  renderChart: (options: DashboardChartRenderOptions) => void
}

export const useDashboardChartRegistry = ({
  timeRange,
  getCurrentUploadStats,
  renderChart,
}: UseDashboardChartRegistryOptions) => {
  const trendChartLoading = ref(false)
  const statusChartLoading = ref(false)
  const tagsChartLoading = ref(false)
  const chaptersChartLoading = ref(false)
  const authorsChartLoading = ref(false)
  const updateFrequencyChartLoading = ref(false)
  const tagRelationChartLoading = ref(false)

  const loadingStates: Record<DashboardChartKey, Ref<boolean>> = {
    trend: trendChartLoading,
    status: statusChartLoading,
    tags: tagsChartLoading,
    chapters: chaptersChartLoading,
    authors: authorsChartLoading,
    updateFrequency: updateFrequencyChartLoading,
    tagRelation: tagRelationChartLoading,
  }

  const getChartLoading = (key: DashboardChartKey) => loadingStates[key].value

  const buildChartDefinitions = (
    novels: NovelSummary[],
  ): Record<DashboardChartKey, DashboardChartDefinition> => ({
    trend: {
      loadingState: trendChartLoading,
      optionFactory: () => buildTrendChartOption(getCurrentUploadStats(), timeRange.value),
      errorMessage: '初始化趋势图失败',
    },
    status: {
      loadingState: statusChartLoading,
      optionFactory: () => buildStatusChartOption(novels),
      errorMessage: '初始化小说状态分布图失败',
    },
    tags: {
      loadingState: tagsChartLoading,
      optionFactory: () => buildTagsChartOption(novels),
      errorMessage: '初始化热门标签分析图失败',
    },
    chapters: {
      loadingState: chaptersChartLoading,
      optionFactory: () => buildChaptersChartOption(novels),
      errorMessage: '初始化章节分布图失败',
    },
    authors: {
      loadingState: authorsChartLoading,
      optionFactory: () => buildAuthorsChartOption(novels),
      errorMessage: '初始化热门作者排行图失败',
    },
    updateFrequency: {
      loadingState: updateFrequencyChartLoading,
      optionFactory: () => buildUpdateFrequencyChartOption(novels),
      errorMessage: '初始化更新频率图失败',
    },
    tagRelation: {
      loadingState: tagRelationChartLoading,
      optionFactory: () => buildTagRelationChartOption(novels),
      errorMessage: '初始化标签关联图失败',
    },
  })

  const renderCharts = (keys: DashboardChartKey[], novels: NovelSummary[]) => {
    const chartDefinitions = buildChartDefinitions(novels)

    keys.forEach((key) => {
      const definition = chartDefinitions[key]
      renderChart({
        key,
        loadingState: definition.loadingState,
        optionFactory: definition.optionFactory,
        onError: () => {
          ElMessage.error(definition.errorMessage)
        },
      })
    })
  }

  const renderTrendChart = (novels: NovelSummary[]) => {
    renderCharts(['trend'], novels)
  }

  const renderAllCharts = (novels: NovelSummary[]) => {
    renderCharts(DASHBOARD_RENDER_ORDER, novels)
  }

  return {
    getChartLoading,
    renderTrendChart,
    renderAllCharts,
  }
}
