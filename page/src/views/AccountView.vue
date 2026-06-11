<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useBackendStore } from '../stores/backend'

const userStore = useUserStore()
const backendStore = useBackendStore()
const router = useRouter()

const mode = ref('login')
const username = ref('')
const password = ref('')
const formMessage = ref('')
const keyName = ref('生产调用')
const keyQuota = ref(1000)
const keyMessage = ref('')
const copied = ref('')
const busy = ref(false)

const totalRequests = computed(() =>
  userStore.apiKeys.reduce((sum, item) => sum + Number(item.total_requests || 0), 0)
)

const totalTokens = computed(() =>
  userStore.apiKeys.reduce((sum, item) => sum + Number(item.total_tokens || 0), 0)
)

const activeKeys = computed(() =>
  userStore.apiKeys.filter((item) => item.is_active).length
)

const endpoint = computed(() => `${backendStore.activeBackend?.baseUrl || window.location.origin}/v1/chat/completions`)

async function submitAuth() {
  formMessage.value = ''
  if (!username.value.trim() || !password.value) {
    formMessage.value = '请输入用户名和密码'
    return
  }
  busy.value = true
  try {
    let data
    if (mode.value === 'login') {
      data = await userStore.login(username.value.trim(), password.value)
      formMessage.value = '已进入账户控制台'
    } else {
      data = await userStore.register(username.value.trim(), password.value)
      formMessage.value = '账户已创建'
    }
    password.value = ''
    if (data?.user?.is_admin) {
      await userStore.fetchAdminData()
      router.push('/admin')
    } else {
      router.push('/account')
    }
  } catch (error) {
    formMessage.value = error.message || '操作失败'
  } finally {
    busy.value = false
  }
}

async function createKey() {
  keyMessage.value = ''
  busy.value = true
  try {
    await userStore.createApiKey(keyName.value, keyQuota.value)
    keyMessage.value = '新的 API Key 已生成，请立即复制保存'
  } catch (error) {
    keyMessage.value = error.message || '创建失败'
  } finally {
    busy.value = false
  }
}

async function revokeKey(keyId) {
  keyMessage.value = ''
  busy.value = true
  try {
    await userStore.revokeApiKey(keyId)
    keyMessage.value = 'API Key 已撤销'
  } catch (error) {
    keyMessage.value = error.message || '撤销失败'
  } finally {
    busy.value = false
  }
}

async function copyText(text, label) {
  await navigator.clipboard.writeText(text)
  copied.value = label
  setTimeout(() => {
    if (copied.value === label) copied.value = ''
  }, 1800)
}

function logout() {
  userStore.logout()
  formMessage.value = ''
  keyMessage.value = ''
}
</script>

