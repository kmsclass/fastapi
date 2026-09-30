# models/events.py
from pydantic import ConfigDict
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel

class EventBase(SQLModel):
    title: str
    image: str
    description: str
    # sqlite 데이터베이스에는 리스트 자료형이 없음. 저장은 JSON형식의 문자열로 저장됨
    tags: list[str] = Field(default_factory=list, sa_type=JSON) 
    location: str

class Event(EventBase, table=True):  #event 테이블
    id: int | None = Field(default=None, primary_key=True)

