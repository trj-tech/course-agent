<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchMe, login, register } from '../api'

const router = useRouter()
const mode = ref('login') // login | register
const username = ref('')
const password = ref('')
const name = ref('')
const studentNo = ref('')
const error = ref('')
const loading = ref(false)

async function goHome(user) {
  localStorage.setItem('role', user.role)
  if (user.role === 'admin') {
    router.push('/manager')
  } else {
    router.push('/')
  }
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await login(username.value.trim(), password.value)
    localStorage.setItem('token', data.access_token)
    await goHome(data.user)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    const data = await register({
      username: username.value.trim(),
      password: password.value,
      name: name.value.trim(),
      student_no: studentNo.value.trim() || null,
    })
    localStorage.setItem('token', data.access_token)
    ElMessage.success('注册成功，已自动登录')
    await goHome(data.user)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    const user = await fetchMe(token)
    localStorage.setItem('role', user.role)
    await goHome(user)
  } catch {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
  }
})
</script>

<template>
  <main class="login-page">
    <div class="card">
      <h1>校园课程智能助手</h1>
      <p class="tagline">基于 Agent 智能系统 · 真实课表 / RAG 问答 / 学习计划</p>

      <form v-if="mode === 'login'" class="form" @submit.prevent="handleLogin">
        <input v-model="username" type="text" placeholder="用户名" autocomplete="username" />
        <input
          v-model="password"
          type="password"
          placeholder="密码"
          autocomplete="current-password"
        />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登 录' }}</button>
        <p class="switch">
          还没有账号？
          <a @click="mode = 'register'; error = ''">注册</a>
        </p>
      </form>

      <form v-else class="form" @submit.prevent="handleRegister">
        <input v-model="username" type="text" placeholder="用户名" autocomplete="username" />
        <input v-model="password" type="password" placeholder="密码" autocomplete="new-password" />
        <input v-model="name" type="text" placeholder="姓名（可选）" />
        <input v-model="studentNo" type="text" placeholder="学号（可选）" />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '注册中…' : '注 册' }}</button>
        <p class="switch">
          已有账号？
          <a @click="mode = 'login'; error = ''">去登录</a>
        </p>
      </form>

      <p class="hint">测试账号：student01 / student01 · admin01 / admin01</p>
    </div>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.card {
  width: 360px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  padding: 32px 28px;
  text-align: center;
}

h1 {
  font-size: 22px;
  margin: 0;
}

.tagline {
  color: #666;
  font-size: 13px;
  margin: 8px 0 24px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.form input:focus {
  border-color: #409eff;
}

.form button {
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: #409eff;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
}

.form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #dc2626;
  font-size: 13px;
  margin: 0;
}

.switch {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 0;
}

.switch a {
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
}

.hint {
  color: #9ca3af;
  font-size: 12px;
  margin-top: 18px;
}
</style>
