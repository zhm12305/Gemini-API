<script setup>
import { useDashboardStore } from '../../stores/dashboard'
import { ref, watch, nextTick, onMounted } from 'vue'

const dashboardStore = useDashboardStore()
const currentFilter = ref('ALL')
const logContainer = ref(null)
const isFirstLoad = ref(true)

function filterLogs(level) {
  currentFilter.value = level
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function isAtBottom() {
  if (!logContainer.value) return false

  const container = logContainer.value
  const threshold = 50
  return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
}

watch(() => dashboardStore.logs, async () => {
  await nextTick()

  if (isFirstLoad.value) {
    scrollToBottom()
    isFirstLoad.value = false
  } else if (isAtBottom()) {
    scrollToBottom()
  }
}, { deep: true })

onMounted(() => {
  if (dashboardStore.logs.length > 0) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})
</script>

<template>
  <section class="info-box log-panel">
    <div class="log-header">
      <div>
        <span class="section-kicker">Observability</span>
        <h2 class="section-title">系统日志</h2>
      </div>
      <span class="log-count">{{ dashboardStore.logs.length }} 条</span>
    </div>

    <div class="log-filter">
      <button
        v-for="level in ['ALL', 'INFO', 'WARNING', 'ERROR']"
        :key="level"
        :class="{ active: currentFilter === level }"
        @click="filterLogs(level)"
      >
        {{ level === 'ALL' ? '全部' : level === 'INFO' ? '信息' : level === 'WARNING' ? '警告' : '错误' }}
      </button>
    </div>

    <div class="log-container" ref="logContainer">
      <div
        v-for="(log, index) in dashboardStore.logs"
        :key="index"
        class="log-entry"
        :class="log.level"
        :style="{ display: currentFilter === 'ALL' || log.level === currentFilter ? 'grid' : 'none' }"
      >
        <span class="log-timestamp">{{ log.timestamp }}</span>
        <span class="log-level" :class="log.level">{{ log.level }}</span>
        <span class="log-message">
          <template v-if="log.key !== 'N/A'">[{{ log.key }}]</template>
          <template v-if="log.request_type !== 'N/A'">{{ log.request_type }}</template>
          <template v-if="log.model !== 'N/A'">[{{ log.model }}]</template>
          <template v-if="log.status_code !== 'N/A'">{{ log.status_code }}</template>
          : {{ log.message }}
          <template v-if="log.error_message">
            - {{ log.error_message }}
          </template>
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.log-panel {
  padding: 20px;
  margin-top: 18px;
}

.log-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.log-count {
  min-height: 32px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  background: var(--color-background-soft);
  font-size: 13px;
  font-weight: 750;
}

.log-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.log-filter button {
  min-height: 34px;
  padding: 7px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--button-secondary);
  color: var(--button-secondary-text);
  cursor: pointer;
  font-weight: 750;
  transition: all var(--transition-fast);
}

.log-filter button:hover,
.log-filter button.active {
  border-color: var(--button-primary);
  background: rgba(15, 118, 110, 0.1);
  color: var(--button-primary);
}

.log-container {
  max-height: 520px;
  overflow-y: auto;
  padding: 12px;
  border: 1px solid var(--log-entry-border);
  border-radius: var(--radius-lg);
  background: var(--log-entry-bg);
  color: #d7dde4;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 13px;
  line-height: 1.55;
}

.log-entry {
  grid-template-columns: 156px 76px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  margin-bottom: 7px;
  padding: 9px 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-left-width: 3px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.035);
  word-break: break-word;
}

.log-entry.INFO {
  border-left-color: #60a5fa;
}

.log-entry.WARNING {
  border-left-color: #f59e0b;
}

.log-entry.ERROR {
  border-left-color: #f87171;
}

.log-entry.DEBUG {
  border-left-color: #34d399;
}

.log-timestamp {
  color: #9ca3af;
  white-space: nowrap;
}

.log-level {
  justify-self: start;
  padding: 1px 7px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0;
  text-transform: uppercase;
}

.log-level.INFO {
  color: #bfdbfe;
  background: rgba(96, 165, 250, 0.16);
}

.log-level.WARNING {
  color: #fde68a;
  background: rgba(245, 158, 11, 0.16);
}

.log-level.ERROR {
  color: #fecaca;
  background: rgba(248, 113, 113, 0.16);
}

.log-level.DEBUG {
  color: #bbf7d0;
  background: rgba(52, 211, 153, 0.16);
}

.log-message {
  color: #e5e7eb;
}

@media (max-width: 760px) {
  .log-panel {
    padding: 16px;
  }

  .log-entry {
    grid-template-columns: 1fr;
    gap: 5px;
  }

  .log-timestamp {
    white-space: normal;
  }
}
</style>
