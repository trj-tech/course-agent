<script setup>
import { onMounted, ref } from 'vue'
import { fetchDocuments, uploadDocument } from '../api'

const props = defineProps({ token: { type: String, required: true } })

const docs = ref([])
const file = ref(null)
const uploading = ref(false)
const error = ref('')

async function load() {
  try {
    docs.value = await fetchDocuments(props.token)
  } catch (e) {
    error.value = e.message
  }
}

function onPick(e) {
  file.value = e.target.files?.[0] || null
}

async function handleUpload() {
  if (!file.value || uploading.value) return
  error.value = ''
  uploading.value = true
  try {
    await uploadDocument(props.token, file.value)
    file.value = null
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="panel">
    <h2>课程资料</h2>
    <p class="tip">上传后自动切片并向量化，聊天时即可按资料作答（支持 pdf / docx / txt / md）</p>

    <div class="upload">
      <input type="file" :accept="'.pdf,.docx,.txt,.md'" @change="onPick" />
      <button :disabled="!file || uploading" @click="handleUpload">
        {{ uploading ? '处理中…' : '上传' }}
      </button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>

    <table>
      <thead>
        <tr>
          <th>文件名</th>
          <th>类型</th>
          <th>状态</th>
          <th>上传时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in docs" :key="d.id">
          <td>{{ d.filename }}</td>
          <td>{{ d.file_type }}</td>
          <td>
            <span class="status" :class="d.status">{{ d.status }}</span>
          </td>
          <td>{{ d.created_at }}</td>
        </tr>
        <tr v-if="!docs.length">
          <td colspan="4" class="empty">还没有上传资料</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
h2 {
  font-size: 16px;
}

.tip {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 12px;
}

.upload {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.upload button {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  background: #16a34a;
  color: #fff;
  cursor: pointer;
}

.upload button:disabled {
  opacity: 0.6;
}

.error {
  color: #dc2626;
  font-size: 13px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  font-size: 14px;
  margin-top: 12px;
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

.status {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.status.ready {
  background: #f0fdf4;
  color: #16a34a;
}

.status.failed {
  background: #fef2f2;
  color: #dc2626;
}

.status.pending,
.status.processing {
  background: #eff6ff;
  color: #2563eb;
}

.empty {
  text-align: center;
  color: #9ca3af;
}
</style>
