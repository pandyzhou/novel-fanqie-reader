import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { io, Socket } from 'socket.io-client'
import type { SearchSortField, SearchSortOrder } from './components/search/search.types'

// --- General API Response Types ---

export interface ErrorResponse {
  error: string
  msg?: string // Sometimes 'msg' is used instead of 'error'
}

export interface MessageResponse {
  msg: string
  message?: string // Sometimes 'message' is used
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
}

// --- Auth Types ---

export interface RegisterCredentials {
  username: string
  password?: string // Password might not be needed in response/profile
}

export interface LoginCredentials {
  username: string
  password?: string
}

export interface LoginResponse {
  access_token: string
}

export interface UserProfile {
  id: number // User ID is integer in backend model
  username: string
}

// --- Novel Types ---
export interface NovelSearchResult {
  id: string // Backend search returns string ID
  title: string
  author: string
  cover: string | null // 封面图片URL
  description: string | null // 小说简介
  category: string | null // 分类标签
  score?: number | null
  bookshelf_count?: number
  heat_score?: number
  local_heat_score?: number
  chapters_in_db?: number
  is_ready?: boolean
  is_cached?: boolean
  total_chapters?: number | null
}

export interface NovelSearchResponse {
  results: NovelSearchResult[]
  page: number
  per_page: number
  has_more: boolean
  next_page: number | null
  next_offset: number | null
  sort?: SearchSortField
  order?: SearchSortOrder
}


export interface AddNovelRequest {
  novel_id: string // Input expects string
  max_chapters?: number // Optional: limit chapters to download (e.g. 10 for preview)
}

// Matches DownloadTask.to_dict() structure in backend
export interface AddNovelResponse {
  id: number
  user_id: number
  novel_id: string // Matches string in backend dict
  novel: {
    id: string // Matches string in backend dict
    title: string
    author: string | null
  } | null
  celery_task_id: string | null
  status: string // Enum name as string
  progress: number
  message: string | null
  created_at: string | null // ISO format string
  updated_at: string | null // ISO format string
}

export interface NovelSummary {
  id: string // String in list response
  title: string
  author: string | null
  status: string | null
  tags: string | null
  total_chapters: number | null // Chapters from source
  last_crawled_at: string | null // ISO format string
  created_at: string | null // ISO format string
  cover_image_url: string | null
}

export interface NovelDetails {
  id: string // String in detail response
  title: string
  author: string | null
  description: string | null
  status: string | null
  tags: string | null
  total_chapters: number | null // Chapters reported by source
  chapters_in_db: number // Chapters actually in DB
  last_crawled_at: string | null // ISO format string
  created_at: string | null // ISO format string
  cover_image_url: string | null
  is_ready?: boolean
}

export interface ChapterSummary {
  id: string // String in list response
  index: number
  title: string
  fetched_at: string | null // ISO format string
}

export interface ChapterDetails {
  id: string // String in detail response
  novel_id: string // String in detail response
  index: number
  title: string
  content: string
  prev_chapter_id?: string | null
  prev_chapter_title?: string | null
  next_chapter_id?: string | null
  next_chapter_title?: string | null
}

// --- Task Types ---

// Corresponds to TaskStatus enum in backend
export enum TaskStatusEnum {
  PENDING = 'PENDING',
  DOWNLOADING = 'DOWNLOADING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  TERMINATED = 'TERMINATED',
}

// Corresponds to DownloadTask.to_dict() in backend models.py
export interface DownloadTask {
  id: number
  user_id: number
  novel_id: string
  novel: {
    id: string
    title: string
    author: string | null
  } | null
  celery_task_id: string | null
  status: TaskStatusEnum // Use string enum for status
  progress: number
  message: string | null
  raw_message?: string | null
  task_stage?: string | null
  error_code?: string | null
  created_at: string | null // ISO format string
  updated_at: string | null // ISO format string
  deleted?: boolean // Added for frontend state management on delete
}

export interface TaskListResponse {
  tasks: DownloadTask[]
}

// Celery task status structure from /api/tasks/status/<task_id>
export interface CeleryTaskStatusMeta {
  // Based on process_novel_task return structure
  status?: string // SUCCESS, FAILURE, TERMINATED etc. from the task itself
  message?: string
  chapters_processed_db?: number
  errors?: number
  // OR Error details if task failed at celery level
  exc_type?: string
  exc_message?: string
  // Or any other structure the task might return/set in meta
  [key: string]: unknown // Allow other properties
}

