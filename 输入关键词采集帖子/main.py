from DrissionPage import Chromium, ChromiumOptions
import time
import random
import csv
import os
import re
import html
import json
import requests
from lxml import html as lh

# 每条链接最多采集的帖子数（按需求每 input 采 100 条）
MAX_POSTS_PER_LINK = 999999999999999
# 帖子页面下是否采集评论贴
isCollectReplyPost=False

tabPort = 5268
dp=Chromium(tabPort)
tab=dp.get_tab()
# tab.ele("@class=asdf",timeout=0.1).click()
def noResult(tab):
    try:
        spanEles=tab.eles("@@class=css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3@@tag()=span",timeout=0.5)
        for spanEle in spanEles:
            if 'No results' in spanEle.text:
                return True
        return False
    except Exception as e:
        return False


def seeMoreClick(ele):
    try:
        btns=ele.eles("@@tag()=button@@class=css-146c3p1 r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-fdjqy7",timeout=0.05)
        for btnItem in btns:
            if 'Show more' in btnItem.text:
                btnItem.click(by_js=True)
                return True
        btns=ele.eles("@@tag()=button@@class=css-g5y9jx r-16y2uox r-1cwvpvk r-1noe1sz r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l",timeout=0.05)
        for btnItem in btns:
            if 'Show replies' in btnItem.text:
                btnItem.click(by_js=True)
                return True
        return False
    except Exception as e:
        return False

def _imgToSpan(m):
    """把正文里的 emoji <img> 替换为 <span>alt文本</span>，并转义防破坏解析"""
    am = re.search(r'alt="([^"]*)"', m.group(0))
    alt = am.group(1) if am else ''
    return f'<span>{html.escape(alt)}</span>'

def parse_quote_url(q):
    """从引用贴 div 的 React fiber 解析被引用帖完整链接；找不到返回 ''"""
    rk = q.run_js('return Object.keys(this).filter(k => k.startsWith("__react"))')
    fiber_key = next((k for k in (rk or []) if 'Fiber' in k), None)
    if not fiber_key:
        return ''
    info = q.run_js(f'''
        let f = this["{fiber_key}"]; let out = []; let n = 0;
        while (f && n < 15) {{
            let p = f.memoizedProps; let s = p ? JSON.stringify(p) : '';
            if (s) {{
                let hits = s.match(/https?:\\/\\/(?:twitter|x)\\.com\\/[^"\\\\]+\\/status\\/\\d+/g);
                if (hits) out.push(hits[0]);
            }}
            f = f.return; n++;
        }}
        return out.join('|');''')
    return (info.split('|')[0] if info else '').replace('https://twitter.com/', 'https://x.com/')

