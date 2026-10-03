<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteAdminDocument,
  fetchAdminDocuments,
  previewAdminDocument,
  reindexAdminDocument,
  uploadDocument,
} from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const loading = ref(false)
const uploading = ref(false)
const previewVisible = ref(false)
const previewData = ref(null)

async function load() {
  loading.value = true
  try {
    const data = await fetchAdminDocuments(token, { page: page.value, page_size: pageSize.value })
    list.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function onUpload(file) {
  uploading.value = true
  try {
    await uploadDocument(token, file.raw || file)
    ElMessage.success('上传成功')
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
  }
  return false // 阻止 el-upload 默认行为
}

async function onReindex(row) {
  try {
    const r = await reindexAdminDocument(token, row.id)
    ElMessage.success(`重新入库完成（状态：${r.status}）`)
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onPreview(row) {
  try {
    previewData.value = await previewAdminDocument(token, row.id)
    previewVisible.value = true
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.filename}」吗？其向量切片也会一并清除。`, '删除确认', {
      type: 'warning',
    })
    await deleteAdminDocument(token, row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

function fmtSize(n) {
  if (!n) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

onMounted(load)
</script>

<template>
  <div class="panel">
    <h2 class="page-title">文档管理</h2>
    <p class="tip">
      支持 txt / md / pdf / docx，与课程无关，同名不可重复，扫描版 PDF 可能抽不出文字；多个文档请逐个入库。
    </p>

    <div class="upload-bar">
      <el-upload :show-file-list="false" :before-upload="onUpload" accept=".txt,.md,.pdf,.docx">
        <el-button type="primary" :loading="uploading">选择文件并上传入库</el-button>
      </el-upload>
    </div>

    <el-table :data="list" v-loading="loading" border stripe class="table">
      <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
      <el-table-column label="大小" width="100">
        <template #default="{ row }">{{ fmtSize(row.size) }}</template>
      </el-table-column>
      <el-table-column prop="file_type" label="类型" width="80" />
      <el-table-column label="已入库" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ready' ? 'success' : row.status === 'failed' ? 'danger' : 'info'" size="small">
            {{ row.status === 'ready' ? '是' : row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="上传用户" width="110" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="210" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="onPreview(row)">预览</el-button>
          <el-button size="small" type="warning" @click="onReindex(row)">重新入库</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="(p) => { page = p; load() }"
    />

    <el-dialog v-model="previewVisible" :title="previewData?.filename" width="640px">
      <pre class="preview">{{ previewData?.content }}</pre>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-title {
  margin: 0;
  font-size: 17px;
}

.tip {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 12px;
}

.upload-bar {
  margin-bottom: 14px;
}

.table {
  width: 100%;
}

.pager {
  margin-top: 14px;
  justify-content: flex-end;
}

.preview {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  max-height: 480px;
  overflow-y: auto;
  margin: 0;
}
</style>
