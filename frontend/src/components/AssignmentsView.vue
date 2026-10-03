<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchMyAssignments, setAssignmentStatus } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const assignments = ref([])
const error = ref('')
const filter = ref('all')

const filtered = computed(() => {
  if (filter.value === 'all') return assignments.value
  return assignments.value.filter((a) => a.status === filter.value)
})

async function load() {
  try {
    assignments.value = await fetchMyAssignments(props.token)
  } catch (e) {
    error.value = e.message
  }
}

async function toggle(a) {
  try {
    await setAssignmentStatus(props.token, a.id, a.status === 'done' ? 'pending' : 'done')
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function dueLabel(a) {
  if (a.status === 'done') return '已完成'
  if (a.overdue) return `已逾期 ${Math.abs(a.days_left).toFixed(1)} 天`
  if (a.days_left <= 1) return '即将截止'
  return `剩余 ${a.days_left} 天`
}

onMounted(load)
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>作业与截止日期</h2>
    <p class="tip">也可以在聊天里问「我最近有什么作业要交」，助手会自动查询</p>

    <el-radio-group v-model="filter" size="small" style="margin-bottom: 14px">
      <el-radio-button value="all">全部（{{ assignments.length }}）</el-radio-button>
      <el-radio-button value="pending">
        未完成（{{ assignments.filter((a) => a.status === 'pending').length }}）
      </el-radio-button>
      <el-radio-button value="done">
        已完成（{{ assignments.filter((a) => a.status === 'done').length }}）
      </el-radio-button>
    </el-radio-group>

    <div class="cards">
      <div v-for="a in filtered" :key="a.id" class="asg" :class="{ done: a.status === 'done' }">
        <div class="asg-head">
          <strong>{{ a.title }}</strong>
          <span class="due" :class="{ danger: a.overdue && a.status === 'pending', ok: a.status === 'done' }">
            {{ dueLabel(a) }}
          </span>
        </div>
        <p v-if="a.description" class="desc">{{ a.description }}</p>
        <div class="asg-foot">
          <span class="meta">
            {{ a.course_name ? `${a.course_name}（${a.course_code}）` : '未关联课程' }} · 截止
            {{ a.due_at }}
          </span>
          <el-button size="small" :type="a.status === 'done' ? 'info' : 'success'" plain @click="toggle(a)">
            {{ a.status === 'done' ? '标记未完成' : '标记完成' }}
          </el-button>
        </div>
      </div>
      <div v-if="!filtered.length" class="empty">没有符合条件的作业</div>
    </div>
  </div>
</template>

<style scoped>
.error {
  color: #dc2626;
  font-size: 13px;
}

h2 {
  font-size: 16px;
}

.tip {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 12px;
}

.cards {
  display: grid;
  gap: 12px;
}

.asg {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
}

.asg.done {
  opacity: 0.65;
}

.asg-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.due {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  background: #fef3c7;
  color: #b45309;
}

.due.danger {
  background: #fef2f2;
  color: #dc2626;
}

.due.ok {
  background: #f0fdf4;
  color: #16a34a;
}

.desc {
  color: #374151;
  font-size: 14px;
  margin: 8px 0;
}

.asg-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta {
  color: #9ca3af;
  font-size: 12px;
}

.empty {
  color: #9ca3af;
  text-align: center;
  padding: 24px;
}
</style>
