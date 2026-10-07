from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from app.llm import llm
from app.config import settings
from app.schemas import HealthResponse,ChatRequest,ChatResponse
import time
from collections.abc import Iterator
from fastapi.responses import StreamingResponse
import json

# uv add accelerate

@asynccontextmanager
async def lifespan(app : FastAPI) :
    await run_in_threadpool(llm.load) # 무거운 동기함수를 별도의 스레드에서 실행. 
    yield

app = FastAPI(
    title="Qwen LLM API",
    description="Hugging Face Qwen 모델을 사용하는 LLM 백엔드",
    lifespan=lifespan
)

# CORS 가능하도록 설정
# 브라우저는 기본적으로 다른 서버의 요청 방지
# 8000번 서버에서 5173번의 요청 허용한것을 응답 헤더로 알려줌
app.add_middleware(
    CORSMiddleware,   # 응답헤더 : Access-Control-Allow-Origin 
    allow_origins=settings.cors_origins,  # 허용된 서버
    allow_credentials=True,    #인증정보 허용. 쿠키 허용
    allow_methods=["*"],       # 모든 메서드방식 허용 ["GET","POST"]
    allow_headers=["*"],       # 브라우저의 요청에 포함 가능한 헤더 정보
)
# 모델의 로딩이 안돼있는 경우
def _ensure_ready() :
    if not llm.is_ready :
        raise HTTPException(status_code=503, detail="모델을 로딩 중입니다. 잠시 후 다시 시도하세요")

def _ensure_last_is_user(req : ChatRequest) -> None :
    #req.messages[-1] : 마지막 메세지
    if req.messages[-1].role != "user" :  #사용자메세지. 
        raise HTTPException(status_code=422, detail="마지막메시지는 role='user' 여야 합니다." )
#=====================================================#
#  route 
#=====================================================#
# response_model : 응답 객체의 자료형.
# tags : /docs 문서에 응답 예시 표시
@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health() :
    return HealthResponse(
        status="ok" if llm.is_ready else "loading",
        model=settings.model_id,
        device=llm.device
    )

@app.post("/api/chat",response_model=ChatResponse, tags=["chat"]) 
def chat(req : ChatRequest) :
    _ensure_ready()
    _ensure_last_is_user(req)
    start = time.time()  #현재시간 초단위.
    #req.messages : 대화기록
    #req.max_new_tokens : 최대 토큰수. 512
    #req.temperature : 창의성정도
    #reply : LLM의 응답데이터
    reply = llm.generate(req.messages,req.max_new_tokens, req.temperature)
    elapsed = round(time.time() - start , 2)  #응답데이터가 도착까지의 시간(초)
    return ChatResponse(reply=reply, model=settings.model_id,elapsed = elapsed)

@app.post("/api/chat/stream", tags=["chat"])
def chat_stream(req: ChatRequest):
    _ensure_ready()
    _ensure_last_is_user(req)
    def event_generator() -> Iterator[str]:
        start = time.time()
        try:
            for piece in llm.stream(req.messages, req.max_new_tokens, req.temperature):
                yield f"data: {json.dumps({'type': 'token', 'content': piece}, ensure_ascii=False)}\n\n"
            elapsed = round(time.time() - start, 2)
            yield f"data: {json.dumps({'type': 'done', 'elapsed': elapsed})}\n\n"
        except Exception as e: 
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "X-Accel-Buffering": "no", 
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000, reload=True)
