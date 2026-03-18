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
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 15px;
  margin-bottom: 20px;
}

/* 移动端优化 - 保持三栏但减小间距 */
@media (max-width: 768px) {
  .stats-grid {
    gap: 6px;
  }
}

.stat-card {
  background-color: var(--stats-item-bg);
  padding: 15px;
  border-radius: var(--radius-lg);
  text-align: center;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--card-border);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: var(--gradient-secondary);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
  border-color: var(--button-primary);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--button-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.3s ease;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text);
  margin-top: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.3s ease;
  opacity: 0.8;
}

/* 移动端优化 - 更紧凑的卡片 */
@media (max-width: 768px) {
  .stat-card {
    padding: 8px 5px;
  }
  
  .stat-value {
    font-size: 16px;
  }
  
  .stat-label {
    font-size: 11px;
    margin-top: 3px;
  }
}

/* 小屏幕手机进一步优化 */
@media (max-width: 480px) {
  .stat-card {
    padding: 6px 3px;
  }
  
  .stat-value {
    font-size: 14px;
  }
  
  .stat-label {
    font-size: 10px;
    margin-top: 2px;
  }
}
</style> 