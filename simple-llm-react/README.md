# 💬 chatbot-react — Qwen 챗봇 프론트엔드

[`chatbot`](../chatbot) FastAPI 백엔드와 대화하는 **React 채팅 화면**입니다.
ChatGPT처럼 답변이 한 글자씩 실시간으로 표시되고, 생성 중지와 새 대화 기능이 있습니다.

```
┌─────────────────────────────────────────────┐
│ 🤖 Qwen Chatbot                   [새 대화]  │  ← ChatHeader (● 모델 상태 표시)
│ ● Qwen/Qwen2.5-1.5B-Instruct · cpu          │
├─────────────────────────────────────────────┤
│                         ┌─────────────────┐ │
│                         │ FastAPI가 뭐야?  │ │  ← 사용자 말풍선 (오른쪽)
│                         └─────────────────┘ │
│ 🤖 ┌──────────────────────────────┐         │
│    │ FastAPI는 파이썬으로 빠르게… ▌ │         │  ← 챗봇 말풍선 (실시간으로 늘어남)
│    └──────────────────────────────┘         │
├─────────────────────────────────────────────┤
│ ┌───────────────────────────────────┬────┐  │
│ │ 메시지를 입력하세요                  │ ■  │  │  ← ChatInput (생성 중에는 중지 버튼)
│ └───────────────────────────────────┴────┘  │
└─────────────────────────────────────────────┘
```

---

## 목차

