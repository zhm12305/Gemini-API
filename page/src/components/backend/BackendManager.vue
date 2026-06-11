<template>
  <section class="backend-manager panel-card">
    <div class="manager-header">
      <div>
        <span class="section-kicker">Instances</span>
        <h3>后端实例管理</h3>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">
        添加实例
      </button>
    </div>

    <div class="stats">
      <div class="stat-item">
        <span class="label">总实例数</span>
        <span class="value">{{ backendStore.backends.length }}</span>
      </div>
      <div class="stat-item">
        <span class="label">已连接</span>
        <span class="value connected">{{ backendStore.connectedBackendsCount }}</span>
      </div>
      <div class="stat-item">
        <span class="label">当前活跃</span>
        <span class="value active">{{ backendStore.activeBackend?.name || '无' }}</span>
      </div>
    </div>

    <div class="backend-list">
      <article
        v-for="backend in backendStore.backends"
        :key="backend.id"
        class="backend-item"
        :class="{ active: backend.isActive, connected: backend.isConnected, disconnected: !backend.isConnected }"
      >
        <div class="backend-info">
          <div class="name-row">
            <h4>{{ backend.name }}</h4>
            <div class="badges">
              <span v-if="backend.isActive" class="badge active">活跃</span>
              <span v-if="backend.isConnected" class="badge connected">已连接</span>
              <span v-else class="badge disconnected">未连接</span>
            </div>
          </div>

          <div class="details">
            <p class="url">{{ backend.baseUrl }}</p>
            <p v-if="backend.description" class="description">{{ backend.description }}</p>
            <p v-if="backend.lastConnected" class="last-connected">
              最后连接：{{ formatTime(backend.lastConnected) }}
            </p>
          </div>
        </div>

        <div class="backend-actions">
          <button
            @click="switchBackend(backend.id)"
            :disabled="backend.isActive"
            class="btn btn-sm"
            :class="backend.isActive ? 'btn-outline' : 'btn-primary'"
          >
            {{ backend.isActive ? '当前活跃' : '切换' }}
          </button>

          <button @click="testConnection(backend.id)" :disabled="testing[backend.id]" class="btn btn-sm btn-outline">
            {{ testing[backend.id] ? '测试中...' : '测试连接' }}
          </button>

          <button @click="editBackend(backend)" class="btn btn-sm btn-outline">
            编辑
          </button>

          <button v-if="backend.id !== 'local'" @click="confirmDelete(backend)" class="btn btn-sm btn-danger">
            删除
          </button>
        </div>
      </article>
    </div>

    <div class="actions">
      <button @click="testAllConnections" :disabled="testingAll" class="btn btn-outline">
        {{ testingAll ? '测试中...' : '测试所有连接' }}
      </button>
      <button @click="refreshAll" class="btn btn-outline">
        刷新状态
      </button>
    </div>

    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h4>{{ showAddModal ? '添加后端实例' : '编辑后端实例' }}</h4>
          <button @click="closeModal" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>实例名称</label>
            <input v-model="formData.name" type="text" placeholder="例如：生产服务器" class="form-control" />
          </div>

          <div class="form-group">
            <label>服务器地址</label>
            <input v-model="formData.baseUrl" type="url" placeholder="https://your-hajimi-instance.com" class="form-control" />
          </div>

          <div class="form-group">
            <label>访问密码（可选）</label>
            <input v-model="formData.password" type="password" placeholder="留空如果不需要密码" class="form-control" />
          </div>

          <div class="form-group">
            <label>描述（可选）</label>
            <textarea v-model="formData.description" placeholder="描述这个实例的用途" class="form-control" rows="3"></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeModal" class="btn">取消</button>
          <button @click="saveBackend" class="btn btn-primary">
            {{ showAddModal ? '添加' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h4>确认删除</h4>
          <button @click="showDeleteModal = false" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <p>确定要删除后端实例 "{{ deleteTarget?.name }}" 吗？</p>
          <p class="warning">此操作不可恢复。</p>
        </div>

        <div class="modal-footer">
          <button @click="showDeleteModal = false" class="btn">取消</button>
          <button @click="deleteBackend" class="btn btn-danger">删除</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useBackendStore } from '@/stores/backend'

const backendStore = useBackendStore()
const showAddModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const testing = reactive({})
const testingAll = ref(false)
const editingBackend = ref(null)
const deleteTarget = ref(null)

const formData = reactive({
  name: '',
  baseUrl: '',
  password: '',
  description: ''
})

function switchBackend(backendId) {
  if (backendStore.switchBackend(backendId)) {
    backendStore.saveToStorage()
  }
}

async function testConnection(backendId) {
  testing[backendId] = true
  try {
    await backendStore.testBackendConnection(backendId)
  } catch (error) {
    console.error('连接测试出错:', error)
  } finally {
    testing[backendId] = false
  }
}

async function testAllConnections() {
  testingAll.value = true
  try {
    await backendStore.testAllConnections()
  } catch (error) {
    console.error('批量测试连接出错:', error)
  } finally {
    testingAll.value = false
  }
}

function refreshAll() {
  testAllConnections()
}

function editBackend(backend) {
  editingBackend.value = backend
  formData.name = backend.name
  formData.baseUrl = backend.baseUrl
  formData.password = backend.password
  formData.description = backend.description
  showEditModal.value = true
}

function confirmDelete(backend) {
  deleteTarget.value = backend
  showDeleteModal.value = true
}

function deleteBackend() {
  if (deleteTarget.value) {
    backendStore.removeBackend(deleteTarget.value.id)
    backendStore.saveToStorage()
    showDeleteModal.value = false
    deleteTarget.value = null
  }
}

function saveBackend() {
  if (!formData.name.trim() || !formData.baseUrl.trim()) {
    alert('请填写实例名称和服务器地址')
    return
  }

  if (showAddModal.value) {
    backendStore.addBackend({
      name: formData.name.trim(),
      baseUrl: formData.baseUrl.trim(),
      password: formData.password.trim(),
      description: formData.description.trim()
    })
  } else if (showEditModal.value && editingBackend.value) {
    backendStore.updateBackend(editingBackend.value.id, {
      name: formData.name.trim(),
      baseUrl: formData.baseUrl.trim(),
      password: formData.password.trim(),
      description: formData.description.trim()
    })
  }

  backendStore.saveToStorage()
  closeModal()
}

function closeModal() {
  showAddModal.value = false
  showEditModal.value = false
  editingBackend.value = null
  formData.name = ''
  formData.baseUrl = ''
  formData.password = ''
  formData.description = ''
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
.backend-manager {
  padding: 20px;
}

.manager-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.manager-header h3 {
  margin: 6px 0 0;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 800;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-item {
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--stats-item-bg);
}

.label {
  display: block;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 750;
}

.value {
  display: block;
  margin-top: 5px;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 850;
  word-break: break-word;
}

.value.connected {
  color: var(--color-success);
}

.value.active {
  color: var(--button-primary);
}

.backend-list {
  display: grid;
  gap: 12px;
}

.backend-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-left-width: 4px;
  border-radius: var(--radius-lg);
  background: var(--card-background);
}

.backend-item.connected {
  border-left-color: var(--color-success);
}

.backend-item.disconnected {
  border-left-color: var(--color-danger);
}

.backend-item.active {
  border-color: rgba(15, 118, 110, 0.42);
  border-left-color: var(--button-primary);
  background: rgba(15, 118, 110, 0.06);
}

.name-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.name-row h4 {
  margin: 0;
  color: var(--color-heading);
  font-size: 17px;
  font-weight: 850;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.badge {
  padding: 3px 7px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 850;
}

.badge.active {
  background: rgba(15, 118, 110, 0.12);
  color: var(--button-primary);
}

.badge.connected {
  background: rgba(15, 159, 110, 0.12);
  color: var(--color-success);
}

.badge.disconnected {
  background: rgba(220, 38, 38, 0.12);
  color: var(--color-danger);
}

.details {
  display: grid;
  gap: 4px;
  margin-top: 10px;
}

.details p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.details .url {
  color: var(--button-primary);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  word-break: break-all;
}

.backend-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-sm {
  min-height: 32px;
  padding: 6px 10px;
  font-size: 12px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
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
  width: min(100%, 520px);
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

.form-group {
  margin-bottom: 16px;
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

.warning {
  color: var(--color-danger);
  font-weight: 750;
}

@media (max-width: 760px) {
  .manager-header,
  .name-row,
  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .stats {
    grid-template-columns: 1fr;
  }

  .backend-item {
    grid-template-columns: 1fr;
  }

  .backend-actions {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
