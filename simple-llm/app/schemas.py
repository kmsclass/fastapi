from typing import Literal
from pydantic import BaseModel,Field

class HealthResponse(BaseModel) :
    status : Literal["ok","loading"]  #Literal : 값의 영역. status 변수값은 ok, loading 
    model : str
    device : str

class ChatMessage(BaseModel) :
    role : Literal["user","assistant"] #user : 사용자메세지, assistant : llm응답
    content : str = Field(...,min_length=1, max_length=8000)


class ChatRequest(BaseModel) :
    messages : list[ChatMessage] = Field(...,min_length=1)
    #선택 settings에서 설정한 기본값
    max_new_tokens : int | None = Field(None, ge=1, le=4096)
    temperature : float | None = Field(None,ge=0.0, le=2.0)

#응답메세지
class ChatResponse(BaseModel) :
    reply : str   #llm답변
    model : str   #모델 ID
    elapsed : float #답변생성 시간(초)
