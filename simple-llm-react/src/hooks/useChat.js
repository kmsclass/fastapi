import { useCallback, useRef, useState } from 'react'
import { streamChat } from '../api/chatApi'

let nextId = 1
const makeMessage = (role, content, extra = {}) => ({ id: nextId++, role, content, ...extra })

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)

  const abortRef = useRef(null)

  const updateMessage = (id, updater) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? updater(m) : m)))
  }

  const send = useCallback(
    async (text) => {
      const content = text.trim()
      if (!content || isStreaming) return
      const userMsg = makeMessage('user', content)
      const botMsg = makeMessage('assistant', '', { pending: true })

      const history = [...messages, userMsg]
        .filter((m) => !m.error && m.content)
        .map(({ role, content }) => ({ role, content }))

      setMessages((prev) => [...prev, userMsg, botMsg])
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        await streamChat(history, {
          signal: controller.signal,
          onToken: (piece) =>
            updateMessage(botMsg.id, (m) => ({ ...m, content: m.content + piece, pending: false })),
          onDone: ({ elapsed }) => updateMessage(botMsg.id, (m) => ({ ...m, elapsed })),
        })
      } catch (err) {
        if (err.name === 'AbortError') {
          updateMessage(botMsg.id, (m) => ({ ...m, stopped: true }))
        } else {
          updateMessage(botMsg.id, (m) => ({
            ...m,
            error: true,
            content: `⚠️ 오류가 발생했습니다: ${err.message}`,
          }))
        }
      } finally {
        updateMessage(botMsg.id, (m) => ({ ...m, pending: false }))
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [messages, isStreaming],
  )
  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
  }, [])

  return { messages, isStreaming, send, stop, reset }
}
