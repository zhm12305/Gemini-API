<script setup>
import { useDashboardStore } from '../../../stores/dashboard'

const dashboardStore = useDashboardStore()
</script>

<template>
  <div class="stats-grid" v-if="!dashboardStore.status.enableVertex">
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.status.keyCount }}</div>
      <div class="stat-label">可用密钥数量</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.status.modelCount }}</div>
      <div class="stat-label">可用模型数量</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.maxRetryNum }}</div>
      <div class="stat-label">最大重试次数</div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stat-card {
  min-height: 104px;
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--stats-item-bg);
  box-shadow: var(--shadow-sm);
}

.stat-value {
  color: var(--color-heading);
  font-size: 28px;
  line-height: 1;
  font-weight: 850;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 750;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    min-height: auto;
  }
}
</style>
