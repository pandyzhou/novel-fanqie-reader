import { ref, type Ref } from 'vue'
import * as echarts from 'echarts/core'
import type { EChartsType } from 'echarts/core'

export type DashboardChartKey =
  | 'trend'
  | 'status'
  | 'tags'
  | 'chapters'
  | 'authors'
  | 'updateFrequency'
  | 'tagRelation'

export type DashboardChartOption = Parameters<EChartsType['setOption']>[0]

export interface DashboardChartRenderOptions {
  key: DashboardChartKey
  loadingState: { value: boolean }
  optionFactory: () => DashboardChartOption
  onError?: (error: unknown) => void
}

interface SetChartRefOptions {
  key: DashboardChartKey
  element: HTMLElement | null
}

export const useDashboardCharts = () => {
  const trendChartRef = ref<HTMLElement | null>(null)
  const statusChartRef = ref<HTMLElement | null>(null)
  const tagsChartRef = ref<HTMLElement | null>(null)
  const chaptersChartRef = ref<HTMLElement | null>(null)
  const authorsChartRef = ref<HTMLElement | null>(null)
  const updateFrequencyChartRef = ref<HTMLElement | null>(null)
  const tagRelationChartRef = ref<HTMLElement | null>(null)

  const chartRefs: Record<DashboardChartKey, Ref<HTMLElement | null>> = {
    trend: trendChartRef,
    status: statusChartRef,
    tags: tagsChartRef,
    chapters: chaptersChartRef,
    authors: authorsChartRef,
    updateFrequency: updateFrequencyChartRef,
    tagRelation: tagRelationChartRef,
  }

  const chartInstances: Partial<Record<DashboardChartKey, EChartsType>> = {}

  const setChartRef = ({ key, element }: SetChartRefOptions) => {
    chartRefs[key].value = element
  }

  const renderChart = ({ key, loadingState, optionFactory, onError }: DashboardChartRenderOptions) => {
    const chartRef = chartRefs[key]
    if (!chartRef.value) {
      return null
    }

    loadingState.value = true

    try {
      chartInstances[key]?.dispose()
      const instance = echarts.init(chartRef.value)
      instance.setOption(optionFactory())
      chartInstances[key] = instance
      return instance
    } catch (error) {
      delete chartInstances[key]
      onError?.(error)
      return null
    } finally {
      loadingState.value = false
    }
  }

  const resizeAllCharts = () => {
    Object.values(chartInstances).forEach((chart) => {
      chart?.resize()
    })
  }

  const disposeAllCharts = () => {
    Object.keys(chartInstances).forEach((key) => {
      const chartKey = key as DashboardChartKey
      chartInstances[chartKey]?.dispose()
      delete chartInstances[chartKey]
    })
  }

  return {
    setChartRef,
    renderChart,
    resizeAllCharts,
    disposeAllCharts,
  }
}
