'''
 서버 실행 방법
 1. uvicorn main:app --reload 
 2. python main.py    => if __name__ == '__main__' 블록을 실행
'''
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import os
from contextlib import asynccontextmanager
from database.connection import conn   #database/connection.py
from routes.todos import todo_router
from routes.events import event_router

# @app.on_event("startup") 이전에 사용됨. 
# 서버시작 또는 종료시에 실행할 코드를 정의 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn()  #yield 전에 실행 하는 부분
    yield #

app = FastAPI(lifespan=lifespan)

# http:localhost:8000 요청이 되면, http:localhost:8000/todo 재요청하도록 설정함
@app.get("/")
async def welcome() -> RedirectResponse :
    return RedirectResponse(url="/todo")  #브라우저에서 localhost:8000/todo 재요청함

app.include_router(todo_router)
app.include_router(event_router, prefix="/event")

# python main.py 명령어로 실행되도록 코드 추가
if __name__ == '__main__' :
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)