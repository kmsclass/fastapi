#
# UploadFile : 업로드된 파일의 내용을 저장하고 있는 객체(파일이름, 종류, 내용)
# File : multipart/form-data 에서 파일 필수, 선택
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status,Query,UploadFile,File
from fastapi.responses import RedirectResponse,FileResponse
from sqlmodel import Session, select, func
from database.connection import get_session
from routes.template_engine import templates 
from models.boards import Board, BoardCategory
from auth.authenticate import LoginRequiredException, get_current_user, is_admin
import math
from routes.uploads import save_upload, delete_upload,has_file,absolute_path

board_router = APIRouter(tags=["Boards"])

PAGE_SIZE = 10
PAGE_LINKS = 5
NOTICES = { "deleted" : ("The Post was Deleted","info")}

# 게시판을 볼수있는 사용자 판단
def check_can_read(request: Request, category: BoardCategory) -> str | None:
    #현재 로그인된(세션) 이메일값을 저장
    email = get_current_user(request)  #로그아웃상태 :  None
    # BoardCategory.FREE : 자유게시판인 경우
    # BoardCategory.NOTICE : 공지사항인 경우
    if category is BoardCategory.FREE and email is None:  #  자유게시판이고, 로그아웃상태
        raise LoginRequiredException()  # 로그인페이지로 이동 
    return email

# 게시물을 작성 권한 여부 판단.
# 공지사항 : 관리자만,
# 자유게시판 : 로그인 된 모든 사용자. 
def can_write(email: str | None, category: BoardCategory) -> bool:
    if email is None:  # 로그아웃 상태
        return False
    # category is BoardCategory.NOTICE : 공지사항인 경우 관리자만 쓰기 권한
    # 자유게시판인 경우는 모든 사용자가 쓰기 권한을 가짐
    return is_admin(email) if category is BoardCategory.NOTICE else True

# 현재 보여지는 HTML페이지의 출력되는 페이지 번호
def paginate(page: int, total: int) -> dict:
    #  page : 현재 페이지
    # total : 전체 등록된 게시물 건수
    # total_pagegs : 등록된 게시물 건수에 맞는 전체 페이지 수
    #       math.ceil(total / PAGE_SIZE) : ceil(305 / 10) => 31
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    # start =  화면에 출력된 시작 페이지번호
    #   page = 1 :  1. : 1 2,3,4,5 
    #.  page = 2 :  1. : 1,2,3,4,5
    #.  page = 6 :  6. : 6,7,8,9,10
    #.  page = 7 :  6
    start = (page - 1) // PAGE_LINKS * PAGE_LINKS + 1
    # end : 화면에 출력된 종료 페이지 번호
    end = min(start + PAGE_LINKS - 1, total_pages)
    return {
        "page": page,
        "total": total,
        "total_pages": total_pages,
        "numbers": list(range(start, end + 1)),
        "prev_block": start - 1 if start > 1 else None,
        "next_block": end + 1 if end < total_pages else None,
    }
#글쓰기 전에 글쓰기 권한 여부 검사
def check_can_write(request: Request, category: BoardCategory) -> str:
    email = get_current_user(request)  #세션에 등록된 이메일 정보
    if email is None:
        raise LoginRequiredException()
    
    if not can_write(email, category):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  #권한 없음
            detail="Only the administrator can write notices",
        )
    return email

# 글쓰기, 글수정에 사용되는 화면 출력
def render_form(
    request: Request,
    category: BoardCategory,
    *,   # 경계선. 이후는 변수명 확인하여 매개변수값 초기화
    post: Board | None = None,
    title: str = "",
    content: str = "",
    error: str | None = None,
):
    return templates.TemplateResponse(
        request=request,
        name="boards/form.html",
        context={
            "category": category,
            "post": post,
            "title": title,
            "content": content,
            "error": error,
            "allow_file": category is BoardCategory.FREE,  #자유게시판만 첨부파일 허용. 
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT if error else status.HTTP_200_OK,
    )
#입력 데이터 검증. 
def validate(title: str, content: str) -> str | None:
    if not title:
        return "Enter a title."
    if len(title) > 200:
        return "The title must be 200 characters or fewer."
    if not content:
        return "Enter the content."
    return None

#post_id 값의 게시글을 db에서 읽어서 Board 객체로 리턴
def get_post(session: Session, category: BoardCategory, post_id: int) -> Board:
    post = session.get(Board, post_id) #key값에 해당하는 데이터 조회
    if post is None or post.category != category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

#글 수정 권한 
def can_edit(email: str | None, post: Board) -> bool:
    if not can_write(email, post.category):  #글쓰기 권한이 있는 경우는 수정이 가능함
        return False
    #글수정 본인글만 수정 가능. 관리자인 경우는 다른 게시글도 수정
    return post.author_email == email or is_admin(email)

#tuple[Board, str] : 튜플의 요소가 2개야. 첫번째 자료형 Board, 두번째 자료형 :  str
def get_editable_post(
    request: Request, session: Session, category: BoardCategory, post_id: int) -> tuple[Board, str]:
    email = check_can_write(request, category)
    post = get_post(session, category, post_id)
    if not can_edit(email, post):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can change this post",
        )
    return post, email

