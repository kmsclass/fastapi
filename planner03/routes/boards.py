from fastapi import APIRouter, Depends, Form, HTTPException, Request, status,Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, func
from database.connection import get_session
from routes.template_engine import templates 
from models.boards import Board, BoardCategory

board_router = APIRouter(tags=["Boards"])

PAGE_SIZE = 10
PAGE_LINKS = 5
NOTICES = { "deleted" : ("The Post was Deleted","info")}


#============================================================================
@board_router.get("/{category}")
async def list_posts(
    # Query : http://...:8080/board/free?page=1
    #         URL 중 ? 이후의 파라미터 값. 없으면 1. 숫자아니면 422 오류발생
    request: Request,category: BoardCategory,page: int = Query(1, ge=1),  # http://...:8080/board/free?page=1
    notice: str | None = None,session: Session = Depends(get_session)) :

    email = check_can_read(request, category)
    # func : SQL사용되는 함수
    total = session.exec(
        select(func.count()).select_from(Board).where(Board.category == category)
    ).one()
    pagination = paginate(page, total)
    if page > pagination["total_pages"]:
        return RedirectResponse(
            url=f"/board/{category.value}?page={pagination['total_pages']}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
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
            "category": category,
            "posts": posts,
            "pagination": pagination,
            "first_number": total - (page - 1) * PAGE_SIZE,
            "can_write": can_write(email, category),
            "notice": message,
            "notice_type": message_type,
        },
    )
