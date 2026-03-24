import {
  clearReadingProgress,
  loadReadingProgress,
  loadReaderPreferences,
  resetReaderPreferences,
  saveReadingProgress,
  saveReaderPreferences,
} from '../useReaderPreferences'

describe('useReaderPreferences', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('在没有存储时返回默认阅读偏好', () => {
    const preferences = loadReaderPreferences()

    expect(preferences.fontSize).toBe(18)
    expect(preferences.theme).toBe('light')
    expect(preferences.lineHeight).toBe(1.9)
    expect(preferences.paragraphSpacing).toBe(1)
  })

  it('保存后能读取并校正阅读偏好', () => {
    saveReaderPreferences({
      fontSize: 48,
      theme: 'sepia',
      lineHeight: 3.2,
      paragraphSpacing: 0.1,
    })

    const preferences = loadReaderPreferences()
    expect(preferences.fontSize).toBe(30)
    expect(preferences.theme).toBe('sepia')
    expect(preferences.lineHeight).toBe(2.6)
    expect(preferences.paragraphSpacing).toBe(0.5)
  })

  it('兼容旧版 readingMode 字段', () => {
    localStorage.setItem(
      'reader-preferences',
      JSON.stringify({ fontSize: 20, readingMode: true, lineHeight: 2.1, paragraphSpacing: 1.4 }),
    )

    const preferences = loadReaderPreferences()
    expect(preferences.theme).toBe('dark')
    expect(preferences.fontSize).toBe(20)
  })

  it('保存和清除阅读进度', () => {
    saveReadingProgress('novel-1', {
      chapterId: 'chapter-9',
      chapterTitle: '第九章',
      scrollTop: 245.8,
      updatedAt: 123456,
    })

    expect(loadReadingProgress('novel-1')).toEqual({
      chapterId: 'chapter-9',
      chapterTitle: '第九章',
      scrollTop: 246,
      updatedAt: 123456,
    })

    clearReadingProgress('novel-1')
    expect(loadReadingProgress('novel-1')).toBeNull()
  })

  it('恢复默认偏好时会重写本地存储', () => {
    saveReaderPreferences({
      fontSize: 24,
      theme: 'oled',
      lineHeight: 2.2,
      paragraphSpacing: 1.8,
    })

    const resetValue = resetReaderPreferences()
    expect(resetValue).toEqual({
      fontSize: 18,
      theme: 'light',
      lineHeight: 1.9,
      paragraphSpacing: 1,
    })
    expect(loadReaderPreferences()).toEqual(resetValue)
  })
})
