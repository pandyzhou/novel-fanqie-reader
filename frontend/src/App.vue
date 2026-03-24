<template>
  <router-view />
</template>

<script setup lang="ts">
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()

initTheme()
</script>

<style>
:root {
  color-scheme: light;
  --bg-base: #e2ebff;
  --bg-elevated: #f7fbff;
  --surface-solid: rgba(255, 255, 255, 0.84);
  --surface-muted: rgba(255, 255, 255, 0.68);
  --surface-glass: rgba(255, 255, 255, 0.62);
  --surface-chrome: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(232, 237, 255, 0.76));
  --text-primary: #141b38;
  --text-secondary: #4d587f;
  --text-tertiary: #737fa8;
  --border-color: rgba(100, 116, 255, 0.24);
  --border-color-light: rgba(109, 125, 255, 0.16);
  --accent: #596cff;
  --accent-strong: #2d46ff;
  --accent-soft: rgba(89, 108, 255, 0.14);
  --neon-cyan: #54e3ff;
  --neon-violet: #9d7bff;
  --neon-pink: #ff6fcf;
  --chrome-line: rgba(255, 255, 255, 0.88);
  --chrome-edge: rgba(120, 134, 255, 0.3);
  --hud-grid: rgba(116, 133, 255, 0.12);
  --hud-grid-strong: rgba(84, 227, 255, 0.14);
  --hero-panel-bg: linear-gradient(140deg, rgba(255, 255, 255, 0.9), rgba(232, 238, 255, 0.72) 48%, rgba(217, 247, 255, 0.54));
  --hero-panel-border: rgba(255, 255, 255, 0.82);
  --hero-panel-shadow: 0 28px 60px rgba(82, 68, 166, 0.18), 0 0 0 1px rgba(118, 131, 255, 0.08);
  --hero-overlay: linear-gradient(135deg, rgba(255, 255, 255, 0.56), rgba(255, 255, 255, 0.12) 38%, rgba(84, 227, 255, 0.14) 66%, transparent 82%);
  --hero-edge: linear-gradient(90deg, rgba(84, 227, 255, 0.16), rgba(157, 123, 255, 0.24), rgba(255, 111, 207, 0.2));
  --success-soft: rgba(5, 150, 105, 0.14);
  --warning-soft: rgba(217, 119, 6, 0.14);
  --danger-soft: rgba(220, 38, 38, 0.12);
  --shadow-soft: 0 22px 48px rgba(67, 60, 135, 0.12);
  --shadow-card: 0 14px 30px rgba(67, 60, 135, 0.08);
  --glow-accent: 0 0 0 1px rgba(84, 227, 255, 0.16), 0 0 26px rgba(84, 227, 255, 0.18), 0 10px 28px rgba(157, 123, 255, 0.16);
  --glow-success: 0 0 22px rgba(5, 150, 105, 0.2);
  --glow-warning: 0 0 22px rgba(217, 119, 6, 0.18);
  --glow-danger: 0 0 22px rgba(220, 38, 38, 0.18);
  --card-hover-shadow: 0 24px 52px rgba(77, 67, 153, 0.18), 0 0 0 1px rgba(84, 227, 255, 0.12);
  --chart-1: #54e3ff;
  --chart-2: #9d7bff;
  --chart-3: #ff6fcf;
  --chart-4: #596cff;
  --chart-5: #2dd4bf;
  --chart-6: #fbbf24;
  --chart-grid: rgba(116, 133, 255, 0.16);
  --chart-axis-pointer: rgba(84, 227, 255, 0.18);
  --chart-tooltip-shadow: 0 18px 36px rgba(67, 60, 135, 0.16);
  --chart-link: rgba(101, 119, 255, 0.28);
  --chart-node-border: rgba(255, 255, 255, 0.78);
  --shell-frame-bg: rgba(255, 255, 255, 0.26);
  --shell-glass-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(234, 238, 255, 0.58));
  --shell-glass-border: rgba(255, 255, 255, 0.78);
  --shell-glass-shadow: 0 28px 56px rgba(67, 60, 135, 0.14);
  --shell-glass-blur: 24px;
  --panel-glass-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(231, 237, 255, 0.72));
  --panel-glass-border: rgba(255, 255, 255, 0.82);
  --panel-glass-shadow: 0 18px 40px rgba(67, 60, 135, 0.1);
  --panel-glass-blur: 18px;
  --panel-subtle-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.76), rgba(234, 238, 255, 0.5));
  --panel-subtle-border: rgba(255, 255, 255, 0.64);
  --panel-subtle-shadow: 0 14px 30px rgba(67, 60, 135, 0.08);
  --panel-raised-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(235, 239, 255, 0.84));
  --panel-raised-border: rgba(255, 255, 255, 0.88);
  --panel-raised-shadow: 0 22px 46px rgba(67, 60, 135, 0.12);

  --el-color-primary: var(--accent);
  --el-color-success: #059669;
  --el-color-warning: #d97706;
  --el-color-danger: #dc2626;
  --el-color-info: #64748b;
  --el-bg-color: rgba(255, 255, 255, 0.9);
  --el-bg-color-page: transparent;
  --el-bg-color-overlay: rgba(255, 255, 255, 0.92);
  --el-fill-color-blank: rgba(255, 255, 255, 0.92);
  --el-fill-color-light: rgba(116, 133, 255, 0.08);
  --el-fill-color-lighter: rgba(116, 133, 255, 0.05);
  --el-fill-color-extra-light: rgba(116, 133, 255, 0.04);
  --el-fill-color-dark: rgba(20, 27, 56, 0.04);
  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-secondary);
  --el-text-color-secondary: var(--text-tertiary);
  --el-border-color: var(--border-color);
  --el-border-color-light: var(--border-color-light);
  --el-border-color-lighter: rgba(116, 133, 255, 0.1);
  --el-border-color-extra-light: rgba(116, 133, 255, 0.08);
  --el-mask-color: rgba(20, 27, 56, 0.36);
  --el-box-shadow-light: 0 14px 30px rgba(67, 60, 135, 0.1);
}

