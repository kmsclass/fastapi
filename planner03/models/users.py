#models/users.py
from pydantic import ConfigDict, EmailStr
from sqlmodel import Field, SQLModel
class UserBase(SQLModel):
    #EmailStr : 이메일 형식의 문자열. 이메일 형식이 아닌 경우 ValidationError 예외 발생
    email: EmailStr = Field(primary_key=True)
    password: str

#user 테이블
class User(UserBase, table=True):
    pass

class UserSignUp(UserBase):
    model_config = ConfigDict( #/docs에서 보이는 부분
        json_schema_extra={
            "example": {
                "email": "fastapi@packt.com",
                "password": "1234",
            }
        }
    )

# 로그인 요청 모델
class UserSignIn(UserBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "fastapi@packt.com",
                "password": "1234",
            }
        }
    )
