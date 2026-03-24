export interface DashboardOverviewStats {
  totalNovels: number
  monthlyNovels: number
  todayNovels: number
}

export interface DashboardWordCloudItem {
  novelId: string
  novelTitle: string
  wordCloudUrl: string
}