html[data-theme='dark'] {
  color-scheme: dark;
  --bg-base: #070b18;
  --bg-elevated: #0d1430;
  --surface-solid: rgba(16, 23, 48, 0.9);
  --surface-muted: rgba(18, 28, 58, 0.82);
  --surface-glass: rgba(11, 18, 40, 0.78);
  --surface-chrome: linear-gradient(180deg, rgba(25, 38, 78, 0.88), rgba(9, 17, 38, 0.7));
  --text-primary: #f4f6ff;
  --text-secondary: #c9d1ff;
  --text-tertiary: #98a5d8;
  --border-color: rgba(105, 125, 255, 0.24);
  --border-color-light: rgba(84, 227, 255, 0.14);
  --accent: #6b7cff;
  --accent-strong: #9ea8ff;
  --accent-soft: rgba(107, 124, 255, 0.16);
  --neon-cyan: #58e7ff;
  --neon-violet: #a987ff;
  --neon-pink: #ff78d4;
  --chrome-line: rgba(255, 255, 255, 0.12);
  --chrome-edge: rgba(84, 227, 255, 0.22);
  --hud-grid: rgba(84, 227, 255, 0.09);
  --hud-grid-strong: rgba(169, 135, 255, 0.12);
  --hero-panel-bg: linear-gradient(145deg, rgba(27, 40, 84, 0.82), rgba(14, 23, 52, 0.82) 46%, rgba(9, 27, 56, 0.76));
  --hero-panel-border: rgba(116, 133, 255, 0.26);
  --hero-panel-shadow: 0 28px 60px rgba(1, 4, 18, 0.46), 0 0 0 1px rgba(84, 227, 255, 0.08);
  --hero-overlay: linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(84, 227, 255, 0.06) 34%, rgba(169, 135, 255, 0.08) 60%, transparent 82%);
  --hero-edge: linear-gradient(90deg, rgba(84, 227, 255, 0.16), rgba(169, 135, 255, 0.24), rgba(255, 120, 212, 0.2));
  --success-soft: rgba(16, 185, 129, 0.16);
  --warning-soft: rgba(245, 158, 11, 0.16);
  --danger-soft: rgba(248, 113, 113, 0.14);
  --shadow-soft: 0 24px 52px rgba(1, 4, 18, 0.42);
  --shadow-card: 0 14px 32px rgba(1, 4, 18, 0.32);
  --glow-accent: 0 0 0 1px rgba(84, 227, 255, 0.14), 0 0 28px rgba(84, 227, 255, 0.24), 0 12px 28px rgba(169, 135, 255, 0.24);
  --glow-success: 0 0 22px rgba(52, 211, 153, 0.26);
  --glow-warning: 0 0 22px rgba(245, 158, 11, 0.24);
  --glow-danger: 0 0 22px rgba(248, 113, 113, 0.22);
  --card-hover-shadow: 0 24px 52px rgba(1, 4, 18, 0.5), 0 0 0 1px rgba(84, 227, 255, 0.14);
  --chart-1: #58e7ff;
  --chart-2: #a987ff;
  --chart-3: #ff78d4;
  --chart-4: #6b7cff;
  --chart-5: #2dd4bf;
  --chart-6: #fbbf24;
  --chart-grid: rgba(84, 227, 255, 0.12);
  --chart-axis-pointer: rgba(84, 227, 255, 0.2);
  --chart-tooltip-shadow: 0 18px 34px rgba(1, 4, 18, 0.42);
  --chart-link: rgba(84, 227, 255, 0.2);
  --chart-node-border: rgba(11, 18, 40, 0.72);
  --shell-frame-bg: rgba(8, 12, 28, 0.3);
  --shell-glass-bg: linear-gradient(180deg, rgba(23, 35, 71, 0.78), rgba(10, 18, 40, 0.62));
  --shell-glass-border: rgba(103, 121, 255, 0.26);
  --shell-glass-shadow: 0 28px 56px rgba(1, 4, 18, 0.38);
  --shell-glass-blur: 20px;
  --panel-glass-bg: linear-gradient(180deg, rgba(24, 38, 76, 0.76), rgba(12, 20, 42, 0.68));
  --panel-glass-border: rgba(102, 120, 255, 0.22);
  --panel-glass-shadow: 0 18px 36px rgba(1, 4, 18, 0.28);
  --panel-glass-blur: 16px;
  --panel-subtle-bg: linear-gradient(180deg, rgba(24, 38, 76, 0.66), rgba(13, 21, 43, 0.54));
  --panel-subtle-border: rgba(84, 227, 255, 0.14);
  --panel-subtle-shadow: 0 14px 30px rgba(1, 4, 18, 0.24);
  --panel-raised-bg: linear-gradient(180deg, rgba(28, 42, 84, 0.82), rgba(14, 23, 50, 0.72));
  --panel-raised-border: rgba(102, 120, 255, 0.24);
  --panel-raised-shadow: 0 22px 42px rgba(1, 4, 18, 0.34);

  --el-bg-color: rgba(14, 21, 44, 0.9);
  --el-bg-color-page: transparent;
  --el-bg-color-overlay: rgba(10, 17, 38, 0.96);
  --el-fill-color-blank: rgba(14, 21, 44, 0.9);
  --el-fill-color-light: rgba(107, 124, 255, 0.12);
  --el-fill-color-lighter: rgba(107, 124, 255, 0.08);
  --el-fill-color-extra-light: rgba(107, 124, 255, 0.05);
  --el-fill-color-dark: rgba(255, 255, 255, 0.06);
  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-secondary);
  --el-text-color-secondary: var(--text-tertiary);
  --el-border-color: var(--border-color);
  --el-border-color-light: var(--border-color-light);
  --el-border-color-lighter: rgba(107, 124, 255, 0.1);
  --el-border-color-extra-light: rgba(107, 124, 255, 0.08);
  --el-mask-color: rgba(1, 4, 18, 0.58);
  --el-box-shadow-light: 0 16px 30px rgba(1, 4, 18, 0.32);
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

