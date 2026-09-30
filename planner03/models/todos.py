from sqlmodel import Field, SQLModel

# todo 테이블
class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item:str