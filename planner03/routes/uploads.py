# routes/uploads.py
import shutil  #폴더 전체 지울때 사용. rmtree
# 지정한 Path 설정
from pathlib import Path
# 무작위 고유 문자열 생성. 임의의 문자열. 업로드된 파일 이름
from uuid import uuid4
# UploadFile : 업로드된 파일의 내용(파일이름, 종류, 내용)
from fastapi import HTTPException, UploadFile, status

# Path(__file__).resolve() : uploads.py파일의 절대 경로
# Path(__file__).resolve().parent : routes 폴더
# PROJECT_DIR  : 프로젝트 폴더 
PROJECT_DIR = Path(__file__).resolve().parent.parent
# 프로젝트폴더/uploads 폴더. 업로드 파일의 위치
UPLOAD_DIR = PROJECT_DIR / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  #업로드 가능 파일의 크기 지정
CHUNK_SIZE = 1024 * 1024  #한번에 읽는 크기 1MB. 

# 실제로 파일 업로드 되었는지 판단.
def has_file(file: UploadFile | None) -> bool:
    return file is not None and bool(file.filename)

# db에 저장된 상대 경로를 절대 경로로 변경함
def absolute_path(attachment_path: str) -> Path:
    path = (PROJECT_DIR / attachment_path).resolve()  #실제 경로
    if not path.is_relative_to(UPLOAD_DIR): # path의 값이 UPLOAD_DIR 내부에 속한 파일?
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return path

# 파일이름(filename)중 경로를 제외한 파일이름 전달
def safe_filename(filename: str | None) -> str:
    # Path에서 이름부분만 남김. 
    name = Path((filename or "").replace("\\", "/")).name.strip()  #윈도우 \\ 를 /로 변경
    if name in ("", ".", ".."):  #이름이 빈이름, ., .. 인 경우는 file로 리턴
        return "file"
    return name[:200] #200자 까지만 이름으로 설정.

# 업로드된 파일 저장
async def save_upload(file: UploadFile) -> str:
    folder = UPLOAD_DIR / uuid4().hex
    folder.mkdir(parents=True)
    path = folder / safe_filename(file.filename)
    size = 0
    try:
        with path.open("wb") as out:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="File is larger than 10MB",
                    )
                out.write(chunk)
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return path.relative_to(PROJECT_DIR).as_posix()

def delete_upload(attachment_path: str | None) -> None:
    if not attachment_path:
        return
    path = (PROJECT_DIR / attachment_path).resolve()
    if path.parent.parent == UPLOAD_DIR:
        shutil.rmtree(path.parent, ignore_errors=True)
