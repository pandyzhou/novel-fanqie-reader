import { ElMessageBox, type ElMessageBoxOptions } from 'element-plus'

export type ConfirmDialogOptions = Omit<ElMessageBoxOptions, 'message' | 'title' | 'icon'>

export const showConfirmDialog = (
  message: ElMessageBoxOptions['message'],
  title: ElMessageBoxOptions['title'],
  options: ConfirmDialogOptions = {},
) => {
  const { type: _ignoredType, ...restOptions } = options

  return ElMessageBox.confirm(message, title, {
    type: '',
    icon: '',
    ...restOptions,
  })
}
