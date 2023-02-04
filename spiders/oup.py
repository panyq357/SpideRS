from pathlib import Path

import requests


OUP_URL_DICT = {
    "PC": "https://academic.oup.com/rss/site_6317/advanceAccess_4077.xml"
}

name = "PC"
url = OUP_URL_DICT["PC"]

def main():
    out_dir_path = Path("rss") / Path(__file__).stem
    try:
        out_dir_path.mkdir(parents=True)
    except FileExistsError:
        pass
    for name, url in OUP_URL_DICT.items():
        feed_str = get_oup_feed(feed_url=url)
        out_feed_path = out_dir_path / (name + ".xml")
        out_feed_path.write_text(feed_str, encoding="UTF-8")


def get_oup_feed(feed_url):
    r = requests.get(feed_url, headers={"user-agent": "Mozilla/5.0"})
    r.encoding = "UTF-8"
    return r.text


if __name__ == "__main__":
    main()
