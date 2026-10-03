<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  chatStream,
  createConversation,
  deleteConversation,
  fetchConversation,
  fetchConversations,
} from '../api'

const props = defineProps({
  token: { type: String, required: true },
  showHistory: { type: Boolean, default: false },
})

const messages = ref([])
const input = ref('')
const busy = ref(false)
const error = ref('')
const conversations = ref([])
const currentConvId = ref(null)

function fromHistory(m) {
  if (m.role === 'user') return { role: 'user', content: m.content }
  return {
    role: 'assistant',
    content: m.content,
    tools: (m.tool_calls || []).map((t) => ({
      name: t.name,
      status: '完成',
    })),
    sources: m.retrieval_sources || null,
    latency_ms: m.latency_ms,
    first_token_ms: m.first_token_ms,
  }
}

// 工具名映射为中文，卡片只显示名称与状态，不展示原始 JSON
const TOOL_LABELS = {
  get_my_schedule: '查询课表',
  search_course_documents: '检索课程资料',
  list_my_documents: '查询课程资料列表',
  save_study_plan: '保存学习计划',
}

// 助手回答按 Markdown 渲染（表格/加粗/列表），DOMPurify 防 XSS
function renderMd(text) {
  return DOMPurify.sanitize(marked.parse(text || '', { breaks: true }))
}

async function loadConversations() {
  if (!props.showHistory) return
  try {
    conversations.value = await fetchConversations(props.token)
  } catch {
    /* 忽略历史加载失败 */
  }
}

