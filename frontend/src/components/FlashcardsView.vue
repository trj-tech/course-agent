<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteFlashcard, fetchDocuments, fetchFlashcards, generateFlashcards, reviewFlashcard } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const cards = ref([])
const docs = ref([])
const error = ref('')
const docId = ref(null)
const count = ref(5)
const generating = ref(false)
const flipped = ref(new Set())

// 复习模式状态
const reviewMode = ref(false)
const reviewQueue = ref([]) // 本次待复习卡片 id 列表
const reviewIdx = ref(0)
const reviewFlipped = ref(false)
const sessionStats = ref({ known: 0, fuzzy: 0, unknown: 0 })
const answering = ref(false)

const RESULT_META = {
  known: { label: '认识', next: '间隔拉长，升入下一记忆周期' },
  fuzzy: { label: '模糊', next: '明天再看一次' },
  unknown: { label: '不会', next: '回到第 1 周期，今天再见' },
}

const dueCards = computed(() => cards.value.filter((c) => c.is_due))
const masteredCount = computed(() => cards.value.filter((c) => c.mastered).length)
const currentReviewCard = computed(() =>
  reviewQueue.value.length ? cards.value.find((c) => c.id === reviewQueue.value[reviewIdx.value]) : null
)

async function load() {
  try {
    cards.value = await fetchFlashcards(props.token)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  load()
  try {
    docs.value = await fetchDocuments(props.token)
  } catch {
    /* 文档列表加载失败不阻塞页面 */
  }
})

