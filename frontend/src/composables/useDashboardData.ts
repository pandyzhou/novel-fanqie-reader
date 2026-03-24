import { ElMessage } from 'element-plus'
import { onUnmounted, ref } from 'vue'
import type { ErrorResponse, NovelSummary, UploadStat } from '../api'
import api from '../api'
import type { DashboardOverviewStats, DashboardWordCloudItem } from '../components/dashboard/dashboard.types'
import { useStatsStore } from '../store'

type DashboardRenderHandler = (novels: NovelSummary[]) => void

const isErrorResponse = (value: unknown): value is ErrorResponse =>
  typeof value === 'object' && value !== null && 'error' in value

export const useDashboardData = () => {
  const statsStore = useStatsStore()

  const refreshing = ref(false)
  const overviewLoading = ref(false)
  const topNovelsLoading = ref(false)
  const wordCloudPanelLoading = ref(false)

  const stats = ref<DashboardOverviewStats>({ totalNovels: 0, monthlyNovels: 0, todayNovels: 0 })
  const topNovels = ref<NovelSummary[]>([])
  const dashboardNovelsCache = ref<NovelSummary[]>([])
  const uploadStatsCache = ref<UploadStat[]>([])
  const wordClouds = ref<DashboardWordCloudItem[]>([])

  let dashboardNovelsRequest: Promise<NovelSummary[]> | null = null

  const getCurrentUploadStats = () =>
    uploadStatsCache.value.length > 0 ? uploadStatsCache.value : (statsStore.uploadStats as UploadStat[])

  const calculateStats = () => {
    const uploadStats = getCurrentUploadStats()
    if (uploadStats.length === 0) {
      stats.value = { totalNovels: 0, monthlyNovels: 0, todayNovels: 0 }
      return
    }

    const total = uploadStats.reduce((sum, item) => sum + item.count, 0)
    const now = new Date()
    const today = now.toISOString().split('T')[0]
    const todayStats = uploadStats.find((item) => item.date === today)
    const todayCount = todayStats ? todayStats.count : 0
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
    const monthlyCount = uploadStats.filter((item) => item.date >= monthStart).reduce((sum, item) => sum + item.count, 0)

    stats.value = { totalNovels: total, monthlyNovels: monthlyCount, todayNovels: todayCount }
  }

  const fetchOverviewData = async () => {
    overviewLoading.value = true
    try {
      await statsStore.fetchUploadStats()
      uploadStatsCache.value = [...statsStore.uploadStats]
      calculateStats()
    } catch {
      ElMessage.error('获取概览数据失败')
    } finally {
      overviewLoading.value = false
    }
  }

  const fetchDashboardNovels = async (force = false): Promise<NovelSummary[]> => {
    if (!force && dashboardNovelsCache.value.length > 0) {
      return dashboardNovelsCache.value
    }

    if (!force && dashboardNovelsRequest) {
      return dashboardNovelsRequest
    }

    dashboardNovelsRequest = (async () => {
      const response = await api.Novels.listAll()
      if ('error' in response) {
        throw new Error(response.error)
      }

      dashboardNovelsCache.value = response
      return response
    })()

    try {
      return await dashboardNovelsRequest
    } finally {
      dashboardNovelsRequest = null
    }
  }

  const syncTopNovels = (novels: NovelSummary[]) => {
    topNovels.value = novels.slice(0, 10)
    stats.value = {
      ...stats.value,
      totalNovels: novels.length,
    }
  }

  const loadTopNovels = async (force = false): Promise<NovelSummary[] | null> => {
    topNovelsLoading.value = true
    try {
      const novels = await fetchDashboardNovels(force)
      syncTopNovels(novels)
      return novels
    } catch {
      ElMessage.error('获取热门小说失败')
      return null
    } finally {
      topNovelsLoading.value = false
    }
  }

  const cleanupWordCloudUrls = (items: DashboardWordCloudItem[] = wordClouds.value) => {
    items.forEach(({ wordCloudUrl }) => {
      if (wordCloudUrl.startsWith('blob:')) {
        URL.revokeObjectURL(wordCloudUrl)
      }
    })
  }

  const loadWordCloudPanel = async (novels: NovelSummary[] = dashboardNovelsCache.value) => {
    wordCloudPanelLoading.value = true

    try {
      const targetNovels = novels.slice(0, 3)
      const nextWordClouds: DashboardWordCloudItem[] = []

      for (const novel of targetNovels) {
        try {
          const wordCloudResult = await api.Stats.fetchWordCloudBlob(novel.id)
          if (typeof wordCloudResult === 'string') {
            nextWordClouds.push({
              novelId: novel.id,
              novelTitle: novel.title,
              wordCloudUrl: wordCloudResult,
            })
          } else if (isErrorResponse(wordCloudResult) && !wordCloudResult.error.includes('Wordcloud not found')) {
            // 单个词云缺失不阻断整个面板加载
          }
        } catch {
          // 单个词云加载失败时忽略，保留其他可展示项
        }
      }

      cleanupWordCloudUrls()
      wordClouds.value = nextWordClouds
    } catch {
      ElMessage.error('初始化词云面板失败')
    } finally {
      wordCloudPanelLoading.value = false
    }
  }

  const initializeDashboard = async (renderCharts: DashboardRenderHandler) => {
    await fetchOverviewData()
    const novels = await loadTopNovels()
    if (!novels) {
      return
    }

    renderCharts(novels)
    await loadWordCloudPanel(novels)
  }

  const refreshDashboard = async (renderCharts: DashboardRenderHandler) => {
    refreshing.value = true
    try {
      await fetchOverviewData()
      const novels = await loadTopNovels(true)
      if (!novels) {
        return
      }

      renderCharts(novels)
      await loadWordCloudPanel(novels)
      ElMessage.success('数据已更新')
    } catch {
      ElMessage.error('刷新数据失败')
    } finally {
      refreshing.value = false
    }
  }

  onUnmounted(() => {
    cleanupWordCloudUrls()
  })

  return {
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
  }
}
