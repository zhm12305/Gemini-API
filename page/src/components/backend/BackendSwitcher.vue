<template>
  <div class="backend-switcher">
    <div class="current-backend">
      <span class="status-indicator" :class="{ connected: activeBackend?.isConnected }"></span>
      <select v-model="selectedBackendId" @change="switchToBackend" class="backend-select">
        <option v-for="backend in backendStore.backends" :key="backend.id" :value="backend.id">
          {{ backend.name }} {{ backend.isConnected ? 'online' : 'offline' }}
        </option>
      </select>
    </div>

    <div class="actions">
      <button
        @click="testCurrentConnection"
        :disabled="testing"
        class="switcher-button"
        :title="testing ? '测试中...' : '测试当前连接'"
      >
        {{ testing ? '测试中' : '测试' }}
      </button>

      <button @click="$emit('openManager')" class="switcher-button" title="管理后端实例">
        管理
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useBackendStore } from '@/stores/backend'

defineEmits(['openManager'])

const backendStore = useBackendStore()
const testing = ref(false)
const selectedBackendId = ref(backendStore.activeBackendId)
const activeBackend = computed(() => backendStore.activeBackend)

watch(() => backendStore.activeBackendId, (newId) => {
  selectedBackendId.value = newId
})

function switchToBackend() {
  if (selectedBackendId.value !== backendStore.activeBackendId) {
    backendStore.switchBackend(selectedBackendId.value)
    backendStore.saveToStorage()
  }
}

async function testCurrentConnection() {
  if (!activeBackend.value) return

  testing.value = true
  try {
    await backendStore.testBackendConnection(activeBackend.value.id)
  } catch (error) {
    console.error('测试连接失败:', error)
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.backend-switcher {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 5px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-sm);
}

.current-backend {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.status-indicator {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: var(--color-danger);
  box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.12);
}

.status-indicator.connected {
  background: var(--color-success);
  box-shadow: 0 0 0 4px rgba(15, 159, 110, 0.12);
}

.backend-select {
  width: 190px;
  min-width: 0;
  border: none;
  background: transparent;
  color: var(--color-heading);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  outline: none;
}

.actions {
  display: flex;
  gap: 4px;
}

.switcher-button {
  min-height: 30px;
  padding: 5px 9px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-background-soft);
  color: var(--color-text);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  transition: all var(--transition-fast);
}

.switcher-button:hover:not(:disabled) {
  border-color: var(--button-primary);
  color: var(--button-primary);
  background: rgba(15, 118, 110, 0.08);
}

.switcher-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 560px) {
  .backend-switcher {
    width: 100%;
  }

  .current-backend {
    flex: 1;
  }

  .backend-select {
    width: 100%;
  }
}
</style>
