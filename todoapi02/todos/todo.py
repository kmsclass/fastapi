''' 
APIRouter : 라우터 정보.  main.py에서 app.include_router() 함수로 등록
Path : 요청 정보 매개변수의 제약조건 설정시 사용
HTTPException : 에러 응답을 위한 예외 객체
status : HTTP 상태코드의 상수값
Request : HTTP 요청객체. 템플릿 호출시 반드시 전달해야함
Depends : 다른 함수를 실행한 결과를 매개변수로 전달. 의존성 주입
Form : JSON 형식의 응답이 아니고, HTML 폼데이터에서 읽도록 지정
'''
from fastapi import APIRouter,Path, HTTPException,status, Request, Depends,Form
# Jinja2Templates : templates 폴더의 HTML에 데이터를 전달하여 응답을 생성함
from fastapi.templating import Jinja2Templates
#RedirectResponse : 클라이언트에서 다른 url로 요청하도록 알려주는 응답객체
from fastapi.responses import RedirectResponse
#FilePath : 파일/폴더 경로를 다루는 표준 라이브러리
from pathlib import Path as FilePath #fastapi의 Path와 이름이 겹치므로, 이름변경
from todos.model import Todo #서버가 실행 되는 기준 폴더가 todoapi02 이므로  todos/model.py파일로 생성하기

todo_router = APIRouter()

todo_list = []

#templates(html)의 위치 지정
#FilePath(__file__) : 현재파일(todo.py)의 위치. /todoapi02/todos/todo.py
# .parent : /todoapi02/todos 폴더
# .parent.parent : /todoapi02 => 프로젝트 폴더
# / "templates" : /todoapi02/templates 폴더
templates = Jinja2Templates(directory=FilePath(__file__).parent.parent / "templates")

####################### 
# Todo 등록하기 : 할일 등록
#######################
@todo_router.post("/todo")
#todo:Todo = Depends(Todo.as_form) : todo 객체에 화면에 내용 저장. 
#                                    저장되기 전에 Todo클래스의 as_form 함수에서 데이터를 저장하고, todo 매개변수에 값을 넣어줌
async def add_todo(request:Request, todo:Todo = Depends(Todo.as_form)) :
    todo.id = max((entry.id or 0 for entry in todo_list),default=0) + 1  #id값을 계산
    todo_list.append(todo)
    return templates.TemplateResponse(  #template에 전달될 내용
        request=request,
        name='todo.html',
        context={"todos":todo_list}
    )

#######################
# 전체 할 일 목록 조회
#######################
@todo_router.get('/todo')
async def todos_list(request:Request) :
    return templates.TemplateResponse(
        request=request,
        name="todo.html",
        context={"todos":todo_list}
    )