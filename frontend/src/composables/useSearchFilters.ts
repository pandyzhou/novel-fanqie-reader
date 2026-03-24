import { computed, type Ref } from 'vue'
import type { NovelSearchResult } from '../api'
import type { SearchSortField, SearchSortOrder } from '../components/search/search.types'

export const useSearchFilters = (
  searchResults: Ref<NovelSearchResult[]>,
  _sortField: Ref<SearchSortField>,
  _sortOrder: Ref<SearchSortOrder>,
  showCachedOnly: Ref<boolean>,
  showReadyOnly: Ref<boolean>,
) => {
  const displayedResults = computed<NovelSearchResult[]>(() => {
    let results = [...searchResults.value]

    if (showCachedOnly.value) {
      results = results.filter((item) => item.is_cached)
    }

    if (showReadyOnly.value) {
      results = results.filter((item) => item.is_ready)
    }

    return results
  })

  const downloadableResults = computed(() => displayedResults.value.filter((item) => !item.is_ready))

  return {
    displayedResults,
    downloadableResults,
  }
}
