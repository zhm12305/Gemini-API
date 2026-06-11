<script setup>
import { useDashboardStore } from '../../stores/dashboard'
import { ref } from 'vue'
import BasicConfig from './config/BasicConfig.vue'
import FeaturesConfig from './config/FeaturesConfig.vue'
import VersionInfo from './config/VersionInfo.vue'
import VertexConfig from './config/VertexConfig.vue'

const dashboardStore = useDashboardStore()
const isExpanded = ref(true)
const basicConfigRef = ref(null)
const featuresConfigRef = ref(null)
const sharedPassword = ref('')
const overallErrorMsg = ref('')
const overallSuccessMsg = ref('')
const isOverallSaving = ref(false)

const getFoldIconClass = (isVisible) => {
  return isVisible ? 'fold-icon rotated' : 'fold-icon'
}

async function handleSaveAllConfigs() {
  if (!sharedPassword.value) {
    overallErrorMsg.value = '请输入管理密码'
    overallSuccessMsg.value = ''
    return
  }

  isOverallSaving.value = true
  overallErrorMsg.value = ''
  overallSuccessMsg.value = ''
  let errors = []
  let successes = []

  try {
    if (basicConfigRef.value && typeof basicConfigRef.value.saveComponentConfigs === 'function') {
      const result = await basicConfigRef.value.saveComponentConfigs(sharedPassword.value)
      if (result.success) successes.push(result.message)
      else errors.push(result.message)
    }

    if (featuresConfigRef.value && typeof featuresConfigRef.value.saveComponentConfigs === 'function') {
      const result = await featuresConfigRef.value.saveComponentConfigs(sharedPassword.value)
      if (result.success) successes.push(result.message)
      else errors.push(result.message)
    }

    if (errors.length > 0) {
      overallErrorMsg.value = errors.join('; ')
    }
    if (successes.length > 0 && errors.length === 0) {
      overallSuccessMsg.value = '所有配置已成功保存: ' + successes.join('; ')
    } else if (successes.length > 0 && errors.length > 0) {
      overallSuccessMsg.value = '部分配置已保存: ' + successes.join('; ') + '. 部分失败.'
    }
  } catch (error) {
    overallErrorMsg.value = error.message || '保存过程中发生意外错误'
  } finally {
    isOverallSaving.value = false
  }
}
</script>

<template>
  <section class="info-box config-panel">
    <div v-if="dashboardStore.status.enableVertex">
      <VertexConfig />
      <VersionInfo />
    </div>

    <div v-else>
      <div class="config-header" @click="isExpanded = !isExpanded">
        <div>
          <span class="section-kicker">Configuration</span>
          <h3 class="section-title">环境配置</h3>
        </div>
        <span :class="getFoldIconClass(isExpanded)">
          <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </span>
      </div>

      <div v-if="!isExpanded" class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.config.maxRequestsPerMinute }}</div>
          <div class="stat-label">每分钟请求限制</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.config.concurrentRequests }}</div>
          <div class="stat-label">并发请求数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.config.currentTime }}</div>
          <div class="stat-label">当前服务器时间</div>
        </div>
      </div>

      <transition name="fold">
        <div v-if="isExpanded" class="fold-content">
          <BasicConfig ref="basicConfigRef" />
          <FeaturesConfig ref="featuresConfigRef" />

          <div class="shared-save-section">
            <div class="password-input-group">
              <label for="sharedPasswordInput" class="shared-password-label">管理密码</label>
              <input
                type="password"
                id="sharedPasswordInput"
                v-model="sharedPassword"
                placeholder="请输入管理密码以保存更改"
                class="config-input"
              >
            </div>
            <button class="save-all-button" @click="handleSaveAllConfigs" :disabled="isOverallSaving">
              {{ isOverallSaving ? '保存中...' : '保存基本与功能配置' }}
            </button>
          </div>

          <div v-if="overallErrorMsg" class="overall-error-message">{{ overallErrorMsg }}</div>
          <div v-if="overallSuccessMsg" class="overall-success-message">{{ overallSuccessMsg }}</div>
        </div>
      </transition>
      <VersionInfo />
    </div>
  </section>
</template>

<style scoped>
.config-panel {
  padding: 20px;
  margin-bottom: 18px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  cursor: pointer;
}

.fold-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--button-primary);
  transition: transform var(--transition-fast), background var(--transition-fast);
}

.config-header:hover .fold-icon {
  background: rgba(15, 118, 110, 0.08);
}

.fold-icon.rotated {
  transform: rotate(180deg);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stat-card {
  padding: 14px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--stats-item-bg);
}

.stat-value {
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 850;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.fold-content {
  overflow: hidden;
}

.fold-enter-active,
.fold-leave-active {
  transition: all var(--transition-normal);
  max-height: 1100px;
  opacity: 1;
}

.fold-enter-from,
.fold-leave-to {
  max-height: 0;
  opacity: 0;
}

.shared-save-section {
  display: grid;
  gap: 12px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}

.shared-password-label {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text);
  font-size: 13px;
  font-weight: 750;
}

.config-input {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  outline: none;
}

.config-input:focus {
  border-color: var(--button-primary);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
}

.save-all-button {
  min-height: 40px;
  border: 1px solid var(--button-primary);
  border-radius: var(--radius-md);
  background: var(--button-primary);
  color: #ffffff;
  cursor: pointer;
  font-weight: 800;
}

.save-all-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.overall-error-message,
.overall-success-message {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 700;
}

.overall-error-message {
  color: var(--color-danger);
  background: var(--color-error-bg);
  border: 1px solid rgba(220, 38, 38, 0.22);
}

.overall-success-message {
  color: var(--color-success);
  background: var(--color-success-bg);
  border: 1px solid rgba(15, 159, 110, 0.22);
}

@media (max-width: 640px) {
  .config-panel {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
