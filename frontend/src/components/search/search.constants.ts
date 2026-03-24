import type { SearchOrderOption, SearchSortField, SearchSortOption, SearchSortOrder } from './search.types'

export const SEARCH_DEFAULT_SORT_FIELD: SearchSortField = 'relevance'
export const SEARCH_DEFAULT_SORT_ORDER: SearchSortOrder = 'desc'

export const SEARCH_SORT_OPTIONS: SearchSortOption[] = [
  { label: '默认相关性', value: 'relevance' },
  { label: '综合热度', value: 'local_heat_score' },
  { label: '热度（收藏量）', value: 'bookshelf_count' },
  { label: '已抓取章节数', value: 'chapters_in_db' },
  { label: '本地缓存', value: 'is_cached' },
  { label: '可读状态', value: 'is_ready' },
  { label: '标题', value: 'title' },
]

export const SEARCH_ORDER_OPTIONS: SearchOrderOption[] = [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' },
]
