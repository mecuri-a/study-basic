# -*- coding: utf-8 -*-
import loguru
from tendo import singleton
from time import sleep
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db_mongo.mongo import MongoDB
from parser_file.site_parser import PARSER


class Crawling_site:
    def __init__(self):
        self.harder = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.LOGGER = loguru.logger.bind(name='service')
        self.cry_list = self.category_list()[0]
        self.sry_list = self.category_list()[1]
        self.parser_start = PARSER()
        
    def category_list(self):
        category_list = {'opinion':'오피니언','autonomy':'자치','economy':'경제','society':'사회','local':'지역',
                         'culture':'문화','sport':'스포츠'}
        subcategory = {}
        subcategory['opinion']={'S2N371':'칼럼','S2N120':'3.15광장','S2N118':'바튼소리','S2N114':'사설'}
        subcategory['autonomy']={'S2N37':'지방의회','S2N38':'행정','S2N39':'국회','S2N40':'정당','S2N41':'정부','S2N36':'선거'}
        subcategory['economy']={'S2N46':'경제일반','S2N44':'산업','S2N42':'금융부동산','S2N43':'소비자유통','S2N55':'연구개발'}
        subcategory['society']={'S2N24':'사회일반','S2N21':'사건사고','S2N22':'법원검찰','S2N23':'노동','S2N373':'교육','S2N30':'보건복지','S2N25':'날씨환경'}
        subcategory['local']={'S2N1':'진주','S2N2':'진해','S2N3':'통영','S2N4':'사천','S2N5':'김해','S2N6':'밀양','S2N7':'거제','S2N8':'양산','S2N9':'의령','S2N10':'함안','S2N11':'창녕','S2N12':'고성','S2N13':'남해','S2N14':'하동','S2N15':'산청','S2N16':'함양','S2N17':'거창','S2N18':'합천','S2N19':'지역종합','S2N20':'부산울산'}
        subcategory['culture']={'S2N70':'문화일반','S2N75':'공연전시','S2N71':'책','S2N73':'음악','S2N76':'영화','S2N82':'문화재'}
        subcategory['sport']={'S2N91':'스포츠일반','S2N99':'야구','S2N96':'축구','S2N97':'농구','S2N92':'체육인'}
        return category_list, subcategory
        
        
    def url_list(self):
        c_key = [i for i in self.cry_list.keys()]
        c_values = [i for i in self.cry_list.values()]
        for i in range(len(c_key)):
            s_key = [j for j in self.sry_list[c_key[i]]]
            s_values = [j for j in self.sry_list[c_key[i]].values()]
            for k in range(len(s_key)):
                sk_list = s_key[k]
                sv_list = s_values[k]
                for p in range(1,3):
                    url_list = f'언론사URL 페이지={p},메인카테고리={c_key[i]},서브카테고리={sk_list}'
                    self.LOGGER.info(url_list)
                    res = requests.get(url_list, headers=self.harder)
                    soup = BeautifulSoup(res.content,'lxml')
                    temp = soup.find('ul',attrs={'class':'section-list-sm'})
                    temp_list = temp.find_all('li')
                    self.insert_mongo(temp_list, c_key[i], c_values[i], sk_list, sv_list)
        return i

    ## 1차 parsing 
    def crawler(self, news, c_key, c_values, sk_list, sv_list):
        crawling_site_list = {}
        self.LOGGER.info(f"crawling_site {c_key}, {c_values}, {sv_list} started...")
        href = news.find('a').get('href')
        aid = href.split('idxno=')[-1]
        crawling_site_list['oid'] = '네이버 기준 언론사 이름'
        crawling_site_list['_id'] = 'oid + 기사URL 번호'
        crawling_site_list['sid'] = '메인카테고리'
        crawling_site_list['sid2'] = '서브카테고리'
        crawling_site_list['aid'] = '기사 URL 번호'
        crawling_site_list['headline'] = '기사 헤드라인'
        crawling_site_list['summary'] = '서머리가 있을 없는 경우 None'
        crawling_site_list['category'] = '메인카테고리 명'
        crawling_site_list['subcategory'] = '서브카테고리 명'
        crawling_site_list['press'] = '언론사 이름'
        ## 기자 이름
        try : 
            crawling_site_list['author'] = news.find('span').find_all('em')[0].text.strip()
        except:
            crawling_site_list['author'] = None
        try:
            crawling_site_list['img_url'] = news.find('em').get('style').replace("background-image:url('",'').replace("')",'').strip()
        except:
            crawling_site_list['img_url'] = None
        ## 기사 시간    
        crawling_site_list['article_date'] = news.find('span').find_all('em')[1].text.strip()[:16]

        crawling_site_list['content_url'] = f'https://www.crawling_site.com/news/articleView.html?idxno={aid}'
        crawling_site_list['naver_link'] = None
        sleep(0.9)

        ## body_raw
        body_res = requests.get(crawling_site_list['content_url'], headers=self.harder)
        body_soup = BeautifulSoup(body_res.text,'lxml')
        crawling_site_list['body_raw'] = f"{body_soup}"
        crawling_site_list['article_editdate'] = None
        crawling_site_list['news_date'] = crawling_site_list['article_date'][:10].replace('.','')
        crawling_site_list['insertTime'] = str(datetime.now())
        return crawling_site_list


    def mongo_data(self,crawling_site_list):
        mongo_data = {'_id' : crawling_site_list['_id'],
                        'sid' : crawling_site_list['sid'],
                        'sid2' : crawling_site_list['sid2'],
                        'oid' : crawling_site_list['oid'],
                        'aid' : crawling_site_list['aid'],
                        'news_date' : crawling_site_list['news_date'],
                        'category' : crawling_site_list['category'],
                        'subcategory' : crawling_site_list['subcategory'],
                        'press' : crawling_site_list['press'],
                        'headline' : crawling_site_list['headline'],
                        'summary' : crawling_site_list['summary'],
                        'body_raw' : crawling_site_list['body_raw'],
                        'article_date' : crawling_site_list['article_date'],
                        'article_editdate' : crawling_site_list['article_editdate'],
                        'author' : crawling_site_list['author'],
                        'content_url' : crawling_site_list['content_url'],
                        'naver_link' : crawling_site_list['naver_link'],
                        'img_url' : crawling_site_list['img_url'],
                        'import_result' : 'N',
                        'search_result' : 'N',
                        'insertTime' : crawling_site_list['insertTime'],
                        }
        return mongo_data
        
        
    def insert_mongo(self, temp_main, c_key, c_values, sk_list, sv_list):
        count = 0
        for news in temp_main:
            try:
                crawling_site_list = self.crawler(news, c_key, c_values, sk_list, sv_list)
            except:
                pass
            ## 중복 처리
            try:
                mongo_data = self.mongo_data(crawling_site_list)
                # print(mongo_data)
                MongoDB().mongodb_connaction(mongo_data, 'crawling_site')
                self.parser_start.parser(mongo_data)
                self.LOGGER.info('crawling_site_news Mongo Insert : ' + mongo_data['_id'])
                sleep(1.3)
            except Exception as ee:
                self.LOGGER.error(ee)
                count += 1
                print('count : ',count)
                if count == 10:
                    MongoDB().__close__()
                    sleep(180)
                    return news
        
        
def main():
    start = Crawling_site()
    start.url_list()
        
if __name__ == '__main__':
    me = singleton.SingleInstance()
    times = datetime.today().strftime("%Y%m%d")
    log_format = '[{time:YYYY-MM-DD HH:mm:ss.SSS}] [{process: >5}] [{level.name:>5}] <level>{message}</level>'
    loguru.logger.add(
        sink=f'./crawling_site/logs/crawling_site_Main_{times}.log',
        format=log_format,
        enqueue=True,
        level='INFO'.upper(),
        rotation='10 MB',
    )
    main()