<script setup>
import { useDashboardStore } from '../../stores/dashboard'
import { ref } from 'vue'
import StatusStats from './status/StatusStats.vue'
import ApiKeyStats from './status/ApiKeyStats.vue'

const dashboardStore = useDashboardStore()

const showResetDialog = ref(false)
const resetPassword = ref('')
const resetError = ref('')
const isResetting = ref(false)

function openResetDialog() {
  showResetDialog.value = true
  resetPassword.value = ''
  resetError.value = ''
}

function closeResetDialog() {
  showResetDialog.value = false
  resetPassword.value = ''
  resetError.value = ''
}

async function resetStats() {
  if (!resetPassword.value) {
    resetError.value = '请输入密码'
    return
  }

  isResetting.value = true
  resetError.value = ''

  try {
    const response = await fetch('/api/reset-stats', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ password: resetPassword.value })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '重置失败')
    }

    await dashboardStore.fetchDashboardData()

    setTimeout(async () => {
      try {
        await dashboardStore.fetchDashboardData()
      } catch (error) {
        console.error('刷新数据失败:', error)
      } finally {
        closeResetDialog()
      }
    }, 1000)
  } catch (error) {
    console.error('重置失败:', error)
    resetError.value = error.message || '重置失败，请检查密码是否正确'
  } finally {
    isResetting.value = false
  }
}
</script>

<template>
  <section class="info-box status-panel">
    <div class="section-header">
      <div>
        <span class="section-kicker">Runtime</span>
        <h2 class="section-title">运行状态</h2>
      </div>
      <div class="section-actions">
        <span class="status-pill">服务运行中</span>
        <button class="reset-button" @click="openResetDialog" v-if="!dashboardStore.status.enableVertex">
          重置次数
        </button>
      </div>
    </div>

    <div class="vertex-notice" v-if="dashboardStore.status.enableVertex">
      <div class="notice-mark">i</div>
      <div class="notice-content">
        <h3 class="notice-title">Vertex 模式说明</h3>
        <p class="notice-text">当前项目处于 Vertex 模式，基于 gzzhongqi/vertex2openai 适配，统计功能正在逐步完善中。</p>
      </div>
    </div>

    <StatusStats />
    <ApiKeyStats />

    <div v-if="showResetDialog" class="dialog-overlay">
      <div class="dialog">
        <h3>重置 API 调用统计</h3>
        <p>请输入管理密码确认重置统计数据。</p>
        <input
          type="password"
          v-model="resetPassword"
          placeholder="请输入密码"
          @keyup.enter="resetStats"
        />
        <div v-if="resetError" class="error-message">{{ resetError }}</div>
        <div class="dialog-buttons">
          <button class="cancel-button" @click="closeResetDialog">取消</button>
          <button class="confirm-button" @click="resetStats" :disabled="isResetting">
            {{ isResetting ? '重置中...' : '确认重置' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.status-panel {
  padding: 20px;
  margin-bottom: 18px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 10px;
  border: 1px solid rgba(15, 159, 110, 0.24);
  border-radius: var(--radius-md);
  background: rgba(15, 159, 110, 0.1);
  color: var(--color-success);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.status-pill::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
}

.reset-button,
.cancel-button,
.confirm-button {
  min-height: 34px;
  padding: 7px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 750;
  transition: all var(--transition-fast);
}

.reset-button,
.cancel-button {
  border: 1px solid var(--color-border);
  background: var(--button-secondary);
  color: var(--button-secondary-text);
}

.reset-button:hover,
.cancel-button:hover {
  border-color: var(--button-primary);
  color: var(--button-primary);
}

.confirm-button {
  border: 1px solid var(--button-primary);
  background: var(--button-primary);
  color: #ffffff;
}

.confirm-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.vertex-notice {
  display: flex;
  gap: 12px;
  padding: 14px;
  margin-bottom: 18px;
  border: 1px solid rgba(37, 99, 235, 0.22);
  border-radius: var(--radius-lg);
  background: rgba(37, 99, 235, 0.08);
}

.notice-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  border-radius: var(--radius-md);
  background: var(--color-info);
  color: #ffffff;
  font-weight: 850;
}

.notice-title {
  margin: 0 0 4px;
  color: var(--color-heading);
  font-size: 15px;
  font-weight: 800;
}

.notice-text {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 110px 18px 18px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
}

.dialog {
  width: min(100%, 420px);
  padding: 22px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-xl);
}

.dialog h3 {
  margin: 0 0 8px;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 800;
}

.dialog p {
  margin: 0 0 16px;
  color: var(--color-text-muted);
}

.dialog input {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  outline: none;
}

.dialog input:focus {
  border-color: var(--button-primary);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
}

.error-message {
  margin-top: 10px;
  padding: 9px 10px;
  border: 1px solid rgba(220, 38, 38, 0.22);
  border-radius: var(--radius-md);
  background: var(--color-error-bg);
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 700;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 640px) {
  .status-panel {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
  }

  .section-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
