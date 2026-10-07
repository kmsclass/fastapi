
import { useEffect, useRef, useState } from 'react'

export default function ChatInput({ onSend, onStop, isStreaming }) {
  
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto' 
    el.style.height = `${Math.min(el.scrollHeight, 200)}px` 
  }, [text])

  
  useEffect(() => {
    if (!isStreaming) textareaRef.current?.focus()
  }, [isStreaming])

  const submit = () => {
    if (!text.trim() || isStreaming) return
    onSend(text)
    setText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault() 
      submit()
    }
  }

  return (
    <footer className="input-bar">
      <div className="input-box">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요 (Enter 전송, Shift+Enter 줄바꿈)"
        />
        {isStreaming ? (
          <button className="btn btn-stop" onClick={onStop} title="중지">
            ■
          </button>
        ) : (
          <button className="btn" onClick={submit} disabled={!text.trim()} title="전송">
            ↑
          </button>
        )}
      </div>
      <p className="hint">AI 답변은 부정확할 수 있습니다. 중요한 정보는 꼭 확인하세요.</p>
    </footer>
  )
}
