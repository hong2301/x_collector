from DrissionPage import Chromium, ChromiumOptions
import time
import random
import csv
import os
import re

tabPort = 2728
dp=Chromium(tabPort)
tab=dp.get_tab()

def seeMoreClick(ele):
    try:
        btns=ele.eles("@@tag()=button@@class=css-146c3p1 r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-fdjqy7",timeout=1)
        for btnItem in btns:
            if 'Show more' in btnItem.text:
                btnItem.click(by_js=True)
                return True
        return False
    except Exception as e:
        return False

# 遍历 input.csv（url,关键词）
tasks = []
with open("input.csv", 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines[1:]:  # 跳过表头
        line = line.strip()
        if not line:
            continue
        parts = line.split(',', 1)
        url = parts[0].strip()
        keyword = parts[1].strip() if len(parts) > 1 else ''
        tasks.append((url, keyword))

for i, (url, keyword) in enumerate(tasks):
    print(f"{i + 1}/{len(tasks)}: {url} | 关键词: {keyword}")
    tab.get(url)

    # 随机等待 3-5 秒
    time.sleep(random.uniform(5, 10))

    # 获取帖子
    checkNum=0
    postCount=0
    urls=[]
    while checkNum<5 and postCount<15:
        checkNum+=1
        postEles=tab.eles("@@class=css-175oi2r r-18u37iz r-1udh08x r-1c4vpko r-1c7gwzm r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21@@tag()=article",timeout=1)
        for postEle in postEles:
            try:
                url=''
                fbz=''
                fbsj=''
                zw=''
                dz=''
                hf=''
                zf=''
                ll=''
                ht=''

                urlEle=postEle.ele("@@tag()=a@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21",timeout=1)
                if urlEle:
                    url=urlEle.link
                    timeEle=urlEle.ele("@tag()=time",timeout=1)
                    if timeEle:
                        fbsj=timeEle.attr("datetime")
                if url in urls:
                    continue
                postEle.scroll.to_see()
                checkNum=0
                urls.append(url)

                fbzEle=postEle.ele("@@class=css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3",timeout=1)
                if fbzEle:
                    fbz=fbzEle.text

                zwEle=postEle.ele("@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-bnwqim",timeout=1)
                if zwEle:
                    seeMoreClick(postEle)
                    time.sleep(random.uniform(1,2))
                    zw=zwEle.text
                    # 提取正文末尾的标签 #xxx
                    tags = re.findall(r'#\w+', zw)
                    ht = ' '.join(tags)

                sjEle=postEle.ele("@class=css-175oi2r r-1kbdv8c r-18u37iz r-1wtj0ep r-1ye8kvj r-1s2bzr4",timeout=1)
                if sjEle:
                    sj=sjEle.attr("aria-label")
                    # 解析4个指标: repost, likes, bookmark/replies, views
                    m_repost  = re.search(r'(\d[\d,]*)\s*repost', sj)
                    m_likes   = re.search(r'(\d[\d,]*)\s*likes?', sj)
                    m_replies = re.search(r'(\d[\d,]*)\s*repl(?:y|ies)', sj)
                    m_book    = re.search(r'(\d[\d,]*)\s*bookmark', sj)
                    m_views   = re.search(r'(\d[\d,]*)\s*views?', sj)
                    zf = m_repost.group(1)  if m_repost  else '0'
                    hf = m_replies.group(1) if m_replies else (m_book.group(1) if m_book else '0')
                    dz = m_likes.group(1)   if m_likes   else '0'
                    ll = m_views.group(1)   if m_views   else '0'

                # 即刻写入 CSV
                CSV_PATH = "output.csv"
                file_exists = os.path.exists(CSV_PATH)
                with open(CSV_PATH, 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['发布者', '发布时间', '正文', '点赞数', '回复数', '转发数', '浏览量', '话题标签', '关键词', '链接'])
                    writer.writerow([fbz, fbsj, zw, dz, hf, zf, ll, ht, keyword, url])
                print(f"已写入: {fbz} | {fbsj}")
                postCount += 1
                if postCount >= 15:
                    break
            except Exception as e:
                pass

