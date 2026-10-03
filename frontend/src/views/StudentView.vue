<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Calendar, FolderOpened, Notebook } from '@element-plus/icons-vue'
import { fetchMe } from '../api'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const user = ref(null)

const MENUS = [
  { index: '/chat', label: '课程助手', icon: ChatDotRound },
  { index: '/schedule', label: '我的课表', icon: Calendar },
  { index: '/documents', label: '课程资料', icon: FolderOpened },
  { index: '/plans', label: '学习计划', icon: Notebook },
]

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
}

function handleSelect(index) {
  if (index === 'logout') return handleLogout()
  if (index !== route.path) router.push(index)
}

onMounted(async () => {
  try {
    user.value = await fetchMe(localStorage.getItem('token') || '')
  } catch {
    handleLogout()
  }
})
</script>

<template>
  <AppLayout
    title="学生端"
    :menus="MENUS"
    :active-index="route.path"
    :user="user"
    :on-select="handleSelect"
  >
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

    <router-view />
  </AppLayout>
</template>
