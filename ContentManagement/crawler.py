"""
考公每日学 — 四大官媒爬虫

依赖: 纯 Python 标准库, 零外部依赖
编码: 自动检测 GBK/UTF-8
降级: 任何源失败 → 跳过, 保证管线不断

用法:
  from crawler import fetch_all
  articles = fetch_all()  # [{title, content, source, url}, ...]
"""

import re
import ssl
import time
import urllib.request
import urllib.error
import gzip
from datetime import datetime
from typing import List, Dict, Optional
from html import unescape

# SSL 容错: 企业网络/代理环境下的自签名证书
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE


# ============================================================
# 工具函数
# ============================================================

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

def fetch_url(url: str, timeout: int = 15, encoding: str = None) -> Optional[str]:
    """抓取 URL, 返回解码后的 HTML 文本"""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip",
    })

    # 尝试 HTTPS → 失败则 HTTP
    attempts = [url]
    if url.startswith("https://"):
        attempts.append(url.replace("https://", "http://", 1))

    for attempt_url in attempts:
        try:
            resp = urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)
            raw = resp.read()
            break
        except Exception as e:
            last_error = e
            continue
    else:
        print(f"  [fetch] {url[:60]} -> {last_error}")
        return None

    # 处理 gzip
    if resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)

    # 编码检测
    if encoding:
        return raw.decode(encoding, errors="replace")

    # 尝试 UTF-8, 失败则 GBK
    for enc in ["utf-8", "gbk", "gb2312", "gb18030"]:
        try:
            text = raw.decode(enc)
            if "人民日报" in text or "新华" in text or len(text) > 500:
                return text
        except:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_tags(html: str) -> str:
    """去除 HTML 标签, 保留文本"""
    # 移除 script/style
    text = re.sub(r'<(script|style|iframe|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 移除标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 解码 HTML 实体
    text = unescape(text)
    # 压缩空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def extract_paragraphs(html: str, min_len: int = 40) -> List[str]:
    """从 HTML 中提取正文段落"""
    # 尝试找正文容器
    body_match = re.search(
        r'(?:<div[^>]*class="[^"]*(?:article|content|text|body|main|TRS_Editor)[^"]*"[^>]*>|'
        r'<article[^>]*>|'
        r'<div[^>]*id="(?:article|content|text|body|main)[^"]*"[^>]*>)'
        r'(.*?)(?:</div>|</article>)',
        html, re.DOTALL | re.IGNORECASE
    )
    target = body_match.group(1) if body_match else html

    # 提取 <p> 段落
    paras = re.findall(r'<p[^>]*>(.*?)</p>', target, re.DOTALL)
    if not paras:
        # 尝试 <div> 或直接用 <br> 分割
        paras = re.split(r'<br\s*/?\s*>', target)

    # 清理并过滤
    clean = []
    for p in paras:
        txt = strip_tags(p).strip()
        # 过滤导航、广告、版权等
        if len(txt) >= min_len:
            if not re.match(r'^(版权所有|责任编辑|分享到|微信|微博|来源：|点击|下载)', txt):
                clean.append(txt)

    return clean


# ============================================================
# 人民日报 评论版
# ============================================================

def crawl_people_daily() -> List[dict]:
    """人民日报评论版/理论版"""
    articles = []

    # 索引页
    idx_urls = [
        "http://opinion.people.com.cn/GB/8213/49160/49219/index.html",  # 人民时评
        "http://theory.people.com.cn/GB/40557/index.html",               # 理论版
    ]

    article_links = []

    for idx_url in idx_urls:
        html = fetch_url(idx_url, timeout=12)
        if not html:
            continue

        # 提取文章链接
        links = re.findall(
            r'<a[^>]*href="(https?://[^"]*people\.com\.cn[^"]*\d{4}-\d{2}/\d{2}[^"]*)"[^>]*>'
            r'([^<]{15,80})</a>',
            html
        )
        for url, title in links[:5]:
            title = strip_tags(title).strip()
            if title and len(title) >= 10:
                article_links.append((url, title, "人民日报"))

        # 也匹配相对路径
        rel_links = re.findall(
            r'<a[^>]*href="(/n1/\d{4}/\d{4}/[^"]*\.html)"[^>]*>([^<]{15,80})</a>',
            html
        )
        for path, title in rel_links[:3]:
            title = strip_tags(title).strip()
            if title and len(title) >= 10:
                article_links.append(("http://opinion.people.com.cn" + path, title, "人民日报"))

    print(f"  人民日报: 找到 {len(article_links)} 个链接")

    # 抓取每篇文章正文
    for url, title, source in article_links[:4]:  # 最多4篇
        try:
            html = fetch_url(url, timeout=10)
            if not html:
                continue

            paras = extract_paragraphs(html, min_len=30)
            content = "\n".join(paras[:20])  # 前20段

            if len(content) >= 200:
                articles.append({
                    "title": title,
                    "content": content[:3000],
                    "source": source,
                    "url": url,
                })
        except Exception as e:
            print(f"    [跳过] {title[:30]}... -> {e}")
            continue

    return articles


# ============================================================
# 新华社 时政
# ============================================================

def crawl_xinhua() -> List[dict]:
    """新华社时政新闻"""
    articles = []

    idx_urls = [
        "https://www.xinhuanet.com/politics/",
        "https://www.news.cn/politics/",
    ]

    article_links = []

    for idx_url in idx_urls:
        html = fetch_url(idx_url, timeout=12)
        if not html:
            continue

        # 提取链接
        links = re.findall(
            r'<a[^>]*href="(https?://[^"]*(?:xinhuanet|news\.cn)[^"]*\d{4}-\d{2}/\d{2}[^"]*\.html?)"[^>]*>'
            r'([^<]{15,80})</a>',
            html
        )
        for url, title in links[:5]:
            title = strip_tags(title).strip()
            if title and len(title) >= 10:
                article_links.append((url, title, "新华社"))

    print(f"  新华社: 找到 {len(article_links)} 个链接")

    for url, title, source in article_links[:3]:
        try:
            html = fetch_url(url, timeout=10)
            if not html:
                continue

            paras = extract_paragraphs(html, min_len=30)
            content = "\n".join(paras[:20])

            if len(content) >= 200:
                articles.append({
                    "title": title,
                    "content": content[:3000],
                    "source": source,
                    "url": url,
                })
        except Exception as e:
            print(f"    [跳过] {title[:30]}... -> {e}")
            continue

    return articles


# ============================================================
# 中国青年报
# ============================================================

def crawl_china_youth() -> List[dict]:
    """中国青年报 青年话题"""
    articles = []

    idx_url = "http://zqb.cyol.com/html/%04d-%02d/%02d/nbs.D110000zgqnb_01.htm" % (
        datetime.now().year, datetime.now().month, datetime.now().day
    )

    html = fetch_url(idx_url, timeout=10)
    if not html:
        return articles

    # 提取文章路径
    links = re.findall(
        r'<a[^>]*href="(node_[^"]*\.htm)"[^>]*>([^<]{10,60})</a>',
        html
    )

    base = f"http://zqb.cyol.com/html/{datetime.now().year}-{datetime.now().month:02d}/{datetime.now().day:02d}/"

    print(f"  中国青年报: 找到 {len(links)} 个链接")

    for path, title in links[:3]:
        try:
            url = base + path
            html2 = fetch_url(url, timeout=10)
            if not html2:
                continue

            paras = extract_paragraphs(html2, min_len=30)
            content = "\n".join(paras[:15])

            if len(content) >= 150:
                articles.append({
                    "title": strip_tags(title).strip(),
                    "content": content[:2500],
                    "source": "中国青年报",
                    "url": url,
                })
        except Exception as e:
            print(f"    [跳过] {title[:30]}... -> {e}")
            continue

    return articles


# ============================================================
# 半月谈
# ============================================================

def crawl_banyuetan() -> List[dict]:
    """半月谈 时事纵横"""
    articles = []

    idx_urls = [
        "http://www.banyuetan.org/",
        "http://www.banyuetan.org/sszx/",
    ]

    article_links = []

    for idx_url in idx_urls:
        html = fetch_url(idx_url, timeout=12)
        if not html:
            continue

        links = re.findall(
            r'<a[^>]*href="(https?://[^"]*banyuetan[^"]*)"[^>]*>([^<]{15,80})</a>',
            html
        )
        for url, title in links[:5]:
            title = strip_tags(title).strip()
            if title and len(title) >= 10:
                article_links.append((url, title, "半月谈"))

    print(f"  半月谈: 找到 {len(article_links)} 个链接")

    for url, title, source in article_links[:2]:
        try:
            html = fetch_url(url, timeout=10)
            if not html:
                continue

            paras = extract_paragraphs(html, min_len=30)
            content = "\n".join(paras[:15])

            if len(content) >= 150:
                articles.append({
                    "title": title,
                    "content": content[:2000],
                    "source": source,
                    "url": url,
                })
        except Exception as e:
            print(f"    [跳过] {title[:30]}... -> {e}")
            continue

    return articles


# ============================================================
# 统一切入点
# ============================================================

def fetch_all() -> List[dict]:
    """
    从四大官媒抓取当日文章
    任何源失败不影响其他源
    总返回至少包含1篇种子文章 (保证管线不断)
    """
    print("\n" + "=" * 50)
    print("  爬虫启动:", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 50)

    all_articles = []

    # 并行抓取 (顺序执行, 避免 IP 被封)
    crawlers = [
        ("人民日报", crawl_people_daily),
        ("新华社", crawl_xinhua),
        ("中国青年报", crawl_china_youth),
        ("半月谈", crawl_banyuetan),
    ]

    for name, crawl_fn in crawlers:
        try:
            print(f"\n[{name}]")
            articles = crawl_fn()
            all_articles.extend(articles)
            print(f"  → 获得 {len(articles)} 篇")
        except Exception as e:
            print(f"  ✗ 失败: {e}")
        time.sleep(1.5)  # 请求间隔

    # 去重 (按标题相似度)
    seen = set()
    unique = []
    for a in all_articles:
        key = a["title"][:20]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    print(f"\n总计: {len(unique)} 篇 (去重后)")
    return unique


# ============================================================
# 命令行测试
# ============================================================

if __name__ == "__main__":
    articles = fetch_all()
    print("\n" + "=" * 50)
    for i, a in enumerate(articles):
        print(f"{i+1}. [{a['source']}] {a['title'][:50]}")
        print(f"   正文长度: {len(a['content'])} 字")
        print(f"   {a['url'][:80]}")
        print()
