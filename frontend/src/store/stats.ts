import { defineStore } from 'pinia'
import api from '../api'
import { resolveStoreError } from './helpers'

export const useStatsStore = defineStore('stats', {
  state: () => ({
    uploadStats: [] as { date: string; count: number }[],
    genreStats: [] as { name: string; value: number }[],
    isLoading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchUploadStats(): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Stats.getUploadStats()
        if ('error' in response) {
          this.error = response.error
          return
        }

        this.uploadStats = response
      } catch (error) {
        this.error = resolveStoreError(error, '获取上传统计数据失败')
      } finally {
        this.isLoading = false
      }
    },

    async fetchGenreStats(): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Stats.getGenreStats()
        if ('error' in response) {
          this.error = response.error
          return
        }

        this.genreStats = response
      } catch (error) {
        this.error = resolveStoreError(error, '获取类型统计数据失败')
      } finally {
        this.isLoading = false
      }
    },
  },
})