1. [주요 기능](#1-주요-기능)
2. [기술 스택](#2-기술-스택)
3. [폴더 구조](#3-폴더-구조)
4. [설치 및 실행](#4-설치-및-실행)
5. [환경 설정 (.env)](#5-환경-설정-env)
6. [컴포넌트 구조와 데이터 흐름](#6-컴포넌트-구조와-데이터-흐름)
7. [핵심 코드 설명](#7-핵심-코드-설명)
8. [빌드 및 배포](#8-빌드-및-배포)
9. [문제 해결](#9-문제-해결)
10. [더 해볼 만한 것](#10-더-해볼-만한-것)

---

## 1. 주요 기능

| 기능 | 설명 |
|---|---|
| 실시간 스트리밍 답변 | 서버가 보내는 SSE 이벤트를 받아 답변을 한 글자씩 화면에 이어 붙입니다. |
| 대화 맥락 유지 | 지금까지의 대화 전체를 서버에 함께 보내 앞의 대화를 기억하게 합니다. |
| 생성 중지 | ■ 버튼을 누르면 요청이 취소되고 서버도 생성을 멈춥니다. 받은 부분까지는 그대로 남습니다. |
| 새 대화 | 대화 내용을 비우고 처음부터 시작합니다. |
| 서버 상태 표시 | 🟢 준비 완료 / 🟡 모델 로딩 중 / 🔴 서버 꺼짐 상태를 헤더에 표시합니다. |
| 예시 질문 | 첫 화면의 예시 질문을 누르면 바로 질문이 전송됩니다. |
| 키보드 입력 | `Enter` 전송, `Shift+Enter` 줄바꿈. 한글 입력 중 Enter 중복 전송 문제도 처리했습니다. |
| 다크 모드 | 운영체제 설정에 따라 라이트/다크 테마가 자동 적용됩니다. |
| 반응형 | 모바일 화면에서도 사용할 수 있습니다. |

---

## 2. 기술 스택

| 기술 | 역할 |
|---|---|
| [React 19](https://react.dev) | 화면을 컴포넌트 단위로 만드는 UI 라이브러리 |
| [Vite](https://vite.dev) | 개발 서버 실행과 배포용 빌드를 맡는 도구 (코드를 저장하면 화면이 바로 바뀜) |
| Fetch API + ReadableStream | 스트리밍 응답(SSE)을 조금씩 읽어오기 위한 브라우저 기본 기능 |
| 순수 CSS | 별도 UI 라이브러리 없이 CSS 변수로 테마(라이트/다크)를 구성 |

> 외부 UI 라이브러리를 쓰지 않아서 React의 기본 동작 방식을 공부하기 좋습니다.

---

## 3. 폴더 구조

```
chatbot-react/
├── index.html                 # HTML 뼈대. <div id="root"> 안에 React 앱이 그려짐
├── vite.config.js             # Vite 설정 (React 플러그인, 개발 서버 포트 5173)
├── package.json               # 프로젝트 정보, 의존성, 실행 스크립트(npm run dev 등)
├── .env.example               # 환경변수 예시 (백엔드 주소)
├── public/
│   └── bot.svg                # 파비콘/챗봇 아이콘 (그대로 복사되어 /bot.svg 로 접근 가능)
└── src/
    ├── main.jsx               # 앱 시작점: <App /> 을 #root 에 렌더링
    ├── App.jsx                # 최상위 컴포넌트: 헤더/대화목록/입력창 배치
    ├── App.css                # 채팅 화면 레이아웃 · 말풍선 · 애니메이션 스타일
    ├── index.css              # 전체 공통 스타일 · 색상 변수 · 다크 모드
    ├── api/
    │   └── chatApi.js         # 백엔드 API 호출 함수 (health, chat, chat/stream)
    ├── hooks/
    │   └── useChat.js         # 대화 상태 관리 커스텀 훅 (보내기/중지/초기화)
    └── components/
        ├── ChatHeader.jsx     # 상단 바: 제목, 모델 상태, [새 대화] 버튼
        ├── MessageList.jsx    # 대화 목록 + 자동 스크롤 + 첫 화면(예시 질문)
        ├── MessageItem.jsx    # 말풍선 1개 (사용자/챗봇/오류/생성 중 표시)
        └── ChatInput.jsx      # 하단 입력창 + 전송/중지 버튼
```

**역할 분리 원칙**

| 폴더 | 담당 | 예 |
|---|---|---|
| `api/` | **서버와 통신**만 담당 | fetch, SSE 파싱 |
| `hooks/` | **상태와 로직**만 담당 | 메시지 추가, 스트리밍 반영, 중지 |
| `components/` | **화면 그리기**만 담당 | 말풍선, 버튼, 입력창 |

이렇게 나눠 두면 예를 들어 서버 주소나 API 형식이 바뀌어도 `api/chatApi.js`만 고치면 됩니다.

---

## 4. 설치 및 실행

### 4-1. 준비물

| 항목 | 버전 | 확인 명령 |
|---|---|---|
| Node.js | 20.19 이상 (22 LTS 권장) | `node --version` |
| npm | Node.js에 포함 | `npm --version` |
| 백엔드 서버 | [`chatbot`](../chatbot) 실행 중 | http://localhost:8000/docs 접속 확인 |

### 4-2. 실행 순서

**① 백엔드 먼저 실행** (터미널 1)

```powershell
cd F:\python\fastapi\chatbot
uv run uvicorn main:app --port 8000
# "Application startup complete." 가 보이면 준비 완료
```

**② 프론트엔드 실행** (터미널 2)

```powershell
cd F:\python\fastapi\chatbot-react
npm install        # 처음 한 번만 (node_modules 폴더에 패키지 설치)
npm run dev        # 개발 서버 실행 → 브라우저가 자동으로 http://localhost:5173 을 엶
```

**③ 브라우저에서 대화하기**

- 헤더의 점이 🟢 초록색이면 바로 질문할 수 있습니다.
- 🟡 노란색이면 백엔드가 모델을 로딩(또는 첫 다운로드) 중이니 기다리세요. 3초마다 자동으로 다시 확인합니다.
- 🔴 빨간색이면 백엔드가 꺼져 있거나 주소가 틀린 것입니다.

### 4-3. npm 명령어

| 명령 | 설명 |
|---|---|
| `npm run dev` | 개발 서버 실행 (코드를 저장하면 화면 자동 갱신) |
| `npm run build` | 배포용 파일을 `dist/` 폴더에 생성 |
| `npm run preview` | 빌드한 `dist/`를 로컬에서 미리 보기 |

---

## 5. 환경 설정 (.env)

백엔드 주소가 기본값(`http://localhost:8000`)과 다를 때만 설정하면 됩니다.

```powershell
Copy-Item .env.example .env
```

```env
VITE_API_URL=http://localhost:8000
```

- Vite에서는 이름이 **`VITE_`로 시작하는 변수만** 코드에서 `import.meta.env.VITE_API_URL`로 읽을 수 있습니다.
- `.env`를 수정한 뒤에는 `npm run dev`를 **다시 실행**해야 적용됩니다.
- 이 값은 빌드할 때 코드 안에 들어가므로 비밀번호나 API 키 같은 비밀 값은 넣으면 안 됩니다.

---

## 6. 컴포넌트 구조와 데이터 흐름

### 6-1. 컴포넌트 트리

```
<App>                          useChat() 로 messages, isStreaming, send, stop, reset 을 얻음
 ├── <ChatHeader  onReset canReset />        ← 스스로 /api/health 를 주기적으로 조회
 ├── <MessageList messages onSuggestion />
 │     └── <MessageItem message /> × N
 └── <ChatInput   onSend onStop isStreaming />
```

React에서 데이터는 **위에서 아래로(props)** 흐르고, 사용자 행동은 **함수(props)를 호출**해서 위로 전달합니다.

### 6-2. 질문 하나가 처리되는 과정

```
① 사용자가 Enter
   ChatInput ──onSend(text)──▶ useChat.send(text)

② 화면에 말풍선 2개 즉시 추가
   messages = [...이전, {user: "질문"}, {assistant: "", pending: true}]
                                              └─▶ "● ● ●" 입력 중 애니메이션

③ 서버에 스트리밍 요청
   streamChat(이전 대화 + 질문)  ──POST /api/chat/stream──▶ FastAPI

④ 조각이 도착할 때마다
   onToken("안녕") → assistant.content += "안녕" → React가 말풍선만 다시 그림
   onToken("하세요") → assistant.content += "하세요"   … 반복

⑤ 완료
   onDone({elapsed: 3.2}) → 말풍선 아래 "3.2초" 표시, isStreaming=false → 입력창 다시 활성화
```

### 6-3. 메시지 데이터 형태

```js
{
  id: 3,                     // 고유 번호 (목록 렌더링 key)
  role: 'assistant',         // 'user' | 'assistant'
  content: 'FastAPI는 …',     // 내용 (스트리밍 중 계속 늘어남)
  pending: false,            // true: 첫 글자 도착 전 → 입력 중 애니메이션
  elapsed: 3.21,             // 생성 시간(초)
  stopped: false,            // 사용자가 중지함
  error: false,              // 오류 메시지 여부 (다음 요청의 대화 기록에서 제외됨)
}
```

서버에는 이 중 `role`과 `content`만 보냅니다.

---

## 7. 핵심 코드 설명

### 7-1. SSE 스트림 읽기 — `src/api/chatApi.js`

브라우저 기본 `EventSource`는 **GET 요청만** 지원해서 대화 기록(JSON)을 보낼 수 없습니다.
그래서 `fetch`로 POST 요청을 보내고 응답 본문을 직접 조금씩 읽습니다.

```js
const reader = res.body.getReader()          // 응답을 조각 단위로 읽는 리더
const decoder = new TextDecoder('utf-8')     // 바이트 → 문자열 (한글이 잘려도 안전)
let buffer = ''

while (true) {
  const { value, done } = await reader.read()  // 다음 조각이 올 때까지 대기
  if (done) break
  buffer += decoder.decode(value, { stream: true })

  const events = buffer.split('\n\n')        // SSE 이벤트는 빈 줄로 구분
  buffer = events.pop()                      // 마지막은 덜 받은 조각일 수 있어 보관
  for (const event of events) { /* "data: {...}" 파싱 → onToken 호출 */ }
}
```

> **왜 `buffer`가 필요한가요?** 네트워크는 데이터를 우리가 원하는 단위로 잘라 주지 않습니다.
> `data: {"type":"tok` 처럼 이벤트가 중간에 잘려 도착할 수 있어, 빈 줄이 나올 때까지 모았다가 처리합니다.

### 7-2. 함수형 업데이트 — `src/hooks/useChat.js`

스트리밍 중에는 1초에도 수십 번 상태가 바뀝니다. 이때 `setMessages(새배열)` 대신
`setMessages(prev => …)` 처럼 **함수를 넘겨야** 항상 최신 상태를 기준으로 글자가 이어 붙습니다.

```js
setMessages((prev) =>
  prev.map((m) => (m.id === botMsg.id ? { ...m, content: m.content + piece } : m)),
)
```

또한 기존 객체를 직접 고치지 않고(`m.content += piece` ❌) **새 객체를 만들어야**(`{ ...m, content: … }` ✅)
React가 변경을 알아채고 화면을 다시 그립니다.

### 7-3. 생성 중지 — `AbortController`

```js
const controller = new AbortController()
fetch(url, { signal: controller.signal })   // 요청에 신호 연결
controller.abort()                          // [중지] 클릭 → 연결 끊김 → fetch 가 AbortError 발생
```

연결이 끊기면 백엔드의 스트리밍 제너레이터가 닫히고, 모델 생성도 즉시 멈춥니다.

### 7-4. 한글 입력 Enter 문제 — `src/components/ChatInput.jsx`

한글은 `ㅎ → 하 → 한` 처럼 **조합 중** 상태가 있습니다. 조합 중에 Enter를 누르면 keydown 이벤트가 두 번 발생해
마지막 글자가 한 번 더 전송되는 문제가 있어, `isComposing`일 때는 무시합니다.

```js
if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { … }
```

### 7-5. 자동 스크롤 — `src/components/MessageList.jsx`

목록 맨 아래에 빈 `<div ref={bottomRef} />`를 두고, `messages`가 바뀔 때마다 그 위치로 스크롤합니다.

```js
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}, [messages])
```

### 7-6. 상태 폴링 — `src/components/ChatHeader.jsx`

`/api/health`를 호출해 모델 상태를 확인합니다. 준비되지 않았으면 3초, 준비되었으면 30초마다 다시 확인합니다.
컴포넌트가 사라질 때는 cleanup 함수에서 타이머를 해제해 메모리 누수를 막습니다.

---

## 8. 빌드 및 배포

```powershell
npm run build
```

`dist/` 폴더에 HTML/JS/CSS 정적 파일이 생성됩니다. 이 파일들은 어떤 웹 서버로도 서비스할 수 있습니다.

**방법 A. FastAPI에서 함께 서비스하기** (서버 1개로 운영)

`dist` 폴더를 백엔드 프로젝트로 복사한 뒤 `main.py` 맨 아래에 추가합니다.

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
```

빌드 전에 `.env`의 `VITE_API_URL`을 실제로 접속할 서버 주소(예: `http://192.168.0.10:8000`)로 맞춰 주세요.
같은 주소에서 화면과 API가 함께 서비스되므로 CORS 설정은 필요 없습니다.

**방법 B. 정적 호스팅 서비스** (Netlify, Vercel, GitHub Pages 등)

`dist` 폴더를 업로드하고, `VITE_API_URL`을 실제 백엔드 주소로 지정해 빌드합니다.
백엔드의 `CORS_ORIGINS`에도 프론트엔드 도메인을 추가해야 합니다.

---

## 9. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| 헤더에 🔴 "서버에 연결할 수 없습니다" | 백엔드가 꺼져 있거나 주소가 다름 → 백엔드 실행, `.env`의 `VITE_API_URL` 확인 |
| 브라우저 콘솔에 `CORS policy` 오류 | 백엔드 `.env`의 `CORS_ORIGINS`에 현재 주소(예: `http://localhost:5174`) 추가 후 백엔드 재시작 |
| ⚠️ "모델을 로딩 중입니다" | 백엔드가 아직 모델 로딩 중 → 헤더가 🟢 가 될 때까지 대기 |
| 답변이 한 번에 몰아서 나옴 | 중간에 프록시/백신 프로그램이 응답을 모아서 전달하는 경우 → 직접 `localhost`로 접속해 확인 |
| `npm run dev` 시 포트 사용 중 | 다른 Vite 서버가 실행 중 → 종료하거나 Vite가 제안한 다른 포트 사용 (CORS 설정도 함께 추가) |
| `.env` 수정이 반영 안 됨 | `npm run dev`를 종료(Ctrl+C) 후 다시 실행 |

---

## 10. 더 해볼 만한 것

- **마크다운 렌더링**: `react-markdown` + `remark-gfm`으로 표, 코드 블록, 목록을 보기 좋게 표시
- **코드 하이라이트**: `react-syntax-highlighter`로 코드 블록에 색 입히기
- **대화 기록 저장**: `localStorage`에 저장해 새로고침해도 대화 유지
- **여러 대화방**: 왼쪽 사이드바에 대화 목록을 두고 전환
- **설정 패널**: temperature, max_new_tokens를 화면에서 조절해 요청에 함께 보내기 (백엔드는 이미 지원)
- **답변 복사 버튼**: `navigator.clipboard.writeText()`로 답변 복사