export interface CeleryTaskStatusResponse {
  task_id: string
  status: string // PENDING, STARTED, SUCCESS, FAILURE, REVOKED etc. (Celery states)
  result: string | null // User-friendly status description from backend
  meta: CeleryTaskStatusMeta | null // Specific task result/error details
  traceback?: string // Optional traceback on failure
}

// --- Stats Types ---
export interface UploadStat {
  date: string // Date string YYYY-MM-DD
  count: number
}

export interface GenreStat {
  name: string // Genre name
  value: number // Count
}

export interface SystemInfoResponse {
  project_root: string
  data_base_path: string
  novel_save_path: string
  novel_status_path: string
  wordcloud_save_path: string
  search_cover_cache_path: string
  database_backend: string
  database_fallback_active?: boolean
  database_fallback_reason?: string | null
  cache_enabled: boolean
  internal_api_mode?: boolean
  internal_api_user_id?: number
  auto_create_tables?: boolean
  run_legacy_runtime_schema_patches?: boolean
  migration_directory?: string
  migration_version_table_present?: boolean
  current_migration_versions?: string[]
}


// --- Axios Instance Setup (HTTP API) ---
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api', // Base URL is /api
})

// --- JWT Interceptor (HTTP API) - DISABLED for internal API mode ---
// No authentication token needed for internal API
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    // Internal API mode - no token required, skip all authentication
    return config
  },
  (error) => Promise.reject(error),
)

// --- Response Data Helper (HTTP API) ---
const responseBody = <T>(response: AxiosResponse<T>): T => response.data

const isErrorResponse = (value: unknown): value is ErrorResponse =>
  typeof value === 'object' && value !== null && 'error' in value

const extractMessageFromPayload = (payload: unknown): string | null => {
  if (typeof payload === 'string' && payload.trim()) {
    return payload.trim()
  }

  if (typeof payload === 'object' && payload !== null) {
    const candidate = payload as Partial<ErrorResponse & MessageResponse>
    if (typeof candidate.error === 'string' && candidate.error.trim()) {
      return candidate.error.trim()
    }
    if (typeof candidate.message === 'string' && candidate.message.trim()) {
      return candidate.message.trim()
    }
    if (typeof candidate.msg === 'string' && candidate.msg.trim()) {
      return candidate.msg.trim()
    }
  }

  return null
}

const toErrorResponse = (error: unknown, fallbackMessage: string): ErrorResponse => {
  if (axios.isAxiosError(error)) {
    const payloadMessage = extractMessageFromPayload(error.response?.data)
    if (payloadMessage) {
      return { error: payloadMessage }
    }

    if (typeof error.message === 'string' && error.message.trim()) {
      return { error: error.message.trim() }
    }
  }

  const payloadMessage = extractMessageFromPayload(error)
  if (payloadMessage) {
    return { error: payloadMessage }
  }

  return { error: fallbackMessage }
}

const requestWithHandling = async <T>(
  requestPromise: Promise<AxiosResponse<T>>,
  fallbackMessage: string,
): Promise<T | ErrorResponse> => {
  try {
    return responseBody(await requestPromise)
  } catch (error) {
    return toErrorResponse(error, fallbackMessage)
  }
}

// --- Generic API Request Functions (HTTP API) ---
const requests = {
  get: <T>(url: string, params?: URLSearchParams, fallbackMessage: string = '请求失败') =>
    requestWithHandling(apiClient.get<T>(url, { params }), fallbackMessage),
  post: <T>(url: string, body: unknown, fallbackMessage: string = '请求失败') =>
    requestWithHandling(apiClient.post<T>(url, body), fallbackMessage),
  delete: <T>(url: string, fallbackMessage: string = '请求失败') =>
    requestWithHandling(apiClient.delete<T>(url), fallbackMessage),
}

// --- HTTP API Function Collections ---

const Auth = {
  register: (credentials: RegisterCredentials): Promise<MessageResponse | ErrorResponse> =>
    requests.post<MessageResponse | ErrorResponse>('/auth/register', credentials, '注册失败'),
  login: (credentials: LoginCredentials): Promise<LoginResponse | ErrorResponse> =>
    requests.post<LoginResponse | ErrorResponse>('/auth/login', credentials, '登录失败'),
  me: (): Promise<UserProfile | ErrorResponse> =>
    requests.get<UserProfile | ErrorResponse>('/auth/me', undefined, '获取当前用户失败'),
}

