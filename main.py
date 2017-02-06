# coding=utf8
# python 3

import requests
from bs4 import BeautifulSoup as bs
import os
import json

"""
# 用库:
BeautifulSoup https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/#id16
requests http://docs.python-requests.org/en/master/user/quickstart/


# 假如客户买的话... (代码加数据1000->700;只数据500)(感觉我引导需求引导得还行... 交流中透露出一些 "咨询", 看他的 utility 了...
TODO:
1. 看example里的格式能否cover所有数据
2. 格式转换咯..
不买就当练习模拟登录了...

模拟登录... http://zqdevres.qiniucdn.com/data/20130909104208/index.html

Pyspider 用 pip 安装时出 XCode 小问题
没有试 Pyspider http://docs.pyspider.org/en/latest/Quickstart/
v2ex 有人说 scrapy 更成熟 :) https://www.v2ex.com/t/188228
没有试 Scrapy http://scrapy-chs.readthedocs.io/zh_CN/0.24/intro/tutorial.html


# 不太相关: html <table> 转 excel xls[x]
http://kyleap.blogspot.com/2015/08/filesaverjs-html-tableexcel.html
http://www.watch-life.net/programming-notes/html-table-2-excel.html
"""

"""搜索结果页的页数范围 [PAGE_FROM, PAGE_TO]

"""

"""
# /html/body/div[2]/div/div[3]/div/div[3]/div/div/div/div[2]/div/div/div/div[1]/div[1]
有直接支持xpath的(bs(尚)不支持)爬虫搜索神器BeautifulSoup和XPath 的使用 www.jianshu.com/p/ea007d71ce2a

div class="v va"
    div class="v-thumb"
        img src=缩略图
    div class="v-link"
        <a href=链接-想去掉?from=>标题

    div class="v-meta-entry"

        播放数 日期


这次用不到:
要处理 js 运行后的结果，可以使用 html5lib。 但我觉得最好的是用 beautifulsoup4 的接口，让它内部用 html5lib。 用Python写爬虫，用什么方式、框架比较好？ https://www.zhihu.com/question/19899608


"""

# 配置
# http://i.youku.com/i/UMjg4MjQ1MzQ0/videos?order=1&page=1
PAGE_FROM_INCLUSIVE = 1
PAGE_TO_INCLUSIVE = 14


def url_for(page):
    return 'http://i.youku.com/i/UMjg4MjQ1MzQ0/videos?order=1&page=%d' % page


def prepare_dir():
    if not os.path.exists('mlsp-result/tmp/'):
        os.mkdir('mlsp-result/tmp/')


def path_for(page):
    return "mlsp-result/tmp/%d.html" % page


def path_for_result():
    return "mlsp-result/result.json"

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
        if os.path.exists(path_for(p)):
            print(u'列表页', p, u'已存在, 不抓了')
        else:
            r = requests.get(url_for(p), headers=headers)
            # print(r.text)
            f = open(path_for(p), "w", encoding="utf-8")
            f.write(r.text)
            f.close()
            print(u'下载保存列表页', p, u'成功')


def parse():
    def safe_ico_SD(v_va):
        """有时,清晰度没写出来。那时返回\"未知\""""
        i_tag = v_va.find('div', class_='v-link').find('div', class_='v-link-tagrt').i
        return i_tag.contents[0] if i_tag is not None else u"未知"

    result = []
    for p in range(PAGE_FROM_INCLUSIVE, PAGE_TO_INCLUSIVE + 1):
        with open(path_for(p), 'r', encoding="utf-8") as fin:
            soup = bs(fin.read())
            v_va_s = soup.find_all('div', class_='v va')
            result.extend(list(map(lambda v_va: {
                "thumbnail-url": v_va.find('div', class_='v-thumb').img['src'],
                "video-page-url": v_va.find(class_='v-link').a['href'],
                "video-quality": safe_ico_SD(v_va),  # 清晰度, 如"超清","标清"
                "duration": v_va.find('div', class_='v-link').find('div', class_='v-link-tagrb').span.contents[0],
                "title": v_va.find('div', class_='v-meta').find('div', class_='v-meta-title').a['title'],
                "publish-date": v_va.find('div', class_='v-meta').find('div', class_='v-meta-entry').find('span',class_='v-publishtime').contents[0],
                "view-count": v_va.find('div', class_='v-meta').find('div', class_='v-meta-entry').find(
                    'span', class_='v-num').contents[0],
            },
                                   v_va_s)))
    result.reverse()  # in-place reverse
    with open(path_for_result(), 'w', encoding="utf-8") as fout:
        # json.dump: Serialize obj as a JSON formatted stream to fp (a .write()-supporting file-like object) using this conversion table.
        # json.dumps: Serialize obj to a JSON formatted str using this conversion table.
        # https://docs.python.org/3.5/library/json.html#py-to-json-table
        # python3 cancels parameter encoding="utf-8"
        # 默认 ensure_ascii=True. 那样，会输出 "title": "\u4e00\u623f\u7b2c\u4e00\u89c6\u89d2 \u9171\u6cb9\u84dd\u732b", 
        ## 而非 "title": "一房第一视角 酱油蓝猫",
        fout.write(json.dumps(obj=result,indent=2,ensure_ascii=False))


    
    for (i,r) in zip(range(1,len(result)+2),result):
        print("MLSP-%03d %s %s" % (i, r['publish-date'],r['title']))
        # print("MLSP-%03d %s %s" % (i, r['title'], r['video_link']))
        # print("MLSP-%03d %-30s %s" % (i, r['title'], r['video_link']))
        


if __name__ == '__main__':
    prepare_dir()
    download()
    parse()
