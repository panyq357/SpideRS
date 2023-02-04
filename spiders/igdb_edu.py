from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
from urllib.request import urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

UTC8 = timezone(timedelta(hours=+8))

PREFIX = "IGDB-EDU-"

def get_igdb_edu_column_url_dict():
    '''
    "zsxx" page contains a "location.replace()" JavaScript function, which will
    redirect page to another page like "zsxx/ssszs_187556/"
    '''
    base_url = "http://www.genetics.cas.cn/edu/zsxx/"
    base_soup = BeautifulSoup(urlopen(base_url), "lxml")
    redirect_url = re.search(r"location.replace\(\"([^\"]+)\"\)", base_soup.script.get_text()).group(1)
    redirect_url = urljoin(base_url, redirect_url)
    real_zsxx_soup = BeautifulSoup(urlopen(redirect_url), "lxml")
    column_a_tag_list = real_zsxx_soup.find("div", {"class": "menu-cont h16"}).find_all("a")
    IGDB_EDU_COLUMN_URL_DICT = dict()
    for a_tag in column_a_tag_list:
        column_name = a_tag.text
        column_url = urljoin(redirect_url, a_tag.attrs["href"])
        IGDB_EDU_COLUMN_URL_DICT[column_name] = column_url
    return IGDB_EDU_COLUMN_URL_DICT

IGDB_EDU_COLUMN_URL_DICT = get_igdb_edu_column_url_dict()

def main():
    out_dir_path = Path("rss") / Path(__file__).stem
    try:
        out_dir_path.mkdir(parents=True)
    except FileExistsError:
        pass
    for title, url in IGDB_EDU_COLUMN_URL_DICT.items():
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
    for record in bs.find_all("li", attrs={"class": "box-s h16"}):
        title_a = record.find("a", {"class": "box-title"})
        title = title_a.get_text().strip()
        href = urljoin(column_url, title_a.attrs["href"])
        date_span = record.find("span", {"class": "box-date"})
        date = datetime.strptime(date_span.text, "%Y-%m-%d").replace(tzinfo=UTC8)
        try:
            contents = extract_artical_contents(href)
        except (HTTPError, URLError):
            contents = f"Unable to get content from <{href}>."
        artical_list.append({"title": title, "date": date, "href": href, "contents": contents})
    return artical_list


def extract_artical_contents(artical_href, contetnts_class="TRS_Editor"):
    artical_response = urlopen(artical_href)
    artical_bs = BeautifulSoup(artical_response, "lxml")
    for img in artical_bs.find_all("img"):
        try:
            img.attrs["src"] = urljoin(artical_href, img.attrs["src"])
            img.attrs["oldsrc"] = urljoin(artical_href, img.attrs["oldsrc"])
        except KeyError:
            continue
    contents_str = str(artical_bs.find("div", {"class": contetnts_class}))
    # Attachments are generated using JavaScript, so no attachments infomations
    # can be extracted.
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
