import { reactive } from 'vue'

export type ReaderTheme = 'light' | 'dark' | 'sepia' | 'eye-care' | 'oled'

export interface ReaderPreferences {
  fontSize: number
  theme: ReaderTheme
  lineHeight: number
  paragraphSpacing: number
}

export interface ReadingProgress {
  chapterId: string
  chapterTitle: string | null
  scrollTop: number
  updatedAt: number
}

const READER_PREFERENCES_STORAGE_KEY = 'reader-preferences'

const DEFAULT_READER_PREFERENCES: ReaderPreferences = {
  fontSize: 18,
  theme: 'light',
  lineHeight: 1.9,
  paragraphSpacing: 1,
}

const isBrowser = () => typeof window !== 'undefined' && typeof localStorage !== 'undefined'

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

const normalizePreferences = (value: unknown): ReaderPreferences => {
  if (typeof value !== 'object' || value === null) {
    return { ...DEFAULT_READER_PREFERENCES }
  }

  const candidate = value as Partial<ReaderPreferences> & { readingMode?: boolean }
  let theme = candidate.theme
  if (!theme && typeof candidate.readingMode === 'boolean') {
    theme = candidate.readingMode ? 'dark' : 'light'
  }

  return {
    fontSize: clamp(Number(candidate.fontSize) || DEFAULT_READER_PREFERENCES.fontSize, 14, 30),
    theme: ['light', 'dark', 'sepia', 'eye-care', 'oled'].includes(String(theme))
      ? (theme as ReaderTheme)
      : DEFAULT_READER_PREFERENCES.theme,
    lineHeight: clamp(Number(candidate.lineHeight) || DEFAULT_READER_PREFERENCES.lineHeight, 1.4, 2.6),
    paragraphSpacing: clamp(
      Number(candidate.paragraphSpacing) || DEFAULT_READER_PREFERENCES.paragraphSpacing,
      0.5,
      2.5,
    ),
  }
}

export const loadReaderPreferences = (): ReaderPreferences => {
  if (!isBrowser()) {
    return { ...DEFAULT_READER_PREFERENCES }
  }

  try {
    const raw = localStorage.getItem(READER_PREFERENCES_STORAGE_KEY)
    if (!raw) {
      return { ...DEFAULT_READER_PREFERENCES }
    }
    return normalizePreferences(JSON.parse(raw))
  } catch {
    return { ...DEFAULT_READER_PREFERENCES }
  }
}

export const saveReaderPreferences = (preferences: ReaderPreferences) => {
  if (!isBrowser()) {
    return
  }

  localStorage.setItem(READER_PREFERENCES_STORAGE_KEY, JSON.stringify(normalizePreferences(preferences)))
}

export const resetReaderPreferences = (): ReaderPreferences => {
  const nextPreferences = { ...DEFAULT_READER_PREFERENCES }
  saveReaderPreferences(nextPreferences)
  return nextPreferences
}

const progressStorageKey = (novelId: string) => `reading_progress_${novelId}`

export const loadReadingProgress = (novelId: string): ReadingProgress | null => {
  if (!isBrowser() || !novelId) {
    return null
  }

  try {
    const raw = localStorage.getItem(progressStorageKey(novelId))
    if (!raw) {
      return null
    }

    const candidate = JSON.parse(raw) as Partial<ReadingProgress>
    if (!candidate.chapterId) {
      return null
    }

    return {
      chapterId: String(candidate.chapterId),
      chapterTitle: candidate.chapterTitle ? String(candidate.chapterTitle) : null,
      scrollTop: clamp(Number(candidate.scrollTop) || 0, 0, Number.MAX_SAFE_INTEGER),
      updatedAt: Number(candidate.updatedAt) || Date.now(),
    }
  } catch {
    return null
  }
}

export const saveReadingProgress = (novelId: string, progress: ReadingProgress) => {
  if (!isBrowser() || !novelId || !progress.chapterId) {
    return
  }

  localStorage.setItem(
    progressStorageKey(novelId),
    JSON.stringify({
      chapterId: progress.chapterId,
      chapterTitle: progress.chapterTitle,
      scrollTop: clamp(Math.round(progress.scrollTop), 0, Number.MAX_SAFE_INTEGER),
      updatedAt: progress.updatedAt,
    }),
  )
}

export const clearReadingProgress = (novelId: string) => {
  if (!isBrowser() || !novelId) {
    return
  }

  localStorage.removeItem(progressStorageKey(novelId))
}

export const useReaderPreferences = () => {
  const preferences = reactive(loadReaderPreferences())

  return {
    preferences,
  }
}
