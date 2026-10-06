#====================================
# 1. uv init --no-package easy-ml-04 
# 2. vscode 실행.
# 3. easy-ml-04 폴더 선택
# 4. terminal 
# 5. uv add fastapi
# 6. uv add uvicorn
# 7. 가상환경 활성화 : 
#   mac : source .venv/bin/activate
#   win : cd .venv/Script
#         activate.bat
# 8. 프로젝트폴더/templates 생성
# 9. templates/index.html 저장하기  
#=====================================
# csv,excel 파일을 업로드하여 머신러닝으로 분석하기
# 회귀분석, 분류, 군집 알고리즘을 선택하여 분석하기
from fastapi import FastAPI,Request,UploadFile,File,HTTPException,Query
from fastapi.templating import Jinja2Templates #uv add jinja2
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Any
import pandas as pd
import csv
from io import BytesIO
from ml import ALGORITHMS,run_model

app = FastAPI(title="CSV 및 Excel 머신러닝 분석 API")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

ALLOWED_EXTENSIONS = {".csv",".xlsx",".xls"}
#업로드 가능 파일의 최대 크기. 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024

async def _read_upload(file : UploadFile, sheet_name : str | None) -> tuple[pd.DataFrame,list[str], str | None] :
    filename = file.filename or ""  #업로드된 파일의 이름
    extension = Path(filename).suffix.lower() #파일이름중 확장자를 소문자 변경 저장

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="CSV, XLSX, XLS 파일만 업로드할 수 있습니다.")

    contents = await file.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE :  #업로드 가능 최대 크기 넘김
        raise HTTPException(status_code=413, detail="파일 크기는 20MB 이하 여야 합니다.")
    
    if not contents : # 내용이 없음
        raise HTTPException(status_code=400, detail="빈 파일은 분석 할 수 없습니다.")
    
    return _load_dataframe(contents, extension,sheet_name)

def _load_dataframe (contents : bytes, extension : str, sheet_name:str | None = None) \
   -> tuple[pd.DataFrame,list[str], str | None] :
    if extension == ".csv" :
        #utf-8-sig : BOM 이 붙은 utf-8도 처리 가능
        #cp949 : 한글 완성형. EUC-KR 포함
        for encoding in ("utf-8-sig","cp949") :
            try:
                #contents.decode(encoding) : contents를 encoding 형식의 문자열로 변경
                #splitlines() : 라인별로 분리하여 리스트로 리턴
                lines = contents.decode(encoding).splitlines()
                #첫번째 줄을 헤더정보로 저장. 헤더 정보가 없는 경우 ""로 리턴
                #next : 공백은 제외하고 내용이 있는 첫줄
                header = next((line for line in lines if line.strip()), "")
                if not header:
                    raise HTTPException(status_code=400, detail="CSV 파일에 데이터가 없습니다.")
                # csv파일의 내용이 있는 경우
                try:
                    #csv.Sniffer().sniff(header) :  header 정보를 분석해서, 구분자를 선택함. 
                    #, ; \t |  : 파일의 구분자로 가능 판단. 확장자가 csv이면서, 셀의 구분자는 4가지로 가능함
                    delimiter = csv.Sniffer().sniff(header, delimiters=",;\t|").delimiter
                except csv.Error:
                    delimiter = ","
                # BytesIO(contents) : 파일객체로 변경
                # csv로 업로드된 파일을 DataFrame으로 변경
                dataframe = pd.read_csv(BytesIO(contents), encoding=encoding, sep=delimiter)
                return dataframe, [], None
            except UnicodeDecodeError:
                continue   #encoding 방식을 다음 인코딩으로 다시 실행
            except pd.errors.ParserError as error:
                raise HTTPException(status_code=400, detail="CSV 형식이 올바르지 않습니다.") from error
        raise HTTPException(status_code=400, detail="CSV 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949 파일을 사용해 주세요.") 
    # excel 파일인 경우
    try :
        workbook = pd.ExcelFile(BytesIO(contents)) # excel파일 읽기
        sheet_names = workbook.sheet_names  #sheet이름들
        selected_sheet = sheet_name or sheet_names[0]  #sheet이름이 없는 경우 첫번째 sheet
        if selected_sheet not in sheet_names :
            raise HTTPException(status_code=400, 
                                detail=f"시트를 찾을 수 없습니다:{selected_sheet}") 
        #엑셀파일에서 선택한  sheet를 읽어 DataFrame객체로 리턴
        return pd.read_excel(workbook,sheet_name=selected_sheet),sheet_names, selected_sheet
    except HTTPException :
        raise
    except Exception as error :
        raise HTTPException(status_code=400,detail="Excel 파일을 읽을 수 없습니다.") from error
#=====================================================================================
@app.get("/",response_class=HTMLResponse)
async def home(request : Request) -> HTMLResponse :
   return templates.TemplateResponse(request=request, name="index.html",context={})

#dict[str,Any] : str 자료형, 모든 자료형 => key자료형:str, value자료형:모든 자료형
@app.post("/columns")
async def list_columns(file : UploadFile = File(...), sheet_name:str | None = None)->dict[str,Any] :
    dataframe,sheets,selected_sheet = await _read_upload(file,sheet_name)
    return {
       "row_count" : int(len(dataframe)),  #데이터의 레코드 갯수
       "sheets" : sheets,  #sheet 이름 목록
       "selected_sheet" : selected_sheet,  #선택한 sheet이름
       "columns" :[  #name : 컬럼이름 한개
          {
             "name" : str(name),
             "dtype" : str(dataframe[name].dtype),
             "numeric" : bool(pd.api.types.is_numeric_dtype(dataframe[name])),
             "unique_count" : int(dataframe[name].nunique())  #범주의 값
          }
          for name in dataframe.columns
       ],
    }

@app.get("/ml/algorithms")
async def ml_algorithms() -> dict[str, dict[str,str]] : 
    return ALGORITHMS

@app.post("/ml")
async def train_model(
    file : UploadFile = File(...),
    task : str = Query(...,description="regression,classfication,clustering"),
    algorithm : str = Query(...),
    features : list[str] = Query(...,description="독립변수 (여러개 지정 가능)"),
    target : str | None = Query(None,description="종속변수 (군집 분석에서는 지정 불가)"),
    sheet_name : str | None = None,
    test_size : float = 0.2,
    n_clusters : int = 3
) -> dict[str, Any] :
    dataframe, sheets, selected_sheet = await _read_upload(file,sheet_name)
    result = run_model(dataframe,task,algorithm,features, target,test_size, n_clusters)
    result["filename"] = file.filename or ""
    if sheets :
        result["selected_sheet"] = selected_sheet
    return result

if __name__ == "__main__":
   import uvicorn
   #host="127.0.0.1" : 서버에 접근 가능한 IP주소
   #host="0.0.0.0" : 외부 접근 가능함
   uvicorn.run("main:app",host="0.0.0.0",port=8000, reload=True)

