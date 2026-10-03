<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAdminAssignment,
  deleteAdminAssignment,
  fetchAdminAssignments,
  fetchAdminCourses,
  fetchAdminUsers,
  updateAdminAssignment,
} from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const filters = reactive({ username: '', status: '' })
const loading = ref(false)

const users = ref([])
const courses = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({
  username: '',
  course_code: '',
  title: '',
  description: '',
  due_at: '',
  status: 'pending',
})

async function load() {
  loading.value = true
  try {
    const data = await fetchAdminAssignments(token, {
      username: filters.username,
      status: filters.status,
      page: page.value,
      page_size: pageSize.value,
    })
    list.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [u, c] = await Promise.all([
      fetchAdminUsers(token, { page_size: 1000 }),
      fetchAdminCourses(token),
    ])
    users.value = u.items
    courses.value = c
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    username: '',
    course_code: '',
    title: '',
    description: '',
    due_at: '',
    status: 'pending',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    username: row.username,
    course_code: row.course_code || '',
    title: row.title,
    description: row.description || '',
    due_at: (row.due_at || '').slice(0, 16),
    status: row.status,
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.username || !form.title || !form.due_at) {
    ElMessage.warning('请填写学生、标题与截止时间')
    return
  }
  try {
    if (editingId.value) {
      await updateAdminAssignment(token, editingId.value, { ...form })
    } else {
      await createAdminAssignment(token, { ...form })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除作业「${row.title}」吗？`, '删除确认', { type: 'warning' })
    await deleteAdminAssignment(token, row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(() => {
  load()
  loadOptions()
})
</script>

<template>
  <div class="page">
    <h2>作业管理</h2>
    <p class="tip">发布与管理学生的作业及截止日期（学生端与 AI 助手同步可见）</p>

    <div class="toolbar">
      <el-input
        v-model="filters.username"
        placeholder="按用户名筛选"
        clearable
        style="width: 180px"
        @change="page = 1; load()"
      />
      <el-select
        v-model="filters.status"
        placeholder="状态"
        clearable
        style="width: 130px"
        @change="page = 1; load()"
      >
        <el-option label="未完成" value="pending" />
        <el-option label="已完成" value="done" />
      </el-select>
      <el-button type="primary" @click="openCreate">发布作业</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column label="学生" width="140">
        <template #default="{ row }">{{ row.name }}（{{ row.username }}）</template>
      </el-table-column>
      <el-table-column label="课程" width="150">
        <template #default="{ row }">
          {{ row.course_name ? `${row.course_name}` : '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="due_at" label="截止时间" width="170" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'done' ? 'success' : 'warning'" size="small">
            {{ row.status === 'done' ? '已完成' : '未完成' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top: 14px; justify-content: flex-end"
      @current-change="load"
    />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑作业' : '发布作业'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="form.username" filterable style="width: 100%">
            <el-option v-for="u in users" :key="u.id" :label="`${u.name}（${u.username}）`" :value="u.username" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联课程">
          <el-select v-model="form.course_code" filterable clearable style="width: 100%">
            <el-option v-for="c in courses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="截止时间" required>
          <el-input v-model="form.due_at" placeholder="2026-10-10T23:59" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="未完成" value="pending" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
h2 {
  font-size: 16px;
  margin-bottom: 4px;
}

.tip {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 14px;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}
</style>
