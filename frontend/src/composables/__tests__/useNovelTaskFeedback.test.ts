import {
  isAlreadyActiveTaskError,
  resolveQueuedNovelErrorPresentation,
  resolveQueuedNovelSuccessMessage,
} from '../useNovelTaskFeedback'

describe('useNovelTaskFeedback', () => {
  it('识别英文 already active 错误', () => {
    expect(isAlreadyActiveTaskError('Task is already active with status DOWNLOADING.')).toBe(true)
  })

  it('识别中文已有进行中的任务错误', () => {
    expect(isAlreadyActiveTaskError('这本小说已有进行中的任务，请稍后重试')).toBe(true)
  })

  it('返回不同模式的成功提示文案', () => {
    expect(resolveQueuedNovelSuccessMessage('full')).toContain('下载全本')
    expect(resolveQueuedNovelSuccessMessage('preview')).toContain('前10章')
    expect(resolveQueuedNovelSuccessMessage('refresh')).toContain('更新队列')
  })

  it('活动任务冲突时返回 warning 展示模型', () => {
    const presentation = resolveQueuedNovelErrorPresentation(
      'Task is already active with status DOWNLOADING.',
      '添加小说失败',
    )

    expect(presentation.type).toBe('warning')
    expect(presentation.message).toContain('已有进行中的任务')
  })

  it('普通错误时返回 error 展示模型', () => {
    const presentation = resolveQueuedNovelErrorPresentation('后端服务不可用', '添加小说失败')

    expect(presentation.type).toBe('error')
    expect(presentation.message).toBe('后端服务不可用')
  })
})
