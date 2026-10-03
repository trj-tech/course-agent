<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAdminSchedule,
  deleteAdminSchedule,
  fetchAdminCourses,
  fetchAdminSchedules,
  fetchAdminUsers,
  updateAdminSchedule,
} from '../../api'

const token = localStorage.getItem('token') || ''
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const filters = reactive({ username: '', weekday: null })
const loading = ref(false)

const users = ref([])
const courses = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = reactive({
  user_id: null,
  course_id: null,
  weekday: 1,
  start_period: 1,
  end_period: 2,
  week_start: 1,
  week_end: 16,
  location: '',
})

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

async function load() {
  loading.value = true
  try {
    const data = await fetchAdminSchedules(token, {
      username: filters.username,
      weekday: filters.weekday,
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
    user_id: null,
    course_id: null,
    weekday: 1,
    start_period: 1,
    end_period: 2,
    week_start: 1,
    week_end: 16,
    location: '',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    user_id: row.user_id,
    course_id: row.course_id,
    weekday: row.weekday,
    start_period: row.start_period,
    end_period: row.end_period,
    week_start: row.week_start,
    week_end: row.week_end,
    location: row.location ?? '',
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.user_id || !form.course_id) {
    ElMessage.warning('请选择学生与课程')
    return
  }
  try {
    if (editingId.value) {
      await updateAdminSchedule(token, editingId.value, { ...form })
    } else {
      await createAdminSchedule(token, { ...form })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } catch (e) {
    // 409 冲突后端已给出明确提示
    ElMessage.error(e.message)
  }
}

async function onDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除 ${row.username} 的「${row.course_name}」课表记录吗？`,
      '删除确认',
      { type: 'warning' },
    )
    await deleteAdminSchedule(token, row.id)
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
  <div>
    <h2 class="page-title">课表管理</h2>

    <div class="bar">
      <el-input
        v-model="filters.username"
        placeholder="按用户名筛选"
        clearable
        style="width: 180px"
        @keyup.enter="page = 1; load()"
        @clear="page = 1; load()"
      />
      <el-select v-model="filters.weekday" placeholder="按星期筛选" clearable style="width: 130px">
        <el-option v-for="(w, i) in WEEKDAYS" :key="i + 1" :label="w" :value="i + 1" />
      </el-select>
      <el-button type="primary" @click="page = 1; load()">查询</el-button>
      <el-button type="success" @click="openCreate">+ 新增课表</el-button>
      <span class="tip">同一学生同一天节次重叠会自动拦截（冲突检测）</span>
    </div>

    <el-table :data="list" v-loading="loading" border stripe class="table">
      <el-table-column prop="username" label="学生" width="100" />
      <el-table-column label="课程" min-width="150">
        <template #default="{ row }">{{ row.course_name }}（{{ row.course_code }}）</template>
      </el-table-column>
      <el-table-column label="星期" width="70">
        <template #default="{ row }">{{ WEEKDAYS[row.weekday - 1] }}</template>
      </el-table-column>
      <el-table-column label="节次" width="80">
        <template #default="{ row }">{{ row.start_period }}-{{ row.end_period }} 节</template>
      </el-table-column>
      <el-table-column label="周次" width="90">
        <template #default="{ row }">{{ row.week_start }}-{{ row.week_end }} 周</template>
      </el-table-column>
      <el-table-column prop="location" label="教室" width="130" />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑课表' : '新增课表'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="学生" required>
          <el-select v-model="form.user_id" filterable placeholder="选择学生" style="width: 100%">
            <el-option
              v-for="u in users.filter((x) => x.role === 'student')"
              :key="u.id"
              :label="`${u.username}（${u.name}）`"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select v-model="form.course_id" filterable placeholder="选择课程" style="width: 100%">
            <el-option v-for="c in courses" :key="c.id" :label="`${c.name}（${c.code}）`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期" required>
          <el-select v-model="form.weekday" style="width: 100%">
            <el-option v-for="(w, i) in WEEKDAYS" :key="i + 1" :label="w" :value="i + 1" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次范围">
          <el-row :gutter="8">
            <el-col :span="12">
              <el-input-number v-model="form.start_period" :min="1" :max="12" style="width: 100%" />
            </el-col>
            <el-col :span="12">
              <el-input-number v-model="form.end_period" :min="1" :max="12" style="width: 100%" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="周次范围">
          <el-row :gutter="8">
            <el-col :span="12">
              <el-input-number v-model="form.week_start" :min="1" :max="25" style="width: 100%" />
            </el-col>
            <el-col :span="12">
              <el-input-number v-model="form.week_end" :min="1" :max="25" style="width: 100%" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="教室">
          <el-input v-model="form.location" placeholder="如 教学楼A301" />
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
  flex-wrap: wrap;
}

.tip {
  color: #9ca3af;
  font-size: 12px;
}

.table {
  width: 100%;
}

.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