def append_image_csv(img_url, img_b64):
    """追加图片记录到图片 CSV（追加模式）：图片链接, base64 数据(data URI), OCR 识别(待填)"""
    IMG_CSV = 'image_ocr.csv'
    file_exists = os.path.exists(IMG_CSV)
    with open(IMG_CSV, 'a', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(['图片链接', 'base64数据', 'ocr识别'])
        w.writerow([img_url, f'data:image/webp;base64,{img_b64}', ''])

def expand_url(u, timeout=10):
    """展开短链/跳转链接，返回最终完整 URL；超时/失败记录为空字符串。走本机代理(7897)"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
    proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
    # GET 优先：一定能拿到跟随 302 后的最终 URL
    try:
        r = requests.get(u, allow_redirects=True, timeout=timeout, headers=headers, proxies=proxies, stream=True)
        return r.url or ''
    except Exception:
        pass
    try:
        r = requests.head(u, allow_redirects=True, timeout=timeout, headers=headers, proxies=proxies)
        return r.url or ''
    except Exception:
        pass
    return ''

def test_expand_urls():
    """测试 expand_url（走代理）：展开真实链接、无跳转原样、不可达兜底"""
    cases = [
        'https://x.com/iChongqing_CIMC',                  # 真实账号页，无重定向 -> 原样
        'https://en.wikipedia.org/wiki/Twitter',          # 无跳转 -> 原样
        'https://www.chinadaily.com.cn/',                 # 无跳转 -> 原样
        'https://nonexistent-domain-xyz-12345.invalid/a', # 不可达 -> 记录为空
    ]
    for u in cases:
        final = expand_url(u)
        print(f'{u}\n  -> {final}\n')

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

# 输入开始/结束索引，支持分段采集（1-based，对应 input.csv 行号）
start = int(input(f"请输入开始索引 (1~{len(tasks)}): ").strip())
end = int(input(f"请输入结束索引 (1~{len(tasks)}): ").strip())
start = max(1, min(start, len(tasks)))
end = max(start, min(end, len(tasks)))

for i, (url, keyword) in enumerate(tasks[start - 1:end], start=start):
    try:
        task_url = url
        print(f"{i}/{len(tasks)}: {task_url} | 关键词: {keyword}")
        tab.get(task_url)
        tab.scroll.to_top()

        # 获取帖子
        checkNum=0
        postCount=0
        urls=[]
        while checkNum<50 and postCount<MAX_POSTS_PER_LINK:
            checkNum+=1
            time.sleep(random.uniform(0.1, 0.2))
            noResultFlag=noResult(tab)
            if noResultFlag:
                print(f"[{i}] 无结果，跳过")
                time.sleep(random.uniform(60, 90))
                break
            postEles=tab.eles("@tag()=article",timeout=1)
            for postEle in postEles:
                postUrl=''
                fbz=''
                fbzNc=''
                fbsj=''
                zw=''
                lang=''
                mentions=''
                wailian=''
                wailian_final=''
                dz=''
                hf=''
                sc=''
                zf=''
                ll=''
                ht=''
                mediaData=[]
                isRetweet=0
                isReply=0
                isQuote=0
                conversationId=''
                retweetedPostId=''
                quotedPostId=''
                inReplyToPostId=''
                inReplyToUserId=''
                quotePostRetweetCount=''

                try:

                    if seeMoreClick(tab):
                        time.sleep(random.uniform(1,2))

                    

                    urlEle=postEle.ele("@@tag()=a@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21",timeout=0.05)
                    if not urlEle:
                        urlEle=postEle.ele("@@tag()=a@@class=css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21",timeout=0.05)
                    if urlEle:
                        postUrl=urlEle.link
                        timeEle=urlEle.ele("@tag()=time",timeout=0.05)
                        if timeEle:
                            fbsj=timeEle.attr("datetime")
                    if postUrl in urls:
                        continue
                    postEle.scroll.to_see()
                    checkNum=0
                    urls.append(postUrl)

                    replyEle=postEle.ele("@class=css-g5y9jx r-4qtqp9 r-zl2h9q",timeout=0.1)
                    if replyEle:
                        if 'Replying' in  replyEle.text:
                            isReply=1
                            # 去掉前面的 "Replying to"，只保留被回复的账号
                            inReplyToUserId=replyEle.text.split('Replying to', 1)[-1].strip()

                    # 引用贴：精确匹配 div[role=link] 且含 tweetText（css-g5y9jx 过于宽泛会误判）
                    for quoteEle in postEle.eles('xpath://div[@role="link"]', timeout=0.1):
                        if 'tweetText' in (quoteEle.inner_html or ''):
                            isQuote=1
                            qUrl = parse_quote_url(quoteEle)  # 从 React fiber 解析被引用帖完整链接
                            if qUrl:
                                quotedPostId = qUrl.rsplit('/status/', 1)[-1]
                            break

                    fbzEles=postEle.eles("@@class=css-g5y9jx r-1wbh5a2 r-dnmrzs@@tag()=div",timeout=0.05)
                    for fbzEle in fbzEles:
                        if fbzEle.text:  # 先判断是否有 text
                            if fbzEle.text[0] == '@':  # 首字符是否为 @
                                fbz=fbzEle.text
                                break  # 赋值后结束循环
                    
                    fbzNcEle=postEle.ele("@class=css-g5y9jx r-1awozwy r-18u37iz r-1wbh5a2 r-dnmrzs",timeout=0.05)
                    if fbzNcEle:
                        fbzNc=fbzNcEle.text

                    zwEle=postEle.ele("@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-bnwqim",timeout=0.05)
                    if not zwEle:
                        zwEle=postEle.ele("@@class=css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-1inkyih r-16dba41 r-bnwqim r-135wba7",timeout=0.05)
                    if zwEle:
                        # 正文语言
                        lang=zwEle.attr('lang')
                        if seeMoreClick(postEle):
                            time.sleep(random.uniform(1,2))
                        # 表情保留：<img> 换成 <span>alt</span>，再交给 lxml 用 xpath 取文本，其余原文不动
                        inner = re.sub(r'<img\b[^>]*>', _imgToSpan, zwEle.inner_html)
                        doc = lh.fromstring(inner)
                        zw = ''.join(doc.xpath('//text()'))
                        # 提取正文末尾的标签 #xxx
                        tags = re.findall(r'#\w+', zw)
                        ht = ' '.join(tags)
                        # 提及账号：保存正文里所有被 @ 的账号（空格分隔）
                        mentions = ' '.join(re.findall(r'@\w+', zw))
                        # 外链原始地址：正文中全部外链 URL（a 标签的 http/https href，排除话题/提及的相对路径）
                        wailian = ' '.join(re.findall(r'<a[^>]+href="(https?://[^"]+)"', inner))
                        # 外链最终地址：短链跟随重定向，保存最终完整 URL
                        wailian_final = ' '.join(expand_url(x) for x in wailian.split()) if wailian else ''

                    sjEle=postEle.ele("@class=css-g5y9jx r-1kbdv8c r-18u37iz r-1wtj0ep r-1ye8kvj r-1s2bzr4",timeout=0.05)
                    if not sjEle:
                        sjEle=postEle.ele("@class=css-g5y9jx r-1kbdv8c r-18u37iz r-1oszu61 r-3qxfft r-n7gxbd r-2sztyj r-1efd50x r-5kkj8d r-h3s6tt r-1wtj0ep",timeout=0.05)
                        
                    if sjEle:
                        sj=sjEle.attr("aria-label")
                        # 解析5个指标: repost, likes, replies, bookmark, views
                        m_repost  = re.search(r'(\d[\d,]*)\s*repost', sj)
                        m_likes   = re.search(r'(\d[\d,]*)\s*likes?', sj)
                        m_replies = re.search(r'(\d[\d,]*)\s*repl(?:y|ies)', sj)
                        m_book    = re.search(r'(\d[\d,]*)\s*bookmark', sj)
                        m_views   = re.search(r'(\d[\d,]*)\s*views?', sj)
                        zf = m_repost.group(1)  if m_repost  else '0'
                        hf = m_replies.group(1) if m_replies else '0'
                        sc = m_book.group(1)    if m_book    else '0'
                        dz = m_likes.group(1)   if m_likes   else '0'
                        ll = m_views.group(1)   if m_views   else '0'
                    
                    # 媒体数据
                    mediaBox=postEle.ele("@class=css-g5y9jx r-9aw3ui",timeout=0.1)
                    if mediaBox:
                        # 多媒体
                        divEles=mediaBox.eles("@tag()=div",timeout=0.1)
                        for divEle in divEles:
                            data_testid = divEle.attr('data-testid') or ''  # 安全访问：无此属性时按空串处理
                            if 'ScrollSnap-List' in data_testid:
                                mediaEles=divEle.children(timeout=1)
                                for mediaIndex,mediaItem in enumerate(mediaEles):
                                    mediaUrl=postUrl+'/photo/'+str(mediaIndex+1)
                                    mediaType='img'
                                    videoDuration=''

                                    buttons=mediaItem.eles("@tag()=button",timeout=0.1)
                                    for button in buttons:
                                        label=button.attr('aria-label') or ''  # 安全访问：无此属性时按空串处理
                                        if 'Play this video' in label:
                                            mediaType='video'
                                            # 视频时长：找含 0:32 样式的 span（eles 遍历，ele 单元素不可迭代）
                                            for span in mediaItem.eles("@tag()=span",timeout=0.1):
                                                if re.search(r'\d+:\d+', span.text or ''):
                                                    videoDuration=span.text or ''
                                                    break
                                        elif 'Play' in label:  # 非视频的 Play 按钮 → gif（video 分支已排除，不再覆盖）
                                            mediaType='gif'
                                    mediaData.append({
                                        'mediaUrl': mediaUrl,
                                        'mediaType': mediaType,
                                        'videoDuration': videoDuration
                                    })
                                    if mediaType=='img':
                                        try:
                                            imgBase64=mediaItem.get_screenshot(as_base64='webp',scroll_to_center=True)
                                            append_image_csv(mediaUrl, imgBase64)  # 追加到图片 CSV
                                        except Exception as e:
                                            print('图片',e)
                                break
                        # 单媒体
                        if len(mediaData)==0:
                            mediaUrl=postUrl+'/photo/1'  # 单媒体只有 1 个（mediaIndex 仅存在于多媒体循环，此处未定义）
                            mediaType='gif'
                            videoDuration=''

                            aEles=mediaBox.eles("@tag()=a",timeout=0.1)
                            for aEle in aEles:
                                if mediaUrl in aEle.link:
                                    mediaType='img'
                                    break
                                
                            # 视频时长：找含 0:32 样式的 span（单媒体时从 mediaBox 找，mediaItem 未定义）
                            spans=mediaBox.eles("@tag()=span",timeout=0.1)
                            for span in spans:
                                if ":" in (span.text or ''):
                                    mediaType='video'
                                    videoDuration=span.text or ''
                                    break
                                if videoDuration!='':
                                    break
                                
                            mediaData.append({
                                'mediaUrl': mediaUrl,
                                'mediaType': mediaType,
                                'videoDuration': videoDuration
                            })
                            if mediaType=='img':
                                try:
                                    imgBase64=mediaBox.get_screenshot(as_base64='webp',scroll_to_center=True)
                                    append_image_csv(mediaUrl, imgBase64)  # 追加到图片 CSV
                                except Exception as e:
                                    print('图片',e)

                    # print(mediaData)
                except Exception as e:
                    print(e)

                # 即刻写入 CSV
                CSV_PATH = "output.csv"
                file_exists = os.path.exists(CSV_PATH)
                with open(CSV_PATH, 'a', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['发布者', '发布者昵称', '发布时间', '正文', '正文语言', '提及账号', '外链原始地址', '外链最终地址', '媒体数据', '是否转发', '是否回复', '是否引用', '会话ID', '转发帖ID', '引用帖ID', '回复帖ID', '被回复账号', '引用帖转发数', '点赞数', '回复数', '收藏数', '转发数', '浏览量', '话题标签', '关键词', '链接', '搜索链接', '写入时间'])
                    writer.writerow([fbz, fbzNc, fbsj, zw, lang, mentions, wailian, wailian_final, json.dumps(mediaData, ensure_ascii=False), isRetweet, isReply, isQuote, conversationId, retweetedPostId, quotedPostId, inReplyToPostId, inReplyToUserId, quotePostRetweetCount, dz, hf, sc, zf, ll, ht, keyword, postUrl, task_url, time.strftime('%Y-%m-%d %H:%M:%S')])
                print(f"[{i}] 已写入: {fbz} | {fbsj}")
                
                # 每次写入后随机短暂等待，避免滚动过快被限流
                time.sleep(random.uniform(1, 2))
                # input(123)

                postCount += 1
                if postCount >= MAX_POSTS_PER_LINK:
                    break
                if isCollectReplyPost and task_url==postUrl:
                    break

            tab.scroll(300)

        # 该链接采集不足60条时增加等待，避免请求过快被限流
        # （无结果分支已另行等待过，不重复叠加）
        if postCount < 60 and not noResultFlag:
            time.sleep(random.uniform(20, 30))
    except Exception as e:
        print(f'[{i}] 采集失败，跳过: {e}')
        time.sleep(random.uniform(10, 15))
