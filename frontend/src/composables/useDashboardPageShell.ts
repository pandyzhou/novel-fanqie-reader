import { nextTick, onMounted, onUnmounted, type ComponentPublicInstance } from 'vue'
import type { NovelSummary } from '../api'
import { DASHBOARD_RENDER_ORDER } from '../components/dashboard/dashboardChartMeta'
import type { DashboardChartKey } from './useDashboardCharts'

interface UseDashboardPageShellOptions {
  initializeDashboard: (renderCharts: (novels: NovelSummary[]) => void) => Promise<void>
  renderAllCharts: (novels: NovelSummary[]) => void
  resizeAllCharts: () => void
  disposeAllCharts: () => void
  setChartRef: (options: { key: DashboardChartKey; element: HTMLElement | null }) => void
  getNovels: () => NovelSummary[]
}

export const useDashboardPageShell = ({
  initializeDashboard,
  renderAllCharts,
  resizeAllCharts,
  disposeAllCharts,
  setChartRef,
  getNovels,
}: UseDashboardPageShellOptions) => {
  const chartRefBinders = DASHBOARD_RENDER_ORDER.reduce(
    (binders, key) => {
      binders[key] = (element: Element | ComponentPublicInstance | null) => {
        setChartRef({ key, element: element instanceof HTMLElement ? element : null })
      }
      return binders
    },
    {} as Record<DashboardChartKey, (element: Element | ComponentPublicInstance | null) => void>,
  )

  let resizeDebounceTimer: number | null = null

  const getChartRefBinder = (key: DashboardChartKey) => chartRefBinders[key]

  const handleResize = () => {
    if (resizeDebounceTimer) {
      clearTimeout(resizeDebounceTimer)
    }

    resizeDebounceTimer = window.setTimeout(() => {
      resizeAllCharts()
    }, 300)
  }

  const handleThemeChange = () => {
    renderAllCharts(getNovels())
  }

  onMounted(async () => {
    await nextTick()
    await initializeDashboard(renderAllCharts)
    window.addEventListener('resize', handleResize)
    window.addEventListener('themechange', handleThemeChange)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('themechange', handleThemeChange)
    disposeAllCharts()
    if (resizeDebounceTimer) {
      clearTimeout(resizeDebounceTimer)
    }
  })

  return {
    getChartRefBinder,
  }
}
