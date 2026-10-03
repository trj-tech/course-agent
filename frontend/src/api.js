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

export function login(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function fetchMe(token) {
  return request('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchMySchedule(token) {
  return request('/api/schedules/me', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchDocuments(token) {
  return request('/api/documents', { headers: { Authorization: `Bearer ${token}` } })
}

export function fetchPlans(token) {
  return request('/api/plans', { headers: { Authorization: `Bearer ${token}` } })
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

/** 流式聊天：POST /api/chat 并以 SSE 方式读取，逐条回调 onEvent({type,...}) */
export async function chatStream(message, token, onEvent) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
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
