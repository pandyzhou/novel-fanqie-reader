import { describe, expect, it } from 'vitest'
import { isStoreErrorResponse, resolveStoreError } from '../helpers'

describe('store/helpers', () => {
  it('识别标准 ErrorResponse', () => {
    expect(isStoreErrorResponse({ error: '请求失败' })).toBe(true)
    expect(isStoreErrorResponse({ message: '请求失败' })).toBe(false)
  })

  it('优先返回 ErrorResponse.error', () => {
    expect(resolveStoreError({ error: '后端错误' }, '默认错误')).toBe('后端错误')
  })

  it('处理 Error 实例', () => {
    expect(resolveStoreError(new Error('网络中断'), '默认错误')).toBe('网络中断')
  })

  it('处理 response.data.error / message / msg', () => {
    expect(resolveStoreError({ response: { data: { error: 'error 字段' } } }, '默认错误')).toBe('error 字段')
    expect(resolveStoreError({ response: { data: { message: 'message 字段' } } }, '默认错误')).toBe(
      'message 字段',
    )
    expect(resolveStoreError({ response: { data: { msg: 'msg 字段' } } }, '默认错误')).toBe('msg 字段')
  })

  it('无法识别时回退默认文案', () => {
    expect(resolveStoreError({ response: { data: {} } }, '默认错误')).toBe('默认错误')
    expect(resolveStoreError(null, '默认错误')).toBe('默认错误')
  })
})
