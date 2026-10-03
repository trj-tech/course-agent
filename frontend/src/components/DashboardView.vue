<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchMyStats } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const stats = ref(null)
const error = ref('')

const TOOL_NAMES = {
  get_my_schedule: '查询课表',
  search_course_documents: '检索资料',
  list_my_documents: '列出资料',
  save_study_plan: '保存计划',
  get_upcoming_assignments: '查询作业',
  get_my_scores: '查询成绩',
}

const toolBars = computed(() => {
  const dist = stats.value?.tool_distribution || {}
  const entries = Object.entries(dist).sort((a, b) => b[1] - a[1])
  const max = Math.max(...entries.map(([, n]) => n), 1)
  return entries.map(([name, n]) => ({
    label: TOOL_NAMES[name] || name,
    count: n,
    pct: Math.round((n / max) * 100),
  }))
})

onMounted(async () => {
  try {
    stats.value = await fetchMyStats(props.token)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>学习数据</h2>
    <p class="tip">你的学习行为与 AI 助手使用情况统计</p>

    <template v-if="stats">
      <div class="stat-grid">
        <div class="stat">
          <div class="stat-num">{{ stats.messages }}</div>
          <div class="stat-label">累计对话消息</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ stats.conversations }}</div>
          <div class="stat-label">会话数</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ stats.tool_calls }}</div>
          <div class="stat-label">AI 工具调用次数</div>
        </div>
        <div class="stat">
          <div class="stat-num">
            {{ stats.avg_latency_ms ? `${(stats.avg_latency_ms / 1000).toFixed(1)}s` : '—' }}
          </div>
          <div class="stat-label">平均回答耗时</div>
        </div>
        <div class="stat">
          <div class="stat-num">
            {{ stats.avg_first_token_ms ? `${(stats.avg_first_token_ms / 1000).toFixed(1)}s` : '—' }}
          </div>
          <div class="stat-label">平均首字耗时</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ stats.documents }}</div>
          <div class="stat-label">课程资料</div>
        </div>
        <div class="stat">
          <div class="stat-num warn">{{ stats.pending_assignments }}</div>
          <div class="stat-label">待完成作业</div>
        </div>
        <div class="stat">
          <div class="stat-num">{{ stats.score_summary?.gpa ?? '—' }}</div>
          <div class="stat-label">GPA（4.0 制）</div>
        </div>
      </div>

      <div class="row">
        <div class="box">
          <h3>工具调用分布</h3>
          <div v-for="t in toolBars" :key="t.label" class="bar-row">
            <span class="bar-label">{{ t.label }}</span>
            <div class="bar-track">
              <div class="bar" :style="{ width: t.pct + '%' }"></div>
            </div>
            <span class="bar-count">{{ t.count }}</span>
          </div>
          <div v-if="!toolBars.length" class="empty">还没有工具调用记录，去和助手聊聊吧</div>
        </div>

        <div class="box">
          <h3>学习提醒</h3>
          <div class="remind">
            <div class="remind-item">
              <span class="remind-label">最近的作业截止</span>
              <span class="remind-value" :class="{ warn: stats.pending_assignments }">
                {{ stats.next_due_at || '暂无待办作业' }}
              </span>
            </div>
            <div class="remind-item">
              <span class="remind-label">最弱科目</span>
              <span class="remind-value">
                {{
                  stats.score_summary?.weakest
                    ? `${stats.score_summary.weakest.course_name}（${stats.score_summary.weakest.score} 分）`
                    : '—'
                }}
              </span>
            </div>
            <div class="remind-item">
              <span class="remind-label">课表课程</span>
              <span class="remind-value">{{ stats.schedules }} 门/周</span>
            </div>
            <div class="remind-item">
              <span class="remind-label">学习计划</span>
              <span class="remind-value">{{ stats.plans }} 份</span>
            </div>
          </div>
          <p class="tip" style="margin-top: 12px">
            在聊天里问「我最近有什么要交的作业」，助手会自动查询并帮你规划时间
          </p>
        </div>
      </div>
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

h3 {
  font-size: 14px;
  margin-bottom: 14px;
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

.stat-num.warn {
  color: #dc2626;
}

.stat-label {
  color: #6b7280;
  font-size: 12px;
  margin-top: 4px;
}

.row {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
}

.box {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.bar-label {
  width: 90px;
  font-size: 13px;
  color: #374151;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 12px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: #1890ff;
  border-radius: 999px;
}

.bar-count {
  width: 32px;
  text-align: right;
  font-size: 12px;
  color: #6b7280;
}

.remind-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}

.remind-item:last-of-type {
  border-bottom: none;
}

.remind-label {
  color: #6b7280;
}

.remind-value {
  color: #0f172a;
  font-weight: 500;
}

.remind-value.warn {
  color: #dc2626;
}

.empty {
  color: #9ca3af;
  font-size: 13px;
  padding: 12px 0;
}
</style>
