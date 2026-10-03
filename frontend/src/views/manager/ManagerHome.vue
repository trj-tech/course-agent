<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchAdminStats } from '../../api'

const router = useRouter()
const token = localStorage.getItem('token') || ''
const stats = ref(null)
const loading = ref(true)

const entries = [
  { key: 'users', label: '用户总数', color: '#409eff' },
  { key: 'students', label: '学生', color: '#67c23a' },
  { key: 'courses', label: '课程', color: '#e6a23c' },
  { key: 'schedules', label: '课表记录', color: '#f56c6c' },
  { key: 'documents', label: '知识库文档', color: '#909399' },
  { key: 'plans', label: '学习计划', color: '#9b59b6' },
  { key: 'assignments', label: '作业', color: '#f0662e' },
  { key: 'scores', label: '成绩记录', color: '#3498db' },
  { key: 'conversations', label: 'AI 会话', color: '#00bcd4' },
  { key: 'messages', label: 'AI 消息', color: '#ff9800' },
]

const quickActions = [
  { path: '/manager/documents', label: '文档管理', desc: '上传/入库课程资料' },
  { path: '/manager/courses', label: '课程管理', desc: '维护课程信息' },
  { path: '/manager/schedules', label: '课表管理', desc: '按学生编排课表' },
  { path: '/manager/chat', label: '课程助手', desc: '验证检索与工具调用' },
  { path: '/manager/users', label: '用户管理', desc: '账号与角色' },
]

onMounted(async () => {
  try {
    stats.value = await fetchAdminStats(token)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="panel">
    <h2>欢迎您：管理员</h2>
    <p class="sub">维护课程与知识库文档，利用课程助手验证检索与工具调用。</p>

    <el-row :gutter="14" v-loading="loading">
      <el-col v-for="e in entries" :key="e.key" :span="6" class="stat-col">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-num" :style="{ color: e.color }">{{ stats?.[e.key] ?? '-' }}</div>
          <div class="stat-label">{{ e.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="section">快速入口</h3>
    <el-row :gutter="14">
      <el-col v-for="a in quickActions" :key="a.path" :span="4" class="quick-col">
        <el-card shadow="hover" class="quick-card" @click="router.push(a.path)">
          <div class="quick-label">{{ a.label }}</div>
          <div class="quick-desc">{{ a.desc }}</div>
        </el-card>
      </el-col>
    </el-row>

    <h3 class="section">演示路径</h3>
    <el-card shadow="never">
      <ol class="steps">
        <li>在「文档管理」上传样例文档（txt/md/pdf/docx），确认「已入库」。</li>
        <li>打开「课程助手」，问「数据结构实验要不要预习？」→ 应出现检索工具过程与来源。</li>
        <li>在「课程管理」维护课程；在「课表管理」按学生增删改查课表（含节次冲突检测）。</li>
        <li>换学生账号登录，对照课表与学习计划，验证助手当前用户隔离。</li>
      </ol>
    </el-card>
  </div>
</template>

<style scoped>
h2 {
  margin: 0;
}

.sub {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 16px;
}

.stat-col {
  margin-bottom: 14px;
}

.stat-card {
  text-align: center;
}

.stat-num {
  font-size: 26px;
  font-weight: 700;
}

.stat-label {
  color: #6b7280;
  font-size: 13px;
  margin-top: 4px;
}

.section {
  margin: 18px 0 10px;
  font-size: 15px;
}

.quick-col {
  margin-bottom: 14px;
}

.quick-card {
  cursor: pointer;
  text-align: center;
}

.quick-label {
  font-weight: 600;
  font-size: 14px;
}

.quick-desc {
  color: #9ca3af;
  font-size: 12px;
  margin-top: 6px;
}

.steps {
  margin: 0;
  padding-left: 20px;
  color: #374151;
  font-size: 14px;
  line-height: 2;
}
</style>
