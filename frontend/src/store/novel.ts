import { defineStore } from 'pinia'
import api from '../api'
import type {
  CeleryTaskStatusResponse,
  ChapterDetails,
  NovelDetails,
  NovelSearchResult,
  NovelSummary,
} from '../api'
import type { SearchSortField, SearchSortOrder } from '../components/search/search.types'
import { resolveStoreError } from './helpers'

export const useNovelStore = defineStore('novel', {
  state: () => ({
    novels: [] as NovelSummary[],
    currentNovel: null as NovelDetails | null,
    currentChapter: null as ChapterDetails | null,
    pagination: {
      total: 0,
      page: 1,
      pages: 1,
      perPage: 10,
    },
    searchResults: [] as NovelSearchResult[],
    searchQuery: '',
    searchPage: 1,
    searchPerPage: 30,
    searchSortField: 'relevance' as SearchSortField,
    searchSortOrder: 'desc' as SearchSortOrder,
    searchHasMore: false,
    searchNextOffset: null as number | null,
    searchLoadingMore: false,
    isLoading: false,
    error: null as string | null,
    taskId: null as string | null,
    taskStatus: null as CeleryTaskStatusResponse | null,
  }),

  actions: {
    async fetchNovels(page: number = 1, perPage: number = 10): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Novels.list(page, perPage)
        if ('error' in response) {
          this.error = response.error
          return
        }

        this.novels = response.items
        this.pagination = {
          total: response.total,
          page: response.page,
          pages: response.pages,
          perPage: response.per_page,
        }
      } catch (error) {
        this.error = resolveStoreError(error, '获取小说列表失败')
      } finally {
        this.isLoading = false
      }
    },

    async searchNovels(
      query: string,
      options: {
        append?: boolean
        perPage?: number
        sortField?: SearchSortField
        sortOrder?: SearchSortOrder
      } = {},
    ): Promise<void> {
      const append = options.append ?? false
      const perPage = options.perPage ?? this.searchPerPage
      const sortField = options.sortField ?? this.searchSortField
      const sortOrder = options.sortOrder ?? this.searchSortOrder
      const nextPage = append ? this.searchPage + 1 : 1
      const useOffsetPagination = sortField === 'relevance'

      if (append) {
        this.searchLoadingMore = true
      } else {
        this.isLoading = true
      }
      this.error = null

      try {
        const response = await api.Novels.search(
          query,
          nextPage,
          perPage,
          append && useOffsetPagination ? this.searchNextOffset : null,
          sortField,
          sortOrder,
        )

        if ('error' in response) {
          this.error = response.error
          if (!append) {
            this.searchResults = []
            this.searchHasMore = false
            this.searchPage = 1
            this.searchNextOffset = null
          }
          return
        }

        this.searchQuery = query
        this.searchPerPage = response.per_page
        this.searchPage = response.page
        this.searchSortField = sortField
        this.searchSortOrder = sortOrder
        this.searchHasMore = response.has_more
        this.searchNextOffset = useOffsetPagination ? response.next_offset : null
        this.searchResults = append
          ? [...this.searchResults, ...response.results].filter((item, index, array) => {
              return array.findIndex((candidate) => candidate.id === item.id) === index
            })
          : response.results
      } catch (error) {
        this.error = resolveStoreError(error, '搜索失败')
        if (!append) {
          this.searchResults = []
          this.searchHasMore = false
          this.searchPage = 1
          this.searchNextOffset = null
        }
      } finally {
        if (append) {
          this.searchLoadingMore = false
        } else {
          this.isLoading = false
        }
      }
    },

    async loadMoreSearchResults(): Promise<void> {
      const useOffsetPagination = this.searchSortField === 'relevance'
      if (
        !this.searchHasMore ||
        !this.searchQuery ||
        this.searchLoadingMore ||
        (useOffsetPagination && this.searchNextOffset === null)
      ) {
        return
      }

      await this.searchNovels(this.searchQuery, {
        append: true,
        perPage: this.searchPerPage,
        sortField: this.searchSortField,
        sortOrder: this.searchSortOrder,
      })
    },

    async fetchNovelDetails(novelId: string): Promise<NovelDetails | null> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Novels.details(novelId)
        if ('error' in response) {
          this.error = response.error
          return null
        }

        this.currentNovel = response
        return response
      } catch (error) {
        this.error = resolveStoreError(error, '获取小说详情失败')
        return null
      } finally {
        this.isLoading = false
      }
    },

    async fetchChapterContent(novelId: string, chapterId: string): Promise<void> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Novels.getChapterContent(novelId, chapterId)
        if ('error' in response) {
          this.error = response.error
          return
        }

        this.currentChapter = response
      } catch (error) {
        this.error = resolveStoreError(error, '获取章节内容失败')
      } finally {
        this.isLoading = false
      }
    },

    async addNovel(novelId: string, maxChapters?: number): Promise<{ task_id: string } | null> {
      this.isLoading = true
      this.error = null

      try {
        const requestData: { novel_id: string; max_chapters?: number } = { novel_id: novelId }
        if (maxChapters !== undefined) {
          requestData.max_chapters = maxChapters
        }

        const response = await api.Novels.add(requestData)
        if ('error' in response) {
          this.error = response.error
          return null
        }

        this.taskId = response.celery_task_id || null
        return { task_id: this.taskId || '' }
      } catch (error) {
        this.error = resolveStoreError(error, '添加小说失败')
        return null
      } finally {
        this.isLoading = false
      }
    },

    async checkTaskStatus(taskId: string): Promise<CeleryTaskStatusResponse | null> {
      this.error = null

      try {
        const response = await api.Tasks.getStatus(taskId)
        if ('error' in response) {
          this.error = response.error
          return null
        }

        this.taskStatus = response
        return response
      } catch (error) {
        this.error = resolveStoreError(error, '获取任务状态失败')
        return null
      }
    },

    async deleteNovel(novelId: string): Promise<boolean> {
      this.isLoading = true
      this.error = null

      try {
        const response = await api.Novels.delete(novelId)
        if ('error' in response) {
          this.error = response.error
          return false
        }

        this.novels = this.novels.filter((item) => item.id !== novelId)
        if (this.currentNovel?.id === novelId) {
          this.currentNovel = null
        }
        if (this.currentChapter?.novel_id === novelId) {
          this.currentChapter = null
        }
        return true
      } catch (error) {
        this.error = resolveStoreError(error, '删除小说失败')
        return false
      } finally {
        this.isLoading = false
      }
    },

    resetSearch(): void {
      this.searchResults = []
      this.searchQuery = ''
      this.searchPage = 1
      this.searchPerPage = 30
      this.searchHasMore = false
      this.searchNextOffset = null
      this.searchLoadingMore = false
    },
  },
})
