// 与后端交互的轻量封装

async function request(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = `请求失败（${res.status}）`
    try {
      const data = await res.json()
      if (data.detail) detail = data.detail
    } catch {
      /* 非 JSON 响应忽略 */
    }
    throw new Error(detail)
  }
  return res.json()
}

// ---------- 认证 ----------

export function login(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function register(payload) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchMe(token) {
  return request('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
}

// ---------- 学生端 ----------

export function fetchMySchedule(token) {
  return request('/api/schedules/me', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchDocuments(token) {
  return request('/api/documents', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchPlans(token) {
  return request('/api/plans', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchPlan(token, id) {
  return request(`/api/plans/${id}`, { headers: { Authorization: `Bearer ${token}` } })
}

export function updatePlan(token, id, payload) {
  return request(`/api/plans/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  })
}

export function deletePlan(token, id) {
  return request(`/api/plans/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function addPlanItem(token, planId, title) {
  return request(`/api/plans/${planId}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title }),
  })
}

export function togglePlanItem(token, planId, itemId, isDone) {
  return request(`/api/plans/${planId}/items/${itemId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ is_done: isDone }),
  })
}

export function deletePlanItem(token, planId, itemId) {
  return request(`/api/plans/${planId}/items/${itemId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function uploadDocument(token, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/documents/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (!res.ok) {
    let detail = '上传失败'
    try {
      detail = (await res.json()).detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

// ---------- 对话历史 ----------

export function fetchConversations(token) {
  return request('/api/conversations', { headers: { Authorization: `Bearer ${token}` } })
}

export function createConversation(token, title = '新对话') {
  return request('/api/conversations', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title }),
  })
}

export function fetchConversation(token, id) {
  return request(`/api/conversations/${id}`, { headers: { Authorization: `Bearer ${token}` } })
}

export function deleteConversation(token, id) {
  return request(`/api/conversations/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
}

// ---------- 管理端 ----------

function adminHeaders(token) {
  return { Authorization: `Bearer ${token}` }
}

export function fetchAdminStats(token) {
  return request('/api/admin/stats', { headers: adminHeaders(token) })
}

export function fetchAdminCourses(token, keyword = '') {
  return request(`/api/admin/courses?keyword=${encodeURIComponent(keyword)}`, {
    headers: adminHeaders(token),
  })
}

export function createAdminCourse(token, data) {
  return request('/api/admin/courses', {
    method: 'POST',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function updateAdminCourse(token, id, data) {
  return request(`/api/admin/courses/${id}`, {
    method: 'PUT',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function deleteAdminCourse(token, id) {
  return request(`/api/admin/courses/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

export function fetchAdminSchedules(token, params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) qs.set(k, v)
  })
  return request(`/api/admin/schedules?${qs.toString()}`, { headers: adminHeaders(token) })
}

export function createAdminSchedule(token, data) {
  return request('/api/admin/schedules', {
    method: 'POST',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function updateAdminSchedule(token, id, data) {
  return request(`/api/admin/schedules/${id}`, {
    method: 'PUT',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function deleteAdminSchedule(token, id) {
  return request(`/api/admin/schedules/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

export function fetchAdminUsers(token, params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) qs.set(k, v)
  })
  return request(`/api/admin/users?${qs.toString()}`, { headers: adminHeaders(token) })
}

export function createAdminUser(token, data) {
  return request('/api/admin/users', {
    method: 'POST',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function updateAdminUser(token, id, data) {
  return request(`/api/admin/users/${id}`, {
    method: 'PUT',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function deleteAdminUser(token, id) {
  return request(`/api/admin/users/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

export function fetchAdminDocuments(token, params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) qs.set(k, v)
  })
  return request(`/api/admin/documents?${qs.toString()}`, { headers: adminHeaders(token) })
}

export function deleteAdminDocument(token, id) {
  return request(`/api/admin/documents/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

export function reindexAdminDocument(token, id) {
  return request(`/api/admin/documents/${id}/reindex`, {
    method: 'POST',
    headers: adminHeaders(token),
  })
}

export function previewAdminDocument(token, id) {
  return request(`/api/admin/documents/${id}/preview`, { headers: adminHeaders(token) })
}

// ---------- 作业 / 成绩 / 统计 ----------

export function fetchMyAssignments(token) {
  return request('/api/assignments', { headers: { Authorization: `Bearer ${token}` } })
}

export function setAssignmentStatus(token, id, status) {
  return request(`/api/assignments/${id}/status`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ status }),
  })
}

export function fetchMyScores(token) {
  return request('/api/scores/me', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchMyStats(token) {
  return request('/api/stats/me', { headers: { Authorization: `Bearer ${token}` } })
}

// ---------- 复习卡片 ----------

export function fetchFlashcards(token) {
  return request('/api/flashcards', { headers: { Authorization: `Bearer ${token}` } })
}

export function generateFlashcards(token, payload) {
  return request('/api/flashcards/generate', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  })
}

export function deleteFlashcard(token, id) {
  return request(`/api/flashcards/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
}

// ---------- 管理端：作业 / 成绩 ----------

export function fetchAdminAssignments(token, params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) qs.set(k, v)
  })
  return request(`/api/admin/assignments?${qs.toString()}`, { headers: adminHeaders(token) })
}

export function createAdminAssignment(token, data) {
  return request('/api/admin/assignments', {
    method: 'POST',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function updateAdminAssignment(token, id, data) {
  return request(`/api/admin/assignments/${id}`, {
    method: 'PUT',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function deleteAdminAssignment(token, id) {
  return request(`/api/admin/assignments/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

export function fetchAdminScores(token, username = '') {
  return request(`/api/admin/scores?username=${encodeURIComponent(username)}`, {
    headers: adminHeaders(token),
  })
}

export function createAdminScore(token, data) {
  return request('/api/admin/scores', {
    method: 'POST',
    headers: adminHeaders(token),
    body: JSON.stringify(data),
  })
}

export function deleteAdminScore(token, id) {
  return request(`/api/admin/scores/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(token),
  })
}

/** 流式聊天：POST /api/chat 并以 SSE 方式读取，逐条回调 onEvent({type,...}) */
export async function chatStream(message, token, onEvent, conversationId = null) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  })
  if (!res.ok || !res.body) {
    throw new Error(`请求失败（${res.status}）`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      try {
        onEvent(JSON.parse(line.slice(6)))
      } catch {
        /* 忽略坏帧 */
      }
    }
  }
}
