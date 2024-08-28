import pymongo
import urllib.parse
import configparser

class MongoDB:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('./config/config.conf', encoding='UTF8')
        self.config_mob = config['MongoDB']
        host1 = self.config_mob['hostname1']
        port = self.config_mob['port']
        username = urllib.parse.quote_plus(self.config_mob['username'])
        password = urllib.parse.quote_plus(self.config_mob['password'])

        try:
            host2 = self.config_mob['hostname2']
            host3 = self.config_mob['hostname3'] # 
            self.conn = pymongo.MongoClient(f'mongodb://{username}:{password}@{host1}:{port},{host2}:{port},{host3}:{port}/?replicaSet=twodigit',maxPoolSize=1)
        except KeyError:
            self.conn = pymongo.MongoClient(f'mongodb://{username}:{password}@{host1}:{port}/')

    def mongodb_connaction(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db = conn[config_mob['db_name']]
        collection = db[table_name]
        collection.insert_one(data)
        conn.close()  # 연결을 닫습니다.
        return collection

    def mongodb_connaction_pre(self, data, table_name):
        config_mob = self.config_mob
        conn = self.conn
        db2 = conn[config_mob['db_name2']]
        collection = db2[table_name]
        collection.insert_one(data)
        conn.close()  # 연결을 닫습니다.
        return collection

    def __close__(self):
        self.conn.close()