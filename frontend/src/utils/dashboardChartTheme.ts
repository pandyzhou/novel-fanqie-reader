const readCssVariable = (name: string, fallback: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback

export interface DashboardChartTheme {
  text: string
  secondary: string
  tertiary: string
  border: string
  gridLine: string
  surface: string
  tooltipBg: string
  tooltipShadow: string
  axisPointer: string
  accentSoft: string
  graphLink: string
  graphNodeBorder: string
  colors: string[]
}

export const getDashboardChartTheme = (): DashboardChartTheme => ({
  text: readCssVariable('--text-primary', '#141b38'),
  secondary: readCssVariable('--text-secondary', '#4d587f'),
  tertiary: readCssVariable('--text-tertiary', '#737fa8'),
  border: readCssVariable('--border-color', 'rgba(100, 116, 255, 0.24)'),
  gridLine: readCssVariable('--chart-grid', 'rgba(116, 133, 255, 0.16)'),
  surface: readCssVariable('--surface-solid', 'rgba(255, 255, 255, 0.84)'),
  tooltipBg: readCssVariable('--surface-solid', 'rgba(255, 255, 255, 0.84)'),
  tooltipShadow: readCssVariable('--chart-tooltip-shadow', '0 18px 36px rgba(67, 60, 135, 0.16)'),
  axisPointer: readCssVariable('--chart-axis-pointer', 'rgba(84, 227, 255, 0.2)'),
  accentSoft: readCssVariable('--accent-soft', 'rgba(89, 108, 255, 0.14)'),
  graphLink: readCssVariable('--chart-link', 'rgba(101, 119, 255, 0.28)'),
  graphNodeBorder: readCssVariable('--chart-node-border', 'rgba(255, 255, 255, 0.78)'),
  colors: [
    readCssVariable('--chart-1', '#54e3ff'),
    readCssVariable('--chart-2', '#9d7bff'),
    readCssVariable('--chart-3', '#ff6fcf'),
    readCssVariable('--chart-4', '#596cff'),
    readCssVariable('--chart-5', '#2dd4bf'),
    readCssVariable('--chart-6', '#fbbf24'),
  ],
})

const applyAxisTheme = (axis: any, theme: DashboardChartTheme): any => {
  if (!axis) {
    return axis
  }

  if (Array.isArray(axis)) {
    return axis.map((item) => applyAxisTheme(item, theme))
  }

  return {
    ...axis,
    axisLabel: {
      color: theme.secondary,
      ...(axis.axisLabel || {}),
    },
    axisLine: {
      ...(axis.axisLine || {}),
      lineStyle: {
        color: theme.border,
        ...((axis.axisLine && axis.axisLine.lineStyle) || {}),
      },
    },
    axisTick: {
      ...(axis.axisTick || {}),
      lineStyle: {
        color: theme.border,
        ...((axis.axisTick && axis.axisTick.lineStyle) || {}),
      },
    },
    splitLine: axis.splitLine
      ? {
          ...axis.splitLine,
          lineStyle: {
            color: theme.gridLine,
            ...((axis.splitLine && axis.splitLine.lineStyle) || {}),
          },
        }
      : axis.splitLine,
  }
}

export const withDashboardChartTheme = (option: any): any => {
  const theme = getDashboardChartTheme()
  const tooltipAxisPointer = option.tooltip?.axisPointer

  return {
    color: option.color || theme.colors,
    backgroundColor: 'transparent',
    ...option,
    legend: option.legend
      ? {
          icon: 'roundRect',
          itemWidth: 12,
          itemHeight: 8,
          itemGap: 14,
          ...option.legend,
          textStyle: {
            color: theme.secondary,
            ...(option.legend.textStyle || {}),
          },
        }
      : option.legend,
    tooltip: option.tooltip
      ? {
          ...option.tooltip,
          backgroundColor: theme.tooltipBg,
          borderColor: theme.border,
          borderWidth: 1,
          textStyle: {
            color: theme.text,
            ...(option.tooltip.textStyle || {}),
          },
          axisPointer: tooltipAxisPointer
            ? {
                ...tooltipAxisPointer,
                lineStyle: {
                  color: theme.axisPointer,
                  ...((tooltipAxisPointer.lineStyle as Record<string, unknown>) || {}),
                },
                shadowStyle: {
                  color: theme.accentSoft,
                  ...((tooltipAxisPointer.shadowStyle as Record<string, unknown>) || {}),
                },
                label: {
                  color: theme.text,
                  backgroundColor: theme.surface,
                  ...((tooltipAxisPointer.label as Record<string, unknown>) || {}),
                },
              }
            : tooltipAxisPointer,
          extraCssText: `box-shadow: ${theme.tooltipShadow}; border-radius: 16px;`,
        }
      : option.tooltip,
    xAxis: applyAxisTheme(option.xAxis, theme),
    yAxis: applyAxisTheme(option.yAxis, theme),
  }
}

export const truncateAxisLabel = (value: string, maxLength = 8) => {
  if (value.length <= maxLength) {
    return value
  }

  return `${value.slice(0, maxLength)}…`
}
