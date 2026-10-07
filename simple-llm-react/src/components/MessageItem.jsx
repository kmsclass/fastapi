
export default function MessageItem({ message }) {
  const { role, content, pending, elapsed, stopped, error } = message
  const isUser = role === 'user'

  return (
    <div className={`row ${isUser ? 'row-user' : 'row-bot'}`}>
      {!isUser && <img className="avatar" src="/bot.svg" alt="bot" />}

      <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-bot'} ${error ? 'bubble-error' : ''}`}>
        {pending && !content ? (
         <span className="typing" aria-label="답변 생성 중">
            <i />
            <i />
            <i />
          </span>
        ) : (
          <p className="content">{content}</p>
        )}
        {!isUser && (elapsed || stopped) && (
          <div className="meta">{stopped ? '⏹ 중지됨' : `${elapsed}초`}</div>
        )}
      </div>
    </div>
  )
}
