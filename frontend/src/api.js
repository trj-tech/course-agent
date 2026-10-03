// 与后端交互的轻量封装，后续可扩展统一错误处理

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
  return request('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function fetchMySchedule(token) {
  return request('/api/schedules/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
}