html,
body {
  margin: 0;
  font-family:
    'Inter', 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  background:
    radial-gradient(circle at 12% 18%, rgba(84, 227, 255, 0.2), transparent 22%),
    radial-gradient(circle at 84% 12%, rgba(255, 111, 207, 0.18), transparent 18%),
    radial-gradient(circle at 78% 72%, rgba(89, 108, 255, 0.16), transparent 22%),
    linear-gradient(180deg, var(--bg-elevated) 0, var(--bg-base) 240px);
  transition:
    background 0.25s ease,
    color 0.25s ease;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(var(--hud-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--hud-grid) 1px, transparent 1px),
    linear-gradient(180deg, transparent, rgba(84, 227, 255, 0.05) 44%, transparent 100%);
  background-size: 44px 44px, 44px 44px, 100% 240px;
  mask-image: radial-gradient(circle at 52% 14%, rgba(0, 0, 0, 0.48), transparent 84%);
  opacity: 0.18;
}

body::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 84% 10%, rgba(255, 255, 255, 0.16), transparent 14%),
    radial-gradient(circle at 22% 78%, rgba(84, 227, 255, 0.12), transparent 18%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), transparent 32%);
  mix-blend-mode: screen;
  opacity: 0.28;
}

html[data-theme='dark'] body::before {
  opacity: 0.12;
}

