import gzip
import re
import os

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import URLError


dirname = os.path.dirname(__file__)
urlpath = os.path.join(dirname, "urls.txt")
outpath = os.path.join(dirname, "pages")

if not os.path.exists(outpath):
    os.makedirs(outpath)

with open(urlpath, "r") as file:
    urls = file.read().splitlines()
    urls = [url for url in urls if not url.startswith("#")]

for url in urls:
    try:
        req = Request(
            url=url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp = urlopen(req)
        print("Downloaded", url)
    except URLError as e:
        print(f"Failed to download {url} - ", str(e))
        continue

    page_html = gzip.decompress(resp.read()) if resp.headers.get(
        "Content-Encoding") == "gzip" else resp.read()

    page_charset = resp.headers.get_content_charset()
    if page_charset:
        page_html = page_html.decode(page_charset)
    else:
        page_html = page_html.decode("utf-8")

    filename = url.replace("https:", "").replace(
        "http:", "").replace("www.", "")
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename += ".txt"

    with open(os.path.join(outpath, filename), "w") as file:
        file.write(page_html)
