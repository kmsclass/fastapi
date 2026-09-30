# routes.template_engine.py
from pathlib import Path
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    #Path(__file__).resolve() : 현재 파일의 절대 경로
    # 템플릿의 폴더 : 프로젝트폴더/templates 폴더
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)