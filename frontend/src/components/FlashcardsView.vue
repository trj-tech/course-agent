<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteFlashcard, fetchDocuments, fetchFlashcards, generateFlashcards } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const cards = ref([])
const docs = ref([])
const error = ref('')
const docId = ref(null)
const count = ref(5)
const generating = ref(false)
const flipped = ref(new Set())

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
    ElMessage.success(`已生成 ${created.length} 张卡片`)
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
</script>

<template>
  <div class="panel">
    <p v-if="error" class="error">{{ error }}</p>
    <h2>AI 复习卡片</h2>
    <p class="tip">基于你上传的课程资料，由 AI 自动生成问答卡片。点击卡片查看答案</p>

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
            <div class="face-tag">问题</div>
            <div class="face-text">{{ c.question }}</div>
            <div v-if="c.filename" class="face-src">{{ c.filename }}</div>
          </div>
          <div class="face back">
            <div class="face-tag">答案</div>
            <div class="face-text">{{ c.answer }}</div>
          </div>
        </div>
        <el-button class="del" size="small" type="danger" plain @click.stop="remove(c.id)">删除</el-button>
      </div>
      <div v-if="!cards.length" class="empty">
        还没有卡片——选好资料后点「生成卡片」，AI 会基于你的课程资料出题
      </div>
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

.face-tag {
  font-size: 12px;
  color: #1890ff;
  margin-bottom: 8px;
}

.back .face-tag {
  color: #0958d9;
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