<template>
  <main class="account-page">
    <section class="account-hero">
      <div class="hero-copy">
        <span class="section-kicker">Account Layer</span>
        <h1>账户、密钥与调用额度</h1>
        <p>每个用户独立领取调用密钥，后台继续统一轮询 Gemini Key 池，前端只暴露稳定的 OpenAI 兼容入口。</p>
      </div>
      <div class="endpoint-panel">
        <span>当前调用地址</span>
        <code>{{ endpoint }}</code>
        <button class="btn btn-outline" @click="copyText(endpoint, 'endpoint')">
          {{ copied === 'endpoint' ? '已复制' : '复制地址' }}
        </button>
      </div>
    </section>

    <section v-if="!userStore.isAuthenticated" class="auth-layout">
      <div class="auth-card">
        <div class="auth-tabs">
          <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>

        <form class="auth-form" @submit.prevent="submitAuth">
          <label>
            <span>用户名</span>
            <input v-model="username" autocomplete="username" placeholder="例如 zhm12305">
          </label>
          <label>
            <span>密码</span>
            <input v-model="password" type="password" autocomplete="current-password" placeholder="至少 8 位">
          </label>
          <button class="btn btn-primary" type="submit" :disabled="busy || userStore.loading">
            {{ mode === 'login' ? '进入控制台' : '创建账户' }}
          </button>
          <p v-if="formMessage" class="form-message">{{ formMessage }}</p>
        </form>
      </div>

      <div class="capability-panel">
        <div class="capability-item">
          <strong>独立 API Key</strong>
          <span>用户拿到自己的 `sk-user` 密钥，后端统一做鉴权、统计和撤销。</span>
        </div>
        <div class="capability-item">
          <strong>每日额度</strong>
          <span>每个 Key 单独设置调用上限，适合公开站点和小范围分发。</span>
        </div>
        <div class="capability-item">
          <strong>审计记录</strong>
          <span>注册、登录、发 Key、撤销和调用行为都能留下可追踪记录。</span>
        </div>
      </div>
    </section>

    <section v-else class="console-grid">
      <aside class="profile-panel">
        <div class="avatar">{{ userStore.user.username.slice(0, 1).toUpperCase() }}</div>
        <div>
          <span class="section-kicker">Signed In</span>
          <h2>{{ userStore.user.username }}</h2>
          <p>账户创建于 {{ userStore.user.created_at }}</p>
        </div>
        <button class="btn btn-outline" @click="logout">退出登录</button>
      </aside>

      <div class="account-main">
        <div class="metric-row">
          <div class="metric-card">
            <span>活跃密钥</span>
            <strong>{{ activeKeys }}</strong>
          </div>
          <div class="metric-card">
            <span>总请求</span>
            <strong>{{ totalRequests }}</strong>
          </div>
          <div class="metric-card">
            <span>总 Token</span>
            <strong>{{ totalTokens }}</strong>
          </div>
        </div>

        <section class="panel-card key-creator">
          <div class="panel-head">
            <div>
              <span class="section-kicker">Issue Key</span>
              <h3 class="section-title">创建调用密钥</h3>
            </div>
            <button class="btn btn-primary" @click="createKey" :disabled="busy">生成 API Key</button>
          </div>
          <div class="creator-form">
            <label>
              <span>密钥名称</span>
              <input v-model="keyName" placeholder="生产调用">
            </label>
            <label>
              <span>每日请求额度</span>
              <input v-model.number="keyQuota" type="number" min="1">
            </label>
          </div>
          <p v-if="keyMessage" class="form-message">{{ keyMessage }}</p>
          <div v-if="userStore.lastIssuedKey" class="issued-key">
            <span>仅显示一次</span>
            <code>{{ userStore.lastIssuedKey.api_key }}</code>
            <button class="btn btn-outline" @click="copyText(userStore.lastIssuedKey.api_key, 'new-key')">
              {{ copied === 'new-key' ? '已复制' : '复制密钥' }}
            </button>
          </div>
        </section>

        <section class="panel-card">
          <div class="panel-head">
            <div>
              <span class="section-kicker">API Keys</span>
              <h3 class="section-title">密钥列表</h3>
            </div>
            <button class="btn btn-outline" @click="userStore.refreshAccountData">刷新</button>
          </div>

          <div class="key-list" v-if="userStore.apiKeys.length">
            <article v-for="item in userStore.apiKeys" :key="item.id" class="key-item">
              <div class="key-main">
                <strong>{{ item.name }}</strong>
                <code>{{ item.key_prefix }}...</code>
              </div>
              <div class="key-stats">
                <span>{{ item.total_requests }} 次</span>
                <span>{{ item.total_tokens }} tokens</span>
                <span>每日 {{ item.quota_daily }}</span>
              </div>
              <button class="btn btn-danger" :disabled="!item.is_active || busy" @click="revokeKey(item.id)">
                {{ item.is_active ? '撤销' : '已撤销' }}
              </button>
            </article>
          </div>
          <p v-else class="empty-state">还没有创建调用密钥。</p>
        </section>

        <section class="panel-card">
          <div class="panel-head">
            <div>
              <span class="section-kicker">Audit</span>
              <h3 class="section-title">最近审计</h3>
            </div>
          </div>
          <div class="audit-list" v-if="userStore.auditLogs.length">
            <div v-for="log in userStore.auditLogs" :key="log.id" class="audit-item">
              <span>{{ log.action }}</span>
              <time>{{ log.created_at }}</time>
            </div>
          </div>
          <p v-else class="empty-state">暂无审计记录。</p>
        </section>
      </div>
    </section>
  </main>
</template>

<style scoped>
.account-page {
  width: min(100%, var(--content-width));
  margin: 0 auto;
  padding: 28px 22px 44px;
}

