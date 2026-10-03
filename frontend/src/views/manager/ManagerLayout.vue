<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  HomeFilled,
  ChatDotRound,
  FolderOpened,
  Reading,
  Calendar,
  EditPen,
  Ticket,
  User,
} from '@element-plus/icons-vue'
import { fetchMe } from '../../api'
import AppLayout from '../../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const user = ref(null)

const MENUS = [
  { index: '/manager/home', label: '系统首页', icon: HomeFilled },
  { index: '/manager/chat', label: '课程助手', icon: ChatDotRound },
  { index: '/manager/documents', label: '文档管理', icon: FolderOpened },
  { index: '/manager/courses', label: '课程管理', icon: Reading },
  { index: '/manager/schedules', label: '课表管理', icon: Calendar },
  { index: '/manager/assignments', label: '作业管理', icon: EditPen },
  { index: '/manager/scores', label: '成绩管理', icon: Ticket },
  { index: '/manager/users', label: '用户管理', icon: User },
]

function handleSelect(index) {
  if (index === 'logout') return handleLogout()
  if (index !== route.path) router.push(index)
}

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
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
    title="管理后台"
    :menus="MENUS"
    :active-index="route.path"
    :user="user"
    :on-select="handleSelect"
  >
    <template #headerExtra>
      <el-button size="small" @click="router.push('/')">返回学生端</el-button>
      <el-button size="small" type="danger" plain @click="handleLogout">退出</el-button>
    </template>

    <router-view />
  </AppLayout>
</template>
