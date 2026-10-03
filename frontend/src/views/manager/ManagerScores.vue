<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAdminScore, deleteAdminScore, fetchAdminCourses, fetchAdminScores, fetchAdminUsers } from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const filters = ref('')
const loading = ref(false)

const users = ref([])
const courses = ref([])
const dialogVisible = ref(false)
const editing = ref(false)
const form = ref({ username: '', course_code: '', score: null })

async function load() {
  loading.value = true
  try {
    list.value = await fetchAdminScores(token, filters.value)
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
  editing.value = false
  form.value = { username: '', course_code: '', score: null }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  form.value = { username: row.username, course_code: row.course_code, score: row.score }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.username || !form.value.course_code || form.value.score === null) {
    ElMessage.warning('请填写完整')
    return
  }
  try {
    await createAdminScore(token, { ...form.value })
    ElMessage.success(editing.value ? '成绩已更新' : '已保存（同一课程重复录入会覆盖原成绩）')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除 ${row.name} 的「${row.course_name}」成绩吗？`,
      '删除确认',
      { type: 'warning' },
    )
    await deleteAdminScore(token, row.id)
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
    <h2>成绩管理</h2>
    <p class="tip">录入学生百分制成绩，GPA 由系统按 4.0 标准换算（学生端与 AI 助手同步可见）</p>

    <div class="toolbar">
      <el-input
        v-model="filters"
        placeholder="按用户名筛选"
        clearable
        style="width: 180px"
        @change="load"
      />
      <el-button type="primary" @click="openCreate">录入成绩</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column label="学生" width="160">
        <template #default="{ row }">{{ row.name }}（{{ row.username }}）</template>
      </el-table-column>
      <el-table-column label="课程" min-width="160">
        <template #default="{ row }">{{ row.course_name }}（{{ row.course_code }}）</template>
      </el-table-column>
      <el-table-column label="成绩" width="120">
        <template #default="{ row }">
          <span :class="{ high: row.score >= 90, low: row.score < 80 }">{{ row.score }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" plain @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改成绩' : '录入成绩'" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="学生" required>
          <el-select v-model="form.username" filterable :disabled="editing" style="width: 100%">
            <el-option v-for="u in users" :key="u.id" :label="`${u.name}（${u.username}）`" :value="u.username" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select v-model="form.course_code" filterable :disabled="editing" style="width: 100%">
            <el-option v-for="c in courses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="成绩" required>
          <el-input-number v-model="form.score" :min="0" :max="100" :precision="1" style="width: 100%" />
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

.high {
  color: #16a34a;
  font-weight: 600;
}

.low {
  color: #dc2626;
  font-weight: 600;
}
</style>
