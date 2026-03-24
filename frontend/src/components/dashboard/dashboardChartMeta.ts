import type { DashboardChartKey } from '../../composables/useDashboardCharts'

export interface DashboardChartCardMeta {
  key: DashboardChartKey
  title: string
  lg?: number
  actions?: 'timeRange'
}

export const DASHBOARD_CHART_ROWS: DashboardChartCardMeta[][] = [
  [
    { key: 'status', title: '小说状态分布' },
    { key: 'tags', title: '热门标签分析' },
  ],
  [
    { key: 'chapters', title: '章节数量分布' },
    { key: 'authors', title: '热门作者排行' },
  ],
  [
    { key: 'updateFrequency', title: '更新频率分析' },
    { key: 'tagRelation', title: '标签关联分析' },
  ],
  [{ key: 'trend', title: '小说添加趋势', lg: 24, actions: 'timeRange' }],
]

export const DASHBOARD_RENDER_ORDER: DashboardChartKey[] = DASHBOARD_CHART_ROWS.flat().map(({ key }) => key)
