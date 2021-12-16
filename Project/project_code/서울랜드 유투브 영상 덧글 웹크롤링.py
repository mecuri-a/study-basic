## 웹드라이버, 셀레니움, CCS 셀렉터를 이용한 웹크롤링 텍스트 추출 예제.

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

## 이 과제에서 주로 생생한 후기를 담은 한국인의 VLOG 글을 참조하였고, 조회수와 덧글이 가장 많은
## 영상 위주로 추출하였다. 날짜는 정한대로 2020년 10월~ 2021년 11월까지의 영상들을 모조리 찾아가며
## 데이터를 수집하는 것을 목표로 하였다.
## 크롬 웹드라이버, 셀레니움을 이용한 크롤링

driver = webdriver.Chrome('C:\Program Files\Google\Chrome/chromedriver')
driver.get('https://play.google.com/store/apps/details?id=com.seoulland.newbird&hl=ko&gl=US')

time.sleep(3)

## CCS 셀렉터를 이용한 수집할 엘레먼트 지정

e = driver.find_element_by_tag_name('body')

for i in range(500):
  e.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)

  comments = []

## for문을 통한 닉네임 수집. 한꺼번에 추출할 수도 있으나,
## csv 파일에 깔끔하게 정리하기 위해서는 따로따로 추출해서 csv 파일에 정리하는 것이 좋다.

  for i in range(950):
      try:
          e = driver.find_elements_by_css_selector('h3.ytd-comment-renderer a span')[i].text ## 닉네임 텍스트 추출
          c = driver.find_elements_by_css_selector('https://play.google.com/store/apps/details?id=com.seoulland.newbird&hl=ko&gl=US&showAllReviews=true')[i].text ## 덧글 텍스트 추출
          print(c,e)
          comments.append(c)
      except:
          pass
  print(c)