html[data-theme='dark'] body::after {
  background:
    radial-gradient(circle at 82% 12%, rgba(255, 120, 212, 0.16), transparent 16%),
    radial-gradient(circle at 18% 72%, rgba(84, 227, 255, 0.14), transparent 20%),
    linear-gradient(180deg, rgba(84, 227, 255, 0.05), transparent 34%);
  opacity: 0.22;
}

.page-title {
  margin: 0;
  font-size: clamp(28px, 3vw, 38px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

button,
input,
textarea,
select {
  font: inherit;
}

.el-card,
.el-table,
.el-dialog,
.el-drawer,
.el-descriptions,
.el-tabs__content,
.el-empty,
.el-result,
.el-page-header,
.el-pagination,
.el-form-item,
.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner {
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.el-card {
  border-radius: 18px;
  border: 1px solid var(--panel-glass-border);
  background: var(--panel-glass-bg);
  box-shadow:
    var(--panel-glass-shadow),
    inset 0 1px 0 var(--chrome-line),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(var(--panel-glass-blur)) saturate(165%);
}

.el-card.is-always-shadow,
.el-card.is-hover-shadow:hover {
  box-shadow:
    var(--panel-glass-shadow),
    inset 0 1px 0 var(--chrome-line),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.el-card__header {
  border-bottom: 1px solid var(--border-color-light);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.04)),
    var(--hero-edge);
  background-size: 100% 100%, 100% 1px;
  background-repeat: no-repeat;
  background-position: 0 0, 0 100%;
}

html[data-theme='dark'] .el-card__header {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.01)),
    var(--hero-edge);
  background-size: 100% 100%, 100% 1px;
  background-repeat: no-repeat;
  background-position: 0 0, 0 100%;
}

.page-panel-card {
  border: 1px solid var(--panel-raised-border);
  background: var(--panel-raised-bg);
  box-shadow:
    var(--panel-raised-shadow),
    inset 0 1px 0 var(--chrome-line),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.page-subtle-shell {
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow:
    var(--panel-subtle-shadow),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(calc(var(--panel-glass-blur) * 0.72)) saturate(155%);
}

.page-table-shell {
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.16)),
    repeating-linear-gradient(90deg, transparent, transparent 22px, rgba(84, 227, 255, 0.04) 22px, rgba(84, 227, 255, 0.04) 23px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

html[data-theme='dark'] .page-table-shell {
  background:
    linear-gradient(180deg, rgba(24, 38, 76, 0.42), rgba(13, 21, 43, 0.22)),
    repeating-linear-gradient(90deg, transparent, transparent 22px, rgba(84, 227, 255, 0.04) 22px, rgba(84, 227, 255, 0.04) 23px);
}

.home-layout,
.main-header,
.aside-panel,
.dashboard-hero,
.search-hero,
.settings-hero,
.upload-hero,
.novels-hero,
.tasks-hero,
.detail-hero,
.chapter-hero,
.auth-card {
  position: relative;
  overflow: hidden;
}

html .aside-panel,
html .dashboard-hero,
html .search-hero,
html .settings-hero,
html .upload-hero,
html .novels-hero,
html .tasks-hero,
html .detail-hero,
html .chapter-hero,
html .auth-card {
  border: 1px solid var(--hero-panel-border);
  background: var(--hero-panel-bg);
  box-shadow:
    var(--hero-panel-shadow),
    inset 0 1px 0 var(--chrome-line),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(170%);
}

html .aside-panel::before,
html .dashboard-hero::before,
html .search-hero::before,
html .settings-hero::before,
html .upload-hero::before,
html .novels-hero::before,
html .tasks-hero::before,
html .detail-hero::before,
html .chapter-hero::before,
html .auth-card::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: var(--hero-overlay);
}

