<script setup>
import { onMounted, ref } from 'vue'
import { fetchMe, fetchMySchedule, login } from './api'

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const user = ref(null)
const schedules = ref([])

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    localStorage.setItem('token', data.access_token)
    user.value = data.user
    schedules.value = await fetchMySchedule(data.access_token)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  localStorage.removeItem('token')
  user.value = null
  schedules.value = []
  username.value = ''
  password.value = ''
}

async function restoreSession() {
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    user.value = await fetchMe(token)
    schedules.value = await fetchMySchedule(token)
  } catch {
    localStorage.removeItem('token')
  }
}

onMounted(restoreSession)
</script>

<template>
  <main class="page">
    <!-- 登录态：欢迎 + 课表 -->
    <template v-if="user">
      <header class="head">
        <h1>校园课程智能助手</h1>
        <button class="logout" @click="handleLogout">退出登录</button>
      </header>
      <p class="welcome">
        你好，{{ user.name }}（{{ user.role === 'admin' ? '管理员' : '学生' }}）{{ user.student_no || '' }}
      </p>

      <section class="table-wrap">
        <h2>我的课表（{{ schedules.length }} 门）</h2>
        <table>
          <thead>
            <tr>
              <th>星期</th>
              <th>节次</th>
              <th>课程</th>
              <th>教师</th>
              <th>周次</th>
              <th>教室</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in schedules" :key="s.id">
              <td>{{ DAYS[s.weekday - 1] }}</td>
              <td>{{ s.start_period }}-{{ s.end_period }}节</td>
              <td>
                <strong>{{ s.course_name }}</strong>
                <span class="code">{{ s.course_code }}</span>
              </td>
              <td>{{ s.teacher }}</td>
              <td>{{ s.week_start }}-{{ s.week_end }}周</td>
              <td>{{ s.location }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>

    <!-- 未登录：登录表单 -->
    <template v-else>
      <h1>校园课程智能助手</h1>
      <p class="tagline">能查真实课表 · 能按文档作答 · 能帮你存计划</p>
      <form class="login" @submit.prevent="handleLogin">
        <input v-model="username" type="text" placeholder="用户名（如 student01）" autocomplete="username" />
        <input v-model="password" type="password" placeholder="密码（同用户名）" autocomplete="current-password" />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
      </form>
    </template>
  </main>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 48px 16px;
  font-family: system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

h1 {
  text-align: center;
}

.tagline {
  text-align: center;
  color: #666;
  font-size: 15px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome {
  color: #374151;
}

.login {
  max-width: 320px;
  margin: 40px auto 0;
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

.logout {
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  color: #374151;
}

.table-wrap {
  margin-top: 24px;
}

.table-wrap h2 {
  font-size: 16px;
  margin-bottom: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  font-size: 14px;
}

th,
td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

th {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 500;
}

.code {
  margin-left: 6px;
  color: #9ca3af;
  font-size: 12px;
}
</style>
