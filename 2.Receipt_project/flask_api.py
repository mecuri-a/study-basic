from flask_cors import CORS
from werkzeug.utils import secure_filename
import sys, os
import shutil
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from receipt import Ocr_api
from mssql import Mssql_execution
from datetime import datetime
from db_mongo.DB_info import Mssql
from flask import Flask, request, jsonify as flask_jsonify
from threading import Thread
from log_file import initialize_logger

app = Flask(__name__)
CORS(app)
## 파일 경로
UPLOAD_FOLDER = '/home/azureuser/receipt-file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 


@app.route('/upload', methods=['POST'])
def upload_files():
    ## 데이터를 추출
    cust_numb = request.form.get('cust_numb')
    bkcode = request.form.get('bkcode')
    bkuse_flag = request.form.get('use_ocr')
    acnt_tax_gbn = request.form.get('acnt_tax_gbn')
    acnt_code = request.form.get('acnt_code')
    dacnt_code = request.form.get('dacnt_code')
    flag = 'I' ## 아이나라
    response_data_a = {}
    initialize_logger('flask').info(f'app data info : {cust_numb}, {bkcode}, {flag}')
    ## 영수증 파일
    r_files = []
    file_paths = []  # 파일 경로들을 저장할 리스트 추가
    i = 0
    while True:
        r_file_key = f'r_file{i}' if i > 0 else 'r_file'
        if r_file_key in request.files:
            print(request.files.get(r_file_key).filename)
            r_file = request.files.get(r_file_key)
            if r_file:
                filename = secure_filename(r_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', cust_numb, bkcode, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                r_file.save(filepath)
                r_files.append(filename)
                file_paths.append(filepath)
        else:
            break
        i += 1

    response_data_a = {}
    if not cust_numb or not bkcode or not bkuse_flag or not r_files:
        ## 데이터 x = 300 return
        response_data_a['returnCode'] = 300
        initialize_logger('flask').error('필수 데이터가 누락되었습니다.')
        return flask_jsonify([response_data_a]), 300
    elif cust_numb and bkcode and bkuse_flag and r_files:
        response_data_a['returnCode'] = 200
        thread = Thread(target=main, args=(cust_numb,bkcode,bkuse_flag,r_files,file_paths,acnt_tax_gbn,acnt_code,dacnt_code,flag))
        thread.start()
        return flask_jsonify([response_data_a]), 200


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
            initialize_logger('flask').info('NN',response_data)
            ## r_status update
            Mssql().mssql_r_status('2',bkcode,flag)
            ## ORC 실행
            Ocr_api().ocr_parser(response_data)
        elif bkuse_flag == 'N':  ## 거래 내역이 있는 경우 
            r_file = []
            for rf in range(len(r_files)):
                r_f = {'r_file': r_files[rf]}
                r_file.append(r_f)
            initialize_logger('flask').info('YY',response_data)
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
        initialize_logger('flask').error(ee)
        Mssql().mssql_r_status('3',bkcode,flag)


@app.route('/delete', methods=['POST'])
def delete():
    cust_numb = request.form.get('cust_numb')
    bkcode = request.form.get('bkcode')
    flag = "I"
    response_data_a = {}
    initialize_logger('flask').info(f'delete : {cust_numb},{bkcode}')
    if not cust_numb or not bkcode:
        response_data_a['returnCode'] = 400
        return flask_jsonify([response_data_a]), 400
    
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], cust_numb, bkcode)
    
    if not os.path.exists(folder_path):
        response_data_a['returnCode'] = 200
        return flask_jsonify([response_data_a]), 200
    try:
        ## file and folder delete
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        Mssql().mssql_r_status('0',bkcode,flag)
        response_data_a['returnCode'] = 200
        return flask_jsonify([response_data_a]), 200
    except Exception as ee:
        initialize_logger('flask').error(ee)
        response_data_a['returnCode'] = 500
        return flask_jsonify([response_data_a]), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
    


