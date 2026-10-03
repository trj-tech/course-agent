<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { deletePlan, fetchPlans, updatePlan } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const plans = ref([])
const error = ref('')
const detailVisible = ref(false)
const editVisible = ref(false)
const current = ref(null)
const form = reactive({ title: '', goal: '', content: '', status: 'active' })

const STATUS_LABEL = { active: '进行中', done: '已完成' }

function renderMd(text) {
  return DOMPurify.sanitize(marked.parse(text || '', { breaks: true }))
}

async function load() {
  try {
    plans.value = await fetchPlans(props.token)
  } catch (e) {
    error.value = e.message
  }
}

function openDetail(p) {
  current.value = p
  detailVisible.value = true
}

function openEdit() {
  Object.assign(form, {
    title: current.value.title,
    goal: current.value.goal || '',
    content: current.value.content || '',
    status: current.value.status || 'active',
  })
  detailVisible.value = false
  editVisible.value = true
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('标题必填')
    return
  }
  try {
    await updatePlan(props.token, current.value.id, { ...form })
    ElMessage.success('已保存')
    editVisible.value = false
    await load()
    current.value = plans.value.find((p) => p.id === current.value.id) || current.value
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remove() {
  try {
    await ElMessageBox.confirm(`确定删除计划「${current.value.title}」吗？`, '删除确认', {
      type: 'warning',
    })
    await deletePlan(props.token, current.value.id)
    ElMessage.success('已删除')
    detailVisible.value = false
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>我的学习计划（{{ plans.length }}）</h2>
    <p class="tip">在聊天里让助手「制定学习计划」即可自动生成并保存；点击卡片查看完整内容</p>

    <div class="cards">
      <div v-for="p in plans" :key="p.id" class="plan" @click="openDetail(p)">
        <div class="plan-head">
          <strong>{{ p.title }}</strong>
          <span class="status" :class="p.status">{{ STATUS_LABEL[p.status] || p.status }}</span>
        </div>
        <p v-if="p.goal" class="goal">目标：{{ p.goal }}</p>
        <p class="time">{{ p.created_at }}</p>
      </div>
      <div v-if="!plans.length" class="empty">还没有学习计划</div>
    </div>

    <!-- 完整内容查看 -->
    <el-dialog v-model="detailVisible" :title="current?.title" width="640px">
      <template v-if="current">
        <div class="detail-meta">
          <el-tag :type="current.status === 'done' ? 'success' : 'primary'" size="small">
            {{ STATUS_LABEL[current.status] || current.status }}
          </el-tag>
          <span class="detail-time">{{ current.created_at }}</span>
        </div>
        <p v-if="current.goal" class="detail-goal">目标：{{ current.goal }}</p>
        <div class="detail-content md-body" v-html="renderMd(current.content)"></div>
      </template>
      <template #footer>
        <el-button type="danger" plain @click="remove">删除</el-button>
        <el-button type="primary" @click="openEdit">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 编辑 -->
    <el-dialog v-model="editVisible" title="编辑学习计划" width="560px">
      <el-form :model="form" label-width="60px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="目标">
          <el-input v-model="form.goal" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="14" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
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
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
}

.plan:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 12px rgba(24, 144, 255, 0.12);
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

.status.active {
  background: #e6f7ff;
  color: #1890ff;
}

.status.done {
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

.detail-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.detail-time {
  color: #9ca3af;
  font-size: 12px;
}

.detail-goal {
  color: #374151;
  font-size: 14px;
  margin: 0 0 10px;
}

.detail-content {
  max-height: 55vh;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
}

/* 对话框内 Markdown 渲染样式 */
.md-body :deep(h1),
.md-body :deep(h2),
.md-body :deep(h3) {
  font-size: 15px;
  margin: 12px 0 6px;
}

.md-body :deep(p) {
  margin: 6px 0;
}

.md-body :deep(ul),
.md-body :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.md-body :deep(li) {
  margin: 3px 0;
}

.md-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
}

.md-body :deep(th),
.md-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 6px 10px;
  text-align: left;
}

.md-body :deep(th) {
  background: #f9fafb;
}

.md-body :deep(strong) {
  color: #0f172a;
}
</style>
