<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMe } from '../api'
import ChatView from '../components/ChatView.vue'
import DocumentsView from '../components/DocumentsView.vue'
import PlansView from '../components/PlansView.vue'
import ScheduleView from '../components/ScheduleView.vue'

const router = useRouter()
const TABS = [
  { key: 'chat', label: '💬 聊天' },
  { key: 'schedule', label: '📅 课表' },
  { key: 'documents', label: '📄 资料' },
  { key: 'plans', label: '🎯 计划' },
]

const user = ref(null)
const token = ref(localStorage.getItem('token') || '')
const activeTab = ref('chat')

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
}

onMounted(async () => {
  try {
    user.value = await fetchMe(token.value)
    // 管理员登录学生端时给出进入后台的入口
  } catch {
    handleLogout()
  }
})
</script>

<template>
  <main class="page">
    <header class="head">
      <h1>校园课程智能助手</h1>
      <div class="head-right">
        <el-button
          v-if="user?.role === 'admin'"
          type="primary"
          size="small"
          link
          @click="router.push('/manager')"
        >
          进入管理后台 →
        </el-button>
        <span class="who">{{ user?.name }}（{{ user?.role === 'admin' ? '管理员' : '学生' }}）</span>
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
      <ChatView v-if="activeTab === 'chat'" :token="token" show-history />
      <ScheduleView v-else-if="activeTab === 'schedule'" :token="token" />
      <DocumentsView v-else-if="activeTab === 'documents'" :token="token" />
      <PlansView v-else :token="token" />
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 920px;
  margin: 0 auto;
  padding: 28px 16px 48px;
  font-family: system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

h1 {
  font-size: 20px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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
  color: #409eff;
  border-bottom-color: #409eff;
  font-weight: 600;
}

.content {
  min-height: 420px;
}
</style>