const Novels = {
  search: (
    query: string,
    page: number = 1,
    perPage: number = 30,
    offset?: number | null,
    sortField: SearchSortField = 'relevance',
    sortOrder: SearchSortOrder = 'desc',
  ): Promise<NovelSearchResponse | ErrorResponse> => {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      per_page: perPage.toString(),
      sort: sortField,
      order: sortOrder,
    })
    if (offset !== undefined && offset !== null) {
      params.set('offset', offset.toString())
    }
    return requests.get<NovelSearchResponse | ErrorResponse>('/search', params, '搜索失败')
  },
  add: (data: AddNovelRequest): Promise<AddNovelResponse | ErrorResponse> =>
    requests.post<AddNovelResponse | ErrorResponse>('/novels', data, '添加小说失败'),
  delete: (novelId: string): Promise<MessageResponse | ErrorResponse> =>
    requests.delete<MessageResponse | ErrorResponse>(`/novels/${novelId}`, '删除小说失败'),

  list: (
    page: number = 1,
    perPage: number = 10,
  ): Promise<PaginatedResponse<NovelSummary> | ErrorResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    })
    type RawNovelListResponse =
      | {
          novels: NovelSummary[]
          total: number
          page: number
          pages: number
          per_page: number
        }
      | ErrorResponse

    return requestWithHandling(apiClient.get<RawNovelListResponse>('/novels', { params }), '获取小说列表失败').then(
      (data) => {
        if (isErrorResponse(data)) {
          return data
        }
        const normalizedData = data as Exclude<RawNovelListResponse, ErrorResponse>
        return {
          items: normalizedData.novels,
          total: normalizedData.total,
          page: normalizedData.page,
          pages: normalizedData.pages,
          per_page: normalizedData.per_page,
        }
      },
    )
  },

  listAll: async (): Promise<NovelSummary[] | ErrorResponse> => {
    const pageSize = 50
    const firstPage = await Novels.list(1, pageSize)
    if ('error' in firstPage) {
      return firstPage
    }

    let items = [...firstPage.items]
    for (let page = 2; page <= firstPage.pages; page += 1) {
      const nextPage = await Novels.list(page, pageSize)
      if ('error' in nextPage) {
        return nextPage
      }
      items = items.concat(nextPage.items)
    }

    return items
  },

  details: (novelId: string): Promise<NovelDetails | ErrorResponse> =>
    requests.get<NovelDetails | ErrorResponse>(`/novels/${novelId}`, undefined, '获取小说详情失败'),

  listChapters: (
    novelId: string,
    page: number = 1,
    perPage: number = 50,
  ): Promise<(PaginatedResponse<ChapterSummary> & { novel_id: string }) | ErrorResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    })
    type RawChapterListResponse =
      | {
          chapters: ChapterSummary[]
          total: number
          page: number
          pages: number
          per_page: number
          novel_id: string
        }
      | ErrorResponse

    return requestWithHandling(
      apiClient.get<RawChapterListResponse>(`/novels/${novelId}/chapters`, { params }),
      '获取章节列表失败',
    ).then((data) => {
      if (isErrorResponse(data)) {
        return data
      }
      const normalizedData = data as Exclude<RawChapterListResponse, ErrorResponse>
      return {
        items: normalizedData.chapters,
        total: normalizedData.total,
        page: normalizedData.page,
        pages: normalizedData.pages,
        per_page: normalizedData.per_page,
        novel_id: normalizedData.novel_id,
      }
    })
  },

  getChapterContent: (
    novelId: string,
    chapterId: string,
  ): Promise<ChapterDetails | ErrorResponse> =>
    requests.get<ChapterDetails | ErrorResponse>(
      `/novels/${novelId}/chapters/${chapterId}`,
      undefined,
      '获取章节内容失败',
    ),

  getCoverUrl: (novelId: string): string => `/api/novels/${novelId}/cover`,

  fetchCoverBlob: (novelId: string): Promise<string | ErrorResponse> => {
    const path = `/novels/${novelId}/cover`
    return apiClient
      .get<Blob>(path, { responseType: 'blob' })
      .then((res) => {
        if (res.data.type.startsWith('image/')) {
          return URL.createObjectURL(res.data)
        } else if (res.data.type === 'application/json') {
          return res.data.text().then((text) => {
            try {
              const payload = JSON.parse(text)
              return { error: extractMessageFromPayload(payload) || '获取封面失败' } as ErrorResponse
            } catch {
              return { error: 'Failed to parse error response for cover' } as ErrorResponse
            }
          })
        } else {
          return { error: 'Unexpected response type for cover image' } as ErrorResponse
        }
      })
      .catch((error) => {
        if (
          error.response &&
          error.response.data instanceof Blob &&
          error.response.data.type === 'application/json'
        ) {
          return error.response.data.text().then((text: string) => {
            try {
              const payload = JSON.parse(text)
              return { error: extractMessageFromPayload(payload) || '获取封面失败' } as ErrorResponse
            } catch {
              return { error: 'Failed to parse error blob for cover' } as ErrorResponse
            }
          })
        }
        return toErrorResponse(error, 'Failed to fetch cover blob')
      })
  },

  getDownloadUrl: (novelId: string): string => `/api/novels/${novelId}/download`,

  fetchNovelBlob: (novelId: string): Promise<Blob | ErrorResponse> => {
    const path = `/novels/${novelId}/download`
    return apiClient
      .get<Blob>(path, { responseType: 'blob' })
      .then((res) => res.data)
      .catch((error) => {
        if (
          error.response &&
          error.response.data instanceof Blob &&
          error.response.data.type === 'application/json'
        ) {
          return error.response.data.text().then((text: string) => {
            try {
              const payload = JSON.parse(text)
              return { error: extractMessageFromPayload(payload) || '下载小说文件失败' } as ErrorResponse
            } catch {
              return { error: 'Failed to parse error response from blob' } as ErrorResponse
            }
          })
        }
        return toErrorResponse(error, 'Failed to download novel file')
      })
  },
}

