<script setup>
import { onMounted, ref } from 'vue'
import { fetchMySchedule } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const schedules = ref([])
const error = ref('')

onMounted(async () => {
  try {
    schedules.value = await fetchMySchedule(props.token)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
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
  </div>
</template>

<style scoped>
.error {
  color: #dc2626;
  font-size: 13px;
}

h2 {
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
