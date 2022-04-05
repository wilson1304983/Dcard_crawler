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

from PIL import Image
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from snownlp import SnowNLP

def to_csv(x):
    x.to_csv(index=False)
    from pathlib import Path  
    filepath = Path('desktop/dcard.csv')  
    filepath.parent.mkdir(parents=True, exist_ok=True)  
    x.to_csv(filepath)

if __name__ == '__main__':
    scroll_time = int(input('請輸入想要捲動幾次'))
    driver = webdriver.Chrome()
    driver.get('https://www.dcard.tw/search/posts?field=all&query=%E7%B4%85%E7%89%9B&sort=relevance') # fill the Dcard search result page url
    results = []
    prev_ele = None
    for now_time in range(1, scroll_time+1):
        sleep(2)
        eles = driver.find_elements_by_class_name('tgn9uw-0')
        # 若串列中存在上一次的最後一個元素，則擷取上一次的最後一個元素到當前最後一個元素進行爬取
        try:
            # print(eles)
            # print(prev_ele)
            eles = eles[eles.index(prev_ele):]
        except:
            pass
        for ele in eles:
            try:
                title = ele.find_element_by_class_name('tgn9uw-3').text
                href = ele.find_element_by_class_name('tgn9uw-3').get_attribute('href')
                like = ele.find_element_by_class_name('cgoejl-3').text
                article_id = href[href.rfind("/")+1:]
                result = {
                    'title': title,
                    'href': href,
                    'like': like,
                    'id':article_id,
                }
                results.append(result)
            except:
                pass
        prev_ele = eles[-1]
        print(f"now scroll {now_time}/{scroll_time}")
        js = "window.scrollTo(0, document.body.scrollHeight);"
        driver.execute_script(js)
        
    df = pd.DataFrame(results, columns =['title', 'href', 'like','id'], dtype = int) 
    to_csv(df)
    #print(results)
    driver.quit()
    
#df = pd.read_csv('desktop/dcard.csv',encoding='unicode_escape')

#抓留言 爬內文
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
def remove_punctuation(line):
    str(line)
    rule = re.compile("[^a-zA-Z0-9\u4e00-\u9fa5]")
    line = rule.sub('',line)
    return line
def separate(content):
    #以換行符號作為分割
    a = content.split('\n')
    #奇怪的洗兩次
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
    
for i in ids:
    try:
        sleep(20) #too short will be blocked
        r = requests.get(f'https://www.dcard.tw/service/api/v2/posts/{i}')
        response = r.text
        data = json.loads(response)
        #清洗
        content = data['content']
        content = separate(content)
        for x in content:
            x = remove_punctuation(x)
            if len(x) > 0:
                contents.append(x)
        print('done')
    except:
        print('error')
#寫出txt
with open('desktop/text.txt', 'w',encoding='utf-8') as f:
    for line in contents:
        f.write(line)
        f.write('\n')
        
#字詞分析、統計
text = open('desktop/text_all.txt', 'r',encoding='utf-8').read()
jieba.set_dictionary('dict.txt.big.txt')
jieba.analyse.set_stop_words('stopwords.txt') #停用詞庫
tags = jieba.analyse.extract_tags(text, topK=20, withWeight=True)
for tag, weight in tags:
    print(tag + "," + str(int(weight * 1000)))
    
#文字雲
dic = {}
for tag, weight in tags:
    dic[tag] = int(weight * 1000)
#bar chart
myList = dic.items()
x, y = zip(*myList) 
plt.bar(x, y)

# 自然語言分析範例
s = SnowNLP(text)
# 列出套件斷句的情況
sum = 0
times = 0
for sentence in s.sentences:
    if (SnowNLP(sentence).sentiments) != 0.5:
        #print(str(sentence)+"："+str(SnowNLP(sentence).sentiments))
        sum = sum + (SnowNLP(sentence).sentiments)
        times += 1
print(sum/times)

#wordcloud
wc = WordCloud(background_color="white",width=1920,height=1080, max_words=20,relative_scaling=0.5,normalize_plurals=False,font_path="simsun.ttc",prefer_horizontal=1).generate_from_frequencies(dic)
plt.imshow(wc)

