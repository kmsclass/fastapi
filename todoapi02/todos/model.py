from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from fastapi import Form

class Todo(BaseModel) :
    id : Optional[int] = None #값이 없어도 되며, 기본값 None. 사용자는 item값만 입력하고, id값은 계산해서 저장
    item : str
    '''
        객체에서 접근되는 메서드가 아니고 클래스에서 바로 호출이 가능한 메서드
        객체 생성전에 Todo.as_form 메서드를 이용하여 Todo객체를 생성하고 전달함 
        cls : Todo 클래스 자신을 의미
        Form(...) : <form ...><input name='item' ..> 파라미터 입력값 
    '''
    @classmethod
    def as_form (cls,item:str = Form(...) ) :
        return cls(item = item)  # Todo클래스의 객체

    #/docs 문서의 예시로 사용되는 부분
    model_config = ConfigDict (
        json_schema_extra= {
            "example" :{
                "id" : 1,
                "item" : "Example Data"
            }
        }
    )