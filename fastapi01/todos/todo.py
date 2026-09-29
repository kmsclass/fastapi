'''
todo.py : API 라우트 모음. 
          요청 정보들의 모임 
APIRouter : 요청경로(라우트)들의 그룹을 관리하는 클래스
todo_router : APIRouter 객체
'''
from fastapi import APIRouter, Path
from model import Todo, TodoItem  #  model.py 

todo_router = APIRouter()

todo_list= []

#등록된 할일 정보 목록 리턴
@todo_router.get("/todo")  #localhost:80000/todo GET 요청
async def retrieve_todos() -> dict :
    return {
        "todos" : todo_list
    }

#할일 등록 기능
@todo_router.post("/todo")  #localhost:80000/todo POST 요청
#todo:Todo : Todo 클래스의 객체가 todo
async def add_todo(todo:Todo) -> dict :
    todo_list.append(todo) #todo 객체:입력데이터
    return {
        "message" : "Todo added Succssfully"
    }

#한건씩 조회하기
@todo_router.get("/todo/{todo_id}") #{todo_id} : 요청 url에 id값 
async def get_todo(todo_id:int) -> dict: #todo_id값이 자동으로 int형변환
    for todo in todo_list :
        if todo_id == todo.id : #todo.id :  todo_list 내의 요소값의 id값
            return {
                "todo" : todo
            }
    return {
        "message":"Todo Id doesn't exist"
    }    

#put : 데이터를 수정시 사용되는 방법
#{todo_id} : 1
#Path(...,title="") :첫번째 인자값(todo_data) 필수값
#                    title : /docs 페이지에 표시되는 설명
@todo_router.put("/todo/{todo_id}") #localhost:8000/todo/1
async def update_todo(todo_data : TodoItem,todo_id:int = Path(...,title="The ID of the todo to be update")) -> dict:
    for todo in todo_list :
        #todo : todo_list내부의 요소 한개. Todo객체 한개
        #todo_id : 수정할 요청 id값 
        if todo.id == todo_id :  #True인 경우 수정 todo 객체 존재
            #todo_data.item : 입력된 내용
            todo.item = todo_data.item
            return {
                "message":"Todo update Successfully"
            }
    return {  #요청ID에 해당하는 todo객체가 없는 경우
        "message":"Todo with supplied ID doesn't exist"
    }
# todo_id 의 todo 객체를 todo_list 에서 제거하기.
# delete : 데이터를 삭제하는 방법
@todo_router.delete("/todo/{todo_id}")  #localhost:8000/todo/1
async def delete_one_todo(todo_id : int) -> dict :
    for index in range(len(todo_list)) : #pop명령어에서 index값 필요
        todo = todo_list[index]
        if todo.id == todo_id :
            todo_list.pop(index) #todo객체를 todo_list에서 제거
            return {
                "message" : "Todo deleted successfully"
            }
    return {
        "message" : "Todo with supplied ID doesn't exist"
    }  
# 모든 todo_list의 요소를 제거하기 : clear()  
@todo_router.delete("/todo")  #localhost:8000/todo
async def delete_all_todo() -> dict :
    todo_list.clear()
    return {
        "message" : "Todos deleted successfully"
    }