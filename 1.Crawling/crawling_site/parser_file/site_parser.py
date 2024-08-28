# -*- coding: utf-8 -*-
import loguru
from time import sleep
import re
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from db_mongo.mongo import MongoDB
import zmq

'''
media_summary(요약)
strong(소제목)
article_content(본문)
'''
media_summary = {}
strongs = {}
article_contents = {}

class PARSER:
    def __init__(self):
        self.LOGGER = loguru.logger.bind(name='service')
    
    def parser_zmq(self,data):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        try:
            socket.connect('tcp://localhost:5999')
            self.LOGGER.info("Connecting to Server on port 5999")
            socket.send_json(data)
        except Exception as ee:
            self.LOGGER.error(f'socket_conn_error: {ee}')

    def parser(self,data):
        id = data['_id']
        author = data['author']
        subcategory = data['subcategory']
        self.LOGGER.info(f'{id} pre start')
        nsbody = data['body_raw'].replace('<p>','<br>').replace('</p>','<br>')
        ns1 = BeautifulSoup(nsbody,'lxml')
        n_rn = ns1.find('div', attrs={'class':'article-body'})
        ## 본문이 다른 태그 아래 있는 경우
        try :
            n_body = ns1.find('article',attrs={'itemprop':'articleBody'})
        except:
            return
        
        ## 불필요한 태그 제거
        try :
            photo = n_body.find_all('figure')
            for photos in range(len(photo)):
                n_body.find('figure').extract()
        except:
            pass
        try :
            divs = n_body.find_all('div')
            for div in range(len(divs)):
                n_body.find('div').extract()
        except:
            pass
        try :
            scripts = n_body.find_all('script')
            for script in range(len(scripts)):
                n_body.find('script').extract()
        except:
            pass
        try :
            articles = n_body.find_all('article')
            for article in range(len(articles)):
                n_body.find('article').extract()
        except:
            pass
        try :
            styles = n_body.find_all('style')
            for style in range(len(styles)):
                n_body.find('style').extract()
        except:
            pass
        for comment in n_rn.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()


        article_content = []
        counx = 0
        contents = []

        content_list = list(n_rn.children)
        body_content_list = list(n_body.children)

        for i in range(len(content_list)):
            article_contents = {}
            strongs = {}
            media_summary = {}
            content = content_list[i]
            
            ## 기본으로 사용하는 if 문
            if type(content) is Comment:
                continue
            elif type(content) == NavigableString:
                article_content.append(content)
            elif type(content) == Tag:
                if content.name == 'br':
                    continue

                ## media_summary 첫번째 
                if '<h2 class="subheading">' in str(content):
                    media_summary['id'] = id+f'.{counx}'
                    media_summary['type'] = 'media_summary'
                    mmc = n_rn.find('h2',attrs={'class':'subheading'})
                    media_list = [re.sub('(<([^>]+)>)', '', i).strip() for i in  str(mmc).split('<br/>')]
                    media_list = list(filter(None, media_list))
                    if not media_list:
                        pass
                    else:
                        media_summary['content'] = media_list
                        contents.append(media_summary)
                        counx += 1

        ## 본문이 다른 태그 아래 있는 경우
        for i in range(len(body_content_list)):
            article_contents = {}
            strongs = {}
            body_content = body_content_list[i]
            
            ## 기본으로 사용하는 if 문
            if type(body_content) is Comment:
                continue
            elif type(body_content) == NavigableString:
                article_content.append(body_content)
            elif type(body_content) == Tag:
                if body_content.name == 'br':
                    continue

                ## strong
                if '<strong>' in str(body_content) :
                    article_content = [i.replace('\xa0',' ').replace('\r','').replace('\t','').replace('\n','').replace('&lt','<').replace('&gt','>').strip() for i in article_content]
                    article_content = list(filter(None, article_content))
                    if not article_content:
                        pass
                    else:
                        article_contents['id'] = f'{id}.{counx}'
                        article_contents['type'] = 'article_content'
                        article_contents['content'] = article_content
                        contents.append(article_contents)
                        counx += 1
                        article_content = []

                    strongs['id'] = f'{id}.{counx}'
                    strongs['type'] = 'strong'
                    storng_list = re.sub('(<([^>]+)>)', '', str(body_content)).replace('\r','').replace('\n','').replace('\xa0',' ').strip()
                    if not storng_list:
                        pass
                    else:
                        strongs['content'] = storng_list
                        contents.append(strongs)
                        counx += 1
                        article_content = []

                else:
                    bodys = re.sub('(<([^>]+)>)', '', str(body_content))
                    bodys = str(bodys).replace('\n','').strip()
                    article_content.append(bodys)


        article_content = [i.replace('\xa0',' ').replace('\r','').replace('\t','').replace('\n','').replace('&lt;','<').replace('&gt;','>').replace(f'/{author}','').strip() for i in article_content]
        article_content = list(filter(None, article_content))
        ## 마지막 문장 진행
        if not article_content:
            pass
        else:
            article_contents['id'] = f'{id}.{counx}'
            article_contents['type'] = 'article_content'
            article_contents['content'] = article_content
            contents.append(article_contents)

        data['contents'] = data.pop('body_raw')
        data['contents'] = contents
        # print(data['contents'])
        try :
            if '[포토]' in data['headline'] or '[영상]' in data['headline']:
                pass
            else:
                data['table_name'] = 'idomin_pre'
                self.parser_zmq(data)
                self.LOGGER.info(f'{id} pre insert')
                sleep(0.1)
                # return data
        except Exception as error:
            self.LOGGER.error(error)
        finally:
            self.LOGGER.info(f'db_perser {id} End')
        