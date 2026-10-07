from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from app.llm import llm
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=8000, reload=True)
