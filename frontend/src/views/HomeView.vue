<template>
  <div class="home-shell">
    <div class="shell-glow shell-glow-a" />
    <div class="shell-glow shell-glow-b" />

    <el-container class="home-layout">
      <el-header class="main-header">
        <div class="brand-group">
          <div class="brand-mark">番</div>
          <div>
            <p class="brand-kicker">Novel Operations Console</p>
            <h1>小说管理系统</h1>
          </div>
        </div>

        <div class="header-actions page-subtle-shell">
          <span class="internal-mode-badge">内部 API 模式</span>
          <button
            class="theme-toggle"
            type="button"
            :aria-pressed="isDarkMode"
            @click="toggleTheme"
          >
            <span>{{ isDarkMode ? '切换浅色' : '切换深色' }}</span>
          </button>
        </div>
      </el-header>

      <el-container class="content-layout">
        <el-aside width="248px" class="main-aside">
          <div class="aside-panel">
            <div class="aside-summary page-subtle-shell">
              <p class="aside-title">导航</p>
              <p class="aside-text">搜索、缓存、下载、阅读，一站式处理你的番茄小说工作流。</p>
            </div>

            <el-menu :default-active="activeMenu" class="main-menu" router>
              <el-menu-item index="/">
                <el-icon><data-analysis /></el-icon>
                <span>数据大屏</span>
              </el-menu-item>
              <el-menu-item index="/novels">
                <el-icon><reading /></el-icon>
                <span>小说列表</span>
              </el-menu-item>
              <el-menu-item index="/search">
                <el-icon><search /></el-icon>
                <span>搜索小说</span>
              </el-menu-item>
              <el-menu-item index="/upload">
                <el-icon><upload /></el-icon>
                <span>添加小说</span>
              </el-menu-item>
              <el-menu-item index="/tasks">
                <el-icon><document /></el-icon>
                <span>任务管理</span>
              </el-menu-item>
              <el-menu-item index="/settings">
                <el-icon><setting /></el-icon>
                <span>设置</span>
              </el-menu-item>
            </el-menu>
          </div>
        </el-aside>

        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataAnalysis, Reading, Search, Upload, Document, Setting } from '@element-plus/icons-vue'
import { useTheme } from '../composables/useTheme'

const route = useRoute()
const activeMenu = computed(() => route.path)
const { isDarkMode, toggleTheme, initTheme } = useTheme()

initTheme()
</script>

<style scoped>
.home-shell {
  position: relative;
  min-height: 100vh;
  padding: 16px;
}

.shell-glow {
  position: fixed;
  z-index: 0;
  width: 320px;
  height: 320px;
  border-radius: 999px;
  filter: blur(68px);
  opacity: 0.24;
  pointer-events: none;
}

.shell-glow-a {
  top: -80px;
  right: 4%;
  background: rgba(255, 111, 207, 0.26);
}

.shell-glow-b {
  bottom: -100px;
  left: 4%;
  background: rgba(84, 227, 255, 0.24);
}

.home-layout {
  position: relative;
  z-index: 1;
  min-height: calc(100vh - 32px);
  border-radius: 22px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.06)),
    var(--shell-frame-bg);
  border: 1px solid rgba(255, 255, 255, 0.34);
  box-shadow: var(--shadow-soft), 0 0 0 1px rgba(84, 227, 255, 0.08);
}

html[data-theme='dark'] .home-layout {
  border-color: rgba(84, 227, 255, 0.14);
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px;
  min-height: 78px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(233, 238, 255, 0.72)),
    repeating-linear-gradient(90deg, transparent, transparent 24px, rgba(84, 227, 255, 0.05) 24px, rgba(84, 227, 255, 0.05) 25px);
  color: var(--text-primary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.76);
  box-shadow: 0 12px 28px rgba(67, 60, 135, 0.1);
  backdrop-filter: blur(10px) saturate(145%);
}

html[data-theme='dark'] .main-header {
  background:
    linear-gradient(180deg, rgba(22, 33, 68, 0.9), rgba(10, 18, 40, 0.82)),
    repeating-linear-gradient(90deg, transparent, transparent 24px, rgba(84, 227, 255, 0.05) 24px, rgba(84, 227, 255, 0.05) 25px);
  border-bottom-color: rgba(84, 227, 255, 0.14);
  box-shadow: 0 12px 28px rgba(1, 4, 18, 0.26);
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 15px;
  background: linear-gradient(145deg, rgba(84, 227, 255, 0.28), rgba(89, 108, 255, 0.22) 58%, rgba(255, 111, 207, 0.18));
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  border: 1px solid rgba(255, 255, 255, 0.38);
  box-shadow: var(--glow-accent), inset 0 1px 0 rgba(255, 255, 255, 0.42);
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.32);
}

