<script setup>
import { useDashboardStore } from '../../stores/dashboard'
import { ref, watch, nextTick, onMounted } from 'vue'

const dashboardStore = useDashboardStore()
const currentFilter = ref('ALL')
const logContainer = ref(null)
const isFirstLoad = ref(true)
const userScrolled = ref(false)

// 过滤日志
function filterLogs(level) {
  currentFilter.value = level
}

// 滚动到底部
function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

// 检查用户是否在底部
function isAtBottom() {
  if (!logContainer.value) return false
  
  const container = logContainer.value
  const threshold = 50 // 距离底部多少像素以内算作"在底部"
  return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
}

// 监听滚动事件
function handleScroll() {
  userScrolled.value = true
}

// 监听日志变化，保持滚动位置
watch(() => dashboardStore.logs, async () => {
  await nextTick()
  
  // 如果是第一次加载，滚动到底部
  if (isFirstLoad.value) {
    scrollToBottom()
    isFirstLoad.value = false
  } 
  // 如果用户已经在底部，则自动滚动到底部
  else if (isAtBottom()) {
    scrollToBottom()
  }
}, { deep: true })

// 组件挂载时，如果有日志数据，滚动到底部
onMounted(() => {
  if (dashboardStore.logs.length > 0) {
    nextTick(() => {
      scrollToBottom()
    })
  }
  
  // 添加滚动事件监听
  if (logContainer.value) {
    logContainer.value.addEventListener('scroll', handleScroll)
  }
})
</script>

<template>
  <div class="info-box">
    <h2 class="section-title">📋 系统日志</h2>
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
        :style="{ display: currentFilter === 'ALL' || log.level === currentFilter ? 'block' : 'none' }"
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
  </div>
</template>

<style scoped>
.info-box {
  background-color: var(--card-background);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-xl);
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.info-box::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--gradient-info);
  opacity: 0.8;
}

/* 移动端优化 - 减小外边距 */
@media (max-width: 768px) {
  .info-box {
    margin-bottom: 12px;
    padding: 15px 10px;
    border-radius: var(--radius-lg);
  }
}

@media (max-width: 480px) {
  .info-box {
    margin-bottom: 8px;
    padding: 12px 8px;
    border-radius: var(--radius-md);
  }
}

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
  background: var(--gradient-info);
}

.log-filter {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
  gap: 10px;
  flex-wrap: wrap;
}

.log-filter button {
  padding: 8px 12px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  background-color: var(--stats-item-bg);
  color: var(--color-text);
  cursor: pointer;
  min-width: 70px;
  transition: all 0.3s ease;
  font-weight: 500;
  position: relative;
  overflow: hidden;
}

.log-filter button::before {
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

.log-filter button:hover::before {
  transform: translateX(100%);
}

.log-filter button.active {
  background: var(--gradient-info);
  color: white;
  border-color: transparent;
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.log-filter button:not(.active):hover {
  background-color: var(--color-background-mute);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

/* 移动端优化 */
@media (max-width: 768px) {
  .log-filter {
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .log-filter button {
    padding: 6px 10px;
    font-size: 12px;
    min-width: 60px;
  }
}

/* 小屏幕手机进一步优化 */
@media (max-width: 480px) {
  .log-filter {
    gap: 4px;
    margin-bottom: 10px;
  }
  
  .log-filter button {
    padding: 5px 8px;
    font-size: 11px;
    min-width: 50px;
  }
}

.log-container {
  background-color: var(--log-entry-bg);
  border: 1px solid var(--log-entry-border);
  border-radius: var(--radius-lg);
  padding: 15px;
  margin-top: 20px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 14px;
  line-height: 1.5;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: var(--color-background-mute);
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb {
  background: var(--button-primary);
  border-radius: 4px;
  opacity: 0.7;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: var(--button-primary-hover);
}

.log-entry {
  margin-bottom: 8px;
  padding: 10px;
  border-radius: var(--radius-md);
  word-break: break-word;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  border-left: 4px solid transparent;
  animation: logEntryAppear 0.3s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}

@keyframes logEntryAppear {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.log-entry::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.log-entry:hover::after {
  transform: translateX(100%);
}

.log-entry.INFO {
  background-color: rgba(59, 130, 246, 0.1);
  border-left: 4px solid #3b82f6;
}

.log-entry.WARNING {
  background-color: rgba(245, 158, 11, 0.1);
  border-left: 4px solid #f59e0b;
}

.log-entry.ERROR {
  background-color: rgba(239, 68, 68, 0.1);
  border-left: 4px solid #ef4444;
}

.log-entry.DEBUG {
  background-color: rgba(16, 185, 129, 0.1);
  border-left: 4px solid #10b981;
}

.log-timestamp {
  color: var(--color-text);
  font-size: 12px;
  margin-right: 10px;
  opacity: 0.8;
  transition: all 0.3s ease;
  font-weight: 500;
}

.log-level {
  font-weight: bold;
  margin-right: 10px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-level.INFO {
  color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.1);
}

.log-level.WARNING {
  color: #f59e0b;
  background-color: rgba(245, 158, 11, 0.1);
}

.log-level.ERROR {
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
}

.log-level.DEBUG {
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
}

.log-message {
  color: var(--color-text);
  transition: all 0.3s ease;
  line-height: 1.6;
}

.log-entry:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-sm);
}

.log-entry:hover .log-timestamp {
  opacity: 1;
  color: var(--button-primary);
}

.log-entry:hover .log-message {
  color: var(--color-heading);
}

@media (max-width: 768px) {
  .log-container {
    padding: 12px;
    font-size: 13px;
    max-height: 400px;
  }
  
  .log-entry {
    padding: 8px;
    margin-bottom: 6px;
  }
  
  .log-timestamp {
    font-size: 11px;
    display: block;
    margin-bottom: 3px;
  }
  
  .log-level {
    font-size: 11px;
    padding: 1px 4px;
  }
}

@media (max-width: 480px) {
  .log-container {
    padding: 10px;
    font-size: 12px;
    max-height: 350px;
  }
  
  .log-entry {
    padding: 6px;
    margin-bottom: 5px;
  }
  
  .log-timestamp {
    font-size: 10px;
  }
  
  .log-level {
    font-size: 10px;
    padding: 1px 3px;
    margin-right: 5px;
  }
  
  .log-message {
    font-size: 11px;
  }
}
</style>