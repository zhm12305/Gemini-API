<template>
  <div class="user-guide" v-if="showGuide">
    <div class="guide-overlay" @click="closeGuide"></div>
    <div class="guide-content">
      <div class="guide-header">
        <h3>多后端实例使用指南</h3>
        <button @click="closeGuide" class="close-btn">×</button>
      </div>

      <div class="guide-body">
        <div class="guide-section">
          <h4>什么是多后端实例？</h4>
          <p>多后端实例功能允许同时管理和切换多个 Hajimi 服务器，比如：</p>
          <ul>
            <li>本地开发环境</li>
            <li>生产服务器</li>
            <li>测试环境</li>
            <li>不同地区的部署</li>
          </ul>
        </div>

        <div class="guide-section">
          <h4>快速开始</h4>
          <div class="guide-steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h5>添加后端实例</h5>
                <p>点击“添加实例”按钮，输入服务器地址和访问密码。</p>
              </div>
            </div>

            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h5>测试连接</h5>
                <p>添加后测试连接，确认服务器可正常访问。</p>
              </div>
            </div>

            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h5>切换实例</h5>
                <p>在顶部下拉菜单中选择要使用的后端实例。</p>
              </div>
            </div>
          </div>
        </div>

        <div class="guide-section">
          <h4>使用技巧</h4>
          <div class="tips">
            <div class="tip">
              <span class="tip-label">管理</span>
              <div class="tip-content">
                <strong>实例维护：</strong>在后端管理页面可以编辑、删除、测试连接。
              </div>
            </div>

            <div class="tip">
              <span class="tip-label">存储</span>
              <div class="tip-content">
                <strong>配置保存：</strong>配置会保存到浏览器本地存储，刷新页面不会丢失。
              </div>
            </div>

            <div class="tip">
              <span class="tip-label">状态</span>
              <div class="tip-content">
                <strong>实时状态：</strong>顶部显示当前连接的后端实例和连接状态。
              </div>
            </div>

            <div class="tip">
              <span class="tip-label">同步</span>
              <div class="tip-content">
                <strong>导入导出：</strong>支持配置导入导出，方便在不同设备间同步。
              </div>
            </div>
          </div>
        </div>

        <div class="guide-section">
          <h4>注意事项</h4>
          <div class="warnings">
            <div class="warning">访问密码将保存在本地浏览器中，请确保设备安全。</div>
            <div class="warning">跨域访问可能需要后端服务器配置 CORS 支持。</div>
            <div class="warning">建议定期测试连接，确保后端服务正常运行。</div>
          </div>
        </div>
      </div>

      <div class="guide-footer">
        <label class="dont-show-again">
          <input type="checkbox" v-model="dontShowAgain" />
          <span>不再显示此指南</span>
        </label>
        <button @click="closeGuide" class="btn btn-primary">
          开始使用
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close'])
const showGuide = ref(false)
const dontShowAgain = ref(false)

onMounted(() => {
  const hasShownGuide = localStorage.getItem('hajimi_guide_shown')
  if (!hasShownGuide) {
    showGuide.value = true
  }
})

function closeGuide() {
  if (dontShowAgain.value) {
    localStorage.setItem('hajimi_guide_shown', 'true')
  }
  showGuide.value = false
  emit('close')
}

function show() {
  showGuide.value = true
}

function reset() {
  localStorage.removeItem('hajimi_guide_shown')
  dontShowAgain.value = false
}

defineExpose({
  show,
  reset
})
</script>

<style scoped>
.user-guide {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.guide-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
}

.guide-content {
  position: relative;
  width: min(100%, 720px);
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  background: var(--card-background);
  box-shadow: var(--shadow-xl);
}

.guide-header,
.guide-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  border-bottom: 1px solid var(--color-border);
}

.guide-footer {
  border-top: 1px solid var(--color-border);
  border-bottom: none;
}

.guide-header h3 {
  margin: 0;
  color: var(--color-heading);
  font-size: 20px;
  font-weight: 850;
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

.guide-body {
  padding: 22px;
}

.guide-section {
  margin-bottom: 28px;
}

.guide-section:last-child {
  margin-bottom: 0;
}

.guide-section h4 {
  margin: 0 0 12px;
  color: var(--color-heading);
  font-size: 16px;
  font-weight: 850;
}

.guide-section p,
.guide-section li {
  color: var(--color-text-muted);
}

.guide-section p {
  margin: 0 0 12px;
}

.guide-section ul {
  margin: 0;
  padding-left: 20px;
}

.guide-steps,
.tips,
.warnings {
  display: grid;
  gap: 12px;
}

.step,
.tip,
.warning {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--stats-item-bg);
}

.step {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
}

.step-number,
.tip-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: rgba(15, 118, 110, 0.12);
  color: var(--button-primary);
  font-weight: 850;
}

.step-number {
  width: 32px;
  height: 32px;
}

.step-content h5 {
  margin: 0 0 4px;
  color: var(--color-heading);
  font-size: 14px;
  font-weight: 800;
}

.step-content p {
  margin: 0;
  font-size: 14px;
}

.tip {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 13px;
}

.tip-label {
  height: 32px;
  font-size: 12px;
}

.tip-content {
  color: var(--color-text-muted);
  font-size: 14px;
}

.tip-content strong {
  color: var(--color-heading);
}

.warning {
  padding: 12px 14px;
  color: var(--color-warning);
  background: rgba(217, 119, 6, 0.1);
  border-color: rgba(217, 119, 6, 0.24);
  font-size: 14px;
}

.dont-show-again {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
}

@media (max-width: 640px) {
  .user-guide {
    padding: 10px;
  }

  .guide-header,
  .guide-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .step,
  .tip {
    grid-template-columns: 1fr;
  }
}
</style>
