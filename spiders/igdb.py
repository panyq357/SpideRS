from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

UTC8 = timezone(timedelta(hours=+8))

PREFIX="IGDB-"

IGDB_COLUMN_URL_DICT = {
    "综合新闻": "http://www.genetics.cas.cn/dtxw/zhxw/",
    "科研进展": "http://www.genetics.cas.cn/dtxw/kyjz/",
    "媒体扫描": "http://www.genetics.cas.cn/dtxw/mtsm/",
    "学者风采": "http://www.genetics.cas.cn/dtxw/xzfc/",
    "学术活动预告": "http://www.genetics.cas.cn/jixs/yg/",
    "学术会议": "http://www.genetics.cas.cn/jixs/xshy/",
    "学术报告": "http://www.genetics.cas.cn/jixs/xsbg/",
    "招聘信息": "http://www.genetics.cas.cn/zp/zpxx/",
    "博士后招聘": "http://www.genetics.cas.cn/zp/bshzp/",
    "通知公告": "http://www.genetics.cas.cn/zp/tzgg/"
}


def main():
    out_dir_path = Path("rss") / Path(__file__).stem
    try:
        out_dir_path.mkdir(parents=True)
    except FileExistsError:
        pass
    for title, url in IGDB_COLUMN_URL_DICT.items():
        rss_str = feed_gen(column_url=url, feed_title=title)
        out_rss_path = out_dir_path / (title + ".rss")
        out_rss_path.write_text(rss_str, encoding="UTF-8")


def extract_artical_list(column_url):
    '''
    Given a IGDB news column URL, return a list.

    The structure of list looks like this:
        [
            (title_str, date_datetime, href_str, contents_str),
            ...
        ]
    '''
    response = urlopen(column_url)
    bs = BeautifulSoup(response, "lxml")
    artical_list = []
    for record in bs.find_all("li", attrs={"class": "row no-gutters py-1"}):
        title_div, date_div = record.find_all("div")
        title = title_div.text.strip()
        date = datetime.strptime(date_div.text, "[%Y.%m.%d]").replace(tzinfo=UTC8)
        href = urljoin(column_url, title_div.a.attrs["href"])
        try:
            contents = extract_artical_contents(href)
        except (HTTPError, URLError):
            contents = f"Unable to get content from <{href}>."
        artical_list.append({"title": title, "date": date, "href": href, "contents": contents})
    return artical_list


def extract_artical_contents(artical_href):
    artical_response = urlopen(artical_href)
    artical_bs = BeautifulSoup(artical_response, "lxml")
    for img in artical_bs.find_all("img"):
        try:
            img.attrs["src"] = urljoin(artical_href, img.attrs["src"])
            img.attrs["oldsrc"] = urljoin(artical_href, img.attrs["oldsrc"])
        except KeyError:
            continue
    contents_str = str(artical_bs.find("div", {"class": "contents"}))
    return contents_str


def feed_gen(column_url, feed_title):
    artical_list = extract_artical_list(column_url)
    fg = FeedGenerator()
    fg.id(column_url)
    fg.title(PREFIX + feed_title)
    fg.link(href='PATHPLACEHOLDER', rel='self' )
    fg.language('zh-CN')
    for artical in artical_list:
        fe = fg.add_entry()
        fe.id(artical["href"])
        fe.title(artical["title"])
        fe.pubDate(artical["date"])
        fe.content(artical["contents"], type="html")
        fe.link(href=artical["href"])
    return fg.atom_str(pretty=True).decode("UTF-8")

if __name__ == "__main__":
    main()