.account-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.6fr);
  gap: 18px;
  margin-bottom: 18px;
}

.hero-copy,
.endpoint-panel,
.auth-card,
.capability-panel,
.profile-panel {
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-md);
}

.hero-copy {
  padding: 26px;
}

.hero-copy h1 {
  margin: 8px 0 10px;
  color: var(--color-heading);
  font-size: 38px;
  line-height: 1.08;
  font-weight: 850;
}

.hero-copy p {
  max-width: 760px;
  margin: 0;
  color: var(--color-text-muted);
}

.endpoint-panel {
  display: grid;
  align-content: center;
  gap: 10px;
  padding: 20px;
}

.endpoint-panel span,
.creator-form span,
.auth-form span {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 750;
}

code {
  display: block;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--code-background);
  color: var(--color-heading);
  font-family: Consolas, "SFMono-Regular", monospace;
  font-size: 13px;
  word-break: break-all;
}

.auth-layout,
.console-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.45fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.auth-card,
.capability-panel,
.profile-panel,
.panel-card {
  padding: 20px;
}

.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-background-soft);
  margin-bottom: 18px;
}

.auth-tabs button {
  min-height: 38px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  font-weight: 800;
}

.auth-tabs button.active {
  background: var(--card-background);
  color: var(--button-primary);
  box-shadow: var(--shadow-sm);
}

.auth-form,
.creator-form {
  display: grid;
  gap: 12px;
}

.auth-form label,
.creator-form label {
  display: grid;
  gap: 7px;
}

input {
  width: 100%;
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--input-background);
  color: var(--color-text);
  outline: none;
}

input:focus {
  border-color: var(--button-primary);
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.14);
}

.form-message {
  margin: 12px 0 0;
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 750;
}

.capability-panel {
  display: grid;
  gap: 12px;
}

.capability-item {
  display: grid;
  gap: 4px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--stats-item-bg);
}

.capability-item strong {
  color: var(--color-heading);
}

.capability-item span {
  color: var(--color-text-muted);
  font-size: 13px;
}

.profile-panel {
  display: grid;
  gap: 14px;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  border: 1px solid rgba(20, 184, 166, 0.35);
  border-radius: var(--radius-lg);
  background: rgba(20, 184, 166, 0.12);
  color: var(--button-primary);
  font-size: 24px;
  font-weight: 850;
}

.profile-panel h2 {
  margin: 5px 0 4px;
  color: var(--color-heading);
}

.profile-panel p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
  word-break: break-word;
}

.account-main {
  display: grid;
  gap: 18px;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
}

.metric-card span {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 750;
}

.metric-card strong {
  color: var(--color-heading);
  font-size: 26px;
  line-height: 1;
  font-weight: 850;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.creator-form {
  grid-template-columns: minmax(0, 1fr) 180px;
}

.issued-key {
  display: grid;
  gap: 10px;
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(20, 184, 166, 0.28);
  border-radius: var(--radius-md);
  background: rgba(20, 184, 166, 0.08);
}

.issued-key span {
  color: var(--color-success);
  font-size: 12px;
  font-weight: 850;
}

.key-list {
  display: grid;
  gap: 10px;
}

.key-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--stats-item-bg);
}

.key-main {
  min-width: 0;
}

.key-main strong {
  display: block;
  margin-bottom: 6px;
  color: var(--color-heading);
}

.key-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 7px;
}

.key-stats span {
  padding: 5px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 750;
}

.audit-list {
  display: grid;
  gap: 8px;
}

.audit-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--stats-item-bg);
}

.audit-item span {
  color: var(--color-heading);
  font-weight: 750;
}

.audit-item time {
  color: var(--color-text-muted);
  font-size: 12px;
  text-align: right;
}

.empty-state {
  margin: 0;
  padding: 18px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-align: center;
}

@media (max-width: 980px) {
  .account-hero,
  .auth-layout,
  .console-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .account-page {
    padding: 18px 12px 32px;
  }

  .hero-copy h1 {
    font-size: 30px;
  }

  .metric-row,
  .creator-form,
  .key-item {
    grid-template-columns: 1fr;
  }

  .key-stats {
    justify-content: flex-start;
  }

  .panel-head {
    flex-direction: column;
  }
}
</style>
