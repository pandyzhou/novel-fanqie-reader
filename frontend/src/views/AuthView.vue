<template>
  <div class="auth-container">
    <div class="auth-background-glow auth-background-glow-a" />
    <div class="auth-background-glow auth-background-glow-b" />

    <el-card class="auth-card page-panel-card">
      <template #header>
        <div class="auth-header">
          <div>
            <p class="auth-badge">账户访问</p>
            <h2>{{ isLogin ? '登录' : '注册' }}</h2>
            <p class="auth-subtitle">深浅色主题共享全局设置，支持键盘导航与即时表单提示。</p>
            <div class="auth-mode-chip page-subtle-shell">
              {{ isLogin ? '欢迎回来，继续你的阅读进度' : '创建账号，保存你的阅读与下载记录' }}
            </div>
          </div>
          <el-switch
            v-model="isLogin"
            active-text="登录"
            inactive-text="注册"
            @change="resetForm"
          />
        </div>
      </template>

      <div class="auth-form-shell page-subtle-shell">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>

        <el-alert
          v-if="authStore.error"
          class="auth-alert"
          :title="authStore.error"
          type="error"
          :closable="false"
          show-icon
        />

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="authStore.isLoading"
            class="submit-button"
          >
            {{ isLogin ? '登录' : '注册' }}
          </el-button>
        </el-form-item>

          <div class="auth-toggle">
            <span>{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
            <el-button text @click="toggleMode">
              {{ isLogin ? '立即注册' : '立即登录' }}
            </el-button>
          </div>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store'
import type { LoginCredentials, RegisterCredentials } from '../api'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const isLogin = ref(true)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = computed(() => {
  const baseRules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' },
    ],
  }

  if (!isLogin.value) {
    return {
      ...baseRules,
      confirmPassword: [
        { required: true, message: '请再次输入密码', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' },
      ],
    }
  }

  return baseRules
})

const resetForm = () => {
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  authStore.error = null
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    try {
      if (isLogin.value) {
        const credentials: LoginCredentials = {
          username: form.username,
          password: form.password,
        }
        const result = await authStore.login(credentials.username, credentials.password ?? '')
        if (result) {
          ElMessage.success('登录成功')
          router.push('/')
        }
      } else {
        const credentials: RegisterCredentials = {
          username: form.username,
          password: form.password,
        }
        const result = await authStore.register(credentials.username, credentials.password ?? '')
        if (result) {
          ElMessage.success('注册成功，请登录')
          isLogin.value = true
          resetForm()
        }
      }
    } catch {
      if (!authStore.error) {
        authStore.error = isLogin.value ? '登录失败，请重试' : '注册失败，请重试'
      }
    }
  })
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.auth-background-glow {
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 999px;
  filter: blur(82px);
  opacity: 0.3;
  pointer-events: none;
}

.auth-background-glow-a {
  top: -80px;
  right: 10%;
  background: rgba(255, 111, 207, 0.24);
}

.auth-background-glow-b {
  bottom: -110px;
  left: 10%;
  background: rgba(84, 227, 255, 0.22);
}

.auth-card {
  width: min(100%, 470px);
  border-radius: 22px;
  overflow: hidden;
  box-shadow: var(--panel-raised-shadow), var(--glow-accent);
}

:deep(.auth-card .el-card__header) {
  padding: 20px 22px 18px;
}

:deep(.auth-card .el-card__body) {
  padding: 22px;
}

.auth-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
}

.auth-badge {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  font-weight: 700;
}

.auth-header h2 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
}

.auth-subtitle {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.auth-mode-chip {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(84, 227, 255, 0.12), rgba(157, 123, 255, 0.08));
}

.auth-form-shell {
  padding: 18px;
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04)),
    var(--panel-subtle-bg);
}

:deep(.auth-form-shell .el-form-item__label) {
  color: var(--text-secondary);
  font-weight: 700;
}

.auth-alert {
  margin-bottom: 16px;
}

.submit-button {
  width: 100%;
  min-height: 48px;
  border-radius: 14px;
  box-shadow: var(--glow-accent);
}

.auth-toggle {
  margin-top: 16px;
  text-align: center;
  color: var(--text-secondary);
}

:deep(.auth-toggle .el-button) {
  font-weight: 700;
}

@media (max-width: 768px) {
  :deep(.auth-card .el-card__header),
  :deep(.auth-card .el-card__body) {
    padding-inline: 18px;
  }

  .auth-form-shell {
    padding: 16px;
  }

  .auth-header {
    flex-direction: column;
  }
}
</style>