html .aside-panel::after,
html .dashboard-hero::after,
html .search-hero::after,
html .settings-hero::after,
html .upload-hero::after,
html .novels-hero::after,
html .tasks-hero::after,
html .detail-hero::after,
html .chapter-hero::after,
html .auth-card::after {
  content: '';
  position: absolute;
  left: 18px;
  right: 18px;
  top: 0;
  height: 2px;
  border-radius: 999px;
  background: var(--hero-edge);
  opacity: 0.92;
  pointer-events: none;
}

html .aside-panel > *,
html .dashboard-hero > *,
html .search-hero > *,
html .settings-hero > *,
html .upload-hero > *,
html .novels-hero > *,
html .tasks-hero > *,
html .detail-hero > *,
html .chapter-hero > *,
html .auth-card > * {
  position: relative;
  z-index: 1;
}

html .dashboard-hero .hero-badge,
html .search-hero .hero-badge,
html .settings-hero .hero-badge,
html .upload-hero .hero-badge,
html .novels-hero .hero-badge,
html .tasks-hero .hero-badge,
html .detail-hero .hero-badge,
html .chapter-hero .hero-badge,
html .auth-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(84, 227, 255, 0.22);
  background:
    linear-gradient(135deg, rgba(84, 227, 255, 0.14), rgba(157, 123, 255, 0.12) 50%, rgba(255, 111, 207, 0.12)),
    rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32), 0 0 18px rgba(84, 227, 255, 0.12);
  color: var(--accent-strong);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

html .dashboard-hero .page-title,
html .search-hero .page-title,
html .settings-hero .page-title,
html .upload-hero .page-title,
html .novels-hero .page-title,
html .tasks-hero .page-title,
html .detail-hero .page-title,
html .chapter-hero .page-title,
html .auth-card h2 {
  text-shadow: 0 0 24px rgba(84, 227, 255, 0.12);
}

html .dashboard-hero .hero-subtitle,
html .search-hero .hero-subtitle,
html .settings-hero .hero-subtitle,
html .upload-hero .hero-subtitle,
html .novels-hero .hero-subtitle,
html .tasks-hero .hero-subtitle,
html .detail-hero .hero-subtitle,
html .chapter-hero .hero-subtitle,
html .auth-subtitle {
  color: var(--text-secondary);
  text-wrap: balance;
}

.home-layout::before,
.main-header::before {
  content: none;
}

.el-dialog,
.el-drawer {
  border: 1px solid var(--panel-raised-border);
  background: var(--panel-raised-bg);
  box-shadow:
    var(--panel-raised-shadow),
    inset 0 1px 0 var(--chrome-line),
    0 0 0 1px rgba(84, 227, 255, 0.06);
  backdrop-filter: blur(var(--panel-glass-blur)) saturate(165%);
}

.el-drawer__header {
  margin-bottom: 0;
  padding: 18px 20px 16px;
  border-bottom: 1px solid var(--border-color-light);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04)),
    var(--hero-edge);
  background-size: 100% 100%, 100% 1px;
  background-repeat: no-repeat;
  background-position: 0 0, 0 100%;
}

html[data-theme='dark'] .el-drawer__header {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.01)),
    var(--hero-edge);
  background-size: 100% 100%, 100% 1px;
  background-repeat: no-repeat;
  background-position: 0 0, 0 100%;
}

.el-drawer__title {
  color: var(--text-primary);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.el-drawer__headerbtn {
  color: var(--text-tertiary);
}

.el-drawer__headerbtn:hover {
  color: var(--text-primary);
}

.el-drawer__body {
  padding: 20px;
  background: transparent;
}

.el-overlay.is-message-box {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  backdrop-filter: blur(6px);
}

.el-message-box {
  width: min(460px, calc(100vw - 32px));
  margin: 0 !important;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--surface-solid);
  box-shadow: 0 24px 52px rgba(15, 23, 42, 0.16);
  overflow: hidden;
}

