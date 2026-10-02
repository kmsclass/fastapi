# routes.template_engine.py
from pathlib import Path
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    #Path(__file__).resolve() : 현재 파일의 절대 경로
    # 템플릿의 폴더 : 프로젝트폴더/templates 폴더
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


from datetime import datetime

from models.boards import KST

def localtime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.astimezone(KST).strftime("%Y-%m-%d %H:%M")
templates.env.filters["localtime"] = localtime
