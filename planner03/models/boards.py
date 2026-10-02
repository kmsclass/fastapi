# models/boards.py
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlmodel import Field, SQLModel
from pydantic import NaiveDatetime

#다중 상속 : str 클래스와  Enum 클래스 상속받은 클래스
class BoardCategory(str, Enum) :
    NOTICE = "notice"
    FREE = "free"
    # 함수를 속성처럼 사용 가능.
    @property
    def label(self) -> str :
        return "Notices" if self is BoardCategory.NOTICE else "Board"

# 표준시.     
def utc_now() -> datetime :
    return datetime.now(timezone.utc)

# 한국시간 : 표준시 + 9
KST = timezone(timedelta(hours=9), "KST")
def kst_now() -> datetime:
    return datetime.now(KST).replace(tzinfo=None)

class Board(SQLModel, table=True) :
    # 글번호. 기본키. 자동으로 번호 생성
    id : int | None = Field(default=None, primary_key=True)
    # 게시판 구분. 
    # index=True : 인덱스 파일 생성. 조회기회가 많으므로 인덱스 설정하여 검색의 성능을 높일 수 있다
    category : BoardCategory = Field(index=True)
    # 작성자
    author_email : str
    # 최대 200자
    title : str = Field(max_length=200)
    # 내용
    content : str
    # 첨부 파일의 위치. 첨부파일이 없는 경우 None 
    attachment_path : str | None = None
    #등록일 한국의 기준 시간으로 설정
    #create_at : datetime = Field(default_factory=kst_now)
    create_at : NaiveDatetime = Field(default_factory=kst_now)
    # 조회 수. 기본값 0
    views : int = Field(default=0)
    