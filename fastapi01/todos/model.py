from pydantic import BaseModel,ConfigDict

#BaseModel :pydantic 모델의 부모클래스. 타입힌트,데이터검증,형변환, JSON형식으로 자동 처리
class Todo(BaseModel): #Todo 클래스의 부모클래스가 BaseModel 클래스임
    id: int
    item: str

#ConfigDict : /docs에 표시되는 영역
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "item": "Example Schema!"
            }
        }
    )

# item 만 가진 모델
# todo내용을 수정시 사용되는 모델
class TodoItem(BaseModel) :
    item : str
    #/docs 에 표시될 내용
    model_config = ConfigDict (
        json_schema_extra={
            "example" : {
                "item": "Item Only Variable"
            }
        }
    )   