<template>
  <div class="upload-container">
    <section class="upload-hero">
      <div>
        <p class="hero-badge">快速添加</p>
        <h2 class="page-title">添加小说</h2>
        <p class="hero-subtitle">直接输入番茄小说 ID，快速加入后台抓取队列。</p>
      </div>
      <el-button type="primary" plain @click="searchInstead">前往搜索页</el-button>
    </section>

    <el-row :gutter="20">
      <el-col :span="24" :lg="16">
        <el-card class="glass-card upload-card page-panel-card">
          <template #header>
            <div class="card-header">
              <div>
                <h3>输入小说 ID</h3>
                <p>适合已知小说 ID 时快速添加。</p>
              </div>
            </div>
          </template>

          <div class="upload-form">
            <p class="upload-tip">系统会自动创建任务并在后台抓取章节与元数据。</p>

            <el-form
              ref="formRef"
              :model="form"
              :rules="rules"
              label-position="top"
              @submit.prevent="handleAddNovel"
            >
              <el-form-item label="小说ID" prop="novelId">
                <el-input v-model="form.novelId" placeholder="请输入小说ID" clearable />
              </el-form-item>

              <div class="upload-buttons">
                <el-button type="primary" @click="handleAddNovel" :loading="novelStore.isLoading">
                  添加小说
                </el-button>
                <el-button @click="resetForm">重置</el-button>
              </div>

              <el-alert
                v-if="novelStore.error"
                class="upload-alert"
                :title="novelStore.error"
                type="error"
                :closable="false"
                show-icon
              />
            </el-form>
          </div>
        </el-card>

        <el-result
          v-if="addSuccess"
          icon="success"
          title="小说添加成功"
          sub-title="任务已提交到后台处理，可前往任务管理查看进度"
          class="success-card"
        >
          <template #extra>
            <el-button type="primary" @click="viewTasks">查看任务进度</el-button>
            <el-button @click="resetForm">继续添加</el-button>
          </template>
        </el-result>
      </el-col>

      <el-col :span="24" :lg="8">
        <el-card class="glass-card instructions-card page-panel-card">
          <template #header>
            <div class="card-header">
              <div>
                <h3>操作指南</h3>
                <p>第一次使用可先看这里。</p>
              </div>
            </div>
          </template>

          <div class="instructions">
            <h4>如何添加</h4>
            <ol>
              <li>输入正确的小说 ID</li>
              <li>点击“添加小说”</li>
              <li>系统自动创建后台任务</li>
              <li>抓取完成后可在书库或任务页查看</li>
            </ol>

            <h4>找不到小说 ID？</h4>
            <p>
              可先去 <router-link to="/search">搜索小说</router-link> 页面，通过关键词找到目标小说。
            </p>

            <h4>注意事项</h4>
            <ul>
              <li>抓取需要一定时间，请耐心等待</li>
              <li>任务提交后可到 <router-link to="/tasks">任务管理</router-link> 页面查看进度</li>
              <li>如果出现失败提示，可稍后重试</li>
            </ul>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  resolveQueuedNovelErrorPresentation,
  resolveQueuedNovelSuccessMessage,
} from '../composables/useNovelTaskFeedback'
import { useNovelStore } from '../store'

const router = useRouter()
const novelStore = useNovelStore()
const formRef = ref()
const addSuccess = ref(false)

const form = reactive({
  novelId: null as string | null,
})

const rules = {
  novelId: [{ required: true, message: '请输入小说ID', trigger: 'blur' }],
}

const handleAddNovel = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid || form.novelId === null) {
      ElMessage.warning('请输入有效的小说ID')
      return
    }

    try {
      const response = await novelStore.addNovel(form.novelId)

      if (response) {
        ElMessage.success(resolveQueuedNovelSuccessMessage('full'))
        addSuccess.value = true
      } else {
        const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '添加小说失败')
        ElMessage[presentation.type](presentation.message)
      }
    } catch {
      const presentation = resolveQueuedNovelErrorPresentation(novelStore.error, '添加小说失败')
      ElMessage[presentation.type](presentation.message)
    }
  })
}

const resetForm = () => {
  form.novelId = null
  novelStore.error = null
  addSuccess.value = false

  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const viewTasks = () => {
  router.push('/tasks')
}

const searchInstead = () => {
  router.push('/search')
}

onMounted(() => {
  resetForm()
})
</script>

<style scoped>
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 32px;
}

.upload-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 22px 24px;
  border-radius: 18px;
  background: var(--shell-glass-bg);
  border: 1px solid var(--shell-glass-border);
  box-shadow: var(--shell-glass-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.34);
  backdrop-filter: blur(var(--shell-glass-blur)) saturate(155%);
}

.hero-badge {
  margin: 0 0 10px;
  color: var(--text-tertiary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 8px;
  color: var(--text-secondary);
}

.glass-card {
  border-radius: 20px;
  overflow: hidden;
}

:deep(.upload-card .el-card__body),
:deep(.instructions-card .el-card__body) {
  padding: 24px;
}

.card-header h3 {
  margin: 0;
  font-size: 20px;
}

.card-header p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.upload-form {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-subtle-border);
  background: var(--panel-subtle-bg);
  box-shadow: var(--panel-subtle-shadow);
}

.upload-tip {
  margin-bottom: 20px;
  color: var(--text-secondary);
}

.upload-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.upload-alert {
  margin-top: 18px;
}

.success-card {
  margin-top: 18px;
  border-radius: 20px;
  border: 1px solid var(--panel-raised-border);
  background: var(--panel-raised-bg);
  box-shadow: var(--panel-raised-shadow);
  overflow: hidden;
}

.instructions {
  padding: 4px;
  color: var(--text-secondary);
}

.instructions h4 {
  margin: 18px 0 8px;
  color: var(--text-primary);
}

.instructions ol,
.instructions ul {
  padding-left: 20px;
  margin: 0 0 12px;
}

.instructions li {
  margin-bottom: 6px;
}

.instructions a {
  color: var(--accent-strong);
  text-decoration: none;
}

.instructions a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .upload-hero {
    padding: 20px;
  }

  :deep(.upload-card .el-card__body),
  :deep(.instructions-card .el-card__body) {
    padding: 18px;
  }

  .upload-form {
    padding: 14px;
  }

  .upload-buttons {
    flex-direction: column;
  }

  .upload-buttons .el-button,
  .upload-hero .el-button {
    width: 100%;
  }

  .instructions {
    padding: 0;
    font-size: 13px;
  }
}
</style>
