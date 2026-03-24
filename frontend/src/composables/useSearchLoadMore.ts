import { nextTick, onMounted, onUnmounted, ref, type Ref, watch } from 'vue'

interface UseSearchLoadMoreOptions {
  enabled: Ref<boolean>
  canLoadMore: Ref<boolean>
  onLoadMore: () => Promise<void> | void
  rootMargin?: string
}

export const useSearchLoadMore = ({
  enabled,
  canLoadMore,
  onLoadMore,
  rootMargin = '300px 0px',
}: UseSearchLoadMoreOptions) => {
  const triggerRef = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  const syncObserver = async () => {
    if (!observer) {
      return
    }

    observer.disconnect()
    await nextTick()

    if (enabled.value && triggerRef.value) {
      observer.observe(triggerRef.value)
    }
  }

  const setTriggerRef = (element: HTMLElement | null) => {
    triggerRef.value = element
    void syncObserver()
  }

  watch(
    () => [enabled.value, canLoadMore.value, triggerRef.value],
    () => {
      void syncObserver()
    },
  )

  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry?.isIntersecting && canLoadMore.value) {
          void onLoadMore()
        }
      },
      {
        rootMargin,
        threshold: 0,
      },
    )

    void syncObserver()
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })

  return {
    setTriggerRef,
  }
}
