
import { useEffect, useRef } from 'react'
import MessageItem from './MessageItem'

const SUGGESTIONS = [
  'FastAPI가 무엇인지 간단히 설명해줘',
  '파이썬으로 리스트를 정렬하는 방법 알려줘',
  'React의 useState를 예제와 함께 설명해줘',
  '오늘 저녁 메뉴 추천해줘',
]

export default function MessageList({ messages, onSuggestion }) {
  const bottomRef = useRef(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <main className="messages empty">
        <div className="welcome">
          <h2>무엇을 도와드릴까요?</h2>
          <p>Hugging Face의 Qwen 모델이 내 컴퓨터에서 직접 답변합니다.</p>
          <div className="suggestions">
            {SUGGESTIONS.map((q) => (
              <button key={q} className="suggestion" onClick={() => onSuggestion(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="messages">
      {messages.map((m) => (
        <MessageItem key={m.id} message={m} />
      ))}
      <div ref={bottomRef} />
    </main>
  )
}
