<template>
  <nav class="navigation">
    <div class="nav-container">
      <router-link to="/" class="nav-brand" aria-label="返回仪表盘">
        <span class="brand-mark">G</span>
        <span class="brand-copy">
          <span class="brand-title">Gemini API</span>
          <span class="brand-subtitle">Proxy Console</span>
        </span>
      </router-link>

      <div class="nav-links">
        <router-link to="/" class="nav-link" :class="{ active: route.path === '/' }">
          仪表盘
        </router-link>

        <router-link to="/account" class="nav-link" :class="{ active: route.path === '/account' }">
          用户中心
          <span v-if="userStore.isAuthenticated" class="nav-badge live">已登录</span>
        </router-link>

        <router-link v-if="userStore.user?.is_admin" to="/admin" class="nav-link" :class="{ active: route.path === '/admin' }">
          管理员
        </router-link>

        <router-link to="/backends" class="nav-link" :class="{ active: route.path === '/backends' }">
          后端实例
          <span v-if="backendStore.connectedBackendsCount > 0" class="nav-badge">
            {{ backendStore.connectedBackendsCount }}
          </span>
        </router-link>
      </div>

      <div class="nav-actions">
        <BackendSwitcher class="nav-switcher" />
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useBackendStore } from '@/stores/backend'
import { useUserStore } from '@/stores/user'
import BackendSwitcher from './backend/BackendSwitcher.vue'

const route = useRoute()
const backendStore = useBackendStore()
const userStore = useUserStore()
</script>

<style scoped>
.navigation {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(10, 12, 12, 0.9);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(18px);
}

.dark-mode .navigation {
  background: rgba(10, 12, 12, 0.9);
}

.nav-container {
  width: min(100%, var(--content-width));
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto minmax(260px, 1fr);
  align-items: center;
  gap: 18px;
  padding: 14px 22px;
}

.nav-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  color: var(--color-heading);
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(20, 184, 166, 0.36);
  background: rgba(20, 184, 166, 0.12);
  color: #ffffff;
  font-weight: 800;
  box-shadow: 0 0 26px rgba(20, 184, 166, 0.16);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand-title {
  color: var(--color-heading);
  font-size: 15px;
  font-weight: 800;
}

.brand-subtitle {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 600;
}

.nav-links {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 13px;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 700;
}

.nav-link:hover {
  color: var(--color-heading);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: var(--button-primary);
  background: rgba(20, 184, 166, 0.1);
  box-shadow: var(--shadow-sm);
}

.nav-badge {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: rgba(15, 118, 110, 0.12);
  color: var(--button-primary);
  font-size: 12px;
  text-align: center;
}

.nav-badge.live {
  background: rgba(52, 211, 153, 0.12);
  color: var(--color-success);
}

.nav-actions {
  display: flex;
  justify-content: flex-end;
  min-width: 0;
}

.nav-switcher {
  max-width: 100%;
}

@media (max-width: 900px) {
  .nav-container {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .nav-links,
  .nav-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 560px) {
  .nav-container {
    padding: 10px 12px;
  }

  .brand-subtitle {
    display: none;
  }

  .nav-links {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr;
  }

  .nav-link {
    justify-content: center;
  }
}
</style>
