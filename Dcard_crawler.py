#在程式碼的一開始導入(import)我們在接下來會用到的packages
#Packages可以想成APP，導入Packages就像在把APP下載下來
#這樣就可以確定在接下來的編碼我們能運用這些APP所帶來的功能
import pandas as pd
import requests
import json
import numpy as np
import matplotlib.pyplot as plt
from selenium import webdriver
from time import sleep
import re

import jieba
import jieba.analyse
from wordcloud import WordCloud

from snownlp import SnowNLP

def to_csv(x):
    x.to_csv(index=False)
    from pathlib import Path  
    filepath = Path('desktop/dcard.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    x.to_csv(filepath)

if __name__ == '__main__':
    #參考來源 https://ithelp.ithome.com.tw/articles/10277885?sc=iThelpR
    #由於Dcard網站的設計是一種動態網站，透過不斷往下方捲動來讀取新文章，
    #也因此我們為了能讀取更多的資料，我們透過Selenium中windowscroll的功能靠程式碼自動往下滾動卷軸讀取新資料協助爬蟲的過程。
    scroll_time = int(input('請輸入想要捲動幾次：'))
    driver = webdriver.Chrome()
    driver.get('https://www.dcard.tw/search/posts?query=tinder') # fill the Dcard search result page url
    results = []
    prev_ele = None
    #接下來的for迴圈是要執行卷軸滾動與資料讀取
    #簡單來說就是在每一次的滾動過程中去將文章的標題，連結，讚數，文章代碼儲存下來
    for now_time in range(1, scroll_time+1):
        sleep(1)
        eles = driver.find_elements_by_class_name('sc-b205d8ae-0')
        # 若串列中存在上一次的最後一個元素，則擷取上一次的最後一個元素到當前最後一個元素進行爬取
        try:    
            eles = eles[eles.index(prev_ele):]   #這一行是為了避免文章的重複擷取 
            #概念上就是從上一次最後存取的文章之後開始存取新的資料
        except:
            pass
        #擷取標題，連結，讚數，文章代碼並將這些代碼儲存起來
        for ele in eles:
            try:
                title = ele.find_element_by_class_name('sc-b205d8ae-3').text
                href = ele.find_element_by_class_name('sc-b205d8ae-3').get_attribute('href')
                like = ele.find_element_by_class_name('sc-28312033-3').text
                article_id = href[href.rfind("/")+1:]
                result = {
                    'title': title,
                    'href': href,
                    'like': like,
                    'id':article_id,
                }
                results.append(result) #放到results裡
            except:
                pass
        prev_ele = eles[-1]
        print(f"now scroll {now_time}/{scroll_time}")
        js = "window.scrollTo(0, document.body.scrollHeight);"
        driver.execute_script(js)
    #將擷取下來的資料存入Dataframe的格式中  
    df = pd.DataFrame(results, columns =['title', 'href', 'like','id'], dtype = int) 
    #to_csv(df)
    driver.quit()
    

#接下來我們可以開始針對擷取下來的資料內文進行分析
#為了抓取內文，我們需要確定文章id沒有重複
contents = []
ids = []
if len(df) == len(results):   
    for i in range(len(results)):
        ids.append(results[i]['id'])
elif len(df) != len(results):      
    for i in range(len(df)):
        ids.append(df['id'][i])
ids = np.unique(ids).tolist()
#清洗func
#為了避免符號，連結等的影響，我們用以下的程式碼移除這些符號
#以下就是我們設計的清洗function
#首先是以句子的開頭來進行清洗
#針對開頭為以下四種的內文句子我們會將他排除在我們的內文分析之外
def remove_punctuation(line):
    str(line)
    rule = re.compile("[^a-zA-Z0-9\u4e00-\u9fa5]")
    line = rule.sub('',line)
    return line
def separate(content):
    #以換行符號作為分割
    a = content.split('\n')
    #清洗2次
    for x in range(0,2):
        for i in a:
            if i[0:4] == 'http':
                a.remove(i)
            if i == '':
                a.remove(i)
            if i == ' ':
                a.remove(i)
            if i == '-':
                a.remove(i)
    return(a)
    
count = 0
#使用API+運用設計好的Function清洗資料
for i in ids:
    try:
        sleep(15) # 為避免被網站阻擋爬蟲，設置時間延遲
        r = requests.get(f'https://www.dcard.tw/service/api/v2/posts/{i}') #參考API https://blog.jiatool.com/posts/dcard_api_v2/
        response = r.text
        data = json.loads(response)
        #清洗
        content = data['content']
        content = separate(content)
        for x in content:
            x = remove_punctuation(x)
            if len(x) > 0: #不是空的句子就加入contents
                contents.append(x)
        count += 1
        print('done '+str(count)+"/"+str(len(ids))) 
    except:
        print('error '+str(count)+"/"+str(len(ids)))
#將清洗後的資料寫成txt並匯出
with open('desktop/text.txt', 'w',encoding='utf-8') as f:
    for line in contents:
        f.write(line)
        f.write('\n')

#透過TF-IDF Method來做字詞分析與統計
text = open('desktop/text.txt', 'r',encoding='utf-8').read()#由桌面匯入清洗過的內文資料  
jieba.set_dictionary('dict.txt.big.txt')
jieba.analyse.set_stop_words('stopwords.txt') #停用詞庫 #去除無用字眼如:哈哈，哈哈哈
tags = jieba.analyse.extract_tags(text, topK=20, withWeight=True) # 找出最重要的字詞TOP20
for tag, weight in tags: #印出重要性排名
    print(tag + "," + str(int(weight * 1000)))
    
dic = {}
for tag, weight in tags:
    dic[tag] = int(weight * 1000)

#將字詞分析統計結果繪製成bar chart
myList = dic.items()
x, y = zip(*myList) 
plt.rcParams['figure.figsize'] = [16, 9]
plt.bar(x, y)

# 自然語言分析範例
s = SnowNLP(text)
# 分析相關字詞的正負面情緒比
sum = 0
times = 0
for sentence in s.sentences:
    if (SnowNLP(sentence).sentiments) != 0.5: #去除中立情緒
        sum = sum + (SnowNLP(sentence).sentiments)
        times += 1
print("正負面情緒比為："+ str(sum/times))

#將結果繪製成文字雲(wordcloud)
wc = WordCloud(background_color="white",width=1920,height=1080, max_words=20,relative_scaling=0.5,normalize_plurals=False,font_path="simsun.ttc",prefer_horizontal=1).generate_from_frequencies(dic)
plt.imshow(wc)