function toggleFlip(id) {
  const next = new Set(flipped.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  flipped.value = next
}

async function generate() {
  generating.value = true
  try {
    const created = await generateFlashcards(props.token, {
      document_id: docId.value,
      count: count.value,
    })
    ElMessage.success(`已生成 ${created.length} 张卡片，已进入今日复习队列`)
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generating.value = false
  }
}

async function remove(id) {
  try {
    await ElMessageBox.confirm('确定删除这张卡片吗？', '删除确认', { type: 'warning' })
    await deleteFlashcard(props.token, id)
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

function startReview() {
  if (!dueCards.value.length) {
    ElMessage.info('今天没有待复习的卡片')
    return
  }
  reviewQueue.value = dueCards.value.map((c) => c.id)
  reviewIdx.value = 0
  reviewFlipped.value = false
  sessionStats.value = { known: 0, fuzzy: 0, unknown: 0 }
  reviewMode.value = true
}

async function answer(result) {
  const card = currentReviewCard.value
  if (!card || answering.value) return
  answering.value = true
  try {
    const updated = await reviewFlashcard(props.token, card.id, result)
    Object.assign(card, updated)
    sessionStats.value[result] += 1
    if (reviewIdx.value < reviewQueue.value.length - 1) {
      reviewIdx.value += 1
      reviewFlipped.value = false
    } else {
      const s = sessionStats.value
      ElMessage.success(
        `本轮复习完成：认识 ${s.known} · 模糊 ${s.fuzzy} · 不会 ${s.unknown}`
      )
      reviewMode.value = false
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    answering.value = false
  }
}

function exitReview() {
  reviewMode.value = false
  load()
}

function boxLabel(c) {
  return c.mastered ? '已掌握' : `记忆周期 ${c.box}/6`
}

function dueLabel(c) {
  if (c.mastered) return null
  if (c.is_due) return '今日待复习'
  return `下次 ${c.due_date?.slice(5)}`
}
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>AI 复习卡片</h2>
    <p class="tip">基于你上传的课程资料生成问答卡。按记忆规律安排复习：认识升周期（1→2→4→7→15→30 天），不会回到第 1 周期</p>

    <!-- 复习模式：逐张过卡 -->
    <div v-if="reviewMode && currentReviewCard" class="review-box">
      <div class="review-head">
        <span class="review-progress">{{ reviewIdx + 1 }} / {{ reviewQueue.length }}</span>
        <span class="review-session">本轮：认识 {{ sessionStats.known }} · 模糊 {{ sessionStats.fuzzy }} · 不会 {{ sessionStats.unknown }}</span>
        <el-button link size="small" @click="exitReview">结束复习</el-button>
      </div>
      <div
        class="card review-card"
        :class="{ flipped: reviewFlipped }"
        @click="reviewFlipped = !reviewFlipped"
      >
        <div class="card-inner">
          <div class="face front">
            <div class="face-tag">问题</div>
            <div class="face-text">{{ currentReviewCard.question }}</div>
            <div class="review-hint">{{ reviewFlipped ? '' : '点击卡片查看答案' }}</div>
          </div>
          <div class="face back">
            <div class="face-tag">答案</div>
            <div class="face-text">{{ currentReviewCard.answer }}</div>
          </div>
        </div>
      </div>
      <div class="review-actions">
        <template v-if="reviewFlipped">
          <el-button type="danger" plain :disabled="answering" @click="answer('unknown')">
            不会
          </el-button>
          <el-button type="warning" plain :disabled="answering" @click="answer('fuzzy')">
            模糊
          </el-button>
          <el-button type="primary" :disabled="answering" @click="answer('known')">
            认识
          </el-button>
        </template>
        <p v-else class="review-tip">先回忆，再翻面对照答案打分</p>
      </div>
    </div>

    <template v-else>
      <div class="stat-bar">
        <div class="stat">
          <strong :class="{ alert: dueCards.length }">{{ dueCards.length }}</strong>
          <span>今日待复习</span>
        </div>
        <div class="stat">
          <strong>{{ masteredCount }}</strong>
          <span>已掌握</span>
        </div>
        <div class="stat">
          <strong>{{ cards.length }}</strong>
          <span>卡片总数</span>
        </div>
        <el-button
          type="primary"
          :disabled="!dueCards.length"
          class="start-btn"
          @click="startReview"
        >
          开始复习{{ dueCards.length ? `（${dueCards.length} 张）` : '' }}
        </el-button>
      </div>

      <div class="gen-bar">
        <el-select v-model="docId" placeholder="全部资料" size="default" style="width: 260px" clearable>
          <el-option v-for="d in docs" :key="d.id" :label="d.filename" :value="d.id" />
        </el-select>
        <el-select v-model="count" style="width: 110px">
          <el-option :value="3" label="3 张" />
          <el-option :value="5" label="5 张" />
          <el-option :value="8" label="8 张" />
          <el-option :value="10" label="10 张" />
        </el-select>
        <el-button type="primary" :loading="generating" @click="generate">
          {{ generating ? 'AI 生成中…' : '生成卡片' }}
        </el-button>
      </div>

      <div class="cards">
        <div
          v-for="c in cards"
          :key="c.id"
          class="card"
          :class="{ flipped: flipped.has(c.id) }"
          @click="toggleFlip(c.id)"
        >
          <div class="card-inner">
            <div class="face front">
              <div class="face-top">
                <span class="face-tag">问题</span>
                <span class="mem-badge" :class="{ master: c.mastered, due: c.is_due }">
                  {{ boxLabel(c) }}<template v-if="dueLabel(c)"> · {{ dueLabel(c) }}</template>
                </span>
              </div>
              <div class="face-text">{{ c.question }}</div>
              <div v-if="c.filename" class="face-src">{{ c.filename }}</div>
            </div>
            <div class="face back">
              <div class="face-tag">答案</div>
              <div class="face-text">{{ c.answer }}</div>
              <div class="face-src">已复习 {{ c.review_count }} 次</div>
            </div>
          </div>
          <el-button class="del" size="small" type="danger" plain @click.stop="remove(c.id)">删除</el-button>
        </div>
        <div v-if="!cards.length" class="empty">
          还没有卡片——选好资料后点「生成卡片」，AI 会基于你的课程资料出题
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

.tip {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 12px;
}

/* 统计栏 */
.stat-bar {
  display: flex;
  align-items: center;
  gap: 28px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 18px;
  margin-bottom: 14px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat strong {
  font-size: 20px;
  color: #1890ff;
}

.stat strong.alert {
  color: #fa8c16;
}

.stat span {
  font-size: 12px;
  color: #6b7280;
}

.start-btn {
  margin-left: auto;
}

/* 复习模式 */
.review-box {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.review-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #6b7280;
}

.review-progress {
  font-weight: 600;
  color: #1890ff;
}

.review-session {
  flex: 1;
}

.review-card {
  height: 240px;
}

.review-hint {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

.review-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
}

.review-tip {
  color: #9ca3af;
  font-size: 13px;
  margin: 0;
}

/* 卡片网格 */
.gen-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.card {
  position: relative;
  height: 190px;
  perspective: 1000px;
  cursor: pointer;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.5s;
  transform-style: preserve-3d;
}

.card.flipped .card-inner {
  transform: rotateY(180deg);
}

.face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.face.back {
  transform: rotateY(180deg);
  background: #e6f7ff;
  border-color: #91caff;
}

.face-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.face-tag {
  font-size: 12px;
  color: #1890ff;
}

.back .face-tag {
  color: #0958d9;
}

.mem-badge {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  background: #f5f5f5;
  color: #8c8c8c;
  white-space: nowrap;
}

.mem-badge.due {
  background: #fff7e6;
  color: #fa8c16;
}

.mem-badge.master {
  background: #f0fdf4;
  color: #16a34a;
}

.face-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.7;
  overflow-y: auto;
}

.face-src {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 6px;
}

.del {
  position: absolute;
  right: 10px;
  bottom: 10px;
  z-index: 2;
}

.empty {
  grid-column: 1 / -1;
  color: #9ca3af;
  text-align: center;
  padding: 40px;
}
</style>
