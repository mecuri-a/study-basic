from fastapi import FastAPI, Form, File, UploadFile, Depends
from pydantic import BaseModel
import uvicorn
from fastapi.responses import JSONResponse
from typing import List

import sys, os
import shutil
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from receipt import Ocr_api
from mssql import Mssql_execution
from datetime import datetime
from db_mongo.DB_info import Mssql
from log_file import initialize_logger

app = FastAPI()
## 파일 경로
UPLOAD_FOLDER = '/home/azureuser/receipt-file'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024 ## 10MB

class DataInput(BaseModel):
    cust_numb : str
    bkcode : str
    use_ocr : str
    acnt_tax_gbn : str
    acnt_code : str
    dacnt_code : str
    files : List[UploadFile] # type: ignore

def as_form(cls: BaseModel):
    def _as_form(
        cust_numb: str = Form(...), 
        bkcode: str = Form(...),
        use_ocr : str = Form(...),
        acnt_tax_gbn : str = Form(...),
        acnt_code : str = Form(...),
        dacnt_code : str = Form(...),
        files: List[UploadFile] = File(...) # type: ignore
    ):
        return cls(cust_numb=cust_numb, bkcode=bkcode, use_ocr=use_ocr, acnt_tax_gbn=acnt_tax_gbn, 
                   acnt_code=acnt_code, dacnt_code=dacnt_code,
                   files=files)
    return _as_form

DataInput = as_form(DataInput)


@app.post('/upload')
async def upload_files(data_input:DataInput = Depends()):
    ## 데이터를 추출
    cust_numb = data_input.cust_numb
    bkcode = data_input.bkcode
    bkuse_flag = data_input.use_ocr
    acnt_tax_gbn = data_input.acnt_tax_gbn
    acnt_code = data_input.acnt_code
    dacnt_code = data_input.dacnt_code
    files = data_input.files
    flag = 'I'
    response_data_a = {}
    initialize_logger('fast').info(f'app data info : {cust_numb}, {bkcode}, {flag}')
    ## 영수증 파일
    r_files = []
    file_paths = []  # 파일 경로들을 저장할 리스트 추가
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, 'temp', cust_numb, bkcode, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        r_files.append(file.filename)
        file_paths.append(file_path)
    if not cust_numb or not bkcode or not bkuse_flag or not r_files:
        ## 데이터 x = 300 return
        response_data_a['returnCode'] = 300
        initialize_logger('fast').error('필수 데이터가 누락되었습니다.')
        return JSONResponse(content=[response_data_a], status_code=300)
    elif cust_numb and bkcode and bkuse_flag and r_files:
        response_data_a['returnCode'] = 200
        main(cust_numb,bkcode,bkuse_flag,r_files,file_paths,acnt_tax_gbn,acnt_code,dacnt_code,flag)
        return JSONResponse(content=[response_data_a], status_code=200)


def main(cust_numb,bkcode,bkuse_flag,r_files,file_paths,acnt_tax_gbn,acnt_code,dacnt_code,flag):
    print(f'ocr 여부 : {bkuse_flag}')
    response_data = {
        'cust_numb': cust_numb,
        'bkcode': bkcode,
        'bkuse_flag': bkuse_flag,
        'r_files': r_files,
        'file_paths': file_paths,  ## 파일 경로 리스트를 추가
        'acnt_tax_gbn':acnt_tax_gbn,
        'acnt_code' : acnt_code,
        'dacnt_code' : dacnt_code,
        'insertTime' : str(datetime.now()),
        'flag' : flag
            }
    try:
        if bkuse_flag == 'Y':  ## 거래 내역이 없는 경우 OCR
            initialize_logger('fast').info('NN',response_data)
            ## r_status update
            Mssql().mssql_r_status('2',bkcode,flag)
            ## ORC 실행
            Ocr_api().ocr_parser(response_data)
        elif bkuse_flag == 'N':  ## 거래 내역이 있는 경우 
            r_file = []
            for rf in range(len(r_files)):
                r_f = {'r_file': r_files[rf]}
                r_file.append(r_f)
            initialize_logger('fast').info('YY',response_data)
            ## r_status update
            Mssql().mssql_r_status('2',bkcode,flag)
            Mssql_execution().mssql_insert(response_data,flag)
        try:
            shutil.rmtree(f'{UPLOAD_FOLDER}/{cust_numb}/{bkcode}')
        except:
            pass
        shutil.copytree(f'{UPLOAD_FOLDER}/temp/{cust_numb}/{bkcode}',f'{UPLOAD_FOLDER}/{cust_numb}/{bkcode}',dirs_exist_ok=True)
        shutil.rmtree(f'{UPLOAD_FOLDER}/temp/{cust_numb}/{bkcode}')
        ## r_status update
        Mssql().mssql_r_status('1',bkcode,flag)
    except Exception as ee:
        initialize_logger('fast').error(ee)
        Mssql().mssql_r_status('3',bkcode,flag)


@app.post('/delete')
async def delete(data_input:DataInput = Depends()):
    cust_numb = data_input.cust_numb
    bkcode = data_input.bkcode
    flag = "I"
    response_data_a = {}
    initialize_logger('fast').info(f'delete : {cust_numb}, {bkcode}')
    if not cust_numb or not bkcode:
        response_data_a['returnCode'] = 400
        return JSONResponse(content=[response_data_a], status_code=400)
    
    folder_path = os.path.join(UPLOAD_FOLDER, flag, cust_numb, bkcode)
    
    if not os.path.exists(folder_path):
        response_data_a['returnCode'] = 200
        return JSONResponse(content=[response_data_a], status_code=200)
    try:
        ## file and folder delete
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        Mssql().mssql_r_status('0',bkcode,flag)
        response_data_a['returnCode'] = 200
        return JSONResponse(content=[response_data_a], status_code=200)
    except Exception as ee:
        initialize_logger('fast').error(ee)
        response_data_a['returnCode'] = 500
        return JSONResponse(content=[response_data_a], status_code=500)

if __name__ == '__main__':
    uvicorn.run(debug=True, host='0.0.0.0', port=8000)
    


