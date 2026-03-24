import { computed, ref } from 'vue'

export type AppTheme = 'light' | 'dark'

const STORAGE_KEY = 'novel-reader-theme'
const theme = ref<AppTheme>('light')
let initialized = false

const resolveInitialTheme = (): AppTheme => {
  const queryTheme = new URLSearchParams(window.location.search).get('theme')
  if (queryTheme === 'dark' || queryTheme === 'light') {
    return queryTheme
  }

  const savedTheme = localStorage.getItem(STORAGE_KEY)
  if (savedTheme === 'dark' || savedTheme === 'light') {
    return savedTheme
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const applyTheme = (value: AppTheme, notify = true) => {
  theme.value = value
  document.documentElement.dataset.theme = value
  localStorage.setItem(STORAGE_KEY, value)

  if (notify) {
    window.dispatchEvent(new Event('themechange'))
  }
}

export const useTheme = () => {
  const initTheme = () => {
    if (initialized) {
      return
    }

    initialized = true
    applyTheme(resolveInitialTheme(), false)
  }

  const setTheme = (value: AppTheme) => {
    applyTheme(value)
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  const isDarkMode = computed({
    get: () => theme.value === 'dark',
    set: (value: boolean) => setTheme(value ? 'dark' : 'light'),
  })

  return {
    theme,
    isDarkMode,
    initTheme,
    setTheme,
    toggleTheme,
  }
}
