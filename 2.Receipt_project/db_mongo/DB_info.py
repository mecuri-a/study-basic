import pymongo
import urllib.parse
import configparser
import pymssql

class MongoDB:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('./config/config.conf', encoding='UTF8')
        self.config_mob = config['MongoDB']
        host1 = self.config_mob['hostname1']
        port = self.config_mob['port']
        username = urllib.parse.quote_plus(self.config_mob['username'])
        password = urllib.parse.quote_plus(self.config_mob['password'])
        self.conn = pymongo.MongoClient(f'mongodb://{username}:{password}@{host1}:{port}/',maxPoolSize=1)

    def mongodb_connaction(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name']]
        collection = db[table_name]
        collection.insert_one(data)
        return collection
    
    def mongodb_connaction2(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name2']]
        collection = db[table_name]
        collection.insert_one(data)
        return collection

    def mongodb_connaction_update(self, query, update_data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name']]
        collection = db[table_name]
        collection.update_one(query,{'$set':update_data})
        return collection

    def mongodb_connaction_pre(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name']]
        collection = db[table_name]
        collection.insert_one(data)
        return collection
    
    def mongodb_acnt_dacnt(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name2']]
        collection = db[table_name]
        find = collection.find({'_id':data})
        return find
    
    def __close__(self):
        self.conn.close()


class Mssql():
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('./config/config.conf', encoding='UTF8')
        self.config_sql = config['Mssql']
        server = self.config_sql['hostname1']
        database = self.config_sql['database']
        database2 = self.config_sql['database2']
        username = self.config_sql['username']
        password = self.config_sql['password']
        # MSSQL에 연결
        self.conn = pymssql.connect(server=server, user=username, password=password, database=database, charset='UTF-8')
        self.conn_ii = pymssql.connect(server=server, user=username, password=password, database=database, charset='EUC-KR')
        self.conn2 = pymssql.connect(server=server, user=username, password=password, database=database2, charset='UTF-8')

    def mssql_connection(self, data, value,flag):
        if flag == 'I':
            cursor = self.conn.cursor()
        elif flag == 'S':
            cursor = self.conn2.cursor()
        try:
            try:
                cursor.execute(data, value)
            except:
                cursor.executemany(data,value)
            self.conn.commit()
        except Exception as e:
            print("Error:", e)
            self.conn.rollback()
        finally:
            cursor.close()
    
    def mssql_connection_fetchall(self, data, value, flag):
        if flag == 'I':
            cursor = self.conn.cursor()
        elif flag == 'S':
            cursor = self.conn2.cursor()
        cursor.execute(data, value)
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return result

    def mssql_connection_fetchone(self, data, value, flag):
        if flag == 'I':
            cursor = self.conn.cursor()
        elif flag == 'II':
            cursor = self.conn_ii.cursor()
        elif flag == 'S':
            cursor = self.conn2.cursor()
        cursor.execute(data, value)
        result_tuple = cursor.fetchone()
        result = dict(zip([desc[0] for desc in cursor.description], result_tuple)) if result_tuple else None
        return result
    
    def mssql_r_status(self, data, bkcode, flag):
        if flag == 'I':
            cursor = self.conn.cursor()
        elif flag == 'S':
            cursor = self.conn2.cursor()
        sql = """UPDATE TBLBANK SET r_status=%s WHERE BKCODE=%s"""
        sql_value = (str(data),str(bkcode))
        cursor.execute(sql,sql_value)
        self.conn.commit()

    def __close__(self):
        self.conn.close()
