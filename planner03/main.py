'''
 서버 실행 방법
 1. uvicorn main:app --reload 
 2. python main.py    => if __name__ == '__main__' 블록을 실행
'''
# Depends : 의존성 주입. 실행 전에 먼저 실행되어야 하는 함수를 지정
from fastapi import FastAPI,Depends
from fastapi.responses import RedirectResponse
import os
from contextlib import asynccontextmanager
from database.connection import conn   #database/connection.py
from routes.todos import todo_router
from routes.events import event_router
from routes.users import user_router
from routes.boards import board_router

from auth.authenticate import require_login,LoginRequiredException,login_required_handler

# SessionMiddleware 
# 요청시마다 쿠키에서 세션정보 읽어서 요청(request)정보에 넣어서 전달
from starlette.middleware.sessions import SessionMiddleware  #pip install itsdangerous

# @app.on_event("startup") 이전에 사용됨. 
# 서버시작 또는 종료시에 실행할 코드를 정의 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn()  #yield 전에 실행 하는 부분
    yield #

app = FastAPI(lifespan=lifespan)

# 미들웨어 설정
app.add_middleware(
    SessionMiddleware, 
     #secret_key : 세션 쿠키를 서명할 때 사용되는 비밀키 
     # 환경변수 저장해서 사용하는 것을 권장함
    secret_key=os.getenv("SESSION_SECRET_KEY", "dev-only-change-me"),
    # 쿠키 유효기간 설정. 초단위
    max_age=60 * 60 * 24,  # 1일 설정
    #same_site="lax" : GET요청은 다른 사이트에서 시작된 요청에 쿠키 전송
    # strict : 다른 사이트 접속 불가.
    # none : 모두 허용. CSRF를 위한 다른 보안 장치가 필요
    same_site="lax",
)

# http:localhost:8000 요청이 되면, http:localhost:8000/todo 재요청하도록 설정함
@app.get("/")
async def welcome() -> RedirectResponse :
    return RedirectResponse(url="/todo")  #브라우저에서 localhost:8000/todo 재요청함
# 로그아웃 상태에서 todo,event를 접근못하도록 하기.
app.include_router(todo_router, dependencies=[Depends(require_login)])
app.include_router(event_router, prefix="/event", dependencies=[Depends(require_login)]) # http://localhost:8000/event/... 요청시 
app.include_router(user_router, prefix="/user")
# requir_login 함수 의존성을 추가하지 않음.
# 공지사항 조회 로그인 상관없음. 
app.include_router(board_router,prefix="/board")

#예외 발생시 핸들러(함수) 호출
app.add_exception_handler(LoginRequiredException, login_required_handler)

# python main.py 명령어로 실행되도록 코드 추가
if __name__ == '__main__' :
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)