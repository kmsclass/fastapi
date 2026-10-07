
export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')


export async function fetchHealth() {
  const res = await fetch(`${API_URL}/api/health`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}


export async function sendChat(messages) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}


export async function streamChat(messages, { onToken, onDone, signal }) {
  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal, // abort() 가 호출되면 연결을 끊음 → 서버도 생성을 멈춤
  })
  if (!res.ok) throw new Error(await readError(res))

  
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = '' 

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    
    const events = buffer.split('\n\n')
    buffer = events.pop() 

    for (const event of events) {
      const line = event.trim()
      if (!line.startsWith('data:')) continue

      const data = JSON.parse(line.slice('data:'.length).trim())
      if (data.type === 'token') onToken(data.content)
      else if (data.type === 'done') onDone?.(data)
      else if (data.type === 'error') throw new Error(data.message)
    }
  }
}

async function readError(res) {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    return JSON.stringify(body.detail ?? body)
  } catch {
    return `HTTP ${res.status} ${res.statusText}`
  }
}
