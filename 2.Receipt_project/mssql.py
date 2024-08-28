from datetime import datetime
from collections import Counter
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db_mongo.DB_info import MongoDB, Mssql
from log_file import initialize_logger
import requests
from bs4 import BeautifulSoup

class Mssql_execution:
    def __init__(self):
        self.conn = Mssql()
    
    def acnt_tax_gbn(self, cust_numb, product,flag):
        sql = """
        SELECT TOP 1 acnt_custom.acnt_code, acnt_custom.dacnt_code, acnt_custom.acnt_name
        FROM cate_acnt_customer02 AS acnt_custom
        LEFT JOIN cate_acnt acnt
            ON acnt_custom.acnt_code = acnt.acnt_code
        WHERE acnt_custom.cust_numb=%s
        AND PATINDEX(CONCAT('%',acnt_custom.acnt_name,'%'), %s) > 0
        ORDER BY CASE WHEN LEN(acnt_custom.acnt_name) = 1 THEN 2 ELSE 1 END, CHARINDEX(acnt_custom.acnt_name, %s) + LEN(acnt_custom.acnt_name) - 1 DESC, LEN(acnt_custom.acnt_name) DESC
        """
        sql_value = (cust_numb,product,product)
        records = self.conn.mssql_connection_fetchall(sql,sql_value,flag)
        try:
            for record in records:
                acnt_code = record['acnt_code']
                dacnt_code = record['dacnt_code']
                acnt_name = record['acnt_name']
            initialize_logger('mssql').info(f'acnt_tax_gbn : {product},{acnt_code},{dacnt_code}')
            return str(acnt_code), str(dacnt_code), str(acnt_name)
        except:
            initialize_logger('mssql').info(f'acnt_tax_gbn : {product} acnt_dacnt = None')
        

    def item_acnt_dacnt(self,product,flag):
        sql = """
            SELECT TOP 1 dumpdata.acnt_code, dumpdata.dacnt_code, dumpdata.acnt_name
            FROM cate_acnt_customer02_dump AS dumpdata
            LEFT JOIN cate_acnt acnt
                ON dumpdata.acnt_code = acnt.acnt_code
            WHERE PATINDEX(CONCAT('%',dumpdata.acnt_name,'%'), %s) > 0 
            ORDER BY CASE WHEN LEN(dumpdata.acnt_name) = 1 THEN 2 ELSE 1 END,  CHARINDEX(dumpdata.acnt_name, %s) + LEN(dumpdata.acnt_name) - 1 DESC, LEN(dumpdata.acnt_name) DESC
            """
        sql_value = (product,product)
        records = self.conn.mssql_connection_fetchall(sql,sql_value,flag)
        try:
            for record in records:
                acnt_code = record['acnt_code']
                dacnt_code = record['dacnt_code']
                acnt_name = record['acnt_name']
            initialize_logger('mssql').info(f'item_acnt_dacnt : {product},{acnt_code},{dacnt_code}')
            return str(acnt_code), str(dacnt_code), str(acnt_name)
        except:
            initialize_logger('mssql').info(f'item_acnt_dacnt : {product} acnt_dacnt = None')
        

    def bkjukyo_acnt_dacnt(self,cust_numb,bkjukyo,flag):
        sql = """
            SELECT *
            FROM [cate_acnt_customer02_bank]
            WHERE cust_numb = %s
            AND acnt_name = [dbo].[getCostomerBankReplace](%s)
            """
        sql_value = (str(cust_numb),str(bkjukyo))
        records = self.conn.mssql_connection_fetchall(sql,sql_value,flag)
        try:
            for record in records:
                acnt_code = record['acnt_code']
                dacnt_code = record['dacnt_code']
            initialize_logger('mssql').info(f'bkjukyo_acnt_dacnt : {bkjukyo},{acnt_code},{dacnt_code}')
            return str(acnt_code), str(dacnt_code)
        except:
            initialize_logger('mssql').info('bkjukyo_acnt_dacnt : acnt_dacnt = None')
    
    def business_acnt_dacnt(self,business_numbers,comp_name,flag):
        bn_table = business_numbers[3:5]
        datas = MongoDB().mongodb_acnt_dacnt(business_numbers,bn_table)
        try:
            for is_code_data in datas:
                is_code = is_code_data['is_code']
            print('mongo bb : ',is_code)
        except:
            is_code = ''
        if not is_code:
            is_code = self.business_scraping(business_numbers,comp_name,bn_table)
        acnt_dacnt_code = MongoDB().mongodb_acnt_dacnt(is_code,f'{flag}_acnt_dacnt_code')
        for adc in acnt_dacnt_code:
            try:
                acnt_group = adc['acnt_group']
                try:
                    acnt_code = adc['acnt_code']
                    dacnt_code = adc['dacnt_code']
                except:
                    acnt_code = ''
                    dacnt_code = '0'
            except:
                initialize_logger('mssql').info(f'business_acnt_dacnt : None')
                pass
        initialize_logger('mssql').info(f'business_acnt_dacnt : {business_numbers},{is_code},{acnt_code},{dacnt_code},{flag}')
        return str(acnt_code), str(dacnt_code), acnt_group
        

    def business_scraping(self,business_numbers,comp_name,bn_table):
        url = 'url'
        key = 'key 값'
        params ={'serviceKey' :key, 'pageNo' : '1', 'numOfRows' : '1', 'v_saeopjaDrno' : business_numbers, 'opaBoheomFg' : '2' }
        try:
            response = requests.get(url, params=params)
            soup = BeautifulSoup(response.text, features='xml')
            is_code = soup.find('gyEopjongCd').text.strip()
            is_name = soup.find('gyEopjongNm').text.replace(' ','').strip()
            mongo_data_a = {'_id':business_numbers,
                            'is_code':is_code,
                            'is_name':is_name,
                            'corp_name':comp_name}
            MongoDB().mongodb_connaction2(mongo_data_a,bn_table)
        except:
            mongo_data = {'_id':business_numbers,
                          'corp_name':comp_name,
                          'insert':'N'}
            MongoDB().mongodb_connaction2(mongo_data,'not_business_number')
            is_code = '999999'
        print(f'is_code : {is_code}')
        return is_code


    def convert_list_to_string(self,items):
        if not items:
            return ''
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return ','.join(items)
        else:
            return f"{items[0]},{items[1]} 외"

    def convert_list_to(self,data):
        ## '9999'를 제외한 3번째 값을 수집
        try:
            values = [entry.split('||')[2]+'!!!'+entry.split('||')[3] for entry in data if entry.split('||')[2] != '9999']
            most_common_value = Counter(values).most_common(1)[0][0]
        except:
            most_common_value = '9999!!!0'
        updated_data = []
        for entry in data:
            parts = entry.split('||')
            if parts[2] != most_common_value[:2] and parts[2] != '28':
                parts[2] = most_common_value.split('!!!')[0]
                parts[3] = most_common_value.split('!!!')[1]
            updated_data.append('||'.join(parts))
        return updated_data

    ## item_sql에서 마지막 자리수에 +1
    def increment_id(self,id_str):
        item_seq_1 = id_str[0]
        number_part = id_str[1:]
        number = int(number_part)
        incremented_number = number + 1
        incremented_number_str = f"{incremented_number:09}"
        new_id_str = f"{item_seq_1}{incremented_number_str}"
        return new_id_str

    def mssql_insert(self, data, flag):
        cust_numb = str(data['cust_numb'])
        bkcode = str(data['bkcode'])
        acnt_code = str(data['acnt_code'])
        dacnt_code = str(data['dacnt_code'])
        acnt_tax_gbn = str(data['acnt_tax_gbn'])
        r_file_list = data['r_file_list']
        bkuse_flag = data['bkuse_flag']
        idx = cust_numb+bkcode
        nowtime = datetime.now()

        ## 거래내역이 있는 경우 bkuse_flag = N
        if bkuse_flag=='N' or acnt_tax_gbn == '01':
            usql_update = """ 
                update tblbank set sendId='app',r_file='',r_file1='',r_file2='',r_file3='',r_file4='',r_file5='',r_file6='',r_file7='',r_file8='',r_file9='' where bkcode=%s;
                """
            usql_update_value = (str(bkcode))
            self.conn.mssql_connection(usql_update,usql_update_value,flag)
            for r in range(0,len(r_file_list)):
                if r == 0:
                    r_file = r_file_list[0]['r_file']
                    usql = """update tblbank set sendId='app',r_file=%s where bkcode=%s;"""
                    usql_value = (str(r_file),str(bkcode))
                    self.conn.mssql_connection(usql,usql_value,flag)
                else:
                    r_file=r_file_list[r]['r_file']          
                    usql = f"""update tblbank set r_file{r}=%s where bkcode=%s;"""
                    usql_value = (str(r_file),str(bkcode))
                    self.conn.mssql_connection(usql,usql_value,flag)

        ## 거래내역이 없는 경우 bkuse_flag = Y
        else:
            itemList=[]
            for r in r_file_list:    
                r_file=r['r_file']
                comp_name=r['comp_name']
                bn = r['business_numbers']
                items=r['items']
                for item in items:
                    itemList.append(item)
                total_pri=r['total_pri']

                #유사목 불러오기
                values=[]
                saved_items = ""
                saved_price=0
                item_list_all = []
                item_list_all_2 = []
                tot_sum = 0
                try:
                    bk_slq = """SELECT BKJUKYO FROM TBLBANK WHERE BKCODE=%s"""
                    bk_value = (str(bkcode))
                    bkjukyo = self.conn.mssql_connection_fetchone(bk_slq,bk_value,'II')['BKJUKYO']
                except:
                    bkjukyo = ""
                if not acnt_code or acnt_code == '9999':
                    try:
                        bi_numbs = self.business_acnt_dacnt(bn,comp_name,flag)
                        bi_acnt_code = bi_numbs[0]
                        bi_dacnt_code = bi_numbs[1]
                    except:
                        bi_acnt_code = '9999'
                        bi_dacnt_code = '0'

                    for it in itemList:
                        pList=it.split(":")
                        product=pList[0].strip()
                        price=pList[1].strip()
                        ## acnt_dacnt_code 검색 : cust_numb, product(품목)
                        acnt_dacnt_code = self.acnt_tax_gbn(cust_numb, product,flag)
                        print(acnt_dacnt_code)
                        try:
                            acnt_code = acnt_dacnt_code[0]
                            dacnt_code = acnt_dacnt_code[1]
                            product_1 = acnt_dacnt_code[2]
                        except:
                            product_1 = 'None'
                            acnt_code = ""
                            dacnt_code = "0"
            
                        ## acnt_dacnt_code 검색 : product(품목)
                        if not acnt_code and acnt_tax_gbn == '02':
                            acnt_dacnt_code = self.item_acnt_dacnt(product,flag)
                            print(acnt_dacnt_code)
                            try:
                                acnt_code = acnt_dacnt_code[0]
                                dacnt_code = acnt_dacnt_code[1]
                                product_1 = acnt_dacnt_code[2]
                            except:
                                product_1 = 'None'
                                acnt_code = ""
                                dacnt_code = "0"
                        ## acnt_dacnt_code 검색 : cust_numb, bkjukyo(은행거래내역)
                        if not acnt_code or product == '품목 없음':
                            if product == '품목 없음':
                                product = bkjukyo
                                product_1 = bkjukyo
                            else:
                                product_1 = product
                            try:
                                acnt_dacnt_code = self.bkjukyo_acnt_dacnt(cust_numb,product,flag)
                                acnt_code = acnt_dacnt_code[0]
                                dacnt_code = acnt_dacnt_code[1]
                            except:
                                acnt_code = "9999"
                                dacnt_code = "0"
                        
                        if acnt_code == '9999' or acnt_code == '':
                            acnt_code = bi_acnt_code
                            dacnt_code = bi_dacnt_code
                        if dacnt_code == '':
                            dacnt_code = '0'
                        item_list_all_2.append(f'{product_1}||{price}||{acnt_code}||{dacnt_code}')
                        item_list_all.append(f'{product_1}||{price}||{acnt_code}||{dacnt_code}')
                else:
                    items_list = []
                    for it in itemList:
                        item_list = it.split(':')[0].strip()
                        price = it.split(':')[1].strip()
                        itl = self.item_acnt_dacnt(item_list,flag)[2]
                        tot_sum += int(it.split(':')[1].strip())
                        items_list.append(itl)
                    item_result = self.convert_list_to_string(items_list)
                    item_list_all_2.append(f'{itl}||{price}||{acnt_code}||{dacnt_code}')
                    item_list_all.append(f'{item_result}||{total_pri}||{acnt_code}||{dacnt_code}')
                        
                ## 거래내역에 같은 bkcode의 데이터가 있는지
                ssql = """select count(item_numb) as cnt from customer_account_item where cust_numb=%s and bkcode=%s;"""
                ssql_value = (str(cust_numb),str(bkcode))        
                srow = self.conn.mssql_connection_fetchone(ssql,ssql_value,flag)
                if srow['cnt'] > 0:   #데이터가 존재 한다면
                    dqry = """delete from customer_account_item where cust_numb=%s and bkcode=%s;"""
                    dqry_value = (str(cust_numb),str(bkcode))
                    self.conn.mssql_connection(dqry,dqry_value,flag)
                    uqry = """update tblbank set use_flag='N', send_yn='N' where bkcode=%s;"""
                    uqry_value = (str(bkcode))
                    self.conn.mssql_connection(uqry,uqry_value,flag)

                ## insert
                ## 먼저 TBLBANK 조회
                bsql = """
                    select bank.*, accnt.mid,accnt.actaccountnum from tblbank bank, tblaccount accnt    
                    where bank.Bkacctno=accnt.Actaccountnum and accnt.mid=%s
                    and bank.bkcode=%s;
                    """
                
                bsql_value = (str(cust_numb),str(bkcode))
                brow = self.conn.mssql_connection_fetchone(bsql,bsql_value,flag)   
                if brow is not None:
                    bkdate = brow['BKDATE']
                    bkjukyo = brow['BKJUKYO']
                    item_date = bkdate[:4]+"-"+bkdate[4:6]+"-"+bkdate[-2:]

                    ## 증빙서 번호 생성
                    item_gbn = '01'
                    item_type = '계좌이체'
                    item_seq = 0
                    icsql = """
                        select count(item_seq) as iseq_cnt from customer_account_item 
                        where cust_numb=%s and item_date >=%s and item_date <= %s
                        """
                    icsql_value = (str(cust_numb),str(bkdate[:4]+'-01-01'),str(bkdate[:4]+'-12-31'))
                    icrow=self.conn.mssql_connection_fetchone(icsql,icsql_value,flag)
                    iseq_cnt = icrow['iseq_cnt']
                    if int(iseq_cnt) > 0 :
                        nsql = """ 
                            select top 1 right(item_seq,9) as iseq from customer_account_item
                            where cust_numb = %s and item_date >= %s and item_date <= %s order by item_numb desc    
                        """          
                        nsql_value = (str(cust_numb),str(bkdate[:4]+'-01-01'),str(bkdate[:4]+'-12-31'))
                        nrow=self.conn.mssql_connection_fetchone(nsql,nsql_value,flag)
                        item_seq=nrow['iseq']
                    if item_seq =='':            
                        item_seq=1
                    elif item_seq.isnumeric():
                        item_seq=item_seq
                    else:
                        item_seq=item_seq+1
                    
                    item_seq = item_seq.zfill(9)
                    acnt_tax_gbn='02'  #지출
                    if acnt_tax_gbn=='01':
                        item_seq = "I"+item_seq
                    elif acnt_tax_gbn=='02':
                        item_seq = "E"+item_seq
                    else:
                        item_seq = "X"+item_seq
                    ## 정렬순서 번호 생성
                    date_seq = 1
                    qry1  = """
                        select count(*)+1 as dcnt from customer_account_item where cust_numb=%s and item_date=%s ;
                    """
                    qry1_value = (str(cust_numb),str(item_date))
                    qrow1=self.conn.mssql_connection_fetchone(qry1,qry1_value,flag)
                    date_seq = qrow1['dcnt']

                ## 데이터 파싱 및 그룹화
                grouped_data = {}
                item_list_all = self.convert_list_to(item_list_all)
                for item in item_list_all:
                    parts = item.split('||')
                    key = (parts[2], parts[3])
                    if key not in grouped_data:
                        grouped_data[key] = {'acnt_code': parts[2], 'dacnt_code': parts[3], 'items': [], 'price_sum': 0}
                    grouped_data[key]['items'].append(parts[0])
                    grouped_data[key]['price_sum'] += int(parts[1])
                

                ## 결과 리스트 변환
                result_list = list(grouped_data.values())

                ## 아이템이 2개를 넘는 경우 처리
                for entry in result_list:
                    items = entry['items']
                    if len(items) > 2:
                        entry['items'] = [f"{items[0]}, {items[1]} 외"]
                    else:
                        entry['items'] = [', '.join(items)]
                

                ## price_sum의 총합 계산
                tot_sum = sum(entry['price_sum'] for entry in result_list)
                use_auto_acnt = 'Y'
                ## 결과 출력
                input_type=''
                if int(len(result_list)) >= 2:
                    input_type='분'
                
                ## SQL문
                isql = """
                INSERT INTO customer_account_item (
                item_seq, cust_numb, acnt_code, dacnt_code, item_gbn, item_date, date_seq, item_price, item_type, 
                item_cont1, item_date2, item_cntr_date, item_enter_date, item_check_date, item_confirm_date, item_reg_date, item_cash_date, item_acnt_date, 
                item_order_date, item_recept_date, regdate, delflag, bkcode, input_type, use_auto_acnt
                ) 
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, CONCAT(%s, '-', %s), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
                """
                for entry in result_list:
                    acnt_code = entry['acnt_code']
                    dacnt_code = entry['dacnt_code']
                    saved_price = entry['price_sum']
                    if str(len(result_list)) == '1':
                        if int(tot_sum) != int(total_pri) and int(total_pri) != 0:
                            saved_price = total_pri
                        elif int(total_pri) == 0:
                            saved_price = tot_sum
                    saved_items = entry['items']
                    values+=[[item_seq,cust_numb,acnt_code,dacnt_code,item_gbn,item_date,str(date_seq),saved_price,item_type, bkjukyo, saved_items,
                            str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),str(item_date),
                            str(nowtime.date()),'N',str(bkcode),str(input_type),str(use_auto_acnt)]]
                    item_seq = self.increment_id(item_seq)
                    date_seq += 1
                    

                initialize_logger('mssql').info(values)
                self.conn.mssql_connection(isql, values, flag)

                if not values:
                    ## r_status update
                    self.conn.mssql_r_status('3',bkcode,flag)
                else:
                    if len(r_file_list[0]['r_file']) >= 11:
                        usql = """
                                update tblbank set use_flag='Y', sendtime=%s,sendId='app',r_file=%s,comp_name=%s where bkcode=%s;
                                """
                        usql_value = (str(nowtime),str(r_file),str(comp_name),str(bkcode))
                        self.conn.mssql_connection(usql,usql_value,flag)
                    else:
                        for r in range(0,len(r_file_list[0]['r_file'])):
                            print(r_file_list[0]['r_file'])
                            if r == 0:
                                r_file = r_file_list[0]['r_file'][0]
                                usql = """
                                        update tblbank set use_flag='Y', sendtime=%s,sendId='app',r_file=%s,comp_name=%s where bkcode=%s;
                                        """
                                usql_value = (str(nowtime),str(r_file),str(comp_name),str(bkcode))
                                self.conn.mssql_connection(usql,usql_value,flag)
                            else:
                                r_file= r_file_list[0]['r_file'][r]
                                usql = f"""update tblbank set use_flag='Y',sendId='app',r_file{r}=%s where bkcode=%s;"""
                                usql_value = (str(r_file),str(bkcode))
                                self.conn.mssql_connection(usql,usql_value,flag)
                    MongoDB().mongodb_connaction_update({'_id': f'{idx}'}, {'mssql_insert': 'Y','item_list':item_list_all_2}, f'{flag}_ocr_pre')
                    ## r_status update
                    self.conn.mssql_r_status('1',bkcode,flag)
                    initialize_logger('mssql').info(f'{idx} Finish')
        Mssql().__close__()
