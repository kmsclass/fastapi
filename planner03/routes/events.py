# routes.events.py
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from models.events import Event
from database.connection import get_session
from routes.template_engine import templates #routes/template_engine.py

event_router = APIRouter(tags=["Events"])

@event_router.get("/page") #http://localhost:8000/event/page
async def event_page(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(
        request=request,
        name="events/events.html",
        context={"events": session.exec(select(Event)).all()},
    )
@event_router.post("/form/new")
async def create_event (
    title : str = Form(...), # 반드시 입력값이 존재해야 함
    image : str = Form(""),  # 입력값이 없어도 됨
    description : str = Form(...),
    tags : str = Form(...),
    location : str = Form(...),
    session : Session = Depends(get_session)) :
    session.add(
        Event(
            title=title.strip(),
            image = image.strip(),
            description=description.strip(),
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            location = location.strip()
        )
    )
    session.commit()
    return RedirectResponse(url="/event/page",status_code=status.HTTP_303_SEE_OTHER)

@event_router.post("/form/{event_id}/delete")
async def delete_event (event_id : int, session : Session = Depends(get_session)) :
    event = session.get(Event,event_id)
    if event is not None :
        session.delete(event)
        session.commit()
    return RedirectResponse(url="/event/page",status_code=status.HTTP_303_SEE_OTHER)    