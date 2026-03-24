import { defineStore } from 'pinia'
import api from '../api'
import type { UserProfile } from '../api'
import { resolveStoreError } from './helpers'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as UserProfile | null,
    isAuthenticated: false,
    isLoading: false,
    error: null as string | null,
  }),

  actions: {
    async login(username: string, password: string): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Auth.login({ username, password })
        if ('error' in response) {
          this.error = response.error
          return false
        }

        localStorage.setItem('accessToken', response.access_token)
        await this.fetchUser()
        return true
      } catch (error) {
        this.error = resolveStoreError(error, '登录失败，请重试')
        return false
      } finally {
        this.isLoading = false
      }
    },

    async register(username: string, password: string): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Auth.register({ username, password })
        if ('error' in response) {
          this.error = response.error
          return false
        }

        return true
      } catch (error) {
        this.error = resolveStoreError(error, '注册失败，请重试')
        return false
      } finally {
        this.isLoading = false
      }
    },

    async fetchUser(): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Auth.me()
        if ('error' in response) {
          this.error = response.error
          this.isAuthenticated = false
          this.user = null
          return
        }

        this.user = response
        this.isAuthenticated = true
      } catch (error) {
        this.error = resolveStoreError(error, '获取用户信息失败')
        this.user = null
        this.isAuthenticated = false
      } finally {
        this.isLoading = false
      }
    },

    logout(): void {
      localStorage.removeItem('accessToken')
      this.user = null
      this.isAuthenticated = false
      this.error = null
    },

    checkAuth(): void {
      const token = localStorage.getItem('accessToken')
      if (token) {
        this.fetchUser()
      }
    },
  },
})
