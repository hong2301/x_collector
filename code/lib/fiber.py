"""React Fiber 取数：DOM 上拿不到的字段（quote_count、会话 ID、转发来源）。

X 的帖子卡片节点上挂着 React fiber，fiber.memoizedProps 里是接口原始数据。
这里只用「字符串匹配」而不递归遍历对象，避免每个帖子卡住浏览器几秒。

拿不到就返回 None，调用方按空值处理。
"""

import json

_JS = r"""
let keys = Object.keys(this).filter(k => k.startsWith("__react") && k.indexOf("Fiber") >= 0);
if (!keys.length) return "";
let node = this[keys[0]];
let quotes = [], pairs = [], conv = [], inReply = [], rts = [];
let seen = new Set(), guard = 0;
while (node && guard < 50) {
  let p = node.memoizedProps;
  if (p) {
    try {
      let s = JSON.stringify(p);
      let m;
      let reQ = /"quote_count":(\d+)/g;
      while ((m = reQ.exec(s))) quotes.push(+m[1]);
      let reR = /"reply_count":(\d+),"retweet_count":(\d+)/g;
      while ((m = reR.exec(s))) {
        let key = m[1] + '|' + m[2];
        if (!seen.has(key)) { seen.add(key); pairs.push({rp: +m[1], rt: +m[2]}); }
      }
      let reC = /"conversation_id_str":"(\d+)"/g;
      while ((m = reC.exec(s))) conv.push(m[1]);
      let reI = /"in_reply_to_status_id_str":"(\d+)"/g;
      while ((m = reI.exec(s))) inReply.push(m[1]);
      let idx = s.indexOf('"retweeted_status_result"');
      if (idx >= 0) {
        let tail = s.slice(idx, idx + 5000);
        let mm = tail.match(/"rest_id":"(\d+)"/);
        if (mm) rts.push(mm[1]);
      }
    } catch(e) {}
  }
  node = node.return; guard++;
}
let uniq = a => { let s = new Set(), o = []; for (const x of a) { if (!s.has(x)) { s.add(x); o.push(x); } } return o; };
quotes = uniq(quotes); conv = uniq(conv); inReply = uniq(inReply); rts = uniq(rts);
return JSON.stringify({
  quoteCount: quotes.length ? quotes[0] : null,
  conversationId: conv.length ? conv[0] : "",
  inReplyToPostId: inReply.length ? inReply[0] : "",
  retweetedPostId: rts.length ? rts[0] : "",
  replyCount: pairs.length ? pairs[0].rp : null,
  retweetCount: pairs.length ? pairs[0].rt : null
});
"""

EMPTY = {
    "quoteCount": None,
    "conversationId": "",
    "inReplyToPostId": "",
    "retweetedPostId": "",
    "replyCount": None,
    "retweetCount": None,
}

_QUOTE_URL_JS = r"""
let keys = Object.keys(this).filter(k => k.startsWith("__react") && k.indexOf("Fiber") >= 0);
if (!keys.length) return "";
let node = this[keys[0]]; let out = []; let guard = 0;
while (node && guard < 15) {
  let p = node.memoizedProps; let s = p ? JSON.stringify(p) : '';
  if (s) {
    let hits = s.match(/https?:\/\/(?:twitter|x)\.com\/[^"\\]+\/status\/\d+/g);
    if (hits) out.push(hits[0]);
  }
  node = node.return; guard++;
}
return out.join('|');
"""


def extract(post_ele, timeout=3):
    """读取单个帖子的 fiber 字段；失败返回全空。"""
    try:
        raw = post_ele.run_js(_JS, timeout=timeout)
        if not raw:
            return dict(EMPTY)
        data = json.loads(raw)
        return {k: data.get(k, v) for k, v in EMPTY.items()}
    except Exception:
        return dict(EMPTY)


def quote_url(ele, timeout=3):
    """引用卡片对应的被引用帖链接；拿不到返回空串。"""
    try:
        raw = ele.run_js(_QUOTE_URL_JS, timeout=timeout) or ""
    except Exception:
        return ""
    first = raw.split("|")[0] if raw else ""
    return first.replace("https://twitter.com/", "https://x.com/")
