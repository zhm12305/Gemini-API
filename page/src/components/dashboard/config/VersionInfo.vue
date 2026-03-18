<script setup>
import { useDashboardStore } from '../../../stores/dashboard'

const dashboardStore = useDashboardStore()
</script>

<template>
  <div>
    <h3 class="section-title">版本信息</h3>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ dashboardStore.config.localVersion }}</div>
        <div class="stat-label">当前版本</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboardStore.config.remoteVersion }}</div>
        <div class="stat-label">最新版本</div>
      </div>
      <div class="stat-card">
        <div class="update-status-container">
          <div class="update-status" v-if="dashboardStore.config.hasUpdate">
            <span class="status-icon update-needed">⚠️</span>
            <span class="status-text update-needed">需要更新</span>
          </div>
          <div class="update-status" v-else>
            <span class="status-icon up-to-date">✓</span>
            <span class="status-text up-to-date">已是最新</span>
          </div>
        </div>
        <div class="stat-label">更新状态</div>
      </div>
    </div>

    <!-- 项目地址 -->
    <div class="project-link-container">
      <a href="https://github.com/wyeeeee/hajimi" target="_blank" rel="noopener noreferrer" class="project-link">
        <span class="github-icon">🌸</span>
        <span class="project-text">项目地址：github.com/wyeeeee/hajimi</span>
        <span class="github-icon">🌸</span>
      </a>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 10px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  position: relative;
  font-weight: 600;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: var(--gradient-primary);
}

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
    gap: 8px;
  }
}

.stat-card {
  background-color: var(--stats-item-bg);
  padding: 10px 15px;
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
  height: 3px;
  background: var(--gradient-secondary);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: var(--button-primary);
}

.stat-card:hover::before {
  opacity: 1;
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
  position: relative;
  display: inline-block;
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

.stat-card:hover .stat-label {
  opacity: 1;
  color: var(--color-heading);
}

/* 版本更新状态样式 */
.update-status-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  width: 100%;
}

.update-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.update-status .status-icon {
  font-size: 1.2em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.update-status .status-text {
  font-size: 1em;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.update-status .status-icon.update-needed,
.update-status .status-text.update-needed {
  color: #ef4444;
}

.update-status .status-icon.up-to-date,
.update-status .status-text.up-to-date {
  color: #10b981;
}

/* 项目链接样式 */
.project-link-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
  margin-top: 20px;
  transition: all 0.3s ease;
}

.project-link {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--button-primary);
  text-decoration: none;
  font-size: 14px;
  padding: 10px 18px;
  border-radius: var(--radius-full);
  background-color: var(--stats-item-bg);
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--card-border);
  position: relative;
  overflow: hidden;
}

.project-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.project-link:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  background-color: var(--color-background-mute);
  border-color: var(--button-primary);
}

.project-link:hover::before {
  transform: translateX(100%);
}

.github-icon {
  font-size: 18px;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.project-link:hover .github-icon {
  opacity: 1;
  transform: scale(1.2) rotate(10deg);
}

.project-text {
  font-weight: 500;
  position: relative;
}

.project-text::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--gradient-primary);
  transition: width 0.3s ease;
}

.project-link:hover .project-text::after {
  width: 100%;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .stat-card {
    padding: 8px 8px;
  }
  
  .stat-value {
    font-size: 16px;
  }
  
  .stat-label {
    font-size: 12px;
    margin-top: 2px;
  }
  
  .update-status {
    padding: 6px 10px;
  }
  
  .update-status .status-icon {
    font-size: 1.1em;
  }
  
  .update-status .status-text {
    font-size: 0.9em;
  }
  
  .project-link {
    font-size: 12px;
    padding: 8px 14px;
  }
  
  .github-icon {
    font-size: 16px;
  }
}

/* 小屏幕手机进一步优化 */
@media (max-width: 480px) {
  .stat-card {
    padding: 6px 6px;
  }
  
  .stat-value {
    font-size: 14px;
  }
  
  .stat-label {
    font-size: 11px;
    margin-top: 1px;
  }
  
  .update-status {
    padding: 4px 8px;
  }
  
  .update-status .status-icon {
    font-size: 1em;
  }
  
  .update-status .status-text {
    font-size: 0.85em;
  }
  
  .project-link {
    font-size: 11px;
    padding: 6px 12px;
  }
  
  .github-icon {
    font-size: 14px;
  }
}
</style> 