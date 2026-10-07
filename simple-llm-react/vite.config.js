// Vite 설정 파일
// Vite: React 코드를 브라우저에서 바로 실행할 수 있도록 변환/번들링해 주는 개발 도구
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  // JSX 문법 변환, 저장 시 화면 자동 갱신(Fast Refresh) 등을 지원하는 React 플러그인
  plugins: [react()],
  server: {
    port: 5173, // 개발 서버 포트 (백엔드 CORS_ORIGINS 설정과 일치해야 함)
    open: true, // npm run dev 실행 시 브라우저 자동 열기
  },
})
