export type SearchSortField =
  | 'relevance'
  | 'local_heat_score'
  | 'bookshelf_count'
  | 'chapters_in_db'
  | 'is_cached'
  | 'is_ready'
  | 'title'

export type SearchSortOrder = 'asc' | 'desc'

export interface SearchSortOption {
  label: string
  value: SearchSortField
}

export interface SearchOrderOption {
  label: string
  value: SearchSortOrder
}