.el-message-box__header {
  position: relative;
  padding: 18px 48px 14px 20px;
  border-bottom: 1px solid var(--border-color-light);
  background: var(--surface-muted);
}

.el-message-box__title {
  color: var(--text-primary);
  font-weight: 700;
  font-size: 16px;
}

.el-message-box__headerbtn {
  position: absolute !important;
  top: 14px !important;
  right: 14px !important;
  left: auto !important;
  transform: none !important;
  color: var(--text-tertiary);
}

.el-message-box__headerbtn:hover {
  color: var(--text-primary);
}

.el-message-box__content {
  padding: 18px 20px 6px;
}

.el-message-box__container {
  align-items: flex-start;
  gap: 14px;
}

.el-message-box__status {
  margin-top: 2px;
  font-size: 20px;
  padding: 10px;
  border-radius: 999px;
  background: var(--warning-soft);
  color: var(--el-color-warning);
}

.el-message-box__message {
  color: var(--text-secondary);
  font-size: 14px;
}

.el-message-box__message p {
  margin: 0;
  line-height: 1.75;
}

.el-message-box__btns {
  padding: 16px 20px 20px;
  border-top: 1px solid var(--border-color-light);
  background: rgba(255, 255, 255, 0.32);
}

html[data-theme='dark'] .el-message-box__btns {
  background: rgba(15, 23, 42, 0.28);
}

.el-message-box__btns .el-button {
  min-width: 92px;
  border-radius: 12px;
}

.el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger) {
  background: var(--surface-solid);
  border: 1px solid var(--border-color-light);
  color: var(--text-secondary);
}

.el-message-box__btns .el-button--primary {
  border-color: rgba(84, 227, 255, 0.28);
  background: linear-gradient(135deg, var(--accent), var(--neon-violet) 60%, var(--neon-pink));
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.16), 0 8px 18px rgba(89, 108, 255, 0.18);
}

.el-message-box__btns .el-button--danger {
  border-color: transparent;
  background: linear-gradient(135deg, #ef4444, #fb7185);
  color: #fff;
  box-shadow: 0 0 18px rgba(239, 68, 68, 0.18), 0 8px 18px rgba(239, 68, 68, 0.22);
}

.el-empty,
.el-result,
.el-descriptions,
.el-page-header,
.el-tabs__nav-wrap::after,
.el-divider {
  border-color: var(--border-color-light);
}

.el-tabs__header,
.el-tabs__nav-wrap,
.el-tabs__nav-scroll,
.el-tabs__nav,
.el-tabs__item,
.el-tab-pane,
.el-radio-button__inner {
  background: transparent;
}

.el-tabs__item {
  color: var(--text-tertiary);
  border-radius: 14px 14px 0 0;
  padding-inline: 16px;
  font-weight: 700;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.el-tabs__item:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.el-tabs__item.is-active {
  color: var(--accent-strong);
  background: linear-gradient(180deg, rgba(84, 227, 255, 0.14), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24), 0 0 18px rgba(84, 227, 255, 0.08);
}

.el-tabs__active-bar {
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet), var(--neon-pink));
}

.el-tabs__content,
.el-tab-pane {
  background: transparent;
}

.el-radio-button__inner {
  color: var(--text-secondary);
  border-color: var(--border-color-light);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.46), rgba(255, 255, 255, 0.22));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

html[data-theme='dark'] .el-radio-button__inner {
  background: linear-gradient(180deg, rgba(24, 38, 76, 0.54), rgba(12, 20, 42, 0.38));
}

.el-radio-button__original-radio:checked + .el-radio-button__inner {
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--neon-violet));
  border-color: rgba(84, 227, 255, 0.4);
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.18);
}

.el-table,
.el-table__expanded-cell,
.el-table th.el-table__cell,
.el-table tr,
.el-table__inner-wrapper::before {
  background: transparent;
}

.el-table__header-wrapper {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0.08)),
    repeating-linear-gradient(90deg, transparent, transparent 32px, rgba(84, 227, 255, 0.05) 32px, rgba(84, 227, 255, 0.05) 33px);
}

