<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Calendar, FolderOpened, Notebook } from '@element-plus/icons-vue'
import { fetchMe } from '../api'
import AppLayout from '../components/AppLayout.vue'
import ChatView from '../components/ChatView.vue'
import DocumentsView from '../components/DocumentsView.vue'
import PlansView from '../components/PlansView.vue'
import ScheduleView from '../components/ScheduleView.vue'

const router = useRouter()
const MENUS = [
  { index: 'chat', label: '课程助手', icon: ChatDotRound },
  { index: 'schedule', label: '我的课表', icon: Calendar },
  { index: 'documents', label: '课程资料', icon: FolderOpened },
  { index: 'plans', label: '学习计划', icon: Notebook },
]

const user = ref(null)
const token = ref(localStorage.getItem('token') || '')
const activeTab = ref('chat')

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
}

function handleSelect(index) {
  if (index === 'logout') return handleLogout()
  activeTab.value = index
}

onMounted(async () => {
  try {
    user.value = await fetchMe(token.value)
  } catch {
    handleLogout()
  }
})
</script>

<template>
  <AppLayout title="学生端" :menus="MENUS" :active-index="activeTab" :user="user" :on-select="handleSelect">
    <template #headerExtra>
      <el-button
        v-if="user?.role === 'admin'"
        type="primary"
        size="small"
        plain
        @click="router.push('/manager')"
      >
        进入管理后台
      </el-button>
    </template>

    <ChatView v-if="activeTab === 'chat'" :token="token" show-history />
    <ScheduleView v-else-if="activeTab === 'schedule'" :token="token" />
    <DocumentsView v-else-if="activeTab === 'documents'" :token="token" />
    <PlansView v-else :token="token" />
  </AppLayout>
</template>
