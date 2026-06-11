import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useBackendStore } from './backend'

const TOKEN_KEY = 'gemini_user_access_token'

export const useUserStore = defineStore('user', () => {
  const accessToken = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(null)
  const apiKeys = ref([])
  const auditLogs = ref([])
  const adminSummary = ref(null)
  const adminUsers = ref([])
  const adminApiKeys = ref([])
  const adminAuditLogs = ref([])
  const loading = ref(false)
  const error = ref('')
  const lastIssuedKey = ref(null)

  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value))

  function authHeaders() {
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken.value}`
    }
  }

  async function request(endpoint, options = {}) {
    const backendStore = useBackendStore()
    const response = await fetch(backendStore.buildApiUrl(endpoint), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(data.detail || data.message || `HTTP ${response.status}`)
    }
    return data
  }

  function setToken(token) {
    accessToken.value = token || ''
    if (accessToken.value) {
      localStorage.setItem(TOKEN_KEY, accessToken.value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function register(username, password) {
    loading.value = true
    error.value = ''
    try {
      const data = await request('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      })
      user.value = data.user
      setToken(data.access_token)
      await refreshAccountData()
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function login(username, password) {
    loading.value = true
    error.value = ''
    try {
      const data = await request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      })
      user.value = data.user
      setToken(data.access_token)
      await refreshAccountData()
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!accessToken.value) return null
    try {
      const data = await request('/api/user/me', {
        headers: authHeaders()
      })
      user.value = data.user
      return data.user
    } catch (err) {
      logout()
      throw err
    }
  }

  async function fetchApiKeys() {
    if (!accessToken.value) return []
    const data = await request('/api/user/api-keys', {
      headers: authHeaders()
    })
    apiKeys.value = data.api_keys || []
    return apiKeys.value
  }

  async function createApiKey(name, quotaDaily) {
    lastIssuedKey.value = null
    const payload = {
      name: name || 'default',
      quota_daily: Number(quotaDaily || 0) || null
    }
    const data = await request('/api/user/api-keys', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload)
    })
    lastIssuedKey.value = data
    await fetchApiKeys()
    await fetchAuditLogs()
    return data
  }

  async function revokeApiKey(keyId) {
    await request(`/api/user/api-keys/${keyId}`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    await fetchApiKeys()
    await fetchAuditLogs()
  }

  async function fetchAuditLogs() {
    if (!accessToken.value) return []
    const data = await request('/api/user/audit-logs?limit=30', {
      headers: authHeaders()
    })
    auditLogs.value = data.logs || []
    return auditLogs.value
  }

  async function refreshAccountData() {
    if (!accessToken.value) return
    await Promise.all([fetchApiKeys(), fetchAuditLogs()])
  }

  async function fetchAdminData() {
    if (!accessToken.value || !user.value?.is_admin) return
    const [summaryData, usersData, keysData, logsData] = await Promise.all([
      request('/api/admin/summary', { headers: authHeaders() }),
      request('/api/admin/users?limit=200', { headers: authHeaders() }),
      request('/api/admin/api-keys?limit=200', { headers: authHeaders() }),
      request('/api/admin/audit-logs?limit=80', { headers: authHeaders() })
    ])
    adminSummary.value = summaryData.summary
    adminUsers.value = usersData.users || []
    adminApiKeys.value = keysData.api_keys || []
    adminAuditLogs.value = logsData.logs || []
  }

  async function updateAdminUser(userId, payload) {
    const data = await request(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(payload)
    })
    await fetchAdminData()
    return data
  }

  async function updateAdminApiKey(keyId, payload) {
    const data = await request(`/api/admin/api-keys/${keyId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(payload)
    })
    await fetchAdminData()
    return data
  }

  function logout() {
    setToken('')
    user.value = null
    apiKeys.value = []
    auditLogs.value = []
    adminSummary.value = null
    adminUsers.value = []
    adminApiKeys.value = []
    adminAuditLogs.value = []
    lastIssuedKey.value = null
  }

  async function bootstrap() {
    if (!accessToken.value) return
    try {
      await fetchMe()
      await refreshAccountData()
      if (user.value?.is_admin) {
        await fetchAdminData()
      }
    } catch {
      logout()
    }
  }

  bootstrap()

  return {
    accessToken,
    user,
    apiKeys,
    auditLogs,
    adminSummary,
    adminUsers,
    adminApiKeys,
    adminAuditLogs,
    loading,
    error,
    lastIssuedKey,
    isAuthenticated,
    register,
    login,
    logout,
    fetchMe,
    fetchApiKeys,
    createApiKey,
    revokeApiKey,
    fetchAuditLogs,
    refreshAccountData,
    fetchAdminData,
    updateAdminUser,
    updateAdminApiKey
  }
})
