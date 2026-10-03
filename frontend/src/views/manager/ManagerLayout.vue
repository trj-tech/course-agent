<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchMe } from '../../api'

const router = useRouter()
const route = useRoute()
const user = ref(null)

const menus = [
  { path: '/manager/home', label: '📊 系统首页' },
  { path: '/manager/chat', label: '💬 课程助手' },
  { path: '/manager/documents', label: '📄 文档管理' },
  { path: '/manager/courses', label: '📚 课程管理' },
  { path: '/manager/schedules', label: '📅 课表管理' },
  { path: '/manager/users', label: '👤 用户管理' },
]

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
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">🏫 校园课程智能助手</div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          {{ m.label }}
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="title">管理后台</span>
        <div class="right">
          <span class="who">{{ user?.name }}（管理员）</span>
          <el-button size="small" @click="router.push('/')">返回学生端</el-button>
          <el-button size="small" type="danger" plain @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: #001529;
  color: #fff;
}

.logo {
  height: 56px;
  line-height: 56px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.menu {
  border-right: none;
  background: transparent;
}

.menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.72);
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.menu :deep(.el-menu-item.is-active) {
  background: #409eff;
  color: #fff;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.who {
  color: #374151;
  font-size: 14px;
}

.main {
  background: #f5f5f5;
}
</style>
