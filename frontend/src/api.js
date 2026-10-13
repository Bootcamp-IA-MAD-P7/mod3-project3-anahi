import { getToken } from './auth'

const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function authHeaders() {
  const token = await getToken()
  if (!token) {
    window.location.href = '/login'
    throw new Error('No token')
  }
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
}

export async function getMe() {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}/me`, { headers })
  if (res.status === 401) { window.location.href = '/login'; return null }
  return res.json()
}

export async function getModels() {
  const headers = await authHeaders()
  const res = await fetch(`${BASE}/models`, { headers })
  if (!res.ok) throw new Error('Failed to load models')
  return res.json()
}

export async function saveContext(userContext, isNew = false) {
  const headers = await authHeaders()
  const method = isNew ? 'POST' : 'PUT'
  const res = await fetch(`${BASE}/me/context`, {
    method,
    headers,
    body: JSON.stringify({ user_context: userContext }),
  })
  if (!res.ok) throw new Error('Failed to save context')
}

export async function streamGenerate(payload, onStatus, onResult, onError) {
  const headers = await authHeaders()
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 120000)

  try {
    const res = await fetch(`${BASE}/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    if (res.status === 401) { window.location.href = '/login'; return }
    if (!res.ok) { onError('Request failed — please try again'); return }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    function dispatchBlock(block) {
      let eventName = 'message'
      for (const line of block.split(/\r?\n/)) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim()
          continue
        }
        if (line.startsWith('data:')) {
          try {
            const data = JSON.parse(line.slice(5).trim())
            console.log('SSE event', eventName, data)
            if (eventName === 'status') onStatus(data.message)
            else if (eventName === 'result') onResult(data)
            else if (eventName === 'error') onError(data.message)
          } catch {
            console.log('SSE parse failed', line)
          }
        }
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split(/\r?\n\r?\n/)
      buffer = blocks.pop()
      for (const block of blocks) {
        dispatchBlock(block)
      }
    }
    if (buffer.trim()) dispatchBlock(buffer)
  } catch (err) {
    if (err.name === 'AbortError') {
      onError('Generation timed out — please try again')
    } else {
      onError('An unexpected error occurred')
    }
  } finally {
    clearTimeout(timeoutId)
  }
}
