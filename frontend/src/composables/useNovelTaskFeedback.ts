export const isAlreadyActiveTaskError = (message: string) =>
  message.toLowerCase().includes('already active') || message.includes('已有进行中的任务')

export const resolveQueuedNovelSuccessMessage = (mode: 'full' | 'preview' | 'refresh') => {
  if (mode === 'preview') {
    return '小说添加成功，开始下载前10章（预览模式），请到任务管理查看进度'
  }

  if (mode === 'refresh') {
    return '已添加到更新队列，请到任务管理查看进度'
  }

  return '小说添加成功，开始下载全本，请到任务管理查看进度'
}

export const resolveQueuedNovelErrorPresentation = (
  errorMessage: string | null | undefined,
  fallbackMessage: string,
) => {
  const normalizedMessage = errorMessage?.trim() || fallbackMessage

  if (isAlreadyActiveTaskError(normalizedMessage)) {
    return {
      type: 'warning' as const,
      message: '这本小说已有进行中的任务，请到任务管理查看进度',
    }
  }

  return {
    type: 'error' as const,
    message: normalizedMessage,
  }
}
