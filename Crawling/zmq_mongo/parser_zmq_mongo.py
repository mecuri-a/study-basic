# -*- coding: utf-8 -*-
import loguru
import zmq
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db_mongo.mongo import MongoDB


class Parser_zmq_mongo():
    def __init__(self):
        self.LOGGER = loguru.logger.bind(name='service')
    
    def mongo_per(self,data):
        table_name = data['table_name']
        del data['table_name']
        try:
            MongoDB().mongodb_connaction_pre(data, table_name)
            self.LOGGER.info(f'{table_name} MongoDB Insert Ok')
        except:
            self.LOGGER.info(f'{table_name} MongoDB Insert False')

if __name__ == '__main__':
    start = Parser_zmq_mongo()
    context = zmq.Context()

    times = datetime.today().strftime("%Y%m%d")
    log_format = '[{time:YYYY-MM-DD HH:mm:ss.SSS}] [{process: >5}] [{level.name:>5}] <level>{message}</level>'
    loguru.logger.add(
        sink=f'./zmq_mongo/logs/zmq_insert_{times}.log',
        format=log_format,
        enqueue=True,
        level='INFO'.upper(),
        rotation='10 MB',
    )

    # Socket to receive messages on
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://*:5999")

    while True:
        data = receiver.recv_json()
        start.mongo_per(data)