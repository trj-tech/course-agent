<script setup>
import { onMounted, ref } from 'vue'
import { fetchMe, login } from './api'
import ChatView from './components/ChatView.vue'
import DocumentsView from './components/DocumentsView.vue'
import PlansView from './components/PlansView.vue'
import ScheduleView from './components/ScheduleView.vue'

const TABS = [
  { key: 'chat', label: '💬 聊天' },
  { key: 'schedule', label: '📅 课表' },
  { key: 'documents', label: '📄 资料' },
  { key: 'plans', label: '🎯 计划' },
]

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const user = ref(null)
const token = ref(localStorage.getItem('token') || '')
const activeTab = ref('chat')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    user.value = data.user
    activeTab.value = 'chat'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  localStorage.removeItem('token')
  token.value = ''
  user.value = null
  username.value = ''
  password.value = ''
}

onMounted(async () => {
  if (!token.value) return
  try {
    user.value = await fetchMe(token.value)
  } catch {
    handleLogout()
  }
})
</script>

<template>
  <main class="page">
    <!-- 未登录：登录表单 -->
    <template v-if="!user">
      <h1>校园课程智能助手</h1>
      <p class="tagline">能查真实课表 · 能按文档作答 · 能帮你存计划</p>
      <form class="login" @submit.prevent="handleLogin">
        <input v-model="username" type="text" placeholder="用户名（如 student01）" autocomplete="username" />
        <input v-model="password" type="password" placeholder="密码（同用户名）" autocomplete="current-password" />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
      </form>
    </template>

    <!-- 已登录：标签页布局 -->
    <template v-else>
      <header class="head">
        <h1>校园课程智能助手</h1>
        <div class="head-right">
          <span class="who">{{ user.name }}（{{ user.role === 'admin' ? '管理员' : '学生' }}）</span>
          <button class="logout" @click="handleLogout">退出</button>
        </div>
      </header>

      <nav class="tabs">
        <button
          v-for="t in TABS"
          :key="t.key"
          :class="{ active: activeTab === t.key }"
          @click="activeTab = t.key"
        >
          {{ t.label }}
        </button>
      </nav>

      <section class="content">
        <ChatView v-if="activeTab === 'chat'" :token="token" />
        <ScheduleView v-else-if="activeTab === 'schedule'" :token="token" />
        <DocumentsView v-else-if="activeTab === 'documents'" :token="token" />
        <PlansView v-else :token="token" />
      </section>
    </template>
  </main>
</template>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 16px 48px;
  font-family: system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

h1 {
  text-align: center;
  font-size: 22px;
}

.tagline {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 6px;
}

.login {
  max-width: 320px;
  margin: 48px auto 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.login input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

.login button {
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: #16a34a;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
}

.login button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #dc2626;
  font-size: 13px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.head h1 {
  text-align: left;
  font-size: 20px;
}

.head-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.who {
  color: #374151;
  font-size: 14px;
}

.logout {
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 8px;
  padding: 5px 12px;
  cursor: pointer;
  color: #374151;
  font-size: 13px;
}

.tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

.tabs button {
  padding: 8px 14px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  border-bottom: 2px solid transparent;
}

.tabs button.active {
  color: #16a34a;
  border-bottom-color: #16a34a;
  font-weight: 600;
}

.content {
  min-height: 420px;
}
</style>