const Tasks = {
  getStatus: (taskId: string): Promise<CeleryTaskStatusResponse | ErrorResponse> =>
    requests.get<CeleryTaskStatusResponse | ErrorResponse>(
      `/tasks/status/${taskId}`,
      undefined,
      '获取任务状态失败',
    ),
  list: (): Promise<TaskListResponse | ErrorResponse> =>
    requests.get<TaskListResponse | ErrorResponse>('/tasks/list', undefined, '获取任务列表失败'),
  terminate: (
    dbTaskId: number,
  ): Promise<(MessageResponse & { task: DownloadTask }) | ErrorResponse> =>
    requests.post<(MessageResponse & { task: DownloadTask }) | ErrorResponse>(
      `/tasks/${dbTaskId}/terminate`,
      {},
      '终止任务失败',
    ),
  delete: (dbTaskId: number): Promise<MessageResponse | ErrorResponse> =>
    requests.delete<MessageResponse | ErrorResponse>(`/tasks/${dbTaskId}`, '删除任务失败'),
  redownload: (
    dbTaskId: number,
  ): Promise<(MessageResponse & { task: DownloadTask }) | ErrorResponse> =>
    requests.post<(MessageResponse & { task: DownloadTask }) | ErrorResponse>(
      `/tasks/${dbTaskId}/redownload`,
      {},
      '重新下载任务失败',
    ),
}

const Stats = {
  getUploadStats: (): Promise<UploadStat[] | ErrorResponse> =>
    requests.get<UploadStat[] | ErrorResponse>('/stats/upload', undefined, '获取上传统计数据失败'),
  getGenreStats: (): Promise<GenreStat[] | ErrorResponse> =>
    requests.get<GenreStat[] | ErrorResponse>('/stats/genre', undefined, '获取类型统计失败'),
  getWordCloudUrl: (novelId: string): string => `/api/stats/wordcloud/${novelId}`,
  fetchWordCloudBlob: (novelId: string): Promise<string | ErrorResponse> => {
    const path = `/stats/wordcloud/${novelId}`
    return apiClient
      .get<Blob>(path, { responseType: 'blob' })
      .then((res) => {
        if (res.data.type.startsWith('image/')) {
          return URL.createObjectURL(res.data)
        } else if (res.data.type === 'application/json') {
          return res.data.text().then((text) => {
            try {
              const payload = JSON.parse(text)
              return { error: extractMessageFromPayload(payload) || '获取词云失败' } as ErrorResponse
            } catch {
              return { error: 'Failed to parse error response for word cloud' } as ErrorResponse
            }
          })
        } else {
          return { error: 'Unexpected response type for word cloud' } as ErrorResponse
        }
      })
      .catch((error) => {
        if (
          error.response &&
          error.response.data instanceof Blob &&
          error.response.data.type === 'application/json'
        ) {
          return error.response.data.text().then((text: string) => {
            try {
              const payload = JSON.parse(text)
              return { error: extractMessageFromPayload(payload) || '获取词云失败' } as ErrorResponse
            } catch {
              return { error: 'Failed to parse error blob' } as ErrorResponse
            }
          })
        }
        return toErrorResponse(error, 'Failed to fetch word cloud blob')
      })
  },
}

