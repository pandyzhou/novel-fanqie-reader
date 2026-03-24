import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { mockTasksApi, mockWebSocketApi } = vi.hoisted(() => ({
  mockTasksApi: {
    list: vi.fn(),
    terminate: vi.fn(),
    delete: vi.fn(),
    redownload: vi.fn(),
  },
  mockWebSocketApi: {
    connect: vi.fn(),
    onTaskUpdate: vi.fn(),
    disconnect: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  default: {
    Tasks: mockTasksApi,
    WebSocketAPI: mockWebSocketApi,
  },
}))

import { useTaskStore } from '../task'

describe('useTaskStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('获取任务列表成功时写入 tasks', async () => {
    mockTasksApi.list.mockResolvedValueOnce({
      tasks: [
        {
          id: 1,
          user_id: 1,
          novel_id: '1',
          novel: { id: '1', title: '测试小说', author: '作者' },
          celery_task_id: 'task-1',
          status: 'PENDING',
          progress: 0,
          message: '等待中',
          created_at: null,
          updated_at: null,
        },
      ],
    })

    const store = useTaskStore()
    await store.fetchTasks()

    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].id).toBe(1)
    expect(store.error).toBeNull()
  })

  it('WebSocket 更新会插入、覆盖和删除任务', () => {
    const store = useTaskStore()

    const baseTask = {
      id: 1,
      user_id: 1,
      novel_id: '1',
      novel: { id: '1', title: '测试小说', author: '作者' },
      celery_task_id: 'task-1',
      status: 'PENDING' as const,
      progress: 0,
      message: '等待中',
      created_at: null,
      updated_at: null,
    }

    store.updateTaskFromWebSocket(baseTask)
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].status).toBe('PENDING')

    store.updateTaskFromWebSocket({ ...baseTask, status: 'COMPLETED', progress: 100 })
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].status).toBe('COMPLETED')
    expect(store.tasks[0].progress).toBe(100)

    store.updateTaskFromWebSocket({ id: 1, deleted: true } as any)
    expect(store.tasks).toHaveLength(0)
  })

  it('setupWebSocketListener 成功时注册回调并在 teardown 时断开', async () => {
    const unsubscribe = vi.fn()
    mockWebSocketApi.connect.mockResolvedValueOnce(true)
    mockWebSocketApi.onTaskUpdate.mockReturnValueOnce(unsubscribe)
    localStorage.setItem('accessToken', 'token-123')

    const store = useTaskStore()
    const connected = await store.setupWebSocketListener()

    expect(connected).toBe(true)
    expect(mockWebSocketApi.connect).toHaveBeenCalledWith('token-123')
    expect(mockWebSocketApi.onTaskUpdate).toHaveBeenCalledTimes(1)

    store.teardownWebSocketListener()
    expect(unsubscribe).toHaveBeenCalledTimes(1)
    expect(mockWebSocketApi.disconnect).toHaveBeenCalledTimes(1)
  })
})
