## 우선 필요한 라이브러리 임포드

import pandas as pd
import time
from selenium import webdriver

pd.set_option('display.max_rows', 100)

data = pd.DataFrame(data=[], columns=['앱이름', '아이디', '리뷰', '별점', '날짜'])

## Selenium의 webdriver를 사용해 페이지를 띄우도록 한다.

driver = webdriver.Chrome('C:\Program Files\Google\Chrome/chromedriver')
url = 'https://play.google.com/store/apps/details?id=com.seoulland.newbird&hl=ko&gl=US'
driver.get(url)

## 그다음 url의 스크롤을 내려서 구글 appstore의 '모든 리뷰 보기' 항목의 xpath를 복사하여 리뷰 데이터를 얻도록 한다.

driver.find_element_by_xpath(
    '//*[@id="fcxH9b"]/div[4]/c-wiz/div/div[2]/div/div/main/div/div[1]/div[6]/div/span/span').click()


## '리뷰 모두 보기'에 해당하는 태그의 xpath를 복사 후 붙였다. 그후,
## 리뷰는 스크롤을 내릴수록 늘어나므로, 스크롤을 내리는 함수도 만들도록 한다.


# 스크롤 다운
def scroll_down(driver):
    driver.execute_script("window.scrollTo(0, 999999999999)")
    time.sleep(1)


scroll_down(driver)

## 이제 데이터를 수집할 것이다. 그런데
## 리뷰 모두 보기 버튼 클릭 후 바로 수집을 하면 태그를 제대로 인식하지 못하는 문제가 발생.

## 따라서 driver.get() 으로 현재 주소를 다시 새로고침 한 뒤 수집.

driver.get('https://play.google.com/store/apps/details?id=com.seoulland.newbird&hl=ko&gl=US')

def crawl(driver, data, k):
    # 어플 이름, 아이디, 리뷰, 별점, 날짜 수집
    app_name = driver.find_element_by_css_selector('.AHFaub')
    user_names = driver.find_elements_by_css_selector('.X43Kjb')
    reviews = driver.find_elements_by_css_selector('.UD7Dzf')
    star_grades = driver.find_elements_by_xpath('//div[@class="pf5lIe"]/div[@role="img"]')
    dates = driver.find_elements_by_css_selector('.p2TkOb')

    # k개의 리뷰를 수집합니다.
    for i in range(k):
        tmp = []
        tmp.append(app_name.text)
        tmp.append(user_names[i].text)
        tmp.append(reviews[i].text)
        tmp.append(star_grades[i].get_attribute('aria-label'))
        tmp.append(dates[i].text)

        # 수집한 1명의 리뷰를 결과 프레임에 추가합니다.
        tmp = pd.DataFrame(data=[tmp], columns=data.columns)
        data = pd.concat([data, tmp])

    print(app_name.text + "앱 리뷰 수집 완료")
    return data


# 스크롤 다운을 한 뒤, 크롤링을 해야 인덱스 에러가 발생하지 않음
scroll_down(driver)

data = crawl(driver, data, 200)
# 인덱스 번호를 다시 0부터 리셋합니다.
data.reset_index(inplace=True, drop=True)
data.head()

# 서울랜드 어플 리뷰 수집 결과


# 2. 데이터 전처리
# 수집한 데이터 중 별점 컬럼은 굳이 문자열로 남겨둘 필요는 없어보인다.
# 숫자값만 남기도록 하겠다.

# 원본 데이터 카피
tmp = data.copy()

# re 라이브러리와 정규표현식을 사용해서 숫자만 뽑아내려고 해보자.

# 그러기 위해 우선 앞에 별표 5 개 부분은 잘라냈다.

# 앞의 별표 5점은 생략
tmp['별점'] = tmp['별점'].apply(lambda x: x[5:])
tmp.head(3)

# 앞 부분 숫자 삭제,그리고 re 라이브러리를 임포트한 후 정규표현식을 사용한다.

# 정규표현식에 대해 간단히 정리하자면

# [a - z]는 a부터 z까지의 알파벳 중 하나를 의미하다.

# [0 - 9] 는 0부터 9까지의 숫자 중 하나를 의미한다.

# *은 앞의 문자(숫자, 특수문자 포함)가 0개 이상 등장함을 의미한다.

# +는 앞의 문자(숫자, 특수문자 포함)가 1개 이상 등장함을 의미한다.

# .은 어떤 문자든 1개가 등장함을 의미한다.

# \(역슬래쉬) 는.이 정규표현식의.이 아니라, 순수한 문자열임을 나타낼 때 표시한다.

import re

m = re.compile('[0-9][\.0-9]*')

tmp['별점'] = tmp['별점'].apply(lambda x: m.findall(x)[0])

# 따라서 정수형 숫자 1개만 있거나, 4.8과 같이 소수점으로 계산된 점수를 추출한다.

tmp.head()

# 데이터 전처리 결과
# 마지막으로 데이터를 저장한다.

#csv파일은 to_csv, excel파일은
# to_excel 함수를 이용하면 된다.

# 파일의 크기가 큰 경우, csv파일은, 를
# 기준으로 값을 저장하기 때문에 효율적입니다.

tmp.to_csv('서울랜드_리뷰평점.csv', encoding='utf-8')
tmp.to_excel('서울랜드_리뷰평점.xlsx')
re = pd.read_csv('서울랜드_리뷰평점.csv', encoding='utf-8')
re.head()


