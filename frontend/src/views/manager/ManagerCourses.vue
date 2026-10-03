<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAdminCourse, deleteAdminCourse, fetchAdminCourses, updateAdminCourse } from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const keyword = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ code: '', name: '', teacher: '', credit: null, semester: '', description: '' })

async function load() {
  loading.value = true
  try {
    list.value = await fetchAdminCourses(token, keyword.value)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { code: '', name: '', teacher: '', credit: null, semester: '', description: '' })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    code: row.code,
    name: row.name,
    teacher: row.teacher ?? '',
    credit: row.credit,
    semester: row.semester ?? '',
    description: row.description ?? '',
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.code || !form.name) {
    ElMessage.warning('课程代码与名称必填')
    return
  }
  try {
    if (editingId.value) {
      await updateAdminCourse(token, editingId.value, { ...form })
    } else {
      await createAdminCourse(token, { ...form })
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
    await ElMessageBox.confirm(`确定删除课程「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteAdminCourse(token, row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="panel">
    <h2 class="page-title">课程管理</h2>

    <div class="bar">
      <el-input
        v-model="keyword"
        placeholder="按课程名/代码/教师搜索"
        clearable
        style="width: 260px"
        @keyup.enter="load"
        @clear="load"
      />
      <el-button type="primary" @click="load">搜索</el-button>
      <el-button type="success" @click="openCreate">+ 新增课程</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe class="table">
      <el-table-column prop="code" label="课程代码" width="120" />
      <el-table-column prop="name" label="课程名称" min-width="160" />
      <el-table-column prop="teacher" label="教师" width="110" />
      <el-table-column prop="credit" label="学分" width="80" />
      <el-table-column prop="semester" label="学期" width="140" />
      <el-table-column prop="description" label="简介" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑课程' : '新增课程'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="课程代码" required>
          <el-input v-model="form.code" placeholder="如 CS101" />
        </el-form-item>
        <el-form-item label="课程名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="教师">
          <el-input v-model="form.teacher" />
        </el-form-item>
        <el-form-item label="学分">
          <el-input-number v-model="form.credit" :min="0" :max="10" :step="0.5" />
        </el-form-item>
        <el-form-item label="学期">
          <el-input v-model="form.semester" placeholder="如 2026-2027-1" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" />
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
.page-title {
  margin: 0;
  font-size: 17px;
}

.bar {
  display: flex;
  gap: 10px;
  margin: 14px 0;
  align-items: center;
}

.table {
  width: 100%;
}
</style>
