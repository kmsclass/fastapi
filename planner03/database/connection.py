########################
# SQLite 데이터 베이스에 연결 설정
# SQLModel : Pydantic + SQLAlchemy
########################
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine
DATABASE_FILE = Path(__file__).resolve().parent.parent / 'planner.db'
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
#'''
#윈도우의 \ 임 
#[mac] sqlite:///Users/...
#[win] sqlite:///c:\Users ....
#from sqlalchemy.engine import URL
#DATABASE_URL = URL.create("sqlite", #database=str(DATABASE_FILE)) 
#'''
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  #여러개의 스레드에서 연결이 가능하도록 설정. 기본:연결된 스레드만 가능
    echo=False,    # True인 경우 sql구문이 콘솔에 출력됨. (디버깅시는 true)
)
#import 된 모델을 테이블로 생성
def conn() -> None :
    import models.todos
    SQLModel.metadata.create_all(engine)
# with 블록이 종료되면 자동으로 세션을 종료시킴
# yield : 함수 실행 중에 호출한 함수로 session 객체을 전달시킴. 
def get_session() :
    with Session(engine) as session :
        yield session