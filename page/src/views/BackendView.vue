<template>
  <main class="backend-view">
    <section class="backend-hero">
      <div class="title-section">
        <span class="section-kicker">Backend Routing</span>
        <h1>后端实例管理</h1>
        <p class="subtitle">维护多个 Hajimi 后端地址，快速切换当前控制台连接目标。</p>
      </div>

      <BackendSwitcher @openManager="scrollToManager" />
    </section>

    <section class="overview-cards">
      <div class="card">
        <span class="card-label">实例总数</span>
        <strong>{{ backendStore.backends.length }}</strong>
      </div>

      <div class="card">
        <span class="card-label">已连接</span>
        <strong>{{ backendStore.connectedBackendsCount }}</strong>
      </div>

      <div class="card wide">
        <span class="card-label">当前活跃</span>
        <strong>{{ backendStore.activeBackend?.name || '无' }}</strong>
      </div>

      <div class="card wide">
        <span class="card-label">最后连接</span>
        <strong>{{ formatTime(backendStore.activeBackend?.lastConnected) || '从未' }}</strong>
      </div>
    </section>

    <section class="quick-actions panel-card">
      <div>
        <span class="section-kicker">Operations</span>
        <h2>快速操作</h2>
      </div>
      <div class="action-buttons">
        <button @click="testAllConnections" :disabled="testingAll" class="btn btn-primary">
          {{ testingAll ? '测试中...' : '测试所有连接' }}
        </button>
        <button @click="showAddModal = true" class="btn btn-primary">
          添加新实例
        </button>
        <button @click="exportConfig" class="btn btn-outline">
          导出配置
        </button>
        <button @click="importConfig" class="btn btn-outline">
          导入配置
        </button>
        <button @click="showUserGuide" class="btn btn-outline">
          使用指南
        </button>
      </div>
    </section>

    <div ref="managerRef">
      <BackendManager />
    </div>

    <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
      <div class="modal quick-add-modal" @click.stop>
        <div class="modal-header">
          <h4>快速添加后端实例</h4>
          <button @click="closeAddModal" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <div class="preset-buttons">
            <button v-for="preset in presets" :key="preset.id" @click="usePreset(preset)" class="preset-btn">
              <div class="preset-icon">{{ preset.icon }}</div>
              <div class="preset-info">
                <h5>{{ preset.name }}</h5>
                <p>{{ preset.description }}</p>
              </div>
            </button>
          </div>

          <div class="divider">或手动添加</div>

          <div class="form-group">
            <label>服务器地址</label>
            <input
              v-model="quickAddUrl"
              type="url"
              placeholder="https://your-hajimi-instance.com"
              class="form-control"
              @keyup.enter="quickAddInstance"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn">取消</button>
          <button @click="quickAddInstance" :disabled="!quickAddUrl.trim()" class="btn btn-primary">
            添加
          </button>
        </div>
      </div>
    </div>

    <input ref="fileInput" type="file" accept=".json" style="display: none" @change="handleFileImport" />
    <UserGuide ref="userGuideRef" />
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBackendStore } from '@/stores/backend'
import BackendManager from '@/components/backend/BackendManager.vue'
import BackendSwitcher from '@/components/backend/BackendSwitcher.vue'
import UserGuide from '@/components/backend/UserGuide.vue'

const backendStore = useBackendStore()
const testingAll = ref(false)
const showAddModal = ref(false)
const quickAddUrl = ref('')
const managerRef = ref(null)
const fileInput = ref(null)
const userGuideRef = ref(null)

const presets = [
  {
    id: 'localhost',
    name: '本地开发',
    icon: 'Local',
    description: '本地开发服务器 (localhost:7860)',
    baseUrl: 'http://localhost:7860'
  },
  {
    id: 'production',
    name: '生产服务器',
    icon: 'Prod',
    description: '生产环境服务器',
    baseUrl: 'https://'
  },
  {
    id: 'staging',
    name: '测试服务器',
    icon: 'Test',
    description: '测试环境服务器',
    baseUrl: 'https://'
  }
]

async function testAllConnections() {
  testingAll.value = true
  try {
    await backendStore.testAllConnections()
  } catch (error) {
    console.error('批量测试失败:', error)
  } finally {
    testingAll.value = false
  }
}

function usePreset(preset) {
  quickAddUrl.value = preset.baseUrl
}

