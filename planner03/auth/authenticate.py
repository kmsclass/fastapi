#auth/authenticate.py
from fastapi import  Request,HTTPException,status

SESSION_USER_KEY = "user"  #로그인 정보 인식하는 키값

#LoginRequiredException : HTTPException  클래스의 하위 클래스.
class LoginRequiredException(HTTPException) :
    #로그인 필요한 경로 호출시 로그아웃상태로 접근된 경우 발생되는 사용자 생성 예외 클래스.
    def __init__(self) -> None :
        super().__init__(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in"
        )

def get_current_user(request: Request) -> str | None:
    #request.session : 브라우저의 session 객체. 
    return request.session.get(SESSION_USER_KEY) #세션에 등록된 user정보. 이메일정보

def login_session(request: Request, email: str) -> None:
    request.session.clear()  #session의 정보를 모두 삭제
    request.session[SESSION_USER_KEY] = email   #request.session['user'] = email 

#세션에 등록된 로그인 정보 조회. 
#로그인 상태 : 등록된 email을 리턴
#로그아웃 상태 : LoginRequiredException 예외 강제 발생
def require_login(request:Request) -> str :
    email = get_current_user(request)
    if email is None :
        raise LoginRequiredException()
    return email

from fastapi.responses import RedirectResponse,JSONResponse

#LoginRequiredException예외가 발생되면 호출되는 핸들러
def login_required_handler(request:Request, exc : LoginRequiredException) :
    # mime타입 : text/html 
    if "text/html" in request.headers.get("accept","") : #html 페이지에서 요청된 경우
        return RedirectResponse(
            url = "/user/page?notice=login-required"
        )
    return JSONResponse (status_code=exc.status_code,  # /docs 등에서 호출된 경우
                         content={"detail":exc.detail}
                         )
