import requests
from bs4 import BeautifulSoup
from googletrans import Translator
import textwrap
import time
import sys
import uuid
import requests
import hashlib
from importlib import reload
import json
import os

import time

policy_url = "https://app.m.kuaishou.com/public/index.html#/protocol/detail?draft=1&id=19&uniqueCode=v3_news_1013106586_1535460891301_3"
try:
    response = requests.get(policy_url)
    response.raise_for_status()
    response.encoding = 'utf-8'
except requests.RequestException as e:
    print(f"网络请求出错: {e}")
    import sys
    sys.exit(1)
soup = BeautifulSoup(response.text, 'html.parser')
#忽略内容
#for script in soup(["script", "style", "noscript", "meta", "link"]):
#    script.decompose()
text = soup.get_text(separator='\n', strip=True)
print(f"文本内容：{text}")

'''
reload(sys)

YOUDAO_URL = 'https://openapi.youdao.com/api'
APP_KEY = '744c7e593c3f11bb'
APP_SECRET = 'Hy11TqRGlnfghU3uKOcPgqt6pjhNi5op'


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_URL, data=data, headers=headers)


def connect(text,scr='zh-CHS',des='en'):
    q = text

    data = {}
    data['from'] = scr
    data['to'] = des
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign
    data['vocabId'] = "您的用户词表ID"

    response = do_request(data)
    contentType = response.headers['Content-Type']
    result = json.loads(response.content.decode('utf-8'))  # 解析JSON

    if result.get('errorCode') == '0':  # 成功时返回翻译结果
        return result.get('translation', [''])[0]  # 取第一个翻译结果
    else:
        print(f"翻译失败: {result.get('errorCode')}, {result.get('message')}")
        return ""  # 失败返回空字符串

def translate(text,chunk=4000):
    # 截断文本为多个块
    chunks = [text[i:i + chunk] for i in range(0, len(text), chunk)]
    translated_text = []

    for c in chunks:
        translated_chunk = connect(c)
        #translated_chunk = translated_chunk.decode('utf-8')
        translated_text.append(translated_chunk)

    return ''.join(translated_text)


translated = translate(text)
print(f"翻译文本：{translated}")

file_path = "饿了么_translated.txt"
directory = os.path.dirname(file_path)
if directory and not os.path.exists(directory):
    os.makedirs(directory)

try:
    with open(file_path, 'w') as file:
        file.write(translated)
except IOError as e:
    print(f"写入文件时出现错误: {e}")
'''