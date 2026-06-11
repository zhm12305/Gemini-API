<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import StatusSection from '../components/dashboard/StatusSection.vue'
import ConfigSection from '../components/dashboard/ConfigSection.vue'
import LogSection from '../components/dashboard/LogSection.vue'
import { useDashboardStore } from '../stores/dashboard'
import { useBackendStore } from '../stores/backend'

const dashboardStore = useDashboardStore()
const backendStore = useBackendStore()
const router = useRouter()
const refreshInterval = ref(null)

const isDarkMode = computed(() => dashboardStore.isDarkMode)
const config = computed(() => dashboardStore.config)
const userAuth = computed(() => dashboardStore.userAuth)
const baseUrlText = computed(() => (config.value.geminiApiBaseUrls || []).join(' / ') || '未配置')

const showPasswordDialog = ref(false)
const password = ref('')
const passwordError = ref('')

onMounted(() => {
  fetchDashboardData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

function startAutoRefresh() {
  if (!refreshInterval.value) {
    refreshInterval.value = setInterval(fetchDashboardData, 1000)
  }
}

function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

async function fetchDashboardData() {
  try {
    await dashboardStore.fetchDashboardData()
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
  }
}

function handleRefresh() {
  fetchDashboardData()
}

function openBackendManager() {
  router.push('/backends')
}

function toggleDarkMode() {
  dashboardStore.toggleDarkMode()
}

function openPasswordDialog() {
  showPasswordDialog.value = true
  password.value = ''
  passwordError.value = ''
}

function closePasswordDialog() {
  showPasswordDialog.value = false
  password.value = ''
  passwordError.value = ''
}

async function verifyAndToggleVertex() {
  if (!password.value) {
    passwordError.value = '请输入密码'
    return
  }

  try {
    await dashboardStore.updateConfig('enableVertex', !config.value.enableVertex, password.value)
    dashboardStore.config.enableVertex = !config.value.enableVertex
    closePasswordDialog()
  } catch (error) {
    passwordError.value = error.message || '密码错误'
  }
}
</script>

<template>
  <main class="dashboard">
    <section class="page-hero">
      <div class="hero-copy">
        <div class="hero-heading">
          <img :src="'/assets/favicon.ico'" alt="Gemini API Proxy" class="hero-logo">
          <span class="section-kicker">Gemini API Proxy</span>
        </div>
        <h1>Gemini Key 池、工具调用与用户密钥网关</h1>
        <p>
          统一接收 OpenAI 与 Gemini 格式请求，后端完成 Key 轮询、健康冷却、真实模型响应透传、工具编排和用户级 API Key 分发。
        </p>
        <div class="hero-tags">
          <span>OpenAI Compatible</span>
          <span>Gemini Native</span>
          <span>Tool Calling</span>
          <span>User API Keys</span>
        </div>
      </div>

      <div class="hero-actions">
        <div class="runtime-card">
          <span class="runtime-label">当前后端</span>
          <strong>{{ backendStore.activeBackend?.name || '未连接' }}</strong>
          <small>{{ baseUrlText }}</small>
          <button class="text-button" @click="openBackendManager">管理实例</button>
        </div>

        <div class="action-row">
          <button class="control-button" :class="{ active: config.enableVertex }" @click="openPasswordDialog">
            Vertex {{ config.enableVertex ? '已启用' : '未启用' }}
          </button>
          <button class="control-button" :class="{ active: isDarkMode }" @click="toggleDarkMode">
            {{ isDarkMode ? '深色模式' : '浅色模式' }}
          </button>
          <button class="control-button primary" @click="handleRefresh">
            刷新数据
          </button>
        </div>
      </div>
    </section>

    <section class="insight-strip">
      <div class="insight-item">
        <span>可用 Key</span>
        <strong>{{ dashboardStore.status.keyCount }}</strong>
      </div>
      <div class="insight-item">
        <span>模型目录</span>
        <strong>{{ dashboardStore.status.modelCount }}</strong>
      </div>
      <div class="insight-item">
        <span>用户账户</span>
        <strong>{{ userAuth.users }}</strong>
      </div>
      <div class="insight-item">
        <span>用户 Key</span>
        <strong>{{ userAuth.active_api_keys }}</strong>
      </div>
    </section>

    <div class="dashboard-grid">
      <StatusSection class="status-section" />
      <ConfigSection class="config-section" />
    </div>

    <LogSection />

    <div class="password-dialog" v-if="showPasswordDialog">
      <div class="password-dialog-content">
        <h3>验证管理密码</h3>
        <p>请输入密码以{{ config.enableVertex ? '禁用' : '启用' }} Vertex AI。</p>
        <input
          type="password"
          v-model="password"
          class="password-input"
          placeholder="请输入密码"
          @keyup.enter="verifyAndToggleVertex"
        >
        <div class="password-error" v-if="passwordError">{{ passwordError }}</div>
        <div class="password-actions">
          <button class="dialog-button" @click="closePasswordDialog">取消</button>
          <button class="dialog-button primary" @click="verifyAndToggleVertex">确认</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.dashboard {
  width: min(100%, var(--content-width));
  margin: 0 auto;
  padding: 28px 22px 42px;
}

.page-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.8fr);
  gap: 22px;
  align-items: stretch;
  margin-bottom: 18px;
}