.brand-kicker {
  margin: 0 0 4px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.brand-group h1 {
  margin: 0;
  font-size: clamp(22px, 2.5vw, 28px);
  font-weight: 800;
}

.header-actions {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.14));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24), 0 10px 22px rgba(67, 60, 135, 0.08);
}

.internal-mode-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.14), rgba(157, 123, 255, 0.1));
  border: 1px solid rgba(84, 227, 255, 0.22);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

html[data-theme='dark'] .internal-mode-badge {
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.12), rgba(157, 123, 255, 0.08));
  border-color: rgba(84, 227, 255, 0.16);
}

.theme-toggle {
  border-radius: 999px;
  padding: 10px 18px;
  cursor: pointer;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--neon-violet) 58%, var(--neon-pink));
  border: 1px solid rgba(84, 227, 255, 0.28);
  box-shadow: var(--glow-accent), inset 0 1px 0 rgba(255, 255, 255, 0.26);
}

.theme-toggle:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 26px rgba(84, 227, 255, 0.22), 0 14px 30px rgba(89, 108, 255, 0.22);
}

html[data-theme='dark'] .theme-toggle {
  border-color: rgba(84, 227, 255, 0.24);
}

.content-layout {
  min-height: calc(100vh - 78px - 32px);
}

.main-aside {
  padding: 20px 16px 20px 20px;
  background: transparent;
  border-right: 1px solid var(--border-color-light);
}

.aside-panel {
  height: 100%;
  padding: 18px;
  border-radius: 18px;
  background: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow: var(--shell-glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.36);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(160%);
}

.aside-summary {
  padding: 14px;
  margin-bottom: 14px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.08)),
    rgba(255, 255, 255, 0.08);
}

.aside-title {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.aside-text {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.main-menu {
  background: transparent;
  border-right: none;
}

:deep(.main-menu .el-menu-item) {
  height: 48px;
  margin-bottom: 8px;
  border-radius: 14px;
  border: 1px solid rgba(84, 227, 255, 0.08);
  color: var(--text-secondary);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

:deep(.main-menu .el-menu-item .el-icon) {
  font-size: 16px;
}

:deep(.main-menu .el-menu-item.is-active) {
  color: var(--accent-strong);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.2), rgba(157, 123, 255, 0.14) 58%, rgba(255, 111, 207, 0.12));
  border-color: rgba(84, 227, 255, 0.24);
  box-shadow: var(--glow-accent);
  font-weight: 700;
}

:deep(.main-menu .el-menu-item:hover) {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.08));
  border-color: rgba(84, 227, 255, 0.18);
  transform: translateX(2px);
}

.main-content {
  padding: 20px 24px 24px;
  overflow-y: auto;
}

@media (max-width: 980px) {
  .content-layout {
    flex-direction: column;
  }

  .main-aside {
    width: 100% !important;
    padding: 14px 20px 0;
    border-right: none;
    border-bottom: 1px solid var(--border-color-light);
  }

  .aside-panel {
    padding: 14px;
  }

  .aside-summary {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 10px;
    align-items: center;
    margin-bottom: 12px;
  }

  .aside-title {
    margin: 0;
  }

  .main-menu {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 4px;
    scrollbar-width: none;
  }

  .main-menu::-webkit-scrollbar {
    display: none;
  }

  :deep(.main-menu .el-menu-item) {
    flex: 0 0 auto;
    min-width: max-content;
    margin-bottom: 0;
    padding-inline: 16px;
    height: 44px;
  }

  :deep(.main-menu .el-menu-item:hover) {
    transform: translateY(-1px);
  }

  .main-content {
    padding: 18px 20px 22px;
  }
}

@media (max-width: 768px) {
  .home-shell {
    padding: 10px;
  }

  .home-layout {
    min-height: calc(100vh - 20px);
    border-radius: 18px;
  }

  .main-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    min-height: auto;
  }

  .brand-group {
    gap: 12px;
  }

  .brand-mark {
    width: 42px;
    height: 42px;
    border-radius: 13px;
    font-size: 18px;
  }

  .brand-kicker {
    margin-bottom: 2px;
    font-size: 11px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
    gap: 10px;
    padding: 6px 8px;
  }

  .internal-mode-badge,
  .theme-toggle {
    flex: 1 1 140px;
    justify-content: center;
    text-align: center;
  }

  .main-aside {
    padding: 12px 16px 0;
  }

  .aside-panel {
    padding: 12px;
  }

  .aside-summary {
    padding: 10px 12px;
  }

  .aside-text {
    font-size: 12px;
  }

  .main-content {
    padding: 16px;
  }
}

@media (max-width: 560px) {
  .aside-summary {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .aside-text {
    display: none;
  }

  :deep(.main-menu .el-menu-item) {
    padding-inline: 14px;
    border-radius: 12px;
  }
}
</style>
