<template>
  <el-card shadow="hover" :class="['data-card', 'page-panel-card', cardClass]">
    <template #header>
      <div class="card-header">
        <h3>{{ title }}</h3>
        <div v-if="$slots.actions" class="card-actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <div :class="bodyClass" v-loading="loading">
      <slot />
    </div>
  </el-card>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    loading?: boolean
    bodyClass?: string
    cardClass?: string
  }>(),
  {
    loading: false,
    bodyClass: '',
    cardClass: '',
  },
)
</script>

<style scoped>
.data-card {
  margin-bottom: 20px;
  border-radius: 20px;
  overflow: hidden;
}

:deep(.data-card .el-card__header) {
  padding: 18px 20px 16px;
}

:deep(.data-card .el-card__body) {
  padding: 20px;
}

.overview-card {
  background: var(--panel-raised-bg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  position: relative;
  height: 400px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 30px, rgba(84, 227, 255, 0.04) 30px, rgba(84, 227, 255, 0.04) 31px),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.table-panel {
  min-height: 180px;
  padding: 0;
}

@media (max-width: 768px) {
  :deep(.data-card .el-card__header),
  :deep(.data-card .el-card__body) {
    padding-inline: 16px;
  }

  .chart-container {
    height: 340px;
    padding: 12px;
  }

  .card-header {
    flex-wrap: wrap;
  }
}
</style>
