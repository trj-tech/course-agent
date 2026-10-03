<script setup>
import { onMounted, ref } from 'vue'
import { fetchMyScores } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const summary = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    summary.value = await fetchMyScores(props.token)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>我的成绩</h2>
    <p class="tip">绩点采用 4.0 标准换算，GPA 按学分加权</p>

    <template v-if="summary">
      <div class="stat-grid">
        <div class="stat">
          <div class="stat-num">{{ summary.gpa ?? '—' }}</div>
          <div class="stat-label">GPA（4.0 制）</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ summary.average ?? '—' }}</div>
          <div class="stat-label">加权平均分</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ summary.courses.length }}</div>
          <div class="stat-label">已修课程</div>
        </div>
        <div class="stat">
          <div class="stat-num weakest">
            {{ summary.weakest ? `${summary.weakest.course_name} ${summary.weakest.score}` : '—' }}
          </div>
          <div class="stat-label">最弱科目</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>课程</th>
            <th>学分</th>
            <th>成绩</th>
            <th>绩点</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in summary.courses" :key="c.course_code">
            <td>{{ c.course_name }}（{{ c.course_code }}）</td>
            <td>{{ c.credit }}</td>
            <td>
              <span class="score" :class="{ low: c.score < 80, high: c.score >= 90 }">{{ c.score }}</span>
            </td>
            <td>{{ c.gpapoint.toFixed(1) }}</td>
          </tr>
          <tr v-if="!summary.courses.length">
            <td colspan="4" class="empty">暂无成绩记录</td>
          </tr>
        </tbody>
      </table>
      <p class="tip" style="margin-top: 10px">也可以在聊天里问「我的 GPA 是多少？哪门课最弱？」</p>
    </template>
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

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.stat-num {
  font-size: 22px;
  font-weight: 600;
  color: #1890ff;
}

.stat-num.weakest {
  font-size: 15px;
  line-height: 32px;
  color: #b45309;
}

.stat-label {
  color: #6b7280;
  font-size: 12px;
  margin-top: 4px;
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

.score {
  font-weight: 600;
}

.score.high {
  color: #16a34a;
}

.score.low {
  color: #dc2626;
}

.empty {
  text-align: center;
  color: #9ca3af;
}
</style>
