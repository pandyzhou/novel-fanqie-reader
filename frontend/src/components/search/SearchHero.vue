<template>
  <section class="search-hero">
    <div>
      <p class="hero-badge">搜索与下载</p>
      <h2 class="page-title">搜索小说</h2>
      <p class="hero-subtitle">支持自动加载、排序筛选、批量下载与本地缓存加速。</p>
    </div>
    <div class="hero-stats">
      <div class="hero-stat-card">
        <span class="stat-label">已加载</span>
        <strong>{{ loadedCount }}</strong>
      </div>
      <div class="hero-stat-card">
        <span class="stat-label">当前结果</span>
        <strong>{{ visibleCount }}</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  loadedCount: number
  visibleCount: number
}>()
</script>

<style scoped>
.search-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  padding: 24px;
  border-radius: 18px;
  background: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow: var(--shell-glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.34);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(155%);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  margin-bottom: 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.hero-subtitle {
  max-width: 720px;
  color: var(--text-secondary);
  font-size: 14px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
}

.hero-stat-card {
  min-width: 120px;
  padding: 16px 18px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04)),
    var(--surface-muted);
  border: 1px solid var(--border-color-light);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.26), 0 0 20px rgba(84, 227, 255, 0.08);
}

.stat-label {
  display: block;
  color: var(--text-tertiary);
  font-size: 12px;
  margin-bottom: 6px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-stat-card strong {
  font-size: 28px;
  color: var(--text-primary);
  text-shadow: 0 0 18px rgba(84, 227, 255, 0.12);
}

@media (max-width: 768px) {
  .search-hero {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 20px;
  }

  .hero-subtitle {
    font-size: 13px;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-stat-card {
    min-width: 0;
    padding: 14px;
  }

  .hero-stat-card strong {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
