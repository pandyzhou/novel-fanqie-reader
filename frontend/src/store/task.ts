import { defineStore } from 'pinia'
import api from '../api'
import type { DownloadTask } from '../api'
import { resolveStoreError } from './helpers'

let removeTaskUpdateListener: (() => void) | null = null

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [] as DownloadTask[],
    isLoading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchTasks(): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Tasks.list()
        if ('error' in response) {
          this.error = response.error
          return
        }

        this.tasks = response.tasks
      } catch (error) {
        this.error = resolveStoreError(error, '获取任务列表失败')
      } finally {
        this.isLoading = false
      }
    },

    async terminateTask(taskId: number): Promise<DownloadTask | null> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Tasks.terminate(taskId)
        if ('error' in response) {
          this.error = response.error
          return null
        }

        const index = this.tasks.findIndex((task) => task.id === taskId)
        if (index !== -1) {
          this.tasks[index] = response.task
        }

        return response.task
      } catch (error) {
        this.error = resolveStoreError(error, '终止任务失败')
        return null
      } finally {
        this.isLoading = false
      }
    },

    async deleteTask(taskId: number): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Tasks.delete(taskId)
        if ('error' in response) {
          this.error = response.error
          return false
        }

        this.tasks = this.tasks.filter((task) => task.id !== taskId)
        return true
      } catch (error) {
        this.error = resolveStoreError(error, '删除任务失败')
        return false
      } finally {
        this.isLoading = false
      }
    },

    async redownloadTask(taskId: number): Promise<DownloadTask | null> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Tasks.redownload(taskId)
        if ('error' in response) {
          this.error = response.error
          return null
        }

        const index = this.tasks.findIndex((task) => task.id === taskId)
        if (index !== -1) {
          this.tasks[index] = response.task
        }

        return response.task
      } catch (error) {
        this.error = resolveStoreError(error, '重新下载任务失败')
        return null
      } finally {
        this.isLoading = false
      }
    },

    updateTaskFromWebSocket(taskData: DownloadTask & { deleted?: boolean }): void {
      if (taskData.deleted) {
        this.tasks = this.tasks.filter((task) => task.id !== taskData.id)
        return
      }

      const index = this.tasks.findIndex((task) => task.id === taskData.id)
      if (index !== -1) {
        this.tasks[index] = taskData
      } else {
        this.tasks.unshift(taskData)
      }
    },

    async setupWebSocketListener(): Promise<boolean> {
      const token = localStorage.getItem('accessToken')

      try {
        const connected = await api.WebSocketAPI.connect(token)
        if (!connected) {
          return false
        }

        if (!removeTaskUpdateListener) {
          removeTaskUpdateListener = api.WebSocketAPI.onTaskUpdate((taskData) => {
            this.updateTaskFromWebSocket(taskData)
          })
        }

        return true
      } catch (error) {
        this.error = resolveStoreError(error, 'WebSocket 连接失败')
        return false
      }
    },

    teardownWebSocketListener(): void {
      if (removeTaskUpdateListener) {
        removeTaskUpdateListener()
        removeTaskUpdateListener = null
      }
      api.WebSocketAPI.disconnect()
    },
  },
})
