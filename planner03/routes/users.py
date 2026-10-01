#routers.users.py
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from models.events import Event
from database.connection import get_session
from routes.template_engine import templates 
from auth.authenticate import get_current_user,login_session  #auth/authenticate.py 
from pydantic import ValidationError
from models.users import User, UserSignUp,UserSignIn

user_router = APIRouter( tags=["User"]) # /docs 에서 User 그룹으로 표시

@user_router.get("/page")
async def user_page(request: Request, notice:str | None = None) :
    # notices : 상태코드 : (코드의내용, BootStrap 색상표)
    notices = {
        "registered": ("Account created. You can sign in now.", "success"),
        "duplicate": ("An account with that email already exists.", "warning"),
        "signed-in": ("Signed in successfully.", "success"),
        "signed-out": ("Signed out.", "info"),
        "login-required": ("Please sign in to continue.", "warning"),
        "missing-user": ("No account was found for that email.", "danger"),
        "wrong-password": ("The password does not match.", "danger"),
        "invalid-email": ("Enter a valid email address.", "danger"),
    }
    # notices.get(키값, 기본값) 
    # message : 코드의내용. 
    # message_type : 색상
    message, message_type = notices.get(notice, (None, "info"))
    return templates.TemplateResponse(
        request=request,
        name="users/users.html",
        context={
            "notice": message,
            "notice_type": message_type,
            "current_user": get_current_user(request),  #현재 로그인된 회원정보. session 객체에 로그인 정보 등록.
        },
    )

@user_router.post("/form/signup")
async def sign_up_from_form(
    email: str = Form(...),password: str = Form(...),session: Session = Depends(get_session)):
    try:
        data = UserSignUp(email=email, password=password) #UserSignUp 객체에 파라미터값을 저장한 객체.
    except ValidationError:
        notice = "invalid-email"
    else:
        if session.get(User, data.email) is not None:  #db에 이미 등록된 이메일인 경우
            notice = "duplicate"
        else:
            #model_validate : pip install 'pydantic[email]'  필요함
            #SQLModel 의 멤버함수. : EmailStr 형식 검증
            session.add(User.model_validate(data))  #데이터베이스에 추가
            session.commit()
            notice = "registered"
    return RedirectResponse(
        url=f"/user/page?notice={notice}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@user_router.post("/form/signin")
async def sign_in_from_form(
    request: Request,email: str = Form(...),password: str = Form(...),
    session: Session = Depends(get_session)):
    try:
        credentials = UserSignIn(email=email, password=password)
    except ValidationError:
        notice = "invalid-email"
    else:
        account = session.get(User, credentials.email) #db에서  email에 해당하는 데이터 한건 조회
        if account is None:  #이메일정보 없는상태
            notice = "missing-user"
        elif account.password != credentials.password:  #이메일정보 조회. 비밀번호 검증. 비밀번호 오류
            notice = "wrong-password"
        else: #이메일일치, 비밀번호 일치
            login_session(request, credentials.email)  #로그인 성공. 로그인 상태를 세션에 등록
            notice = "signed-in"
    return RedirectResponse(
        url=f"/user/page?notice={notice}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@user_router.post("/form/signout")
async def sign_out_from_form(request: Request):
    request.session.clear()  #세션 정보 모두 제거
    return RedirectResponse(
        url="/user/page?notice=signed-out",status_code=status.HTTP_303_SEE_OTHER)