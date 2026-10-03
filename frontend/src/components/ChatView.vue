<script setup>
import { ref } from 'vue'
import { chatStream } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const messages = ref([])
const input = ref('')
const busy = ref(false)
const error = ref('')

async function send() {
  const text = input.value.trim()
  if (!text || busy.value) return
  error.value = ''
  messages.value.push({ role: 'user', content: text })
  const assistant = ref({ role: 'assistant', content: '', tools: [] })
  messages.value.push(assistant.value)
  input.value = ''
  busy.value = true

  const updateTool = (name, patch) => {
    const t = assistant.value.tools.find((x) => x.name === name)
    if (t) Object.assign(t, patch)
  }

  try {
    await chatStream(text, props.token, (ev) => {
      switch (ev.type) {
        case 'tool_start':
          assistant.value.tools.push({
            name: ev.name,
            input: JSON.stringify(ev.input ?? {}),
            output: '',
            status: '运行中',
          })
          break
        case 'tool_end':
          updateTool(ev.name, { output: String(ev.output ?? ''), status: '完成' })
          break
        case 'text':
          assistant.value.content += ev.delta
          break
        case 'error':
          error.value = ev.message
          break
        case 'done':
          break
      }
    })
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="chat">
    <div class="list">
      <div v-if="!messages.length" class="empty">
        <p>我是校园课程智能助手，可以帮你：</p>
        <ul>
          <li>查询课表：比如「我明天有什么课？」</li>
          <li>资料问答：比如「讲讲什么是装饰器」</li>
          <li>制定计划：比如「帮我制定下周的学习计划」</li>
        </ul>
      </div>

      <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
        <div class="bubble">
          <template v-if="m.role === 'user'">{{ m.content }}</template>
          <template v-else>
            <!-- 工具调用过程卡片 -->
            <div v-for="(t, ti) in m.tools" :key="ti" class="tool">
              <div class="tool-head">
                <span class="tool-name">🔧 {{ t.name }}</span>
                <span class="tool-status" :class="t.status === '完成' ? 'ok' : 'run'">{{ t.status }}</span>
              </div>
              <div class="tool-input">{{ t.input }}</div>
              <div v-if="t.output" class="tool-output">{{ t.output }}</div>
            </div>
            <div v-if="m.content" class="answer">{{ m.content }}</div>
            <div v-else-if="m.tools.length" class="thinking">正在组织回答…</div>
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
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 420px;
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

.empty ul {
  margin-top: 8px;
  text-align: left;
  list-style: none;
  padding: 0;
}

.empty li {
  margin: 4px 0;
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
  background: #16a34a;
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

.tool-input,
.tool-output {
  margin-top: 4px;
  color: #64748b;
  word-break: break-all;
  max-height: 120px;
  overflow: hidden;
}

.answer {
  margin-top: 2px;
}

.thinking {
  color: #9ca3af;
  font-size: 13px;
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
}

.row button {
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  background: #16a34a;
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