.hero-copy,
.runtime-card,
.insight-strip,
.password-dialog-content {
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-md);
}

.hero-copy {
  padding: 26px;
  position: relative;
  overflow: hidden;
}

.hero-copy::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--accent-bar);
}

.hero-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-logo {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
}

.hero-copy h1 {
  margin: 8px 0 10px;
  color: var(--color-heading);
  font-size: 42px;
  line-height: 1.08;
  font-weight: 850;
  letter-spacing: 0;
}

.hero-copy p {
  max-width: 760px;
  margin: 0;
  color: var(--color-text-muted);
  font-size: 15px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.hero-tags span {
  padding: 6px 9px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--stats-item-bg);
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 800;
}

.hero-actions {
  display: grid;
  gap: 12px;
}

.runtime-card {
  display: grid;
  gap: 6px;
  padding: 20px;
}

.runtime-label {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 700;
}

.runtime-card strong {
  color: var(--color-heading);
  font-size: 24px;
  font-weight: 850;
  word-break: break-word;
}

.runtime-card small {
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.45;
  word-break: break-word;
}

.text-button {
  justify-self: start;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--button-primary);
  cursor: pointer;
  font-weight: 750;
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.control-button {
  min-height: 44px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--card-background);
  color: var(--color-text);
  cursor: pointer;
  font-weight: 750;
  transition: all var(--transition-fast);
}

.control-button:hover {
  border-color: var(--button-primary);
  color: var(--button-primary);
  transform: translateY(-1px);
}

.control-button.active {
  background: rgba(15, 118, 110, 0.1);
  border-color: rgba(15, 118, 110, 0.35);
  color: var(--button-primary);
}

.control-button.primary {
  grid-column: 1 / -1;
  background: var(--button-primary);
  color: #ffffff;
  border-color: var(--button-primary);
}

.insight-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  margin-bottom: 18px;
  background: var(--color-border);
}

.insight-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px;
  background: var(--card-background);
}

.insight-item span {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 700;
}

.insight-item strong {
  color: var(--color-heading);
  font-size: 18px;
  font-weight: 850;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);
  gap: 18px;
  align-items: start;
}

.password-dialog {
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

.password-dialog-content {
  width: min(100%, 420px);
  padding: 22px;
}

.password-dialog-content h3 {
  margin: 0 0 8px;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 800;
}

.password-dialog-content p {
  margin: 0 0 16px;
  color: var(--color-text-muted);
}

.password-input {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  outline: none;
}

.password-input:focus {
  border-color: var(--button-primary);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
}

.password-error {
  margin-top: 10px;
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 700;
}

.password-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

.dialog-button {
  min-height: 38px;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  background: var(--button-secondary);
  color: var(--button-secondary-text);
  cursor: pointer;
  font-weight: 750;
}

.dialog-button.primary {
  border-color: var(--button-primary);
  background: var(--button-primary);
  color: #ffffff;
}

@media (max-width: 1020px) {
  .page-hero,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard {
    padding: 18px 12px 30px;
  }

  .hero-copy {
    padding: 20px;
  }

  .hero-copy h1 {
    font-size: 30px;
  }

  .action-row,
  .insight-strip {
    grid-template-columns: 1fr;
  }

  .insight-item {
    padding: 13px 14px;
  }
}
</style>
