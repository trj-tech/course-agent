<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAdminUser, deleteAdminUser, fetchAdminUsers, updateAdminUser } from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const filters = reactive({ keyword: '', role: '' })
const loading = ref(false)

const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({ username: '', password: '', name: '', role: 'student', student_no: '' })

async function load() {
  loading.value = true
  try {
    const data = await fetchAdminUsers(token, {
      keyword: filters.keyword,
      role: filters.role,
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

function openCreate() {
  editingId.value = null
  Object.assign(form, { username: '', password: '', name: '', role: 'student', student_no: '' })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    username: row.username,
    password: '',
    name: row.name,
    role: row.role,
    student_no: row.student_no ?? '',
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.username) {
    ElMessage.warning('用户名必填')
    return
  }
  if (!editingId.value && !form.password) {
    ElMessage.warning('新用户必须设置密码')
    return
  }
  try {
    if (editingId.value) {
      await updateAdminUser(token, editingId.value, { ...form, password: form.password || null })
    } else {
      await createAdminUser(token, { ...form })
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
    await ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '删除确认', { type: 'warning' })
    await deleteAdminUser(token, row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="page-title">用户管理</h2>

    <div class="bar">
      <el-input
        v-model="filters.keyword"
        placeholder="按用户名/姓名/学号搜索"
        clearable
        style="width: 220px"
        @keyup.enter="page = 1; load()"
        @clear="page = 1; load()"
      />
      <el-select v-model="filters.role" placeholder="按角色筛选" clearable style="width: 130px">
        <el-option label="学生" value="student" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-button type="primary" @click="page = 1; load()">查询</el-button>
      <el-button type="success" @click="openCreate">+ 新增用户</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe class="table">
      <el-table-column prop="username" label="用户名" width="130" />
      <el-table-column prop="name" label="姓名" width="130" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
            {{ row.role === 'admin' ? '管理员' : '学生' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="created_at" label="创建时间" min-width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="480px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item :label="editingId ? '重置密码' : '密码'" :required="!editingId">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId ? '留空则不修改' : '必填'"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="学生" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="form.student_no" />
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

.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
