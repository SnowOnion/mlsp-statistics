#!/usr/bin/env python3
# coding=utf8

import requests
from bs4 import BeautifulSoup as bs
import os
import json
from datetime import timedelta, timezone, datetime
import copy

"""
# 用库:
BeautifulSoup https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/#id16
requests http://docs.python-requests.org/en/master/user/quickstart/

# 数据源

# http://i.youku.com/i/UMjg4MjQ1MzQ0/videos?order=1&page=1

/html/body/div[2]/div/div[3]/div/div[3]/div/div/div/div[2]/div/div/div/div[1]/div[1]

有直接支持xpath的(bs(尚)不支持)爬虫搜索神器BeautifulSoup和XPath 的使用 www.jianshu.com/p/ea007d71ce2a

div class="v va"
    div class="v-thumb"
        img src=缩略图
    div class="v-link"
        <a href=链接-想去掉?from=>标题

    div class="v-meta-entry"

        播放数 日期


# 这次用不到:
要处理 js 运行后的结果，可以使用 html5lib。 但我觉得最好的是用 beautifulsoup4 的接口，让它内部用 html5lib。 用Python写爬虫，用什么方式、框架比较好？ https://www.zhihu.com/question/19899608
"""

# 配置(但是既然撒萌萌停更了,也不会再增加了……)
PAGE_FROM_INCLUSIVE = 1
PAGE_TO_INCLUSIVE = 14
PATH_OF_HTML_TMP = 'mlsp-result/html-tmp/'
PATH_OF_RAW_RESULT = 'mlsp-result/result-raw.json'
PATH_OF_SONION_CONVERTED_RESULT = 'mlsp-result/result-converted-for-lee.json'


def url_for(page):
    return 'https://i.youku.com/i/UMjg4MjQ1MzQ0/videos?order=1&page=%d' % page


def path_for_html(page):
    return PATH_OF_HTML_TMP + "%d.html" % page


# 常函数哈哈哈
def path_for_raw_result():
    return PATH_OF_RAW_RESULT


def path_for_converted_result():
    return PATH_OF_SONION_CONVERTED_RESULT


############### 配置结束 ###############

def prepare_dir():
    if not os.path.exists(PATH_OF_HTML_TMP):
        os.makedirs(PATH_OF_HTML_TMP)


def download():
    # 嘿, 有防爬取
    # http://stackoverflow.com/questions/10606133/sending-user-agent-using-requests-library-in-python
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    })

    for p in range(PAGE_FROM_INCLUSIVE, PAGE_TO_INCLUSIVE + 1):
        print(u'获取列表页', p)
        # 简单粗暴的增量抓取 # 嗯一个issue是 播放数是会变的
        # 许多种判断法 2333 http://stackoverflow.com/questions/82831/how-do-i-check-whether-a-file-exists-using-python
        if os.path.exists(path_for_html(p)):
            print(u'列表页', p, u'已存在, 不抓了')
        else:
            r = requests.get(url_for(p), headers=headers)
            # print(r.text)
            f = open(path_for_html(p), "w", encoding="utf-8")
            f.write(r.text)
            f.close()
            print(u'下载保存列表页', p, u'成功')


def parse():
    def safe_ico_SD(v_va):
        """有时,清晰度没写出来。那时返回\"未知\""""
        i_tag = v_va.find('div', class_='v-link').find('div', class_='v-link-tagrt').i
        return i_tag.contents[0] if i_tag is not None else u"未知"

    data_result = []
    for p in range(PAGE_FROM_INCLUSIVE, PAGE_TO_INCLUSIVE + 1):
        with open(path_for_html(p), 'r', encoding="utf-8") as fin:
            soup = bs(fin.read())
            v_va_s = soup.find_all('div', class_='v va')
            data_result.extend(list(map(lambda v_va: {
                "thumbnail-url": v_va.find('div', class_='v-thumb').img['src'],
                "video-page-url": v_va.find(class_='v-link').a['href'],
                "video-quality": safe_ico_SD(v_va),  # 清晰度, 如"超清","标清"
                "duration": v_va.find('div', class_='v-link').find('div', class_='v-link-tagrb').span.contents[0],
                "title": v_va.find('div', class_='v-meta').find('div', class_='v-meta-title').a['title'],
                "publish-date": v_va.find('div', class_='v-meta').find('div', class_='v-meta-entry').find('span',
                                                                                                          class_='v-publishtime').contents[
                    0],
                "view-count": v_va.find('div', class_='v-meta').find('div', class_='v-meta-entry').find(
                    'span', class_='v-num').contents[0],
            },
                                        v_va_s)))
    data_result.reverse()  # in-place reverse

    result = {
        "update": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S%z"),
        "data": data_result
    }

    with open(path_for_raw_result(), 'w', encoding="utf-8") as fout:
        # json.dump: Serialize obj as a JSON formatted stream to fp (a .write()-supporting file-like object) using this conversion table.
        # json.dumps: Serialize obj to a JSON formatted str using this conversion table.
        # https://docs.python.org/3.5/library/json.html#py-to-json-table
        # python3 cancels parameter encoding="utf-8"
        # 默认 ensure_ascii=True. 那样，会输出 "title": "\u4e00\u623f\u7b2c\u4e00\u89c6\u89d2 \u9171\u6cb9\u84dd\u732b", 
        ## 而非 "title": "一房第一视角 酱油蓝猫",
        fout.write(json.dumps(obj=result, indent=2, ensure_ascii=False))

    for (i, r) in zip(range(1, len(data_result) + 2), data_result):
        print("MLSP-%03d %s %s" % (i, r['publish-date'], r['title']))
        # print("MLSP-%03d %s %s" % (i, r['title'], r['video_link']))
        # print("MLSP-%03d %-30s %s" % (i, r['title'], r['video_link']))


if __name__ == '__main__':
    prepare_dir()
    download()
    parse()