async function newConversation() {
  if (busy.value) return
  try {
    const conv = await createConversation(props.token)
    currentConvId.value = conv.id
    messages.value = []
    await loadConversations()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function openConversation(id) {
  if (busy.value) return
  try {
    const conv = await fetchConversation(props.token, id)
    currentConvId.value = conv.id
    messages.value = conv.messages.map(fromHistory)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function removeConversation(id) {
  try {
    await deleteConversation(props.token, id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
    await loadConversations()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

const SUGGESTIONS = [
  '我明天有什么课？',
  '我最近有什么作业要交？',
  '我的 GPA 多少，哪门最弱？',
  '帮我制定下周的学习计划',
]

async function doSend(text) {
  if (!text || busy.value) return
  error.value = ''
  messages.value.push({ role: 'user', content: text })
  const assistant = ref({ role: 'assistant', content: '', tools: [] })
  messages.value.push(assistant.value)
  busy.value = true

  const updateTool = (name, patch) => {
    const t = assistant.value.tools.find((x) => x.name === name)
    if (t) Object.assign(t, patch)
  }

  try {
    await chatStream(text, props.token, (ev) => {
      switch (ev.type) {
        case 'tool_start':
          assistant.value.tools.push({ name: ev.name, status: '运行中' })
          break
        case 'tool_end':
          updateTool(ev.name, { status: '完成' })
          break
        case 'text':
          assistant.value.content += ev.delta
          break
        case 'error':
          error.value = ev.message
          break
        case 'done':
          assistant.value.latency_ms = ev.latency_ms
          assistant.value.first_token_ms = ev.first_token_ms
          if (ev.conversation_id && currentConvId.value !== ev.conversation_id) {
            currentConvId.value = ev.conversation_id
            if (props.showHistory) loadConversations()
          }
          break
      }
    }, currentConvId.value)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
    if (props.showHistory) loadConversations()
  }
}

function send() {
  const text = input.value.trim()
  if (!text || busy.value) return
  input.value = ''
  doSend(text)
}

onMounted(() => {
  if (props.showHistory) loadConversations()
})
</script>

<template>
  <div class="chat" :class="{ withHistory: showHistory }">
    <!-- 会话历史侧栏 -->
    <aside v-if="showHistory" class="history">
      <el-button type="primary" class="new-btn" :disabled="busy" @click="newConversation">
        + 新对话
      </el-button>
      <div
        v-for="c in conversations"
        :key="c.id"
        class="conv"
        :class="{ active: currentConvId === c.id }"
        @click="openConversation(c.id)"
      >
        <div class="conv-title">{{ c.title }}</div>
        <div class="conv-meta">{{ c.msg_count }} 条消息</div>
        <el-button
          class="conv-del"
          size="small"
          text
          type="danger"
          @click.stop="removeConversation(c.id)"
        >
          删除
        </el-button>
      </div>
      <p v-if="!conversations.length" class="history-empty">暂无历史对话</p>
    </aside>

    <div class="main">
      <div class="list">
        <div v-if="!messages.length" class="empty">
          <p class="hello">你好，我是校园课程智能助手</p>
          <p class="sub">可以帮你查课表、盯作业、背卡片、答疑资料、做计划——点一个问题直接开始，或在下方输入</p>
          <div class="suggestions">
            <button v-for="s in SUGGESTIONS" :key="s" class="chip" @click="doSend(s)">
              {{ s }}
            </button>
          </div>
        </div>

        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble">
            <template v-if="m.role === 'user'">{{ m.content }}</template>
            <template v-else>
              <!-- 工具调用过程卡片（只显示中文名称与状态） -->
              <div v-for="(t, ti) in m.tools" :key="ti" class="tool">
                <div class="tool-head">
                  <span class="tool-name">🔧 {{ TOOL_LABELS[t.name] || t.name }}</span>
                  <span class="tool-status" :class="t.status === '完成' ? 'ok' : 'run'">{{ t.status }}</span>
                </div>
              </div>
              <!-- 检索溯源 -->
              <div v-if="m.sources && m.sources.length" class="sources">
                <div class="sources-title">📚 检索来源</div>
                <div v-for="(s, si) in m.sources" :key="si" class="source">
                  <span class="source-file">{{ s.filename }}</span>
                  <span class="source-score">相似度 {{ s.score }}</span>
                </div>
              </div>
              <div v-if="m.content" class="answer md" v-html="renderMd(m.content)"></div>
              <div v-else-if="m.tools.length" class="thinking">正在组织回答…</div>
              <div v-if="m.latency_ms" class="latency">
                <template v-if="m.first_token_ms">首字 {{ (m.first_token_ms / 1000).toFixed(1) }} 秒 · </template>总耗时 {{ (m.latency_ms / 1000).toFixed(1) }} 秒
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="composer">
        <p v-if="error" class="error">{{ error }}</p>
        <div class="row">
          <input
            v-model="input"
            placeholder="输入你的问题…"
            :disabled="busy"
            @keyup.enter="send"
          />
          <button :disabled="busy || !input.trim()" @click="send">
            {{ busy ? '思考中…' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  height: calc(100vh - 140px);
  min-height: 460px;
  gap: 14px;
}

.chat:not(.withHistory) {
  display: block;
  height: calc(100vh - 140px);
  min-height: 420px;
}

.history {
  width: 230px;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px;
  overflow-y: auto;
  background: #fff;
}

.new-btn {
  width: 100%;
  margin-bottom: 10px;
}

.conv {
  position: relative;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 6px;
  border: 1px solid transparent;
}

.conv:hover {
  background: #f3f4f6;
}

.conv.active {
  background: #ecf5ff;
  border-color: #409eff;
}

.conv-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  padding-right: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.conv-del {
  position: absolute;
  right: 2px;
  top: 2px;
}

.history-empty {
  color: #9ca3af;
  font-size: 12px;
  text-align: center;
  margin-top: 20px;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 4px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.empty {
  margin: auto;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
}

.empty .hello {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}

.empty .sub {
  margin-bottom: 16px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  max-width: 480px;
  margin: 0 auto;
}

.suggestions .chip {
  padding: 8px 16px;
  border: 1px solid #91caff;
  border-radius: 999px;
  background: #fff;
  color: #1890ff;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}

.suggestions .chip:hover {
  background: #e6f7ff;
  box-shadow: 0 1px 6px rgba(24, 144, 255, 0.2);
}

.msg {
  display: flex;
}

.msg.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .bubble {
  background: #409eff;
  color: #fff;
}

.msg.assistant .bubble {
  background: #fff;
  border: 1px solid #e5e7eb;
  width: 78%;
}

.tool {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
  font-size: 12px;
}

.tool-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-name {
  font-weight: 600;
  color: #0f172a;
}

.tool-status.ok {
  color: #16a34a;
}

.tool-status.run {
  color: #2563eb;
}

.sources {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
  font-size: 12px;
}

.sources-title {
  font-weight: 600;
  color: #92400e;
  margin-bottom: 4px;
}

.source {
  display: flex;
  justify-content: space-between;
  color: #78350f;
}

.source-score {
  color: #b45309;
}

.answer {
  margin-top: 2px;
}

/* Markdown 渲染样式：覆盖气泡的 pre-wrap，统一表格/列表观感 */
.md {
  white-space: normal;
  line-height: 1.7;
}

.md :deep(p) {
  margin: 6px 0;
}

.md :deep(p:first-child) {
  margin-top: 0;
}

.md :deep(p:last-child) {
  margin-bottom: 0;
}

.md :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
  display: block;
  overflow-x: auto;
}

.md :deep(th),
.md :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 6px 10px;
  text-align: left;
}

.md :deep(th) {
  background: #f9fafb;
  color: #4b5563;
  font-weight: 600;
}

.md :deep(ul),
.md :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.md :deep(li) {
  margin: 2px 0;
}

.md :deep(strong) {
  color: #0f172a;
}

.md :deep(code) {
  background: #f1f5f9;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 12px;
}

.thinking {
  color: #9ca3af;
  font-size: 13px;
}

.latency {
  color: #9ca3af;
  font-size: 11px;
  margin-top: 6px;
  text-align: right;
}

.composer {
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
}

.row {
  display: flex;
  gap: 8px;
}

.row input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.row button {
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  background: #409eff;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.row button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 8px;
}
</style>
