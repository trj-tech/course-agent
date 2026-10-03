<script setup>
import { onMounted, ref } from 'vue'
import { fetchPlans } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const plans = ref([])
const error = ref('')

onMounted(async () => {
  try {
    plans.value = await fetchPlans(props.token)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div>
    <p v-if="error" class="error">{{ error }}</p>
    <h2>我的学习计划（{{ plans.length }}）</h2>
    <p class="tip">在聊天里让助手「制定学习计划」即可自动生成并保存</p>

    <div class="cards">
      <div v-for="p in plans" :key="p.id" class="plan">
        <div class="plan-head">
          <strong>{{ p.title }}</strong>
          <span class="status">{{ p.status }}</span>
        </div>
        <p v-if="p.goal" class="goal">目标：{{ p.goal }}</p>
        <p class="time">{{ p.created_at }}</p>
      </div>
      <div v-if="!plans.length" class="empty">还没有学习计划</div>
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

.plan {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
}

.plan-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: #f0fdf4;
  color: #16a34a;
}

.goal {
  color: #374151;
  font-size: 14px;
  margin: 8px 0 4px;
}

.time {
  color: #9ca3af;
  font-size: 12px;
}

.empty {
  color: #9ca3af;
  text-align: center;
  padding: 24px;
}
</style>
