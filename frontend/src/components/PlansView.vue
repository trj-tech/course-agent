<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { addPlanItem, deletePlan, deletePlanItem, fetchPlan, fetchPlans, togglePlanItem, updatePlan } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const plans = ref([])
const error = ref('')
const detailVisible = ref(false)
const editVisible = ref(false)
const current = ref(null)
const form = reactive({ title: '', goal: '', content: '', status: 'active' })
const newItem = ref('')
const itemsLoading = ref(false)

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
  current.value = { ...p, items: p.items || [] }
  detailVisible.value = true
  if (!p.items) loadItems()
}

async function loadItems() {
  itemsLoading.value = true
  try {
    const detail = await fetchPlan(props.token, current.value.id)
    current.value = detail
    syncProgress(current.value)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    itemsLoading.value = false
  }
}

function syncProgress(detail) {
  const inList = plans.value.find((p) => p.id === detail.id)
  if (inList) inList.progress = detail.progress
}

async function onToggleItem(item, val) {
  const old = item.is_done
  item.is_done = val
  try {
    await togglePlanItem(props.token, current.value.id, item.id, val)
    const done = current.value.items.filter((i) => i.is_done).length
    current.value.progress = { done, total: current.value.items.length }
    syncProgress(current.value)
  } catch (e) {
    item.is_done = old
    ElMessage.error(e.message)
  }
}

async function onAddItem() {
  const title = newItem.value.trim()
  if (!title) return
  try {
    const it = await addPlanItem(props.token, current.value.id, title)
    current.value.items.push(it)
    current.value.progress = {
      done: current.value.items.filter((i) => i.is_done).length,
      total: current.value.items.length,
    }
    syncProgress(current.value)
    newItem.value = ''
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onRemoveItem(item) {
  try {
    await deletePlanItem(props.token, current.value.id, item.id)
    current.value.items = current.value.items.filter((i) => i.id !== item.id)
    current.value.progress = {
      done: current.value.items.filter((i) => i.is_done).length,
      total: current.value.items.length,
    }
    syncProgress(current.value)
  } catch (e) {
    ElMessage.error(e.message)
  }
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
        <div v-if="p.progress?.total" class="card-progress">
          <el-progress
            :percentage="Math.round((p.progress.done / p.progress.total) * 100)"
            :stroke-width="6"
            :show-text="false"
          />
          <span class="card-progress-text">{{ p.progress.done }}/{{ p.progress.total }} 条完成</span>
        </div>
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

        <div v-loading="itemsLoading" class="items-box">
          <div class="items-head">
            <strong>任务清单</strong>
            <span v-if="current.progress?.total" class="items-count">
              已完成 {{ current.progress.done }}/{{ current.progress.total }}
            </span>
          </div>
          <el-progress
            v-if="current.progress?.total"
            :percentage="Math.round((current.progress.done / current.progress.total) * 100)"
            :stroke-width="8"
          />
          <div v-if="current.items?.length" class="item-list">
            <div v-for="it in current.items" :key="it.id" class="item-row">
              <el-checkbox :model-value="it.is_done" @change="(v) => onToggleItem(it, v)">
                <span :class="{ done: it.is_done }">{{ it.title }}</span>
              </el-checkbox>
              <el-button link type="danger" size="small" @click="onRemoveItem(it)">移除</el-button>
            </div>
          </div>
          <p v-else class="items-empty">暂无任务条目，可在下方手动添加</p>
          <div class="item-add">
            <el-input
              v-model="newItem"
              size="small"
              placeholder="添加新任务，如：完成第4章课后习题"
              @keyup.enter="onAddItem"
            />
            <el-button size="small" type="primary" plain @click="onAddItem">添加</el-button>
          </div>
        </div>

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

.card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0 2px;
}

.card-progress :deep(.el-progress) {
  flex: 1;
}

.card-progress-text {
  color: #6b7280;
  font-size: 12px;
  white-space: nowrap;
}

.items-box {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  background: #f9fafb;
}

.items-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.items-count {
  color: #1890ff;
  font-size: 13px;
}

.item-list {
  margin: 8px 0;
}

.item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.item-row:last-child {
  border-bottom: none;
}

.item-row :deep(.done) {
  color: #9ca3af;
  text-decoration: line-through;
}

.items-empty {
  color: #9ca3af;
  font-size: 13px;
  margin: 8px 0;
}

.item-add {
  display: flex;
  gap: 8px;
  margin-top: 8px;
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
