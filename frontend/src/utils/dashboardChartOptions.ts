import type { NovelSummary, UploadStat } from '../api'
import { getDashboardChartTheme, truncateAxisLabel, withDashboardChartTheme } from './dashboardChartTheme'

export type DashboardTimeRange = 'week' | 'month' | 'year'

const getRecentUploadStats = (uploadStats: UploadStat[], timeRange: DashboardTimeRange) => {
  if (uploadStats.length === 0) {
    return []
  }

  const now = new Date()
  const days = timeRange === 'week' ? 7 : timeRange === 'month' ? 30 : 365
  const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

  return uploadStats.filter((item) => item.date >= startDate)
}

const collectTagMap = (novels: NovelSummary[]) => {
  const tagMap: Record<string, number> = {}

  novels.forEach((novel) => {
    if (!novel.tags) {
      return
    }

    novel.tags
      .split('|')
      .map((tag) => tag.trim())
      .filter(Boolean)
      .forEach((tag) => {
        tagMap[tag] = (tagMap[tag] || 0) + 1
      })
  })

  return tagMap
}

export const buildTrendChartOption = (uploadStats: UploadStat[], timeRange: DashboardTimeRange) => {
  const theme = getDashboardChartTheme()
  const filteredData = getRecentUploadStats(uploadStats, timeRange)

  return withDashboardChartTheme({
    tooltip: { trigger: 'axis', formatter: '{b}: {c} 本' },
    grid: { top: 24, left: '4%', right: '3%', bottom: timeRange === 'year' ? '14%' : '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: filteredData.map((item) => item.date),
      boundaryGap: false,
      axisLabel: { rotate: timeRange === 'year' ? 45 : 0 },
    },
    yAxis: {
      type: 'value',
      name: '小说数量',
      minInterval: 1,
      splitLine: { show: true },
    },
    series: [
      {
        name: '新增小说',
        type: 'line',
        data: filteredData.map((item) => item.count),
        smooth: true,
        showSymbol: filteredData.length <= 45,
        symbolSize: 7,
        lineStyle: { width: 3 },
        itemStyle: { color: theme.colors[0] },
        areaStyle: { opacity: 0.18, color: theme.colors[0] },
      },
    ],
  })
}

export const buildStatusChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const statusMap: Record<string, number> = {}

  novels.forEach((novel) => {
    const status = novel.status || '未知'
    statusMap[status] = (statusMap[status] || 0) + 1
  })

  const statusData = Object.entries(statusMap).map(([name, value]) => ({ name, value }))

  return withDashboardChartTheme({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 本 ({d}%)' },
    legend: { bottom: 0, left: 'center' },
    series: [
      {
        name: '小说状态',
        type: 'pie',
        radius: ['42%', '72%'],
        center: ['50%', '42%'],
        padAngle: 2,
        data: statusData,
        itemStyle: { borderColor: theme.surface, borderWidth: 2 },
        label: {
          color: theme.secondary,
          formatter: '{b}\n{c} 本',
        },
        labelLine: {
          lineStyle: { color: theme.border },
        },
        emphasis: {
          scale: true,
          scaleSize: 10,
        },
      },
    ],
  })
}

export const buildTagsChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const tagMap = collectTagMap(novels)
  const tagsData = Object.entries(tagMap)
    .map(([name, value]) => ({ name, value }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 10)

  return withDashboardChartTheme({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: ({ 0: first }: { 0: { axisValue: string; value: number } }) => `${first.axisValue}: ${first.value} 本`,
    },
    grid: { top: 18, left: '5%', right: '4%', bottom: '6%', containLabel: true },
    xAxis: { type: 'value', splitLine: { show: true } },
    yAxis: {
      type: 'category',
      data: tagsData.map((item) => item.name),
      axisLabel: { formatter: (value: string) => truncateAxisLabel(value, 8) },
    },
    series: [
      {
        name: '小说数量',
        type: 'bar',
        barMaxWidth: 22,
        data: tagsData.map((item) => item.value),
        itemStyle: {
          color: theme.colors[1],
          borderRadius: [0, 999, 999, 0],
        },
      },
    ],
  })
}

export const buildChaptersChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const ranges = [
    { min: 0, max: 50, label: '0-50章' },
    { min: 51, max: 100, label: '51-100章' },
    { min: 101, max: 200, label: '101-200章' },
    { min: 201, max: 500, label: '201-500章' },
    { min: 501, max: 1000, label: '501-1000章' },
    { min: 1001, max: Infinity, label: '1000章以上' },
  ]

  const distribution = ranges.map((range) => ({ name: range.label, value: 0 }))

  novels.forEach((novel) => {
    const chapterCount = novel.total_chapters || 0
    const rangeIndex = ranges.findIndex((range) => chapterCount >= range.min && chapterCount <= range.max)
    if (rangeIndex !== -1) {
      distribution[rangeIndex].value += 1
    }
  })

  return withDashboardChartTheme({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c} 本' },
    grid: { top: 24, left: '4%', right: '3%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: distribution.map((item) => item.name),
      axisLabel: { rotate: 20 },
    },
    yAxis: { type: 'value', splitLine: { show: true } },
    series: [
      {
        name: '小说数量',
        type: 'bar',
        barMaxWidth: 30,
        data: distribution.map((item) => item.value),
        itemStyle: {
          color: theme.colors[5],
          borderRadius: [999, 999, 0, 0],
        },
      },
    ],
  })
}