#============================================================================
@board_router.get("/{category}")
async def list_posts(
    # Query : http://...:8080/board/free?page=1
    #         URL 중 ? 이후의 파라미터 값. 없으면 1. 숫자아니면 422 오류발생
    request: Request,category: BoardCategory,page: int = Query(1, ge=1),  # http://...:8080/board/free?page=1
    notice: str | None = None,session: Session = Depends(get_session)) :

    email = check_can_read(request, category)  # 로그인된 이메일 정보
    # func : SQL사용되는 함수
    # select count(*) from board where category = 'free'
    total = session.exec(
        select(func.count()).select_from(Board).where(Board.category == category)
    ).one()
    pagination = paginate(page, total)
    if page > pagination["total_pages"]:  #조회되는 페이지 번호가 최대페이지번호가 크면, 최대페이지로 재요청 
        return RedirectResponse(
            url=f"/board/{category.value}?page={pagination['total_pages']}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    # 페이지에 보여질 게시글 목록. 한페이지에 10건 게시물 표시. 
    # select * from board where category = 'free' order by id desc limit 0, 10
    posts = session.exec(
        select(Board)
        .where(Board.category == category)
        .order_by(Board.id.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).all()
    message, message_type = NOTICES.get(notice, (None, "info"))
    return templates.TemplateResponse(
        request=request,
        name="boards/list.html",
        context={
            "category": category,  # 게시판 종류   
            "posts": posts,        # 출력될 게시물 목록
            "pagination": pagination,  #화면 하단의 페이지번호 출력 정보
            "first_number": total - (page - 1) * PAGE_SIZE,  #화면에 출력될 게시물 번호
            "can_write": can_write(email, category),  #게시판글쓰기 버튼 표시를 위한 정보
            "notice": message,    #결과 출력
            "notice_type": message_type,  #결과 출력의 글자색
        },
    )
# first_number : 화면에 보여지는 게시물의 번호.  
# 1페이지 : 15
# 2페이지 : 5
# total : 게시판종류별 전체 등록 게시물 건수. 15건

# 글쓰기 화면 출력
@board_router.get("/{category}/new")
async def new_post_page(request: Request, category: BoardCategory):
    check_can_write(request, category)
    return render_form(request, category)

#글등록 실행
@board_router.post("/{category}/new")
async def create_post(
    request: Request,
    category: BoardCategory,
    title: str = Form(""),
    content: str = Form(""),
    file: UploadFile | None = File(None),  #첨부파일은 없어도 가능함
    session: Session = Depends(get_session),  #db에 데이터 등록을 위한 세션
):
    # 권한 검증
    email = check_can_write(request, category)
    title, content = title.strip(), content.strip()
    
    # 입력데이터 검증
    if error := validate(title, content):  #True인 경우 입력 오류 발생
        return render_form(request, category, title=title, content=content, error=error)

    attachment_path = None
    #자유게시판에서만 첨부파일을 업로드함
    if category is BoardCategory.FREE and has_file(file):  #자유게시판이고 첨부파일이 존재. 
        attachment_path = await save_upload(file)  #파일 업로드 실행

    #db에 데이터 저장하기
    post = Board(
        category=category,
        author_email=email,
        title=title,
        content=content,
        attachment_path=attachment_path,
    )
    session.add(post)  #db의 board 테이블에 데이터 저장
    try:
        session.commit()
    except Exception:
        delete_upload(attachment_path)  #오류 발생시 첨부파일 제거
        raise
    session.refresh(post)
    return RedirectResponse(
        url=f"/board/{category.value}", status_code=status.HTTP_303_SEE_OTHER
    )

# 글 보기 (조회수 1 증가)
@board_router.get("/{category}/{post_id}")
async def read_post(
    request: Request,
    category: BoardCategory,
    post_id: int,
    session: Session = Depends(get_session),
):
    email = check_can_read(request, category)  #권한 검증
    post = get_post(session, category, post_id)  #post_id : 게시글번호. 키값
    post.views += 1   #조회수 1 증가
    session.add(post) #Board 수정. 
    session.commit()
    session.refresh(post) #재 로드. 조회수가 1이 증가상태로 
    return templates.TemplateResponse(
        request=request,
        name="boards/detail.html",
        context={
            "category": category,
            "post": post,
            "attachment_name": post.attachment_path.rsplit("/", 1)[-1] if post.attachment_path else None,
            "can_edit": can_edit(email, post),
        },
    )

# 글 수정 페이지
@board_router.get("/{category}/{post_id}/edit")
async def edit_post_page(
    request: Request,
    category: BoardCategory,
    post_id: int,
    session: Session = Depends(get_session),
):
    # post_id 의 게시글을 현재 사용자가 수정 가능한 권한이 있는지 검증 
    # 권한이 있는경우 : 게시글,이메일 정보 리턴
    post, _ = get_editable_post(request, session, category, post_id)
    # form.html 에 게시글정보 전달.
    return render_form(request, category, post=post, title=post.title, content=post.content)

# 글 수정 (폼 제출)
# multipart/form-data
@board_router.post("/{category}/{post_id}/edit")
async def edit_post(
    request: Request,
    category: BoardCategory,
    post_id: int,
    title: str = Form(""),
    content: str = Form(""),
    remove_file: bool = Form(False),
    file: UploadFile | None = File(None),  #업로드 파일의 내용
    session: Session = Depends(get_session),
):
    #수정 권한 검증 + 수정할 게시글데이터
    #post, _ = get_editable_post(request, session, category, post_id)
    post = get_editable_post(request, session, category, post_id)
    post = post[0]
    title, content = title.strip(), content.strip()
    if error := validate(title, content):
        return render_form(request, category, post=post, title=title, content=content, error=error)

    old_path = post.attachment_path  #db에 저장된 첨부파일
    new_path = old_path  #기존 첨부파일 내용
    if category is BoardCategory.FREE:  #자유게시판만 첨부가능
        if has_file(file):  #업로드된 파일이 있어?
            new_path = await save_upload(file)
        elif remove_file:
            new_path = None

    post.title = title
    post.content = content
    post.attachment_path = new_path
    session.add(post)  #수정
    try:
        session.commit()
    except Exception:
        if new_path != old_path:
            delete_upload(new_path)  #수정된 첨부파일을 제거
        raise
    if old_path != new_path:
        delete_upload(old_path)  #기존 첨부파일을 제거
    return RedirectResponse(
        url=f"/board/{category.value}/{post.id}", status_code=status.HTTP_303_SEE_OTHER
    )

# 글 삭제 (폼 제출)
@board_router.post("/{category}/{post_id}/delete")
async def delete_post(
    request: Request,
    category: BoardCategory,
    post_id: int,
    session: Session = Depends(get_session),
):
    #권한 검증 + 삭제할 게시물데이터
    post, _ = get_editable_post(request, session, category, post_id)
    attachment_path = post.attachment_path  #첨부파일 정보
    session.delete(post)  #db의 데이터 제거
    session.commit()
    delete_upload(attachment_path) #첨부파일 제거
    return RedirectResponse(
        url=f"/board/{category.value}?notice=deleted", status_code=status.HTTP_303_SEE_OTHER
    )
# 첨부 파일 다운로드
@board_router.get("/{category}/{post_id}/download")
async def download_attachment(
    request: Request,
    category: BoardCategory,
    post_id: int,
    session: Session = Depends(get_session),
):
    check_can_read(request, category)  # 읽기권한
    post = get_post(session, category, post_id) #db에서 게시물 조회
    #파일의 정보 검증.
    if not post.attachment_path:  #해당 게시물에 첨부파일 정보 없는 경우
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This post has no attachment")
    path = absolute_path(post.attachment_path)
    if not path.is_file(): #파일 아님
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File is missing on the server")

    # 브라우저에 전달된 파일의 형식을 application/octet-stream 전달함
    #  text/html 전달하는 경우 : 브라우저 화면에 바로 출력
    #  image/jpec 전달하는 경우 : 브라우저에 이미지를 출력
    #....
    return FileResponse(  #파일 객체를 응답
        path,
        media_type="application/octet-stream",   #다운로드 
        filename=path.name,
        headers={"X-Content-Type-Options": "nosniff"},
    )