function quickAddInstance() {
  if (!quickAddUrl.value.trim()) return

  try {
    const url = new URL(quickAddUrl.value)
    backendStore.addBackend({
      name: url.hostname,
      baseUrl: quickAddUrl.value.trim(),
      password: '',
      description: `通过快速添加创建: ${url.hostname}`
    })

    backendStore.saveToStorage()
    closeAddModal()
  } catch (error) {
    alert('请输入有效的 URL 地址')
  }
}

function closeAddModal() {
  showAddModal.value = false
  quickAddUrl.value = ''
}

function scrollToManager() {
  if (managerRef.value) {
    managerRef.value.scrollIntoView({ behavior: 'smooth' })
  }
}

function exportConfig() {
  const config = {
    backends: backendStore.backends,
    activeBackendId: backendStore.activeBackendId,
    exportTime: new Date().toISOString()
  }

  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `hajimi-backends-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function importConfig() {
  fileInput.value?.click()
}

function handleFileImport(event) {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const config = JSON.parse(e.target.result)

      if (config.backends && Array.isArray(config.backends)) {
        const localBackend = backendStore.backends.find(b => b.id === 'local')
        const importedBackends = config.backends.filter(b => b.id !== 'local')

        backendStore.backends.splice(0, backendStore.backends.length)
        if (localBackend) {
          backendStore.backends.push(localBackend)
        }
        backendStore.backends.push(...importedBackends)

        backendStore.saveToStorage()
        alert(`成功导入 ${importedBackends.length} 个后端实例`)
      } else {
        alert('无效的配置文件格式')
      }
    } catch (error) {
      alert('配置文件解析失败: ' + error.message)
    }
  }
  reader.readAsText(file)
  event.target.value = ''
}

function showUserGuide() {
  userGuideRef.value?.show()
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  testAllConnections()
})
</script>

<style scoped>
.backend-view {
  width: min(100%, var(--content-width));
  min-height: 100vh;
  margin: 0 auto;
  padding: 28px 22px 42px;
}

.backend-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 18px;
  padding: 24px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-sm);
}

.title-section h1 {
  margin: 6px 0 8px;
  color: var(--color-heading);
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.1;
  font-weight: 850;
}

.subtitle {
  margin: 0;
  color: var(--color-text-muted);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.card {
  display: grid;
  gap: 6px;
  min-height: 112px;
  padding: 18px;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-sm);
}

.card-label {
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 750;
}

.card strong {
  align-self: end;
  color: var(--color-heading);
  font-size: 24px;
  font-weight: 850;
  word-break: break-word;
}

.card.wide strong {
  font-size: 18px;
}

.quick-actions {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 20px;
  margin-bottom: 18px;
}

.quick-actions h2 {
  margin: 6px 0 0;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 800;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
}

.modal {
  width: min(100%, 600px);
  max-height: 90vh;
  overflow: auto;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-xl);
}

.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border);
}

.modal-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-border);
  border-bottom: none;
}

.modal-header h4 {
  margin: 0;
  color: var(--color-heading);
  font-size: 18px;
  font-weight: 800;
}

.close-btn {
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  background: var(--button-secondary);
  color: var(--button-secondary-text);
  cursor: pointer;
  font-size: 20px;
}

.modal-body {
  padding: 20px;
}

.preset-buttons {
  display: grid;
  gap: 10px;
}

.preset-btn {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  width: 100%;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--stats-item-bg);
  color: var(--color-text);
  cursor: pointer;
  text-align: left;
}

.preset-btn:hover {
  border-color: var(--button-primary);
}

.preset-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  border-radius: var(--radius-md);
  background: rgba(15, 118, 110, 0.1);
  color: var(--button-primary);
  font-size: 12px;
  font-weight: 850;
}

.preset-info h5 {
  margin: 0 0 4px;
  color: var(--color-heading);
  font-size: 15px;
  font-weight: 800;
}

.preset-info p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.divider {
  margin: 20px 0;
  color: var(--color-text-muted);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text);
  font-size: 13px;
  font-weight: 750;
}

.form-control {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  outline: none;
}

.form-control:focus {
  border-color: var(--button-primary);
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
}

@media (max-width: 900px) {
  .backend-hero,
  .quick-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .action-buttons {
    justify-content: flex-start;
  }
}

@media (max-width: 560px) {
  .backend-view {
    padding: 18px 12px 30px;
  }

  .overview-cards {
    grid-template-columns: 1fr;
  }

  .preset-btn {
    grid-template-columns: 1fr;
  }
}
</style>