export const buildAuthorsChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const authorMap: Record<string, number> = {}

  novels.forEach((novel) => {
    if (!novel.author) {
      return
    }

    authorMap[novel.author] = (authorMap[novel.author] || 0) + 1
  })

  const authorsData = Object.entries(authorMap)
    .map(([name, value]) => ({ name, value }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 10)

  return withDashboardChartTheme({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: ({ 0: first }: { 0: { axisValue: string; value: number } }) => `${first.axisValue}: ${first.value} 本`,
    },
    grid: { top: 18, left: '5%', right: '4%', bottom: '6%', containLabel: true },
    xAxis: { type: 'value', splitLine: { show: true } },
    yAxis: {
      type: 'category',
      data: authorsData.map((item) => item.name),
      axisLabel: { formatter: (value: string) => truncateAxisLabel(value, 8) },
    },
    series: [
      {
        name: '作品数量',
        type: 'bar',
        barMaxWidth: 22,
        data: authorsData.map((item) => item.value),
        itemStyle: {
          color: theme.colors[2],
          borderRadius: [0, 999, 999, 0],
        },
      },
    ],
  })
}

export const buildUpdateFrequencyChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const now = new Date()
  const ranges = [
    { max: 1, label: '今天' },
    { min: 1, max: 7, label: '一周内' },
    { min: 7, max: 30, label: '一月内' },
    { min: 30, max: 90, label: '三月内' },
    { min: 90, max: 180, label: '半年内' },
    { min: 180, max: Infinity, label: '半年以上' },
  ]

  const distribution = ranges.map((range) => ({ name: range.label, value: 0 }))

  novels.forEach((novel) => {
    if (!novel.last_crawled_at) {
      return
    }

    const updateDate = new Date(novel.last_crawled_at)
    const daysDiff = Math.floor((now.getTime() - updateDate.getTime()) / (1000 * 60 * 60 * 24))
    const rangeIndex = ranges.findIndex(
      (range) => (range.min === undefined || daysDiff >= range.min) && (range.max === undefined || daysDiff < range.max),
    )

    if (rangeIndex !== -1) {
      distribution[rangeIndex].value += 1
    }
  })

  return withDashboardChartTheme({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 本 ({d}%)' },
    legend: { bottom: 0, left: 'center' },
    series: [
      {
        type: 'pie',
        radius: ['38%', '70%'],
        center: ['50%', '42%'],
        roseType: 'area',
        data: distribution,
        itemStyle: { borderColor: theme.surface, borderWidth: 2 },
        label: {
          color: theme.secondary,
          formatter: '{b}\n{c} 本',
        },
        labelLine: {
          lineStyle: { color: theme.border },
        },
      },
    ],
  })
}

export const buildTagRelationChartOption = (novels: NovelSummary[]) => {
  const theme = getDashboardChartTheme()
  const tagRelations: Record<string, number> = {}
  const tagCounts: Record<string, number> = {}

  novels.forEach((novel) => {
    if (!novel.tags) {
      return
    }

    const tags = novel.tags
      .split('|')
      .map((tag) => tag.trim())
      .filter(Boolean)

    tags.forEach((tag) => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1
    })

    for (let i = 0; i < tags.length; i += 1) {
      for (let j = i + 1; j < tags.length; j += 1) {
        const pair = [tags[i], tags[j]].sort().join('-')
        tagRelations[pair] = (tagRelations[pair] || 0) + 1
      }
    }
  })

  const topTags = Object.entries(tagCounts)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 10)
    .map(([tag]) => tag)

  const nodes = topTags.map((tag, index) => ({
    name: tag,
    value: tagCounts[tag],
    symbolSize: 26 + Math.sqrt(tagCounts[tag]) * 7,
    itemStyle: {
      color: theme.colors[index % theme.colors.length],
      borderColor: theme.graphNodeBorder,
      borderWidth: 2,
      shadowBlur: 18,
      shadowColor: theme.accentSoft,
    },
    label: {
      color: theme.text,
      backgroundColor: theme.surface,
      padding: [4, 8],
      borderRadius: 999,
    },
  }))

  const links: { source: string; target: string; value: number; lineStyle: { width: number; color: string; opacity: number } }[] = []

  Object.entries(tagRelations).forEach(([pair, count]) => {
    const [source, target] = pair.split('-')
    if (topTags.includes(source) && topTags.includes(target)) {
      links.push({
        source,
        target,
        value: count,
        lineStyle: {
          width: Math.max(1.5, Math.min(5.5, count * 0.6)),
          color: theme.graphLink,
          opacity: 0.75,
        },
      })
    }
  })

  return withDashboardChartTheme({
    tooltip: {
      formatter: (params: { dataType: string; data: { name?: string; value?: number; source?: string; target?: string } }) => {
        if (params.dataType === 'node') {
          return `${params.data.name}: ${params.data.value} 本小说`
        }

        return `${params.data.source} - ${params.data.target}: 共现 ${params.data.value} 次`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links,
        roam: true,
        draggable: true,
        label: { show: true, position: 'right' },
        force: { repulsion: 220, edgeLength: [70, 140] },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { opacity: 1, width: 4 },
        },
        lineStyle: { curveness: 0.18 },
      },
    ],
  })
}
