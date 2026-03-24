import type { ErrorResponse } from '../api'

export const isStoreErrorResponse = (value: unknown): value is ErrorResponse =>
  typeof value === 'object' && value !== null && 'error' in value && typeof (value as ErrorResponse).error === 'string'

export const resolveStoreError = (error: unknown, fallbackMessage: string): string => {
  if (isStoreErrorResponse(error)) {
    return error.error
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message.trim()
  }

  if (typeof error === 'object' && error !== null && 'response' in error) {
    const candidate = error as { response?: { data?: { error?: string; message?: string; msg?: string } } }
    const payload = candidate.response?.data
    if (typeof payload?.error === 'string' && payload.error.trim()) {
      return payload.error.trim()
    }
    if (typeof payload?.message === 'string' && payload.message.trim()) {
      return payload.message.trim()
    }
    if (typeof payload?.msg === 'string' && payload.msg.trim()) {
      return payload.msg.trim()
    }
  }

  return fallbackMessage
}