const System = {
  info: (): Promise<SystemInfoResponse | ErrorResponse> =>
    requests.get<SystemInfoResponse | ErrorResponse>('/system/info', undefined, '获取系统信息失败'),
}

// --- WebSocket API Module ---
const WebSocketAPI = (() => {
  let socket: Socket | null = null
  const taskUpdateListeners = new Set<(taskData: DownloadTask) => void>()

  interface ServerToClientEvents {
    request_auth: (data: { message: string }) => void
    auth_response: (data: { success: boolean; message: string; user_id?: number }) => void
    task_update: (taskData: DownloadTask) => void
  }

  interface ClientToServerEvents {
    authenticate: (data: { token: string }) => void
  }

  function connect(token: string | null = null): Promise<boolean> {
    return new Promise((resolve, reject) => {
      if (socket?.connected) {
        resolve(true)
        return
      }

      if (socket) {
        socket.disconnect()
        socket = null
      }

      const socketUrl = undefined
      const socketPath = '/socket.io'
      let settled = false
      let authTimeout: ReturnType<typeof setTimeout> | null = null

      const settleResolve = (value: boolean) => {
        if (settled) {
          return
        }
        settled = true
        if (authTimeout) {
          clearTimeout(authTimeout)
          authTimeout = null
        }
        resolve(value)
      }

      const settleReject = (error: Error) => {
        if (settled) {
          return
        }
        settled = true
        if (authTimeout) {
          clearTimeout(authTimeout)
          authTimeout = null
        }
        reject(error)
      }

      socket = io(socketUrl, {
        path: socketPath,
        autoConnect: false,
      }) as Socket<ServerToClientEvents, ClientToServerEvents>

      socket.off('connect')
      socket.off('request_auth')
      socket.off('auth_response')
      socket.off('task_update')
      socket.off('connect_error')
      socket.off('disconnect')

      socket.on('connect', () => {
        authTimeout = setTimeout(() => {
          if (!settled) {
            socket?.disconnect()
            settleReject(new Error('WebSocket authentication timed out.'))
          }
        }, 5000)
      })

      socket.on('request_auth', () => {
        if (token) {
          socket?.emit('authenticate', { token })
          return
        }

        socket?.disconnect()
        settleReject(new Error('No authentication token available.'))
      })

      socket.on('auth_response', (data) => {
        if (data.success) {
          settleResolve(true)
          return
        }

        socket?.disconnect()
        settleReject(new Error(data.message || 'WebSocket authentication failed.'))
      })

      socket.on('task_update', (taskData) => {
        taskUpdateListeners.forEach((listener) => {
          listener(taskData)
        })
      })

      socket.on('connect_error', (err) => {
        if (socket) {
          socket.disconnect()
          socket = null
        }
        settleReject(err instanceof Error ? err : new Error('WebSocket connection failed.'))
      })

      socket.on('disconnect', () => {
        if (authTimeout) {
          clearTimeout(authTimeout)
          authTimeout = null
        }
        socket = null
      })

      socket.connect()
    })
  }

  function disconnect(): void {
    if (socket?.connected) {
      socket.disconnect()
    }
    socket = null
  }

  function onTaskUpdate(callback: (taskData: DownloadTask) => void): () => void {
    taskUpdateListeners.add(callback)
    return () => {
      taskUpdateListeners.delete(callback)
    }
  }

  function isConnected(): boolean {
    return socket?.connected ?? false
  }

  return {
    connect,
    disconnect,
    onTaskUpdate,
    isConnected,
  }
})()

// --- Default Export ---
export default {
  Auth,
  Novels,
  Tasks,
  Stats,
  System,
  WebSocketAPI,
  apiClient,
}
