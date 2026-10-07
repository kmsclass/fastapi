
import { useEffect, useState } from 'react'
import { fetchHealth } from '../api/chatApi'

export default function ChatHeader({ onReset, canReset }) {
  
  const [health, setHealth] = useState(null)

  
  useEffect(() => {
    let timer
    let cancelled = false 

    const check = async () => {
      let next
      try {
        next = await fetchHealth()
      } catch {
        next = { status: 'offline' }
      }
      if (cancelled) return
      setHealth(next)
      
      timer = setTimeout(check, next.status === 'ok' ? 30000 : 3000)
    }
    check()

    
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, []) 

  const status = health?.status ?? 'checking'
  const label = {
    checking: '연결 확인 중…',
    ok: `${health?.model} · ${health?.device}`,
    loading: '모델 로딩 중… (첫 실행은 다운로드로 수 분 걸릴 수 있어요)',
    offline: '서버에 연결할 수 없습니다 (백엔드 실행 확인)',
  }[status]

  return (
    <header className="header">
      <div className="header-title">
        <img src="/bot.svg" alt="" width="28" height="28" />
        <div>
          <h1>Qwen Chatbot</h1>
          <p className="status">
            <span className={`dot dot-${status}`} />
            {label}
          </p>
        </div>
      </div>
      <button className="btn-ghost" onClick={onReset} disabled={!canReset}>
        새 대화
      </button>
    </header>
  )
}
