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
    # todo 객체 : item 변수에 화면에 item 파라미터값을 저장한 객체
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
async def list_todo(request:Request) : #request:Request => request 개체의 자료형이 Request 클래스임
    return templates.TemplateResponse(  #템플릿에서 응답하도록 설정
        request=request, #반드시 요청객체를 템플릿에 전달해야 함
        name="todo.html",  #템플릿이름
        context={"todos":todo_list} # 호출된 템플릿에 전달할 데이터
    )

#######################
# 할 일 한개 조회
#######################
@todo_router.get("/todo/{todo_id}")  # <a href='/todo/{{ todo.id }}' ... >
async def get_todo(request : Request, todo_id : int = Path(..., title='ID값은 자동 생성')) :
    for todo in todo_list :
        if todo.id == todo_id :
            return templates.TemplateResponse(
                request=request,
                name='todo.html',
                context={'todo':todo}
            ) 
    raise HTTPException ( # todo.id에 값이 입력된 값과 다른경우. 강제로 예외 발생함.  
        #HTTPException : http 의 오류 발생.
        status_code =status.HTTP_404_NOT_FOUND,  #HTTP 오류코드 : 404 코드로 설정함 
        detail = "해당 TODO 데이터 없음"
    )    

#######################
# 할 일 한개 수정
# 수정 후 url을 목록보기로 요청하도록 함
#######################
@todo_router.post("/todo/{todo_id}/edit")
async def update_todo (todo_id : int = Path(..., title="Todo 데이터 수정"),
                       item : str = Form(...)) -> RedirectResponse :
    # item : 폼필드 중 item 파라미터값을 저장. Form(...):필수입력임
    for todo in todo_list :
        if todo.id == todo_id :
            todo.item = item
            #status_code=status.HTTP_303_SEE_OTHER : 현재의 POST 방식이 아니고 다른 방식으로 요청(GET)
            return RedirectResponse("/todo",status_code=status.HTTP_303_SEE_OTHER) #get방식의 /todo => 목록보기 재요청
    raise HTTPException ( 
        status_code =status.HTTP_404_NOT_FOUND,  #HTTP 오류코드 : 404 코드로 설정함 
        detail = "해당 TODO 데이터 없음"
    )     
#######################
# 할 일 한개 삭제
# 삭제 후 url을 목록보기로 요청하도록 함
#######################
@todo_router.post("/todo/{todo_id}/delete")
async def delete_todo( todo_id: int = Path(..., title="Todo 데이터 한개 삭제하기")) -> RedirectResponse:
    for index, todo in enumerate(todo_list):
        if todo.id == todo_id:
            todo_list.pop(index) #index에 해당하는 요소를 todo_list에서 제거
            return RedirectResponse("/todo", status_code=status.HTTP_303_SEE_OTHER)
        # HTTP오류 코드  
        # 200 : 정상
        # 300 : 리다이렉트
        # 404 : 해당페이지 없음
        # 500 : 서버페이지 오류
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Todo with supplied ID doesn't exist",
    )