html[data-theme='dark'] .el-table__header-wrapper {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.01)),
    repeating-linear-gradient(90deg, transparent, transparent 32px, rgba(84, 227, 255, 0.04) 32px, rgba(84, 227, 255, 0.04) 33px);
}

.el-table th.el-table__cell {
  color: var(--text-tertiary);
  font-weight: 800;
  letter-spacing: 0.04em;
}

.el-table td.el-table__cell,
.el-table th.el-table__cell {
  border-color: var(--border-color-light);
}

.el-table .cell {
  color: var(--text-primary);
}

.el-table tr:hover > td.el-table__cell {
  background: var(--accent-soft) !important;
}

.el-statistic,
.el-statistic__content,
.el-statistic__head,
.el-page-header__title,
.el-page-header__content,
.el-empty__description,
.el-result__subtitle,
.el-descriptions__label,
.el-descriptions__content {
  color: var(--text-primary);
}

.el-empty__description,
.el-result__subtitle,
.el-descriptions__label {
  color: var(--text-secondary);
}

.el-input__wrapper,
.el-select__wrapper,
.el-textarea__inner {
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0.42));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.74),
    inset 0 0 0 1px rgba(255, 255, 255, 0.24),
    0 14px 28px rgba(67, 60, 135, 0.06);
}

html[data-theme='dark'] .el-input__wrapper,
html[data-theme='dark'] .el-select__wrapper,
html[data-theme='dark'] .el-textarea__inner {
  background: linear-gradient(180deg, rgba(21, 33, 68, 0.62), rgba(11, 19, 41, 0.46));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 0 0 1px rgba(84, 227, 255, 0.1),
    0 14px 28px rgba(1, 4, 18, 0.2);
}

.el-input__wrapper.is-focus,
.el-select__wrapper.is-focused,
.el-textarea__inner:focus {
  box-shadow:
    inset 0 0 0 1px rgba(84, 227, 255, 0.72),
    0 0 0 4px rgba(84, 227, 255, 0.12),
    0 0 26px rgba(157, 123, 255, 0.12);
}

.el-button {
  border-radius: 14px;
  border-color: var(--border-color-light);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0.24));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44), 0 10px 24px rgba(67, 60, 135, 0.08);
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

html[data-theme='dark'] .el-button {
  background: linear-gradient(180deg, rgba(23, 35, 71, 0.74), rgba(10, 18, 40, 0.54));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 10px 24px rgba(1, 4, 18, 0.24);
}

.el-button--primary {
  border-color: rgba(84, 227, 255, 0.38);
  background: linear-gradient(135deg, var(--accent), var(--neon-violet) 62%, var(--neon-pink));
  color: #fff;
  box-shadow: 0 0 22px rgba(84, 227, 255, 0.18), 0 12px 26px rgba(89, 108, 255, 0.24);
}

.el-button--primary.is-plain {
  background: linear-gradient(180deg, rgba(84, 227, 255, 0.14), rgba(157, 123, 255, 0.08));
  color: var(--accent-strong);
}

.el-button--success {
  box-shadow: var(--glow-success), 0 10px 22px rgba(5, 150, 105, 0.16);
}

.el-button--warning {
  box-shadow: var(--glow-warning), 0 10px 22px rgba(217, 119, 6, 0.16);
}

.el-button--danger {
  box-shadow: var(--glow-danger), 0 10px 22px rgba(220, 38, 38, 0.18);
}

.el-button:not(.is-disabled):hover {
  transform: translateY(-1px);
}

.el-button.is-loading {
  box-shadow: 0 0 18px rgba(84, 227, 255, 0.14), 0 10px 24px rgba(67, 60, 135, 0.12);
}

.el-button.is-loading::before {
  border-radius: inherit;
  background: rgba(8, 12, 28, 0.18);
}

.el-message {
  border-radius: 14px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-raised-bg);
  box-shadow: var(--panel-raised-shadow);
  backdrop-filter: blur(var(--panel-glass-blur)) saturate(155%);
}

.el-message__content {
  color: var(--text-primary);
  font-weight: 600;
}

