from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import re
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db_mongo.DB_info import MongoDB
from mssql import Mssql_execution
from log_file import initialize_logger

class Ocr_api:
    def __init__(self):
        self.key = "key 값"
        self.endpoint = "Azure endpoint"
        self.mssql = Mssql_execution()


    def extract_business_numbers(self,text):
        pattern = r"\b\d{3}-\d{2}-\d{5}\b"
        business_numbers = re.findall(pattern, text)
        return business_numbers
    

    def mongo_data(self,cust_numb,bkcode,r_file,flag):
        mongo_data = {'_id': cust_numb+bkcode,
                        'cust_numb':cust_numb,
                        'bkcode': bkcode,
                        'r_file_list': r_file,
                        'insertTime':str(datetime.now())}
        try:
            MongoDB().mongodb_connaction(mongo_data, f'{flag}_ocr_data')
            initialize_logger('ocr').info(f'Mongo_Data_insert : ocr_data {cust_numb+bkcode}')
        except:
            MongoDB().mongodb_connaction_update({'_id': mongo_data['_id']}, {'r_file_list': mongo_data['r_file_list']}, f'{flag}_ocr_data')
            initialize_logger('ocr').info(f'Mongo_Data_update : ocr_data {cust_numb+bkcode}')
    

    def r_file_list_pres(self, data):
        try:
            merged_data = {'r_file': [], 'comp_name': '', 'date': None, 'business_numbers': None, 'items': [], 'total_pri': 0, 'msg': None}
            for item in data:
                for key, value in item.items():
                    if key == 'r_file':
                        merged_data['r_file'].append(''.join(value))
                    elif key == 'items':
                        merged_data['items'].extend(value)
                    elif key == 'msg':
                        merged_data['msg'] = '' if merged_data['msg'] is None else merged_data['msg'] + ', ' + value if value is not None else merged_data['msg']
                    elif key == 'comp_name':
                        merged_data['comp_name'] = value if value is not None else ''
                    elif key in ['date', 'business_numbers']:
                        merged_data[key] = value if value is not None else merged_data[key]
                    elif key == 'total_pri':
                        merged_data[key] += int(value) if value is not None else 0
                    else:
                        merged_data[key] = value
        except Exception as ee:
            print(ee)
        return [merged_data]


    def ocr_parser(self,data):
        cust_numb = data['cust_numb']
        bkcode = data['bkcode']
        r_files = data['r_files']
        file_paths = data['file_paths']
        acnt_tax_gbn = data['acnt_tax_gbn']
        acnt_code = data['acnt_code']
        dacnt_code = data['dacnt_code']
        flag = data['flag']
        r_file_list = []
        r_file_list_pre = []
        # DocumentAnalysisClient 인스턴스 생성
        document_analysis_client = DocumentAnalysisClient(self.endpoint, AzureKeyCredential(self.key))
        # 문서 분석 수행
        for f_int in range(len(file_paths)):
            with open(file_paths[f_int], "rb") as f:
                poller = document_analysis_client.begin_analyze_document("prebuilt-receipt", document=f)
            receipts = poller.result()
            text = receipts.content.split()
            # 사업자 등록 번호 추출
            business_numbers = []
            try:
                for item in text:
                    extracted_numbers = self.extract_business_numbers(item)
                    if extracted_numbers:
                        business_numbers.extend(extracted_numbers)
                business_number = business_numbers[0].replace('-','').strip()
                print("추출된 사업자 등록 번호:", business_number)
            except Exception as ee:
                initialize_logger('ocr').error(ee)
                business_number = None
            
            for idx, receipt in enumerate(receipts.documents):
                ## 상호명
                merchant_name = receipt.fields.get("MerchantName")
                if merchant_name:
                    comp_name = str(merchant_name.value).replace('_',' ').replace('-',' ').replace('\n',' ').strip()
                    if comp_name == None or comp_name == '':
                        comp_name = None
                else:
                    comp_name = None

                ## 날짜
                transaction_date = receipt.fields.get("TransactionDate")
                if transaction_date:
                    date = re.sub(r'\D','',str(transaction_date.value)).strip()
                    if date == None or date == '':
                        date = None
                else:
                    date = None
                
                ## 품목 리스트
                total_pri = 0    
                if receipt.fields.get("Items"):
                    '''
                    품목 : item_description.value
                    합계 : item_total_price.value
                    '''
                    item_list = []
                    item_pri_sum = 0
                    for idx, item in enumerate(receipt.fields.get("Items").value):
                        item_description = item.value.get("Description")
                        item_total_price = item.value.get("TotalPrice")
                        if item_description and item_total_price:
                            item_name = item_description.value.replace('\n','').strip()
                            if item_total_price:
                                try:
                                    item_tot_pri = int(item_total_price.value)
                                    item_pri_sum += item_tot_pri
                                    item_total_list = f'{item_name} : {item_tot_pri}'
                                    item_list.append(item_total_list)
                                except:
                                    pass

                    # 영수증 합계    
                    total = receipt.fields.get("Total")
                    try:
                        totaltax = receipt.fields.get('TotalTax').value
                    except:
                        totaltax = 0
                    if total and total.value is not None:
                        total_pri = int(total.value) - int(totaltax)
                    if item_pri_sum == total_pri:
                        msg = None
                    else:
                        msg = '합계가 맞지 않습니다. 영수증 확인 부탁드립니다.'
                else:
                    item_list = None
                    total = receipt.fields.get("Total")
                    if total:
                        total_pri = int(total.value)
                    msg = '상품 목록이 없습니다.'
                file_x = r_files[f_int]
                r_files[f_int] = {'r_file':r_files[f_int],'comp_name':comp_name,'date':date,
                             'business_numbers':business_number,
                             'items': item_list if item_list is not None and item_list != [] else ['품목없음:0'],
                             'total_pri': f'{total_pri}',
                             'msg':msg}
                r_file_list_pre.append(r_files[f_int])
            
            ## MongoDB_insert
            r_files[f_int] = {'r_file':file_x,'text':text,'receipt':f'{receipt}'}
            r_file_list.append(r_files[f_int])
        
        print(r_file_list_pre)
        if int(len(r_file_list_pre)) == 1:
            r_file_pre = r_file_list_pre
        else:
            r_file_pre = self.r_file_list_pres(r_file_list_pre)
            print(r_file_pre)

        self.mongo_data(cust_numb,bkcode,r_file_list,flag)

        mongodata = {'_id': cust_numb+bkcode,
                             'cust_numb':cust_numb,
                             'bkcode': bkcode,
                             'bkuse_flag' : 'Y',
                             'acnt_tax_gbn' : acnt_tax_gbn,
                             'r_file_list' : r_file_pre,
                             'acnt_code' : acnt_code,
                             'dacnt_code' : dacnt_code,
                             'mssql_insert' : 'N',
                             'insertTime':str(datetime.now())}
        
        try:
            MongoDB().mongodb_connaction_pre(mongodata, f'{flag}_ocr_pre')
            initialize_logger('ocr').info(f'Mongo_Data_insert : ocr_pre {cust_numb+bkcode}')
            try:
                self.mssql.mssql_insert(mongodata, flag)
            except Exception as ee:
                print(ee)
        except Exception as ee:
            MongoDB().mongodb_connaction_update({'_id': mongodata['_id']}, {'r_file_list': mongodata['r_file_list']}, f'{flag}_ocr_pre')
            initialize_logger('ocr').info(f'Mongo_Data_update : ocr_pre {cust_numb+bkcode}')
            try:
                self.mssql.mssql_insert(mongodata, flag)
            except Exception as ee:
                print(ee)
        finally:
            MongoDB().__close__()

