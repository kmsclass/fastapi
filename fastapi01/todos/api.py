from fastapi import FastAPI
from todo import todo_router #todo.py 파일 생성
app = FastAPI()

@app.get("/")  #http://localhost:8000  요청시 호출되는 메서드
async def welcome() -> dict :  #리턴값은 dict타입
    return {
        "message":"Hello World"
    }

app.include_router(todo_router) #요청 정보 추가