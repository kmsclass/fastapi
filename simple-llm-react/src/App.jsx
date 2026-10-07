import { useChat } from './hooks/useChat'
import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import './App.css'

export default function App() {
  const { messages, isStreaming, send, stop, reset } = useChat()

  return (
    <div className="app">
      <ChatHeader onReset={reset} canReset={messages.length > 0} />
      <MessageList messages={messages} onSuggestion={send} />
      <ChatInput onSend={send} onStop={stop} isStreaming={isStreaming} />
    </div>
  )
}
