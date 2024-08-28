# 국내 언론사 Crawling

## config
 - 서버IP 및 정보 저장

## crawling_site
 - log (로그저장 파일)
 - parser_file (site_parser.py : 본문 파싱 파일)
 - site.json (PM2 실행파일)
 - site.py (언론사 크롤링 파일)

## db_mongo
 - mongo.py (MongoDB 연동 및 명령어 구분 파일)

## zmq_mongo
 - parser_zmq_mongo.py (Parsing 완료 이후 DB 저장을 위한 ZMQ)
 - zmq_mongo.json (PM2 실행파일)