.el-message .el-icon {
  color: var(--accent-strong);
}

.el-tag {
  border-radius: 999px;
  border-color: rgba(84, 227, 255, 0.16);
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.12), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.el-alert {
  border-radius: 14px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.el-alert__title,
.el-alert__description {
  color: var(--text-primary);
}

.el-loading-mask {
  border-radius: inherit;
  background:
    linear-gradient(180deg, rgba(8, 12, 28, 0.26), rgba(8, 12, 28, 0.18)),
    repeating-linear-gradient(90deg, transparent, transparent 26px, rgba(84, 227, 255, 0.05) 26px, rgba(84, 227, 255, 0.05) 27px);
  backdrop-filter: blur(8px) saturate(130%);
}

.el-loading-spinner .circular {
  filter: drop-shadow(0 0 14px rgba(84, 227, 255, 0.28));
}

.el-loading-spinner .path {
  stroke: var(--neon-cyan);
  stroke-linecap: round;
}

.el-loading-spinner .el-loading-text {
  margin-top: 10px;
  color: var(--text-primary);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  text-shadow: 0 0 16px rgba(84, 227, 255, 0.12);
}

.el-progress-bar__outer {
  height: 12px !important;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12), inset 0 0 0 1px rgba(84, 227, 255, 0.06);
}

.el-progress-bar__inner {
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--accent), var(--neon-violet)) !important;
  box-shadow: 0 0 16px rgba(84, 227, 255, 0.2);
}

.el-progress.is-success .el-progress-bar__inner {
  background: linear-gradient(90deg, #34d399, var(--neon-cyan)) !important;
}

.el-progress.is-warning .el-progress-bar__inner {
  background: linear-gradient(90deg, #fbbf24, var(--neon-pink)) !important;
}

.el-progress.is-exception .el-progress-bar__inner {
  background: linear-gradient(90deg, #ef4444, #fb7185) !important;
}

.el-progress__text {
  color: var(--text-primary);
  font-weight: 700;
}

.el-empty,
.el-result {
  position: relative;
  overflow: hidden;
  padding: 20px 18px;
  border-radius: 20px;
  border: 1px solid var(--panel-subtle-border);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04)),
    repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(84, 227, 255, 0.04) 28px, rgba(84, 227, 255, 0.04) 29px),
    var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.el-empty::before,
.el-result::before {
  content: '';
  position: absolute;
  top: 0;
  left: 18px;
  right: 18px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-violet), var(--neon-pink));
  opacity: 0.9;
}

.el-empty__image,
.el-result__icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.1), rgba(157, 123, 255, 0.08));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16), 0 0 18px rgba(84, 227, 255, 0.08);
}

.el-empty__description p,
.el-result__subtitle p {
  margin: 0;
  line-height: 1.8;
}

.el-result__title,
.el-empty__description {
  color: var(--text-primary);
}

.el-result__extra,
.el-empty__bottom {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.el-skeleton {
  position: relative;
  overflow: hidden;
}

.el-skeleton__item {
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.32), rgba(84, 227, 255, 0.18), rgba(255, 255, 255, 0.16));
  background-size: 220% 100%;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(100, 116, 139, 0.4);
  border: 2px solid transparent;
  background-clip: padding-box;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.56);
  background-clip: padding-box;
}

@media (max-width: 768px) {
  .page-title {
    font-size: clamp(24px, 7vw, 30px);
  }

  .page-subtle-shell,
  .page-panel-card,
  .page-table-shell,
  .el-card,
  .el-dialog,
  .el-drawer,
  .el-message-box {
    border-radius: 16px;
  }

  .el-drawer {
    width: min(100vw, 420px) !important;
  }

  .el-drawer__header {
    padding: 16px 16px 14px;
  }

  .el-drawer__body {
    padding: 16px;
  }

  .el-message-box {
    width: min(100vw - 20px, 420px);
  }

  .el-message-box__header,
  .el-message-box__content,
  .el-message-box__btns {
    padding-left: 16px;
    padding-right: 16px;
  }

  .el-pagination {
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .el-pagination .btn-prev,
  .el-pagination .btn-next,
  .el-pagination .el-pager li,
  .el-pagination .el-input__wrapper {
    min-width: 32px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
