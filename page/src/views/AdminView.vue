<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const message = ref('')
const busy = ref(false)

const summary = computed(() => userStore.adminSummary || {
  users: 0,
  active_users: 0,
  admins: 0,
  total_api_keys: 0,
  active_api_keys: 0,
  total_requests: 0,
  total_tokens: 0
})

onMounted(() => {
  if (userStore.user?.is_admin) {
    userStore.fetchAdminData()
  }
})

async function updateUser(user, payload) {
  message.value = ''
  busy.value = true
  try {
    await userStore.updateAdminUser(user.id, payload)
    message.value = '用户状态已更新'
  } catch (error) {
    message.value = error.message || '更新失败'
  } finally {
    busy.value = false
  }
}

async function updateApiKey(item, payload) {
  message.value = ''
  busy.value = true
  try {
    await userStore.updateAdminApiKey(item.id, payload)
    message.value = 'API Key 已更新'
  } catch (error) {
    message.value = error.message || '更新失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="admin-page">
    <section class="admin-hero">
      <div>
        <span class="section-kicker">Admin Console</span>
        <h1>用户、额度与密钥治理</h1>
        <p>管理员账户可以查看全部用户、调整账户状态、控制用户 API Key 额度，并追踪系统审计事件。</p>
      </div>
      <button v-if="userStore.user?.is_admin" class="btn btn-primary" @click="userStore.fetchAdminData" :disabled="busy">
        刷新管理数据
      </button>
    </section>

    <section v-if="!userStore.isAuthenticated" class="empty-panel">
      <h2>请先登录</h2>
      <p>管理员控制台需要账户登录后访问。</p>
      <RouterLink to="/account" class="btn btn-primary">前往登录</RouterLink>
    </section>

    <section v-else-if="!userStore.user?.is_admin" class="empty-panel">
      <h2>当前账户不是管理员</h2>
      <p>普通用户可以在用户中心创建和管理自己的调用密钥。</p>
      <RouterLink to="/account" class="btn btn-primary">返回用户中心</RouterLink>
    </section>

    <template v-else>
      <section class="metric-grid">
        <div class="metric-card">
          <span>用户总数</span>
          <strong>{{ summary.users }}</strong>
        </div>
        <div class="metric-card">
          <span>活跃用户</span>
          <strong>{{ summary.active_users }}</strong>
        </div>
        <div class="metric-card">
          <span>管理员</span>
          <strong>{{ summary.admins }}</strong>
        </div>
        <div class="metric-card">
          <span>活跃 Key</span>
          <strong>{{ summary.active_api_keys }}</strong>
        </div>
        <div class="metric-card">
          <span>总请求</span>
          <strong>{{ summary.total_requests }}</strong>
        </div>
        <div class="metric-card">
          <span>总 Token</span>
          <strong>{{ summary.total_tokens }}</strong>
        </div>
      </section>

      <p v-if="message" class="admin-message">{{ message }}</p>

      <section class="panel-card">
        <div class="panel-head">
          <div>
            <span class="section-kicker">Users</span>
            <h2 class="section-title">账户管理</h2>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>用户</th>
                <th>角色</th>
                <th>状态</th>
                <th>Key</th>
                <th>请求</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in userStore.adminUsers" :key="item.id">
                <td>
                  <strong>{{ item.username }}</strong>
                  <small>{{ item.created_at }}</small>
                </td>
                <td>{{ item.is_admin ? '管理员' : '普通用户' }}</td>
                <td>{{ item.is_active ? '启用' : '禁用' }}</td>
                <td>{{ item.api_key_count }}</td>
                <td>{{ item.total_requests }}</td>
                <td class="actions">
                  <button class="btn btn-outline" :disabled="busy || item.id === userStore.user.id" @click="updateUser(item, { is_active: !item.is_active })">
                    {{ item.is_active ? '禁用' : '启用' }}
                  </button>
                  <button class="btn btn-outline" :disabled="busy || item.id === userStore.user.id" @click="updateUser(item, { is_admin: !item.is_admin })">
                    {{ item.is_admin ? '降为用户' : '设为管理员' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-head">
          <div>
            <span class="section-kicker">User API Keys</span>
            <h2 class="section-title">密钥治理</h2>
          </div>
        </div>
        <div class="key-grid">
          <article v-for="item in userStore.adminApiKeys" :key="item.id" class="admin-key-card">
            <div>
              <strong>{{ item.name }}</strong>
              <code>{{ item.key_prefix }}...</code>
              <small>{{ item.username }}</small>
            </div>
            <div class="key-meta">
              <span>{{ item.total_requests }} 次</span>
              <span>{{ item.total_tokens }} tokens</span>
              <span>每日 {{ item.quota_daily }}</span>
            </div>
            <div class="quota-row">
              <input
                type="number"
                min="0"
                :value="item.quota_daily"
                @change="updateApiKey(item, { quota_daily: Number($event.target.value || 0) })"
              >
              <button class="btn btn-outline" :disabled="busy" @click="updateApiKey(item, { is_active: !item.is_active })">
                {{ item.is_active ? '停用' : '启用' }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-head">
          <div>
            <span class="section-kicker">Audit</span>
            <h2 class="section-title">系统审计</h2>
          </div>
        </div>
        <div class="audit-list">
          <div v-for="log in userStore.adminAuditLogs" :key="log.id" class="audit-item">
            <span>{{ log.action }}</span>
            <strong>{{ log.username || 'system' }}</strong>
            <time>{{ log.created_at }}</time>
          </div>
        </div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.admin-page {
  width: min(100%, var(--content-width));
  margin: 0 auto;
  padding: 28px 22px 44px;
}

.admin-hero,
.empty-panel,
.panel-card,
.metric-card {
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-md);
}

.admin-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding: 26px;
  margin-bottom: 18px;
}

.admin-hero h1,
.empty-panel h2 {
  margin: 7px 0 8px;
  color: var(--color-heading);
  font-size: 36px;
  line-height: 1.1;
}

.admin-hero p,
.empty-panel p {
  margin: 0;
  color: var(--color-text-muted);
}

.empty-panel {
  display: grid;
  gap: 12px;
  justify-items: start;
  padding: 26px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.metric-card {
  display: grid;
  gap: 6px;
  padding: 16px;
}

.metric-card span {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 800;
}

.metric-card strong {
  color: var(--color-heading);
  font-size: 25px;
  line-height: 1;
}

.admin-message {
  margin: 0 0 18px;
  padding: 11px 13px;
  border: 1px solid rgba(20, 184, 166, 0.24);
  border-radius: var(--radius-md);
  background: rgba(20, 184, 166, 0.08);
  color: var(--color-success);
  font-weight: 750;
}

.panel-card {
  padding: 20px;
  margin-bottom: 18px;
}

.panel-head {
  margin-bottom: 16px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 780px;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

th {
  color: var(--color-text-muted);
  font-size: 12px;
  text-transform: uppercase;
}

td {
  color: var(--color-text);
}

td strong,
.admin-key-card strong {
  display: block;
  color: var(--color-heading);
}

td small,
.admin-key-card small {
  display: block;
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.key-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.admin-key-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--stats-item-bg);
}

code {
  display: block;
  margin-top: 7px;
  padding: 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--code-background);
  color: var(--color-text);
  font-family: Consolas, "SFMono-Regular", monospace;
  font-size: 12px;
  word-break: break-all;
}

.key-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.key-meta span {
  padding: 5px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 750;
}

.quota-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

input {
  min-height: 38px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--input-background);
  color: var(--color-text);
}

.audit-list {
  display: grid;
  gap: 8px;
}

.audit-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px 220px;
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

.audit-item strong,
.audit-item time {
  color: var(--color-text-muted);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .metric-grid,
  .key-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .admin-page {
    padding: 18px 12px 32px;
  }

  .admin-hero {
    flex-direction: column;
  }

  .admin-hero h1 {
    font-size: 30px;
  }

  .metric-grid,
  .key-grid,
  .audit-item {
    grid-template-columns: 1fr;
  }
}
</style>
