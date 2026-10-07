// React 앱의 시작점(Entry point)
// index.html 의 <div id="root"> 안에 <App /> 컴포넌트를 그려 넣습니다.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css' // 전체 공통 스타일(색상 변수, 기본 글꼴 등)

createRoot(document.getElementById('root')).render(
  // StrictMode: 개발 중에만 잠재적인 문제를 찾아 경고해 주는 도우미 (배포 빌드에는 영향 없음)
  <StrictMode>
    <App />
  </StrictMode>,
)
