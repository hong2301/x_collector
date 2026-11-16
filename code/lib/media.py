"""媒体采集：图片 / 视频 / GIF 列表，图片截图落盘为 JSON。"""

import json
import os

from . import config, dom

MEDIA_BOX = "@@class=css-g5y9jx r-9aw3ui"


def _media_items(box):
    """多媒体时取 ScrollSnap-List 的子节点；否则整体当一个媒体。"""
    for div in dom.eles(box, "@tag()=div", timeout=0.1):
        if "ScrollSnap-List" in dom.safe_attr(div, "data-testid"):
            children = div.children(timeout=1) or []
            if children:
                return list(children)
    return [box]


def _duration(item):
    """视频时长文本（如 "0:32"）。"""
    for span in dom.eles(item, "@tag()=span", timeout=0.1):
        text = dom.safe_text(span).strip()
        if text and ":" in text and any(c.isdigit() for c in text):
            return text
    return ""


def _kind(item):
    """媒体类型：video / gif / img。"""
    for button in dom.eles(item, "@tag()=button", timeout=0.1):
        label = dom.safe_attr(button, "aria-label")
        if "Play this video" in label:
            return "video"
    if dom.ele(item, '@@data-testid=videoPlayer', timeout=0.05):
        return "video"
    if dom.ele(item, '@@data-testid=tweetPhoto', timeout=0.05):
        return "img"
    for button in dom.eles(item, "@tag()=button", timeout=0.1):
        if "Play" in dom.safe_attr(button, "aria-label"):
            return "gif"
    for a in dom.eles(item, "@tag()=a", timeout=0.05):
        if "/photo/" in dom.safe_link(a):
            return "img"
    return "gif"


def save_image(img_url, b64, images_dir=None):
    """图片截图存为 JSON：文件名 = 帖子 id + 图片序号（如 123_1.json）。"""
    images_dir = images_dir or config.IMAGES_DIR
    import re

    m = re.search(r"/status/(\d+)(?:/photo/(\d+))?", img_url or "")
    if not m:
        return ""
    post_id = m.group(1)
    idx = m.group(2) or "1"
    os.makedirs(images_dir, exist_ok=True)
    path = os.path.join(images_dir, f"{post_id}_{idx}.json")
    payload = {
        "imageUrl": img_url,
        "base64": f"data:image/webp;base64,{b64}",
        "ocr": "",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def collect(post_ele, post_url, images_dir=None, logger=None):
    """采集帖子的媒体列表；images_dir 为 None 时不截图（只记 URL）。"""
    box = dom.ele(post_ele, MEDIA_BOX, timeout=0.1)
    if not box:
        return []
    result = []
    for i, item in enumerate(_media_items(box)):
        media_url = f"{post_url}/photo/{i + 1}"
        kind = _kind(item)
        entry = {
            "mediaUrl": media_url,
            "mediaType": kind,
            "videoDuration": _duration(item) if kind == "video" else "",
        }
        result.append(entry)
        if kind == "img" and images_dir:
            try:
                b64 = item.get_screenshot(as_base64="webp", scroll_to_center=True)
                save_image(media_url, b64, images_dir)
            except Exception as exc:
                if logger:
                    logger.warning("图片截图失败 %s: %r", media_url, exc)
    return result
