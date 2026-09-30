# routes.todos.py
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
# Session : db연결객체.
# select :  select sql 생성하는 함수
from sqlmodel import Session, select

from database.connection import get_session
from models.todos import Todo
from routes.template_engine import templates #routes/template_engine.py

#tags=["Todos"] : /docs에서 그룹으로 인식
todo_router = APIRouter(tags=["Todos"])

#DB에 저장된 모든  Todo 데이터를 조회 함수
#list[Todo] : 요소의 자료형이 Todo 객체인 list 객체
# select(Todo) : todo 테이블의 모든 데이터 조회
# order_by(Todo.id) : id컬럼 순으로 정렬 리턴
# all() : 조회된 데이터를 리스트리턴 
def all_todos(session : Session) -> list[Todo] :
    return session.exec(select(Todo).order_by(Todo.id)).all()

# todo_id에 해당하는   Todo 레코드를 조회 
def get_todo(session: Session, todo_id: int) -> Todo:
    todo = session.get(Todo, todo_id)  #select * from todo where id = todo_id
    if todo is not None:  #조회되는 데이터가 존재 
        return todo
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Todo not found",
    )

# Todo 등록 
@todo_router.post("/todo")
async def add_todo(item: str = Form(...), session: Session = Depends(get_session)):
    item = item.strip()  #공백 제거
    if not item:    #item데이터가 없는 경우 
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Todo item cannot be empty",
        )
    session.add(Todo(item=item))  #데이터베이스에 todo 테이블에 입력된 item데이터 등록.  id는 자동 생성
    session.commit() #데이터 추가 완료. 
    return RedirectResponse(url="/todo", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get("/todo")
async def list_todos(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(
        request=request,
        name="todos/todo.html",
        context={"todos": all_todos(session), "item": ""},
    )

@todo_router.get("/todo/{todo_id}")
async def show_todo(request: Request, todo_id: int, session: Session = Depends(get_session)):
    return templates.TemplateResponse(
        request=request,
        name="todos/todo.html",
        context={"todo": get_todo(session, todo_id), "todos": all_todos(session), "item": ""},
    )
@todo_router.post("/todo/{todo_id}/edit")
async def update_todo(todo_id:int, item: str = Form(...), session: Session = Depends(get_session)):
    item = item.strip()  #공백 제거
    if not item:    #item데이터가 없는 경우 
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Todo item cannot be empty",
        )
    todo = get_todo(session,todo_id)
    
    todo.item = item
    session.add(todo)  #추가,수정은 같은 함수. 같은 키값이 존재하면 수정. 이미 등록된 키가 없으면 추가
    session.commit() #데이터 추가 완료. 
    return RedirectResponse(url="/todo", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get("/todo/{todo_id}/delete")
async def delete_todo(todo_id:int, session: Session = Depends(get_session)) :
    todo = get_todo(session,todo_id)
    session.delete(todo)
    session.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_303_SEE_OTHER)