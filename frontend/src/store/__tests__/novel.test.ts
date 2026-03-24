import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { mockNovelsApi, mockTasksApi } = vi.hoisted(() => ({
  mockNovelsApi: {
    add: vi.fn(),
    search: vi.fn(),
  },
  mockTasksApi: {
    getStatus: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  default: {
    Novels: mockNovelsApi,
    Tasks: mockTasksApi,
  },
}))

import { useNovelStore } from '../novel'

describe('useNovelStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('addNovel 成功时记录 celery task id', async () => {
    mockNovelsApi.add.mockResolvedValueOnce({
      celery_task_id: 'celery-123',
    })

    const store = useNovelStore()
    const result = await store.addNovel('1001')

    expect(result).toEqual({ task_id: 'celery-123' })
    expect(store.taskId).toBe('celery-123')
    expect(store.error).toBeNull()
  })

  it('addNovel API 返回业务错误时保留错误信息', async () => {
    mockNovelsApi.add.mockResolvedValueOnce({
      error: 'Task is already active with status DOWNLOADING.',
    })

    const store = useNovelStore()
    const result = await store.addNovel('1001')

    expect(result).toBeNull()
    expect(store.error).toBe('Task is already active with status DOWNLOADING.')
  })

  it('searchNovels 追加结果时会去重并保留分页状态', async () => {
    mockNovelsApi.search
      .mockResolvedValueOnce({
        results: [
          { id: '1', title: '小说一', author: '作者', cover: null, description: null, category: null },
          { id: '2', title: '小说二', author: '作者', cover: null, description: null, category: null },
        ],
        page: 1,
        per_page: 2,
        has_more: true,
        next_page: 2,
        next_offset: 2,
      })
      .mockResolvedValueOnce({
        results: [
          { id: '2', title: '小说二', author: '作者', cover: null, description: null, category: null },
          { id: '3', title: '小说三', author: '作者', cover: null, description: null, category: null },
        ],
        page: 2,
        per_page: 2,
        has_more: false,
        next_page: null,
        next_offset: null,
      })

    const store = useNovelStore()
    await store.searchNovels('测试')
    await store.searchNovels('测试', { append: true })

    expect(store.searchResults.map((item) => item.id)).toEqual(['1', '2', '3'])
    expect(store.searchPage).toBe(2)
    expect(store.searchHasMore).toBe(false)
  })
})
